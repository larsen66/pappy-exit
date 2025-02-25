from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('Пользователь')
    )
    bio = models.TextField(_('О себе'), blank=True)
    location = models.CharField(_('Местоположение'), max_length=200, blank=True)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)

    class Meta:
        verbose_name = _('Профиль пользователя')
        verbose_name_plural = _('Профили пользователей')

    def __str__(self):
        return f'Профиль пользователя {self.user.phone}'

class SellerProfile(models.Model):
    SELLER_TYPE_CHOICES = [
        ('individual', _('Частное лицо')),
        ('entrepreneur', _('ИП')),
        ('company', _('Компания')),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='seller_profile',
        verbose_name=_('Пользователь')
    )
    seller_type = models.CharField(
        _('Тип продавца'),
        max_length=20,
        choices=SELLER_TYPE_CHOICES,
        default='individual'
    )
    company_name = models.CharField(_('Название компании'), max_length=200, blank=True)
    inn = models.CharField(_('ИНН'), max_length=12, blank=True)
    description = models.TextField(_('Описание'), blank=True)
    website = models.URLField(_('Веб-сайт'), blank=True)
    is_verified = models.BooleanField(_('Верифицирован'), default=False)
    rating = models.DecimalField(
        _('Рейтинг'),
        max_digits=3,
        decimal_places=2,
        default=0
    )
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)

    class Meta:
        verbose_name = _('Профиль продавца')
        verbose_name_plural = _('Профили продавцов')

    def __str__(self):
        return f'Профиль продавца {self.user.phone}'

class SpecialistProfile(models.Model):
    SPECIALIZATION_CHOICES = [
        ('veterinarian', _('Ветеринар')),
        ('groomer', _('Грумер')),
        ('trainer', _('Кинолог')),
        ('handler', _('Хендлер')),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='specialist_profile',
        verbose_name=_('Пользователь')
    )
    specialization = models.CharField(
        _('Специализация'),
        max_length=20,
        choices=SPECIALIZATION_CHOICES
    )
    experience_years = models.PositiveIntegerField(_('Опыт работы (лет)'))
    services = models.TextField(_('Услуги'))
    price_range = models.CharField(_('Ценовой диапазон'), max_length=100)
    certificates = models.JSONField(_('Сертификаты'), null=True, blank=True)
    is_verified = models.BooleanField(_('Верифицирован'), default=False)
    rating = models.DecimalField(
        _('Рейтинг'),
        max_digits=3,
        decimal_places=2,
        default=0
    )
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)

    class Meta:
        verbose_name = _('Профиль специалиста')
        verbose_name_plural = _('Профили специалистов')

    def __str__(self):
        return f'Профиль специалиста {self.user.phone}'

class VerificationDocument(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='verification_documents',
        verbose_name=_('Пользователь')
    )
    document = models.FileField(
        _('Документ'),
        upload_to='verification_documents/%Y/%m/%d/'
    )
    uploaded_at = models.DateTimeField(_('Дата загрузки'), auto_now_add=True)
    is_verified = models.BooleanField(_('Проверен'), default=False)
    comment = models.TextField(_('Комментарий'), blank=True)

    class Meta:
        verbose_name = _('Документ верификации')
        verbose_name_plural = _('Документы верификации')
        ordering = ['-uploaded_at']

    def __str__(self):
        return f'Документ верификации {self.user.phone}'

class Review(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews_written',
        verbose_name=_('Автор')
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='seller_reviews',
        verbose_name=_('Продавец'),
        null=True,
        blank=True
    )
    specialist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='specialist_reviews',
        verbose_name=_('Специалист'),
        null=True,
        blank=True
    )
    rating = models.PositiveSmallIntegerField(
        _('Оценка'),
        choices=[(i, str(i)) for i in range(1, 6)]
    )
    comment = models.TextField(_('Комментарий'))
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)

    class Meta:
        verbose_name = _('Отзыв')
        verbose_name_plural = _('Отзывы')
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(seller__isnull=False, specialist__isnull=True) |
                    models.Q(seller__isnull=True, specialist__isnull=False)
                ),
                name='review_target_mutual_exclusivity'
            )
        ]

    def __str__(self):
        return f'Отзыв от {self.author.phone}'

    def clean(self):
        if self.seller and self.specialist:
            raise ValidationError(_('Отзыв должен быть либо о продавце, либо о специалисте'))
        if not self.seller and not self.specialist:
            raise ValidationError(_('Отзыв должен быть о продавце или специалисте'))
        if self.author == self.seller or self.author == self.specialist:
            raise ValidationError(_('Нельзя оставить отзыв о себе'))

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        # Обновляем рейтинг продавца или специалиста
        target = self.seller or self.specialist
        if target:
            reviews = Review.objects.filter(
                models.Q(seller=target) | models.Q(specialist=target)
            )
            avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
            if target.is_seller:
                target.seller_profile.rating = avg_rating
                target.seller_profile.save()
            if target.is_specialist:
                target.specialist_profile.rating = avg_rating
                target.specialist_profile.save() 