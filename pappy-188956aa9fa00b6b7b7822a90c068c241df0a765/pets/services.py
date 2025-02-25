from typing import List
from django.db.models import Q, Exists, OuterRef
from django.contrib.auth import get_user_model
from announcements.models import Announcement
from .models import SwipeAction, Match

User = get_user_model()

class SwipeSystem:
    def get_next_cards(self, user_id: int, count: int = 10) -> List[Announcement]:
        """Получение следующих карточек для показа"""
        # Получаем текущего пользователя
        user = User.objects.get(id=user_id)
        
        # Получаем все объявления, которые пользователь еще не свайпал
        viewed_announcements = SwipeAction.objects.filter(
            user=user,
            announcement=OuterRef('pk')
        )
        
        available_announcements = Announcement.objects.filter(
            status='active',
            type='animal'
        ).exclude(
            author=user  # Исключаем собственные объявления
        ).exclude(
            Exists(viewed_announcements)  # Исключаем уже просмотренные
        ).order_by('?')  # Случайный порядок
        
        return list(available_announcements[:count])

    def process_swipe(self, user_id: int, announcement_id: int, direction: str) -> bool:
        """Обработка свайпа"""
        user = User.objects.get(id=user_id)
        announcement = Announcement.objects.get(id=announcement_id)
        
        # Создаем запись о свайпе
        SwipeAction.objects.create(
            user=user,
            announcement=announcement,
            direction=direction.upper()
        )
        
        # Если это лайк, проверяем на взаимность
        if direction.upper() == 'LIKE':
            # Проверяем, есть ли встречный лайк
            reverse_like = SwipeAction.objects.filter(
                user=announcement.author,
                announcement__author=user,
                direction='LIKE'
            ).first()
            
            if reverse_like:
                # Создаем матч
                Match.objects.create(
                    user1=user,
                    user2=announcement.author,
                    announcement1=announcement,
                    announcement2=reverse_like.announcement
                )
                return True
        
        return False

    def get_matches(self, user_id: int) -> List[Match]:
        """Получение списка совпадений"""
        user = User.objects.get(id=user_id)
        return Match.objects.filter(
            Q(user1=user) | Q(user2=user),
            is_active=True
        ).order_by('-created_at') 