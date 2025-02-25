from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from .models import LostFoundAnnouncement, Announcement
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from notifications.models import Notification
from users.models import User

class AreaNotificationService:
    """Сервис для отправки уведомлений в радиусе"""
    
    def notify_users_in_radius(self, announcement):
        """Отправляет уведомления пользователям в заданном радиусе"""
        if not announcement.latitude or not announcement.longitude:
            return []
            
        center_point = Point(announcement.longitude, announcement.latitude)
        radius_km = announcement.search_radius or 5
        
        # Находим пользователей в радиусе
        nearby_users = User.objects.filter(
            last_location__distance_lte=(center_point, D(km=radius_km))
        ).annotate(
            distance=Distance('last_location', center_point)
        ).order_by('distance')
        
        # Отправляем уведомления
        for user in nearby_users:
            self._send_notification(user, announcement)
            
        return nearby_users
        
    def _send_notification(self, user, announcement):
        """Отправляет уведомление конкретному пользователю"""
        notification_data = {
            'title': _('Потерянный питомец рядом') if announcement.type == 'lost' 
                    else _('Найденный питомец рядом'),
            'body': f"{announcement.announcement.title} в районе {announcement.last_seen_location}",
            'data': {
                'announcement_id': announcement.id,
                'type': announcement.type
            }
        }
        
        # Отправляем через выбранный сервис уведомлений
        try:
            if hasattr(settings, 'PUSH_NOTIFICATIONS_SETTINGS'):
                # Используем push-уведомления если настроены
                device = user.fcm_device
                if device:
                    device.send_message(**notification_data)
            else:
                # Иначе создаем уведомление в базе
                Notification.objects.create(
                    user=user,
                    title=notification_data['title'],
                    message=notification_data['body'],
                    data=notification_data['data']
                )
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")


class LostPetMatchingService:
    """Сервис для поиска совпадений объявлений о потерянных/найденных животных"""
    
    def find_matches(self, announcement):
        """Находит потенциальные совпадения для объявления"""
        # Базовый queryset исключает текущее объявление
        base_queryset = LostFoundAnnouncement.objects.exclude(
            id=announcement.id
        ).select_related('announcement')
        
        # Ищем объявления противоположного типа
        opposite_type = 'found' if announcement.type == 'lost' else 'lost'
        matches = base_queryset.filter(
            type=opposite_type,
            # В пределах 30 дней от даты пропажи/находки
            date_lost_found__range=(
                announcement.date_lost_found - timedelta(days=30),
                announcement.date_lost_found + timedelta(days=30)
            )
        )
        
        if announcement.latitude and announcement.longitude:
            # Если есть координаты, учитываем расстояние
            center_point = Point(announcement.longitude, announcement.latitude)
            matches = matches.filter(
                latitude__isnull=False,
                longitude__isnull=False
            ).annotate(
                distance=Distance('location', center_point)
            ).filter(
                distance__lte=D(km=10)  # В радиусе 10 км
            )
        
        # Считаем релевантность для каждого совпадения
        scored_matches = []
        for match in matches:
            score = self._calculate_match_score(announcement, match)
            if score > 0.3:  # Минимальный порог релевантности
                scored_matches.append({
                    'match': match,
                    'score': score,
                    'reasons': self._get_match_reasons(announcement, match)
                })
        
        # Сортируем по релевантности
        return sorted(scored_matches, key=lambda x: x['score'], reverse=True)
    
    def _calculate_match_score(self, announcement1, announcement2):
        """Вычисляет оценку совпадения двух объявлений"""
        score = 0.0
        
        # Базовые характеристики (50% веса)
        if announcement1.animal_type == announcement2.animal_type:
            score += 0.2
        if announcement1.breed == announcement2.breed:
            score += 0.1
        if announcement1.color == announcement2.color:
            score += 0.1
        if announcement1.size == announcement2.size:
            score += 0.1
            
        # Геолокация (30% веса)
        if announcement1.latitude and announcement1.longitude and \
           announcement2.latitude and announcement2.longitude:
            distance = self._calculate_distance(
                announcement1.latitude, announcement1.longitude,
                announcement2.latitude, announcement2.longitude
            )
            if distance <= 1:  # До 1 км
                score += 0.3
            elif distance <= 5:  # До 5 км
                score += 0.2
            elif distance <= 10:  # До 10 км
                score += 0.1
                
        # Временной промежуток (20% веса)
        time_diff = abs(announcement1.date_lost_found - announcement2.date_lost_found)
        if time_diff.days <= 1:
            score += 0.2
        elif time_diff.days <= 3:
            score += 0.15
        elif time_diff.days <= 7:
            score += 0.1
            
        return score
        
    def _get_match_reasons(self, announcement1, announcement2):
        """Возвращает причины, почему объявления могут совпадать"""
        reasons = []
        
        if announcement1.animal_type == announcement2.animal_type:
            reasons.append(_('Совпадает вид животного'))
        if announcement1.breed == announcement2.breed:
            reasons.append(_('Совпадает порода'))
        if announcement1.color == announcement2.color:
            reasons.append(_('Совпадает окрас'))
        if announcement1.size == announcement2.size:
            reasons.append(_('Совпадает размер'))
            
        # Проверяем расстояние
        if announcement1.latitude and announcement1.longitude and \
           announcement2.latitude and announcement2.longitude:
            distance = self._calculate_distance(
                announcement1.latitude, announcement1.longitude,
                announcement2.latitude, announcement2.longitude
            )
            reasons.append(_(f'Расстояние между точками: {distance:.1f} км'))
            
        # Проверяем временной промежуток
        time_diff = abs(announcement1.date_lost_found - announcement2.date_lost_found)
        reasons.append(_(f'Разница во времени: {time_diff.days} дней'))
        
        return reasons
        
    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        """Вычисляет расстояние между двумя точками в километрах"""
        from math import sin, cos, sqrt, atan2, radians
        
        R = 6371  # Радиус Земли в километрах
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        distance = R * c
        
        return distance 


