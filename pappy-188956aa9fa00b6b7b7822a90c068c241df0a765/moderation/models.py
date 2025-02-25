from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class ModerationAction(models.Model):
    """Модель для хранения действий модерации"""
    ACTION_CHOICES = [
        ('approve', 'Одобрено'),
        ('reject', 'Отклонено'),
        ('block', 'Заблокировано'),
        ('warn', 'Предупреждение'),
    ]

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    moderator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='moderation_actions',
        verbose_name=_('модератор')
    )
    action = models.CharField(_('действие'), max_length=20, choices=ACTION_CHOICES)
    reason = models.TextField(_('причина'))
    created_at = models.DateTimeField(_('создано'), auto_now_add=True)

    class Meta:
        verbose_name = _('действие модерации')
        verbose_name_plural = _('действия модерации')
        ordering = ['-created_at']

class UserWarning(models.Model):
    """Модель для хранения предупреждений пользователей"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='warnings',
        verbose_name=_('пользователь')
    )
    moderator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='given_warnings',
        verbose_name=_('модератор')
    )
    reason = models.TextField(_('причина'))
    created_at = models.DateTimeField(_('создано'), auto_now_add=True)
    is_active = models.BooleanField(_('активно'), default=True)

    class Meta:
        verbose_name = _('предупреждение')
        verbose_name_plural = _('предупреждения')
        ordering = ['-created_at']

class UserBan(models.Model):
    """Модель для хранения банов пользователей"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bans',
        verbose_name=_('пользователь')
    )
    moderator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='given_bans',
        verbose_name=_('модератор')
    )
    reason = models.TextField(_('причина'))
    starts_at = models.DateTimeField(_('начало бана'), auto_now_add=True)
    expires_at = models.DateTimeField(_('окончание бана'))
    is_permanent = models.BooleanField(_('перманентный'), default=False)

    class Meta:
        verbose_name = _('бан')
        verbose_name_plural = _('баны')
        ordering = ['-starts_at']

    @property
    def is_active(self) -> bool:
        """Проверка активности бана"""
        return self.is_permanent or timezone.now() < self.expires_at

class ModerationQueue(models.Model):
    """Модель очереди модерации"""
    STATUS_CHOICES = [
        ('pending', 'На рассмотрении'),
        ('approved', 'Одобрено'),
        ('rejected', 'Отклонено'),
    ]

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    status = models.CharField(_('статус'), max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(_('создано'), auto_now_add=True)
    updated_at = models.DateTimeField(_('обновлено'), auto_now=True)
    moderator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='moderated_items',
        verbose_name=_('модератор')
    )
    comment = models.TextField(_('комментарий'), blank=True)

    class Meta:
        verbose_name = _('элемент очереди модерации')
        verbose_name_plural = _('очередь модерации')
        ordering = ['created_at']

    def __str__(self):
        return f"{self.content_type} - {self.object_id} ({self.get_status_display()})" 