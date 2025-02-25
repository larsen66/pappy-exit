from django.test import TransactionTestCase
from django.urls import reverse
from django.conf import settings
from django.core.cache import cache
from login_auth.models import User, PhoneVerification
from unittest.mock import patch

class PhoneRegistrationTest(TransactionTestCase):
    def setUp(self):
        self.phone = '+79991234567'
        self.password = 'testpass123'
        cache.clear()
    
    @patch('login_auth.services.send_verification_code')
    def test_phone_registration_flow(self, mock_send_code):
        """
        Test the complete phone registration flow according to TZ:
        1. User enters phone number
        2. System sends verification code
        3. User verifies code
        4. User completes registration
        """
        # Mock the SMS sending
        mock_send_code.return_value = True
        verification_code = '123456'
        
        # Step 1: Request verification code
        response = self.client.post(reverse('login_auth:request_code'), {
            'phone': self.phone
        })
        self.assertEqual(response.status_code, 200)
        mock_send_code.assert_called_once()
        
        # Simulate code being saved in cache/db
        PhoneVerification.objects.create(
            phone=self.phone,
            code=verification_code,
            is_verified=False
        )
        
        # Step 2: Verify code
        response = self.client.post(reverse('login_auth:verify_code'), {
            'phone': self.phone,
            'code': verification_code
        })
        self.assertEqual(response.status_code, 200)
        
        # Step 3: Complete registration
        response = self.client.post(reverse('login_auth:register'), {
            'phone': self.phone,
            'password1': self.password,
            'password2': self.password,
            'first_name': 'Test',
            'last_name': 'User'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Verify user was created
        user = User.objects.get(phone=self.phone)
        self.assertTrue(user.check_password(self.password))
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertFalse(user.is_seller)  # Should start as regular user

    def test_invalid_phone_format(self):
        """Test that system validates phone number format"""
        response = self.client.post(reverse('login_auth:request_code'), {
            'phone': 'invalid'
        })
        self.assertEqual(response.status_code, 400)
    
    def test_invalid_verification_code(self):
        """Test system handles invalid verification codes"""
        # Request code first
        self.client.post(reverse('login_auth:request_code'), {
            'phone': self.phone
        })
        
        # Try invalid code
        response = self.client.post(reverse('login_auth:verify_code'), {
            'phone': self.phone,
            'code': '000000'
        })
        self.assertEqual(response.status_code, 400)
    
    def test_verification_code_expiry(self):
        """Test that verification codes expire after settings.CODE_EXPIRY_MINUTES"""
        with patch('django.utils.timezone.now') as mock_now:
            # Create expired verification
            verification = PhoneVerification.objects.create(
                phone=self.phone,
                code='123456',
                is_verified=False
            )
            
            # Move time forward past expiry
            mock_now.return_value = verification.created + \
                settings.CODE_EXPIRY_MINUTES + 1
            
            # Try to verify
            response = self.client.post(reverse('login_auth:verify_code'), {
                'phone': self.phone,
                'code': '123456'
            })
            self.assertEqual(response.status_code, 400)
            
    def test_max_verification_attempts(self):
        """Test that system limits number of verification attempts"""
        verification = PhoneVerification.objects.create(
            phone=self.phone,
            code='123456',
            is_verified=False
        )
        
        # Try max_attempts + 1 times
        for _ in range(settings.MAX_VERIFICATION_ATTEMPTS + 1):
            response = self.client.post(reverse('login_auth:verify_code'), {
                'phone': self.phone,
                'code': '000000'  # Wrong code
            })
        
        # Last attempt should be blocked
        self.assertEqual(response.status_code, 400)
        verification.refresh_from_db()
        self.assertTrue(verification.is_blocked) 