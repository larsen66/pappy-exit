from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

class VIPSubscription(models.Model):
    LEVEL_CHOICES = [
        ('basic', 'Базовый'),
        ('premium', 'Премиум'),
        ('elite', 'Элитный'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vip_subscriptions',
        verbose_name=_('пользователь')
    )
    level = models.CharField(
        _('уровень'),
        max_length=20,
        choices=LEVEL_CHOICES
    )
    starts_at = models.DateTimeField(_('начало подписки'), auto_now_add=True)
    expires_at = models.DateTimeField(_('окончание подписки'))
    auto_renew = models.BooleanField(_('автопродление'), default=False)
    is_active = models.BooleanField(_('активна'), default=True)
    payment_id = models.CharField(_('ID платежа'), max_length=100, blank=True)
    
    class Meta:
        verbose_name = _('VIP подписка')
        verbose_name_plural = _('VIP подписки')
        ordering = ['-starts_at']

    def __str__(self):
        return f"{self.user} - {self.get_level_display()}"

    def extend_subscription(self, days: int) -> None:
        """Продление подписки"""
        if self.expires_at > timezone.now():
            self.expires_at += timedelta(days=days)
        else:
            self.expires_at = timezone.now() + timedelta(days=days)
        self.is_active = True
        self.save()

    def cancel_subscription(self) -> bool:
        """Отмена автопродления"""
        self.auto_renew = False
        self.save()
        return True

    @property
    def is_expired(self) -> bool:
        """Проверка истечения срока подписки"""
        return timezone.now() > self.expires_at

class VIPFeature(models.Model):
    """Модель для хранения доступных VIP функций"""
    name = models.CharField(_('название'), max_length=100)
    description = models.TextField(_('описание'))
    subscription_level = models.CharField(
        _('уровень подписки'),
        max_length=20,
        choices=VIPSubscription.LEVEL_CHOICES
    )
    is_active = models.BooleanField(_('активна'), default=True)

    class Meta:
        verbose_name = _('VIP функция')
        verbose_name_plural = _('VIP функции')

    def __str__(self):
        return f"{self.name} ({self.get_subscription_level_display()})" 