class LostPetSuggestionService:
    """Сервис для предоставления подсказок по поиску потерянных животных"""
    
    def get_suggestions(self, announcement):
        """Возвращает подсказки для объявления"""
        suggestions = []
        
        # Добавляем популярные места
        suggestions.extend(self._get_popular_places(announcement))
        
        # Добавляем похожие случаи
        suggestions.extend(self._get_similar_cases(announcement))
        
        # Добавляем ветклиники и приюты поблизости
        suggestions.extend(self._get_nearby_facilities(announcement))
        
        return suggestions
        
    def _get_popular_places(self, announcement):
        """Возвращает популярные места для поиска в районе"""
        popular_places = [
            {
                'type': 'park',
                'title': _('Парки и скверы'),
                'description': _('Животные часто прячутся в парках и зеленых зонах'),
                'priority': 'high'
            },
            {
                'type': 'basement',
                'title': _('Подвалы домов'),
                'description': _('Проверьте подвалы ближайших домов'),
                'priority': 'medium'
            },
            {
                'type': 'construction',
                'title': _('Стройки и заброшенные здания'),
                'description': _('Животные могут прятаться на стройках'),
                'priority': 'medium'
            }
        ]
        
        return [{
            'category': 'popular_places',
            'title': _('Популярные места'),
            'items': popular_places
        }]
        
    def _get_similar_cases(self, announcement):
        """Находит похожие случаи и извлекает из них полезную информацию"""
        similar_cases = LostFoundAnnouncement.objects.filter(
            type=announcement.type,
            animal_type=announcement.animal_type,
            announcement__status='closed'  # Только успешные случаи
        ).order_by('-date_lost_found')[:5]
        
        if not similar_cases:
            return []
            
        case_suggestions = []
        for case in similar_cases:
            if case.search_history:
                case_suggestions.append({
                    'type': 'similar_case',
                    'title': case.announcement.title,
                    'description': _('Питомец был найден в районе {}').format(
                        case.last_seen_location
                    ),
                    'search_areas': case.search_history.get('searched_areas', []),
                    'success_factors': case.search_history.get('success_factors', [])
                })
                
        return [{
            'category': 'similar_cases',
            'title': _('Похожие случаи'),
            'items': case_suggestions
        }] if case_suggestions else []
        
    def _get_nearby_facilities(self, announcement):
        """Находит ближайшие ветклиники и приюты"""
        if not announcement.latitude or not announcement.longitude:
            return []
            
        center_point = Point(announcement.longitude, announcement.latitude)
        radius_km = 5  # Радиус поиска учреждений
        
        # Находим ветклиники
        vet_clinics = ServiceAnnouncement.objects.filter(
            service_type='veterinary',
            announcement__status='active',
            location__distance_lte=(center_point, D(km=radius_km))
        ).annotate(
            distance=Distance('location', center_point)
        ).order_by('distance')[:5]
        
        # Находим приюты
        shelters = User.objects.filter(
            is_shelter=True,
            is_active=True,
            last_location__distance_lte=(center_point, D(km=radius_km))
        ).annotate(
            distance=Distance('last_location', center_point)
        ).order_by('distance')[:5]
        
        facilities = []
        
        # Добавляем ветклиники
        for clinic in vet_clinics:
            facilities.append({
                'type': 'vet_clinic',
                'title': clinic.announcement.title,
                'address': clinic.announcement.location,
                'phone': clinic.announcement.contact_phone,
                'distance': round(clinic.distance.km, 1)
            })
            
        # Добавляем приюты
        for shelter in shelters:
            facilities.append({
                'type': 'shelter',
                'title': shelter.profile.organization_name,
                'address': shelter.profile.address,
                'phone': shelter.phone,
                'distance': round(shelter.distance.km, 1)
            })
            
        return [{
            'category': 'nearby_facilities',
            'title': _('Ближайшие учреждения'),
            'items': facilities
        }] if facilities else [] 


