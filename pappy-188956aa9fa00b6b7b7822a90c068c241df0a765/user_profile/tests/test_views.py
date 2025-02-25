from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import io

from ..models import UserProfile, SellerProfile, SpecialistProfile, VerificationDocument

User = get_user_model()

class UserProfileViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123'
        )
        self.client.login(phone='+79991234567', password='testpass123')

    def test_profile_settings_view(self):
        """Тест представления настроек профиля"""
        response = self.client.get(reverse('user_profile:settings'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_profile/settings.html')

    def test_profile_update(self):
        """Тест обновления профиля"""
        response = self.client.post(reverse('user_profile:settings'), {
            'bio': 'Test bio',
            'location': 'Test City'
        })
        self.assertEqual(response.status_code, 302)  # Редирект после успешного обновления
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.bio, 'Test bio')
        self.assertEqual(self.user.profile.location, 'Test City')

class SellerProfileViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123'
        )
        self.client.login(phone='+79991234567', password='testpass123')

    def create_test_image(self):
        """Создание тестового изображения"""
        file = io.BytesIO()
        image = Image.new('RGB', (100, 100), 'white')
        image.save(file, 'JPEG')
        file.seek(0)
        return SimpleUploadedFile('test.jpg', file.getvalue(), content_type='image/jpeg')

    def test_seller_profile_create_view(self):
        """Тест представления создания профиля продавца"""
        response = self.client.get(reverse('user_profile:create_seller_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_profile/seller_profile_form.html')

    def test_seller_profile_create(self):
        """Тест создания профиля продавца"""
        self.user.is_verified = True
        self.user.save()
        
        response = self.client.post(reverse('user_profile:create_seller_profile'), {
            'seller_type': 'individual',
            'description': 'Test seller'
        })
        self.assertEqual(response.status_code, 302)  # Редирект после успешного создания
        self.assertTrue(SellerProfile.objects.filter(user=self.user).exists())

    def test_seller_profile_update(self):
        """Тест обновления профиля продавца"""
        profile = SellerProfile.objects.create(
            user=self.user,
            seller_type='individual',
            description='Initial description'
        )
        
        response = self.client.post(
            reverse('user_profile:update_seller_profile', kwargs={'pk': profile.pk}),
            {
                'seller_type': 'individual',
                'description': 'Updated description'
            }
        )
        self.assertEqual(response.status_code, 302)
        profile.refresh_from_db()
        self.assertEqual(profile.description, 'Updated description')

class SpecialistProfileViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123'
        )
        self.client.login(phone='+79991234567', password='testpass123')

    def create_test_image(self):
        """Создание тестового изображения"""
        file = io.BytesIO()
        image = Image.new('RGB', (100, 100), 'white')
        image.save(file, 'JPEG')
        file.seek(0)
        return SimpleUploadedFile('test.jpg', file.getvalue(), content_type='image/jpeg')

    def test_specialist_profile_create_view(self):
        """Тест представления создания профиля специалиста"""
        response = self.client.get(reverse('user_profile:create_specialist_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_profile/specialist_profile_form.html')

    def test_specialist_profile_create(self):
        """Тест создания профиля специалиста"""
        self.user.is_verified = True
        self.user.save()
        
        response = self.client.post(reverse('user_profile:create_specialist_profile'), {
            'specialization': 'veterinarian',
            'experience_years': 5,
            'services': 'Test services'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(SpecialistProfile.objects.filter(user=self.user).exists())

    def test_specialist_profile_update(self):
        """Тест обновления профиля специалиста"""
        profile = SpecialistProfile.objects.create(
            user=self.user,
            specialization='veterinarian',
            experience_years=5,
            services='Initial services'
        )
        
        response = self.client.post(
            reverse('user_profile:update_specialist_profile', kwargs={'pk': profile.pk}),
            {
                'specialization': 'veterinarian',
                'experience_years': 6,
                'services': 'Updated services'
            }
        )
        self.assertEqual(response.status_code, 302)
        profile.refresh_from_db()
        self.assertEqual(profile.experience_years, 6)
        self.assertEqual(profile.services, 'Updated services')

class VerificationViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123'
        )
        self.client.login(phone='+79991234567', password='testpass123')

    def create_test_image(self):
        """Создание тестового изображения"""
        file = io.BytesIO()
        image = Image.new('RGB', (100, 100), 'white')
        image.save(file, 'JPEG')
        file.seek(0)
        return SimpleUploadedFile('test.jpg', file.getvalue(), content_type='image/jpeg')

    def test_verification_request_view(self):
        """Тест представления запроса верификации"""
        response = self.client.get(reverse('user_profile:verification_request'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_profile/verification_request.html')

    def test_verification_document_upload(self):
        """Тест загрузки документов для верификации"""
        test_image = self.create_test_image()
        response = self.client.post(reverse('user_profile:upload_document'), {
            'document': test_image,
            'document_type': 'passport',
            'comment': 'Test document'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(VerificationDocument.objects.filter(user=self.user).exists())

    def test_verification_status_view(self):
        """Тест представления статуса верификации"""
        doc = VerificationDocument.objects.create(
            user=self.user,
            document=self.create_test_image(),
            document_type='passport',
            status='pending'
        )
        
        response = self.client.get(reverse('user_profile:verification_status'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_profile/verification_status.html')
        self.assertIn('documents', response.context)
        self.assertEqual(response.context['documents'][0], doc) 