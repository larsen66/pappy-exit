from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.crypto import get_random_string
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.core.validators import RegexValidator

class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError('The Phone field must be set')
        location = extra_fields.pop('location', None)
        user = self.model(phone=phone, **extra_fields)
        if location:
            user.location = location
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(phone, password, **extra_fields)

class User(AbstractUser):
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Номер телефона должен быть в формате: '+999999999'. До 15 цифр."
    )
    
    # Основные поля
    phone = models.CharField(_('телефон'), validators=[phone_regex], max_length=17, unique=True)
    email = models.EmailField(_('email'), blank=True)
    
    # Статусы пользователя
    is_verified = models.BooleanField(_('верифицирован'), default=False)
    is_seller = models.BooleanField(_('продавец'), default=False)
    is_specialist = models.BooleanField(_('специалист'), default=False)
    is_shelter = models.BooleanField(_('приют'), default=False)
    
    # Дополнительные поля
    rating = models.DecimalField(_('рейтинг'), max_digits=3, decimal_places=2, default=0)
    
    # Настройки Django
    username = None
    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []
    
    objects = UserManager()
    
    class Meta:
        verbose_name = _('пользователь')
        verbose_name_plural = _('пользователи')
        
    def __str__(self):
        return self.phone

class PhoneVerification(models.Model):
    phone = models.CharField('Телефон', max_length=15)
    code = models.CharField('Код', max_length=6)
    attempts = models.IntegerField('Попытки', default=0)
    is_verified = models.BooleanField('Подтвержден', default=False)
    is_blocked = models.BooleanField('Заблокирован', default=False)
    created = models.DateTimeField('Создан', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Верификация телефона'
        verbose_name_plural = 'Верификации телефонов'
    
    def __str__(self):
        return f'{self.phone} - {self.code}'
    
    def generate_code(self):
        """Генерирует новый код подтверждения"""
        self.code = get_random_string(6, '0123456789')
        self.attempts = 0
        self.is_verified = False
        self.is_blocked = False
        self.created = timezone.now()
        self.save()
        return self.code
    
    def verify(self, code):
        """Проверяет код подтверждения"""
        if self.is_blocked:
            return False
        
        if self.is_expired():
            return False
        
        if self.attempts >= settings.MAX_VERIFICATION_ATTEMPTS:
            self.is_blocked = True
            self.save()
            return False
        
        if self.code == code:
            self.is_verified = True
            self.save()
            return True
        
        self.attempts += 1
        self.save()
        return False
    
    def is_expired(self):
        """Проверяет, истек ли срок действия кода"""
        expiry = self.created + timedelta(minutes=settings.CODE_EXPIRY_MINUTES)
        return timezone.now() > expiry

class SellerVerification(models.Model):
    STATUS_CHOICES = (
        ('pending', 'На рассмотрении'),
        ('approved', 'Одобрено'),
        ('rejected', 'Отклонено'),
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='seller_verifications',
        verbose_name='Пользователь'
    )
    status = models.CharField(
        'Статус',
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    passport_scan = models.FileField(
        'Скан паспорта',
        upload_to='seller_verification/passport'
    )
    selfie_with_passport = models.FileField(
        'Селфи с паспортом',
        upload_to='seller_verification/selfie'
    )
    additional_document = models.FileField(
        'Дополнительный документ',
        upload_to='seller_verification/additional',
        blank=True,
        null=True
    )
    rejection_reason = models.TextField(
        'Причина отказа',
        blank=True
    )
    created = models.DateTimeField(
        'Создано',
        auto_now_add=True
    )
    updated = models.DateTimeField(
        'Обновлено',
        auto_now=True
    )
    
    class Meta:
        verbose_name = 'Верификация продавца'
        verbose_name_plural = 'Верификации продавцов'
    
    def __str__(self):
        return f'{self.user.get_full_name()} - {self.get_status_display()}'
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if self.status == 'approved' and not is_new and \
           timezone.now() - self.created > timedelta(hours=48):
            self.user.is_seller = True
            self.user.save()

class VerificationRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'На рассмотрении'),
        ('approved', 'Одобрено'),
        ('rejected', 'Отклонено'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_requests')
    documents = models.JSONField(_('документы'))
    status = models.CharField(_('статус'), max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(_('создано'), auto_now_add=True)
    updated_at = models.DateTimeField(_('обновлено'), auto_now=True)
    comment = models.TextField(_('комментарий'), blank=True)
    
    class Meta:
        verbose_name = _('запрос на верификацию')
        verbose_name_plural = _('запросы на верификацию')
        ordering = ['-created_at'] 