class SearchHistoryService:
    """Сервис для отслеживания истории поиска потерянных животных"""
    
    def track_search_activity(self, announcement, search_data):
        """Записывает активность поиска"""
        if not announcement.search_history:
            announcement.search_history = {
                'searched_areas': [],
                'contacted_users': [],
                'timeline': [],
                'success_factors': []
            }
            
        # Добавляем информацию о поисковой активности
        if search_data.get('area'):
            self._track_searched_area(announcement, search_data['area'])
            
        if search_data.get('contacted_user'):
            self._track_contacted_user(announcement, search_data['contacted_user'])
            
        if search_data.get('event'):
            self._track_timeline_event(announcement, search_data['event'])
            
        if search_data.get('success_factor'):
            self._track_success_factor(announcement, search_data['success_factor'])
            
        announcement.save()
        
    def _track_searched_area(self, announcement, area_data):
        """Добавляет информацию о проверенной территории"""
        searched_areas = announcement.search_history['searched_areas']
        
        # Проверяем, не была ли эта область уже проверена
        area_exists = any(
            existing['latitude'] == area_data['latitude'] and
            existing['longitude'] == area_data['longitude']
            for existing in searched_areas
        )
        
        if not area_exists:
            searched_areas.append({
                'latitude': area_data['latitude'],
                'longitude': area_data['longitude'],
                'radius': area_data.get('radius', 0.5),  # радиус в км
                'date_searched': timezone.now().isoformat(),
                'description': area_data.get('description', ''),
                'found_traces': area_data.get('found_traces', False)
            })
            
    def _track_contacted_user(self, announcement, user_data):
        """Добавляет информацию о контакте с пользователем"""
        contacted_users = announcement.search_history['contacted_users']
        
        # Проверяем, не связывались ли мы уже с этим пользователем
        if user_data['user_id'] not in [u['user_id'] for u in contacted_users]:
            contacted_users.append({
                'user_id': user_data['user_id'],
                'date_contacted': timezone.now().isoformat(),
                'contact_type': user_data.get('contact_type', 'message'),
                'response_received': user_data.get('response_received', False),
                'useful_info': user_data.get('useful_info', False)
            })
            
    def _track_timeline_event(self, announcement, event_data):
        """Добавляет событие в таймлайн поиска"""
        timeline = announcement.search_history['timeline']
        
        timeline.append({
            'date': timezone.now().isoformat(),
            'event_type': event_data['type'],
            'description': event_data['description'],
            'location': event_data.get('location'),
            'importance': event_data.get('importance', 'normal')
        })
        
    def _track_success_factor(self, announcement, factor_data):
        """Добавляет фактор, который помог в поиске"""
        success_factors = announcement.search_history['success_factors']
        
        success_factors.append({
            'factor_type': factor_data['type'],
            'description': factor_data['description'],
            'effectiveness': factor_data.get('effectiveness', 'medium')
        })
        
    def get_search_statistics(self, announcement):
        """Возвращает статистику по поиску"""
        if not announcement.search_history:
            return None
            
        history = announcement.search_history
        
        return {
            'total_areas_searched': len(history['searched_areas']),
            'total_users_contacted': len(history['contacted_users']),
            'timeline_events': len(history['timeline']),
            'success_factors': len(history['success_factors']),
            'search_duration': self._calculate_search_duration(announcement),
            'most_effective_methods': self._get_most_effective_methods(history),
            'coverage_map': self._generate_coverage_map(history['searched_areas'])
        }
        
    def _calculate_search_duration(self, announcement):
        """Вычисляет продолжительность поиска"""
        if not announcement.search_history['timeline']:
            return None
            
        first_event = min(
            timezone.parse_datetime(event['date'])
            for event in announcement.search_history['timeline']
        )
        last_event = max(
            timezone.parse_datetime(event['date'])
            for event in announcement.search_history['timeline']
        )
        
        return (last_event - first_event).days
        
    def _get_most_effective_methods(self, history):
        """Определяет наиболее эффективные методы поиска"""
        if not history['success_factors']:
            return []
            
        # Группируем факторы по типу и подсчитываем их эффективность
        methods = {}
        for factor in history['success_factors']:
            method_type = factor['factor_type']
            effectiveness = {
                'high': 3,
                'medium': 2,
                'low': 1
            }.get(factor['effectiveness'], 0)
            
            if method_type not in methods:
                methods[method_type] = {
                    'total_score': 0,
                    'count': 0
                }
                
            methods[method_type]['total_score'] += effectiveness
            methods[method_type]['count'] += 1
            
        # Вычисляем средний балл для каждого метода
        return sorted([
            {
                'type': method_type,
                'average_score': data['total_score'] / data['count']
            }
            for method_type, data in methods.items()
        ], key=lambda x: x['average_score'], reverse=True)
        
    def _generate_coverage_map(self, searched_areas):
        """Генерирует карту покрытия поиска"""
        if not searched_areas:
            return None
            
        # Находим границы области поиска
        latitudes = [area['latitude'] for area in searched_areas]
        longitudes = [area['longitude'] for area in searched_areas]
        
        return {
            'center': {
                'latitude': sum(latitudes) / len(latitudes),
                'longitude': sum(longitudes) / len(longitudes)
            },
            'bounds': {
                'north': max(latitudes),
                'south': min(latitudes),
                'east': max(longitudes),
                'west': min(longitudes)
            },
            'searched_points': [
                {
                    'latitude': area['latitude'],
                    'longitude': area['longitude'],
                    'radius': area['radius'],
                    'date': area['date_searched']
                }
                for area in searched_areas
            ]
        } 

