from django.test import TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
from login_auth.models import User
from user_profile.models import VIPSubscription
from chat.models import Dialog, Message
from unittest.mock import patch

class VIPTest(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123'
        )
        self.client.login(phone='+79991234567', password='testpass123')
        
        # Create VIP concierge user
        self.concierge = User.objects.create_user(
            phone='+79990000000',
            password='concierge123',
            is_staff=True
        )
    
    @patch('user_profile.services.process_payment')
    def test_vip_subscription_flow(self, mock_payment):
        """
        Test the complete VIP subscription flow according to TZ:
        1. User purchases VIP subscription
        2. VIP chat becomes available
        3. User can communicate with concierge
        """
        # Mock successful payment
        mock_payment.return_value = {'status': 'success', 'transaction_id': '123'}
        
        # Purchase subscription
        response = self.client.post(reverse('user_profile:purchase_vip'), {
            'plan': 'monthly',
            'payment_token': 'mock_token'
        })
        self.assertEqual(response.status_code, 200)
        
        # Check subscription was created
        subscription = VIPSubscription.objects.get(user=self.user)
        self.assertTrue(subscription.is_active)
        self.assertEqual(subscription.plan, 'monthly')
        
        # Check VIP chat was created
        dialog = Dialog.objects.get(is_vip=True)
        self.assertIn(self.user, dialog.participants.all())
        self.assertIn(self.concierge, dialog.participants.all())
        
        # Test sending message in VIP chat
        response = self.client.post(reverse('chat:send_message'), {
            'dialog': dialog.id,
            'text': 'Нужна помощь в выборе котенка'
        })
        self.assertEqual(response.status_code, 200)
    
    def test_vip_expiration(self):
        """Test that VIP features become unavailable after subscription expires"""
        # Create expired subscription
        subscription = VIPSubscription.objects.create(
            user=self.user,
            plan='monthly',
            expires_at=timezone.now() - timedelta(days=1)
        )
        
        # Create VIP dialog
        dialog = Dialog.objects.create(is_vip=True)
        dialog.participants.add(self.user, self.concierge)
        
        # Try to send message
        response = self.client.post(reverse('chat:send_message'), {
            'dialog': dialog.id,
            'text': 'Тестовое сообщение'
        })
        self.assertEqual(response.status_code, 403)
    
    def test_vip_renewal(self):
        """Test that VIP subscription can be renewed"""
        # Create expiring subscription
        subscription = VIPSubscription.objects.create(
            user=self.user,
            plan='monthly',
            expires_at=timezone.now() + timedelta(days=1)
        )
        
        with patch('user_profile.services.process_payment') as mock_payment:
            mock_payment.return_value = {'status': 'success', 'transaction_id': '123'}
            
            # Renew subscription
            response = self.client.post(reverse('user_profile:renew_vip'), {
                'payment_token': 'mock_token'
            })
            self.assertEqual(response.status_code, 200)
            
            # Check expiration was extended
            subscription.refresh_from_db()
            self.assertTrue(
                subscription.expires_at > timezone.now() + timedelta(days=25)
            )
    
    def test_vip_features_access(self):
        """Test access to VIP-only features"""
        # Try to access VIP features without subscription
        response = self.client.get(reverse('user_profile:vip_features'))
        self.assertEqual(response.status_code, 403)
        
        # Create active subscription
        subscription = VIPSubscription.objects.create(
            user=self.user,
            plan='monthly',
            expires_at=timezone.now() + timedelta(days=30)
        )
        
        # Try again with subscription
        response = self.client.get(reverse('user_profile:vip_features'))
        self.assertEqual(response.status_code, 200)
    
    def test_vip_chat_privacy(self):
        """Test that VIP chat is private"""
        # Create VIP dialog
        dialog = Dialog.objects.create(is_vip=True)
        dialog.participants.add(self.user, self.concierge)
        
        # Create another user
        other_user = User.objects.create_user(
            phone='+79995555555',
            password='pass123'
        )
        self.client.login(phone='+79995555555', password='pass123')
        
        # Try to access VIP chat
        response = self.client.get(reverse('chat:dialog_messages',
                                         kwargs={'dialog_id': dialog.id}))
        self.assertEqual(response.status_code, 403)
    
    @patch('user_profile.services.process_payment')
    def test_invalid_vip_payment(self, mock_payment):
        """Test handling of failed VIP subscription payment"""
        # Mock failed payment
        mock_payment.return_value = {'status': 'failed', 'error': 'Invalid card'}
        
        # Try to purchase subscription
        response = self.client.post(reverse('user_profile:purchase_vip'), {
            'plan': 'monthly',
            'payment_token': 'mock_token'
        })
        self.assertEqual(response.status_code, 400)
        
        # Check no subscription was created
        self.assertFalse(VIPSubscription.objects.filter(user=self.user).exists()) 