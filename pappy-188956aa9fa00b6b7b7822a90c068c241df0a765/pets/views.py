from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Exists, OuterRef, F, Count
from django.core.paginator import Paginator
from announcements.models import Announcement
from .models import SwipeAction, SwipeHistory, Match
import json

class SwipeSystem:
    @staticmethod
    def get_next_cards(user, announcement_type='animals', count=10):
        """Получение следующих карточек для показа"""
        already_swiped = SwipeAction.objects.filter(
            user=user,
            announcement=OuterRef('pk')
        )
        
        # Базовый запрос
        announcements = Announcement.objects.filter(
            status='active',
            type=announcement_type
        ).exclude(
            author=user
        ).exclude(
            Exists(already_swiped)
        )
        
        # Приоритизация объявлений
        if announcement_type == 'animals':
            announcements = announcements.annotate(
                premium_score=Count('pets_swipes'),  # Популярность
                distance_score=F('price')  # Временно используем цену как score
            ).order_by(
                '-is_premium',  # Сначала премиум
                '-premium_score',  # Затем по популярности
                '?'  # Случайный порядок для остальных
            )[:count]
        
        return announcements

    @staticmethod
    def process_swipe(user, announcement_id, direction):
        """Обработка свайпа"""
        announcement = get_object_or_404(Announcement, id=announcement_id, status='active')
        
        swipe = SwipeAction.objects.create(
            user=user,
            announcement=announcement,
            direction=direction
        )
        
        # Проверяем необходимость создания пары для вязки
        if direction == SwipeAction.LIKE and announcement.type == 'animals':
            mutual_like = SwipeAction.objects.filter(
                user=announcement.author,
                announcement__author=user,
                announcement__type='animals',
                direction=SwipeAction.LIKE
            ).first()
            
            if mutual_like:
                match = Match.objects.create(
                    user1=user,
                    user2=announcement.author,
                    announcement1=mutual_like.announcement,
                    announcement2=announcement,
                    is_breeding_match=True
                )
                # Рассчитываем совместимость
                match.compatibility_score = match.check_compatibility()
                match.save()
        
        return swipe

@login_required
def swipe_view(request):
    """Отображение карточек для свайпа"""
    announcement_type = request.GET.get('type', 'animals')
    
    # Используем SwipeSystem для получения карточек
    announcements = SwipeSystem.get_next_cards(request.user, announcement_type, count=1)
    announcement = announcements.first() if announcements else None
    
    if announcement:
        # Записываем в историю просмотров
        SwipeHistory.objects.create(
            user=request.user,
            announcement=announcement
        )

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'has_cards': bool(announcement)
        })

    return render(request, 'pets/swipe.html', {
        'announcement': announcement,
        'announcement_type': announcement_type
    })

@login_required
@require_http_methods(["POST"])
def process_swipe(request):
    """Обработка свайпа"""
    try:
        data = json.loads(request.body)
        announcement_id = data.get('announcement_id')
        direction = data.get('direction')
        
        if not announcement_id or direction not in [SwipeAction.LIKE, SwipeAction.DISLIKE]:
            return JsonResponse({'error': 'Invalid parameters'}, status=400)
        
        swipe = SwipeSystem.process_swipe(request.user, announcement_id, direction)
        response_data = {'success': True}
        
        # Если это лайк, добавляем URL для чата
        if direction == SwipeAction.LIKE:
            response_data.update({
                'chat_url': f'/chat/{swipe.announcement.id}/',
                'message': 'Вы увидите свой лайк в «Сообщениях»'
            })
            
        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@require_http_methods(["POST"])
def undo_last_swipe(request):
    """Отмена последнего свайпа"""
    try:
        # Получаем последнюю запись из истории просмотров
        last_history = SwipeHistory.objects.filter(
            user=request.user,
            is_returned=False
        ).order_by('-viewed_at').first()

        if last_history:
            # Удаляем последний свайп, если он есть
            SwipeAction.objects.filter(
                user=request.user,
                announcement=last_history.announcement
            ).delete()
            
            # Помечаем запись как возвращенную
            last_history.is_returned = True
            last_history.save()
            
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'error': 'No history found'}, status=404)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def get_next_cards(request):
    """Получение следующих карточек"""
    announcement_type = request.GET.get('type', 'animals')
    page = int(request.GET.get('page', 1))
    
    # Используем SwipeSystem для получения карточек
    announcements = SwipeSystem.get_next_cards(request.user, announcement_type)
    
    paginator = Paginator(announcements, 10)
    cards = paginator.get_page(page)
    
    return JsonResponse({
        'success': True,
        'has_more': cards.has_next(),
        'cards': [{
            'id': card.id,
            'title': card.title,
            'price': str(card.price),
            'old_price': str(card.old_price) if card.old_price else None,
            'images': [img.image.url for img in card.images.all()],
            'organization': {
                'name': card.user.organization_name,
                'rating': card.user.rating,
                'review_count': card.user.review_count
            },
            'details': {
                'species': card.pet.species,
                'breed': card.pet.breed,
                'age': card.pet.age,
                'gender': card.pet.gender
            } if announcement_type == 'animals' else {
                'type': card.specialist_type,
                'experience': card.experience
            }
        } for card in cards]
    })

@login_required
def matches_view(request):
    """Страница с совпадениями и лайками"""
    # Получаем активные совпадения для вязки
    breeding_matches = Match.objects.filter(
        Q(user1=request.user) | Q(user2=request.user),
        is_active=True,
        is_breeding_match=True
    ).select_related(
        'announcement1',
        'announcement2',
        'user1',
        'user2'
    ).order_by('-compatibility_score', '-created_at')
    
    # Получаем обычные лайки
    likes = SwipeAction.objects.filter(
        user=request.user,
        direction=SwipeAction.LIKE,
        announcement__type__in=['animal', 'specialist']
    ).select_related(
        'announcement',
        'announcement__author'
    ).order_by('-created_at')
    
    return render(request, 'pets/matches.html', {
        'breeding_matches': breeding_matches,
        'likes': likes
    }) 