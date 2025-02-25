from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from .models import UserProfile, SellerProfile, SpecialistProfile

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Создает профиль пользователя при создании нового пользователя"""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Сохраняет профиль пользователя при сохранении пользователя"""
    if not hasattr(instance, 'profile'):
        UserProfile.objects.create(user=instance)
    instance.profile.save()

@receiver(post_save, sender=User)
def create_seller_profile(sender, instance, created, **kwargs):
    """Создает профиль продавца при активации статуса продавца"""
    if instance.is_seller and not hasattr(instance, 'seller_profile'):
        SellerProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def create_specialist_profile(sender, instance, created, **kwargs):
    """Создает профиль специалиста при активации статуса специалиста"""
    if instance.is_specialist and not hasattr(instance, 'specialist_profile'):
        SpecialistProfile.objects.create(user=instance) 