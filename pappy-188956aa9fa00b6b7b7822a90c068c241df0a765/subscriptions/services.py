from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from .models import VIPSubscription, VIPFeature

class VIPService:
    """Сервис для работы с VIP-подписками"""
    
    @staticmethod
    def create_subscription(user, level: str, duration_days: int, payment_id: str = None) -> VIPSubscription:
        """Создание новой подписки"""
        with transaction.atomic():
            # Деактивируем текущие активные подписки
            user.vip_subscriptions.filter(is_active=True).update(is_active=False)
            
            # Создаем новую подписку
            subscription = VIPSubscription.objects.create(
                user=user,
                level=level,
                expires_at=timezone.now() + timedelta(days=duration_days),
                payment_id=payment_id
            )
            return subscription

    @staticmethod
    def get_active_subscription(user) -> VIPSubscription:
        """Получение активной подписки пользователя"""
        return user.vip_subscriptions.filter(
            is_active=True,
            expires_at__gt=timezone.now()
        ).first()

    @staticmethod
    def get_available_features(user) -> list:
        """Получение доступных функций для текущей подписки"""
        subscription = VIPService.get_active_subscription(user)
        if not subscription:
            return []
            
        return VIPFeature.objects.filter(
            subscription_level=subscription.level,
            is_active=True
        )

    @staticmethod
    def process_subscription_expiration():
        """Обработка истекших подписок"""
        expired_subscriptions = VIPSubscription.objects.filter(
            is_active=True,
            expires_at__lte=timezone.now()
        )
        
        for subscription in expired_subscriptions:
            if subscription.auto_renew:
                # TODO: Implement auto-renewal logic with payment processing
                pass
            else:
                subscription.is_active = False
                subscription.save()

    @staticmethod
    def has_feature(user, feature_name: str) -> bool:
        """Проверка наличия определенной VIP-функции у пользователя"""
        subscription = VIPService.get_active_subscription(user)
        if not subscription:
            return False
            
        return VIPFeature.objects.filter(
            name=feature_name,
            subscription_level=subscription.level,
            is_active=True
        ).exists()

class VIPAnnouncementService:
    """Сервис для работы с VIP-функциями объявлений"""
    
    @staticmethod
    def boost_announcement(announcement_id: int, user) -> bool:
        """Поднятие объявления в топ"""
        if not VIPService.has_feature(user, 'boost_announcement'):
            return False
            
        # TODO: Implement announcement boosting logic
        return True

    @staticmethod
    def get_extended_stats(user) -> dict:
        """Получение расширенной статистики"""
        if not VIPService.has_feature(user, 'extended_stats'):
            return {}
            
        # TODO: Implement extended statistics gathering
        return {
            'views': 0,
            'likes': 0,
            'matches': 0,
            'conversion_rate': 0
        } 