class NotificationService:
    """Сервис для работы с уведомлениями"""
    
    @staticmethod
    def notify_users_in_radius(announcement, radius_km: int) -> int:
        """
        Отправка уведомлений пользователям в заданном радиусе
        Возвращает количество уведомленных пользователей
        """
        # Создаем точку из координат объявления
        center_point = Point(
            float(announcement.longitude),
            float(announcement.latitude)
        )
        
        # Получаем пользователей в радиусе
        nearby_users = User.objects.filter(
            is_active=True,
            location__distance_lte=(center_point, D(km=radius_km))
        ).annotate(
            distance=Distance('location', center_point)
        ).exclude(
            id=announcement.author.id  # Исключаем автора объявления
        )
        
        # Создаем уведомления
        notifications = []
        for user in nearby_users:
            notification = Notification(
                recipient=user,
                actor=announcement.author,
                verb='lost_pet',
                action_object=announcement,
                description=_(
                    'В радиусе {distance:.1f} км от вас пропало животное: {pet_type} {breed}'
                ).format(
                    distance=user.distance.km,
                    pet_type=announcement.get_pet_type_display(),
                    breed=announcement.breed
                )
            )
            notifications.append(notification)
        
        # Сохраняем уведомления пакетом
        with transaction.atomic():
            Notification.objects.bulk_create(notifications)
        
        # Отправляем WebSocket уведомления
        channel_layer = get_channel_layer()
        for notification in notifications:
            async_to_sync(channel_layer.group_send)(
                f"notifications_{notification.recipient.id}",
                {
                    "type": "notification.message",
                    "message": {
                        "type": "lost_pet",
                        "announcement_id": announcement.id,
                        "title": _("Пропало животное поблизости"),
                        "message": notification.description,
                        "url": announcement.get_absolute_url()
                    }
                }
            )
        
        return len(notifications)

    @staticmethod
    def send_match_notification(announcement, similar_announcement):
        """Отправка уведомления о возможном совпадении"""
        notification = Notification.objects.create(
            recipient=announcement.author,
            actor=similar_announcement.author,
            verb='potential_match',
            action_object=similar_announcement,
            description=_(
                'Найдено возможное совпадение с вашим объявлением о пропаже: {pet_type} {breed}'
            ).format(
                pet_type=similar_announcement.get_pet_type_display(),
                breed=similar_announcement.breed
            )
        )
        
        # Отправляем WebSocket уведомление
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"notifications_{notification.recipient.id}",
            {
                "type": "notification.message",
                "message": {
                    "type": "potential_match",
                    "announcement_id": similar_announcement.id,
                    "title": _("Найдено возможное совпадение"),
                    "message": notification.description,
                    "url": similar_announcement.get_absolute_url()
                }
            }
        )
        
        return notification 