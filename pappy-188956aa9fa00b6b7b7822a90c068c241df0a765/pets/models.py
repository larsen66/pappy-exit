from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from announcements.models import Announcement
from chat.models import Dialog
from django.conf import settings
from django.utils import timezone
from django.db.models import Q

User = get_user_model()

class SwipeAction(models.Model):
    """Модель для хранения действий свайпа (лайк/дизлайк)"""
    LIKE = 'like'
    DISLIKE = 'dislike'
    DIRECTION_CHOICES = [
        (LIKE, 'Лайк'),
        (DISLIKE, 'Дизлайк'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='pets_swipes',
        verbose_name=_('Пользователь')
    )
    announcement = models.ForeignKey(
        'announcements.Announcement',
        on_delete=models.CASCADE,
        related_name='pets_swipes',
        verbose_name=_('Объявление')
    )
    direction = models.CharField(
        max_length=10,
        choices=DIRECTION_CHOICES,
        verbose_name=_('Направление')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )

    class Meta:
        app_label = 'pets'
        verbose_name = _('Действие свайпа')
        verbose_name_plural = _('Действия свайпов')
        ordering = ['-created_at']
        unique_together = ['user', 'announcement']

    def __str__(self):
        return f"{self.user} {self.get_direction_display()} {self.announcement}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new and self.direction == self.LIKE:
            # Проверяем взаимный лайк
            mutual_like = SwipeAction.objects.filter(
                user=self.announcement.author,
                announcement__author=self.user,
                direction=self.LIKE
            ).first()
            
            if mutual_like:
                # Создаем пару
                Match.objects.create(
                    user1=self.user,
                    user2=self.announcement.author,
                    announcement1=mutual_like.announcement,
                    announcement2=self.announcement
                )
            
            # В любом случае создаем диалог
            Dialog.objects.get_or_create(
                announcement=self.announcement,
                user=self.user
            )

class SwipeHistory(models.Model):
    """История просмотров для возможности возврата к предыдущей карточке"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='pets_swipe_history',
        verbose_name=_('Пользователь')
    )
    announcement = models.ForeignKey(
        'announcements.Announcement',
        on_delete=models.CASCADE,
        related_name='pets_view_history',
        verbose_name=_('Объявление')
    )
    viewed_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=_('Дата просмотра')
    )
    is_returned = models.BooleanField(
        default=False,
        verbose_name=_('Было возвращение')
    )

    class Meta:
        app_label = 'pets'
        verbose_name = _('История свайпов')
        verbose_name_plural = _('История свайпов')
        ordering = ['-viewed_at']
        unique_together = ['user', 'announcement']

    def __str__(self):
        return f"{self.user} просмотрел {self.announcement}"

class Match(models.Model):
    """Модель для хранения совпадений (взаимных лайков)"""
    user1 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='matches_as_user1',
        verbose_name=_('Пользователь 1')
    )
    user2 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='matches_as_user2',
        verbose_name=_('Пользователь 2')
    )
    announcement1 = models.ForeignKey(
        Announcement,
        on_delete=models.CASCADE,
        related_name='matches_as_first',
        verbose_name=_('Объявление 1')
    )
    announcement2 = models.ForeignKey(
        Announcement,
        on_delete=models.CASCADE,
        related_name='matches_as_second',
        verbose_name=_('Объявление 2')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Активно')
    )
    is_breeding_match = models.BooleanField(
        default=False,
        verbose_name=_('Совпадение для вязки')
    )
    compatibility_score = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_('Оценка совместимости')
    )

    class Meta:
        app_label = 'pets'
        verbose_name = _('Совпадение')
        verbose_name_plural = _('Совпадения')
        ordering = ['-created_at']

    def __str__(self):
        return f"Совпадение между {self.user1} и {self.user2}"

    def check_compatibility(self):
        """Проверка совместимости животных для вязки"""
        if not self.is_breeding_match:
            return None
            
        pet1 = self.announcement1.animal_details
        pet2 = self.announcement2.animal_details
        
        if not (pet1 and pet2):
            return 0.0
            
        score = 0.0
        # Базовая совместимость
        if pet1.species == pet2.species:
            score += 0.5
            if pet1.breed == pet2.breed:
                score += 0.3
        
        # Проверка возраста
        if pet1.age and pet2.age:
            age_diff = abs(pet1.age - pet2.age)
            if age_diff <= 2:
                score += 0.2
                
        return min(score, 1.0) 