from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

from catalog.models import Product, Category
from chat.models import Dialog, Message
from .models import Notification

class NotificationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        self.user = self.User.objects.create(phone='+79991234567')
        self.other_user = self.User.objects.create(phone='+79991234568')
        self.client.force_login(self.user)
        
        # Создаем тестовую категорию и продукт
        self.category = Category.objects.create(
            name='Тестовая категория',
            slug='test-category'
        )
        self.product = Product.objects.create(
            seller=self.other_user,
            category=self.category,
            title='Тестовый продукт',
            slug='test-product',
            description='Описание тестового продукта',
            price=Decimal('1000.00'),
            condition='new',
            location='Москва, Центральный район'
        )
        
        # Создаем диалог с сообщением
        self.dialog = Dialog.objects.create(product=self.product)
        self.dialog.participants.add(self.user, self.other_user)
        self.message = Message.objects.create(
            dialog=self.dialog,
            sender=self.other_user,
            text='Тестовое сообщение'
        )
    
    def test_notifications_list(self):
        """Тест списка уведомлений"""
        # Создаем тестовые уведомления
        Notification.create_message_notification(self.user, self.dialog)
        Notification.create_match_notification(self.user, self.product)
        
        response = self.client.get(reverse('notifications:notifications_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['notifications']), 2)
    
    def test_mark_all_as_read(self):
        """Тест отметки всех уведомлений как прочитанных"""
        # Создаем несколько непрочитанных уведомлений
        Notification.create_message_notification(self.user, self.dialog)
        Notification.create_match_notification(self.user, self.product)
        
        # Проверяем, что есть непрочитанные уведомления
        self.assertTrue(
            Notification.objects.filter(recipient=self.user, is_read=False).exists()
        )
        
        # Отмечаем все как прочитанные
        response = self.client.post(reverse('notifications:mark-all-read'))
        self.assertEqual(response.status_code, 200)
        
        # Проверяем, что все уведомления отмечены как прочитанные
        self.assertFalse(
            Notification.objects.filter(recipient=self.user, is_read=False).exists()
        )
    
    def test_clear_all_notifications(self):
        """Тест удаления всех уведомлений"""
        # Создаем несколько уведомлений
        Notification.create_message_notification(self.user, self.dialog)
        Notification.create_match_notification(self.user, self.product)
        
        # Проверяем, что уведомления созданы
        self.assertTrue(Notification.objects.filter(recipient=self.user).exists())
        
        # Удаляем все уведомления
        response = self.client.post(reverse('notifications:clear-all'))
        self.assertEqual(response.status_code, 200)
        
        # Проверяем, что все уведомления удалены
        self.assertFalse(Notification.objects.filter(recipient=self.user).exists())
    
    def test_message_notification(self):
        """Тест уведомления о новом сообщении"""
        notification = Notification.create_message_notification(self.user, self.dialog)
        
        self.assertEqual(notification.type, 'message')
        self.assertEqual(notification.recipient, self.user)
        self.assertIn(self.other_user.get_full_name(), notification.text)
        self.assertIn(self.product.title, notification.text)
        self.assertEqual(notification.link, f'/chat/dialog/{self.dialog.id}/')
        self.assertFalse(notification.is_read)
    
    def test_match_notification(self):
        """Тест уведомления о взаимном лайке"""
        notification = Notification.create_match_notification(self.user, self.product)
        
        self.assertEqual(notification.type, 'match')
        self.assertEqual(notification.recipient, self.user)
        self.assertIn(self.product.title, notification.text)
        self.assertEqual(notification.link, f'/chat/create/{self.product.id}/')
    
    def test_product_status_notification(self):
        """Тест уведомления об изменении статуса объявления"""
        # Добавляем русские названия статусов
        status_choices = {
            'active': 'активный',
            'archived': 'в архиве',
            'draft': 'черновик',
            'moderation': 'на модерации',
            'rejected': 'отклонен'
        }
        
        for status, status_name in status_choices.items():
            notification = Notification.create_product_status_notification(
                self.user, self.product, status
            )
            
            self.assertEqual(notification.type, 'product_status')
            self.assertEqual(notification.recipient, self.user)
            self.assertIn(self.product.title, notification.text)
            self.assertIn(status_name, notification.text.lower())
            self.assertEqual(notification.link, f'/catalog/product/{self.product.slug}/')
    
    def test_verification_notification(self):
        """Тест уведомления о верификации"""
        # Проверяем успешную верификацию
        notification = Notification.create_verification_notification(self.user, True)
        self.assertEqual(notification.type, 'verification')
        self.assertIn('подтвержден', notification.text)
        
        # Проверяем отклоненную верификацию
        notification = Notification.create_verification_notification(self.user, False)
        self.assertIn('отклонен', notification.text)
    
    def test_lost_pet_notification(self):
        """Тест уведомления о потерянном питомце"""
        notification = Notification.create_lost_pet_notification(self.user, self.product)
        
        self.assertEqual(notification.type, 'lost_pet_nearby')
        self.assertEqual(notification.recipient, self.user)
        self.assertIn(self.product.title, notification.text)
        self.assertIn(self.product.location, notification.text)
        self.assertEqual(notification.link, f'/catalog/product/{self.product.slug}/')
    
    def test_notification_ordering(self):
        """Тест сортировки уведомлений"""
        # Создаем несколько уведомлений с небольшой задержкой
        notification1 = Notification.create_message_notification(self.user, self.dialog)
        notification2 = Notification.create_match_notification(self.user, self.product)
        
        # Проверяем порядок сортировки (от новых к старым)
        notifications = list(Notification.objects.all())
        self.assertEqual(notifications[0], notification2)
        self.assertEqual(notifications[1], notification1)
    
    def test_notification_str_representation(self):
        """Тест строкового представления уведомления"""
        notification = Notification.create_message_notification(self.user, self.dialog)
        expected_str = f'Новое сообщение для {self.user.get_full_name()}'
        self.assertEqual(str(notification), expected_str)
    
    def test_mark_as_read(self):
        """Тест отметки уведомления как прочитанного"""
        notification = Notification.create_message_notification(self.user, self.dialog)
        self.assertFalse(notification.is_read)
        
        # Отмечаем как прочитанное
        notification.is_read = True
        notification.save()
        
        # Проверяем, что статус обновился
        notification.refresh_from_db()
        self.assertTrue(notification.is_read) 