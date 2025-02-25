from django.utils import timezone
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from .models import ModerationAction, UserWarning, UserBan, ModerationQueue

class ModerationService:
    """Сервис для работы с модерацией"""
    
    @staticmethod
    def add_to_queue(obj) -> ModerationQueue:
        """Добавление объекта в очередь модерации"""
        content_type = ContentType.objects.get_for_model(obj)
        
        queue_item = ModerationQueue.objects.create(
            content_type=content_type,
            object_id=obj.id
        )
        return queue_item

    @staticmethod
    def process_item(queue_item: ModerationQueue, moderator, action: str, reason: str = None) -> bool:
        """Обработка элемента очереди модерации"""
        with transaction.atomic():
            # Создаем запись о действии модерации
            ModerationAction.objects.create(
                content_type=queue_item.content_type,
                object_id=queue_item.object_id,
                moderator=moderator,
                action=action,
                reason=reason or ''
            )
            
            # Обновляем статус в очереди
            queue_item.status = 'approved' if action == 'approve' else 'rejected'
            queue_item.moderator = moderator
            queue_item.comment = reason
            queue_item.save()
            
            return True

    @staticmethod
    def warn_user(user, moderator, reason: str) -> UserWarning:
        """Выдача предупреждения пользователю"""
        warning = UserWarning.objects.create(
            user=user,
            moderator=moderator,
            reason=reason
        )
        
        # Проверяем количество активных предупреждений
        active_warnings = UserWarning.objects.filter(
            user=user,
            is_active=True
        ).count()
        
        # Если больше 3 предупреждений - баним на неделю
        if active_warnings >= 3:
            ModerationService.ban_user(
                user=user,
                moderator=moderator,
                duration_days=7,
                reason="Превышено количество предупреждений"
            )
        
        return warning

    @staticmethod
    def ban_user(user, moderator, duration_days: int = None, reason: str = None, permanent: bool = False) -> UserBan:
        """Бан пользователя"""
        expires_at = None if permanent else timezone.now() + timezone.timedelta(days=duration_days)
        
        ban = UserBan.objects.create(
            user=user,
            moderator=moderator,
            reason=reason,
            expires_at=expires_at,
            is_permanent=permanent
        )
        return ban

    @staticmethod
    def check_ban_status(user) -> bool:
        """Проверка статуса бана пользователя"""
        active_ban = UserBan.objects.filter(
            user=user,
            expires_at__gt=timezone.now()
        ).first()
        
        return bool(active_ban)

    @staticmethod
    def get_pending_items(content_type=None) -> list:
        """Получение списка элементов на модерацию"""
        queryset = ModerationQueue.objects.filter(status='pending')
        if content_type:
            queryset = queryset.filter(content_type=content_type)
        return list(queryset)

class AutoModerationService:
    """Сервис для автоматической модерации"""
    
    @staticmethod
    def check_announcement(announcement) -> dict:
        """Автоматическая проверка объявления"""
        results = {
            'passed': True,
            'issues': []
        }
        
        # TODO: Implement checks for:
        # - Запрещенные слова
        # - Спам-признаки
        # - Проверка изображений
        # - Проверка цен
        # - и т.д.
        
        return results

    @staticmethod
    def process_appeal(queue_item: ModerationQueue, appeal_text: str) -> bool:
        """Обработка апелляции"""
        if queue_item.status != 'rejected':
            return False
            
        # Возвращаем объект в очередь модерации
        queue_item.status = 'pending'
        queue_item.comment += f"\n\nАпелляция: {appeal_text}"
        queue_item.save()
        
        return True 