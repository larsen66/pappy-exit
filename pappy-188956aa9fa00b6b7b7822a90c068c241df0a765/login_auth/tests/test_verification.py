from django.test import TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.core.files.uploadedfile import SimpleUploadedFile
from login_auth.models import User, SellerVerification
from user_profile.models import SellerProfile
from unittest.mock import patch

class SellerVerificationTest(TransactionTestCase):
    def setUp(self):
        # Create regular user
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.client.login(phone='+79991234567', password='testpass123')
        
        # Create test document
        self.document = SimpleUploadedFile(
            "passport.pdf",
            b"file_content",
            content_type="application/pdf"
        )
    
    def test_seller_verification_flow(self):
        """
        Test the complete seller verification flow according to TZ:
        1. User submits verification request with documents
        2. Request goes to moderation
        3. After 48 hours moderator approves/rejects
        4. User gets seller status
        """
        # Step 1: Submit verification request
        response = self.client.post(reverse('login_auth:request_verification'), {
            'passport_scan': self.document,
            'selfie_with_passport': self.document,
            'additional_document': self.document,
        })
        self.assertEqual(response.status_code, 200)
        
        # Verify request was created
        verification = SellerVerification.objects.get(user=self.user)
        self.assertEqual(verification.status, 'pending')
        self.assertFalse(self.user.is_seller)
        
        # Step 2: Move time forward 48 hours
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = timezone.now() + timedelta(hours=48)
            
            # Step 3: Moderator approves
            verification.status = 'approved'
            verification.save()
            
            # Step 4: Check user became seller
            self.user.refresh_from_db()
            self.assertTrue(self.user.is_seller)
            
            # Check seller profile was created
            self.assertTrue(SellerProfile.objects.filter(user=self.user).exists())
    
    def test_verification_rejection(self):
        """Test that rejected verification requests are handled properly"""
        # Submit request
        self.client.post(reverse('login_auth:request_verification'), {
            'passport_scan': self.document,
            'selfie_with_passport': self.document,
        })
        
        verification = SellerVerification.objects.get(user=self.user)
        
        # Moderator rejects
        verification.status = 'rejected'
        verification.rejection_reason = 'Documents unclear'
        verification.save()
        
        # User should not become seller
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_seller)
        
        # User should be able to submit new request
        response = self.client.post(reverse('login_auth:request_verification'), {
            'passport_scan': self.document,
            'selfie_with_passport': self.document,
        })
        self.assertEqual(response.status_code, 200)
    
    def test_early_verification_approval(self):
        """Test that verification cannot be approved before 48 hours"""
        # Submit request
        self.client.post(reverse('login_auth:request_verification'), {
            'passport_scan': self.document,
            'selfie_with_passport': self.document,
        })
        
        verification = SellerVerification.objects.get(user=self.user)
        
        # Try to approve immediately
        verification.status = 'approved'
        verification.save()
        
        # User should not become seller yet
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_seller)
    
    def test_missing_required_documents(self):
        """Test that all required documents must be provided"""
        # Try without selfie
        response = self.client.post(reverse('login_auth:request_verification'), {
            'passport_scan': self.document,
        })
        self.assertEqual(response.status_code, 400)
        
        # Verify no request was created
        self.assertFalse(SellerVerification.objects.filter(user=self.user).exists())
    
    def test_invalid_document_format(self):
        """Test that only allowed document formats are accepted"""
        invalid_doc = SimpleUploadedFile(
            "document.exe",
            b"file_content",
            content_type="application/x-msdownload"
        )
        
        response = self.client.post(reverse('login_auth:request_verification'), {
            'passport_scan': invalid_doc,
            'selfie_with_passport': self.document,
        })
        self.assertEqual(response.status_code, 400) 