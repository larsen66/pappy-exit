from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import io

from user_profile.forms import SellerProfileForm, SpecialistProfileForm
from ..models import UserProfile, SellerProfile, SpecialistProfile

User = get_user_model()

class UserProfileFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123'
        )
        self.profile = self.user.profile

    def test_valid_profile_form(self):
        """Тест валидной формы профиля"""
        form_data = {
            'bio': 'Test bio',
            'location': 'Test City'
        }
        form = UserProfileForm(data=form_data, instance=self.profile)
        self.assertTrue(form.is_valid())

    def test_empty_form(self):
        """Тест пустой формы"""
        form = UserProfileForm(data={}, instance=self.profile)
        self.assertTrue(form.is_valid())  # Все поля опциональны

class SellerProfileFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123'
        )

    def create_test_image(self):
        """Создание тестового изображения"""
        file = io.BytesIO()
        image = Image.new('RGB', (100, 100), 'white')
        image.save(file, 'JPEG')
        file.seek(0)
        return SimpleUploadedFile('test.jpg', file.getvalue(), content_type='image/jpeg')

    def test_valid_individual_seller_form(self):
        """Тест формы индивидуального продавца"""
        form_data = {
            'seller_type': 'individual',
            'description': 'Test seller'
        }
        form = SellerProfileForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_valid_company_seller_form(self):
        """Тест формы компании-продавца"""
        form_data = {
            'seller_type': 'company',
            'company_name': 'Test Company',
            'inn': '1234567890',
            'description': 'Test company description'
        }
        form = SellerProfileForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_inn(self):
        """Тест невалидного ИНН"""
        form_data = {
            'seller_type': 'company',
            'company_name': 'Test Company',
            'inn': '123',  # Слишком короткий ИНН
            'description': 'Test description'
        }
        form = SellerProfileForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('inn', form.errors)

class SpecialistProfileFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123'
        )

    def create_test_image(self):
        """Создание тестового изображения"""
        file = io.BytesIO()
        image = Image.new('RGB', (100, 100), 'white')
        image.save(file, 'JPEG')
        file.seek(0)
        return SimpleUploadedFile('test.jpg', file.getvalue(), content_type='image/jpeg')

    def test_valid_specialist_form(self):
        """Тест валидной формы специалиста"""
        form_data = {
            'specialization': 'veterinarian',
            'experience_years': 5,
            'services': 'Test services',
            'price_range': '1000-5000'
        }
        form = SpecialistProfileForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_experience(self):
        """Тест невалидного опыта работы"""
        form_data = {
            'specialization': 'veterinarian',
            'experience_years': -1,  # Отрицательное значение
            'services': 'Test services'
        }
        form = SpecialistProfileForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('experience_years', form.errors)

    def test_required_fields(self):
        """Тест обязательных полей"""
        form = SpecialistProfileForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('specialization', form.errors)
        self.assertIn('experience_years', form.errors)
        self.assertIn('services', form.errors)

    def test_certificates_upload(self):
        """Тест загрузки сертификатов"""
        test_image = self.create_test_image()
        form_data = {
            'specialization': 'veterinarian',
            'experience_years': 5,
            'services': 'Test services'
        }
        file_data = {
            'certificates': test_image
        }
        form = SpecialistProfileForm(data=form_data, files=file_data)
        self.assertTrue(form.is_valid()) 