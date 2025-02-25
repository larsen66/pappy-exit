from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from PIL import Image
import io

from user_profile.models import UserProfile, SellerProfile, SpecialistProfile, VerificationDocument, Review

User = get_user_model()

class UserProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123'
        )

    def test_user_profile_creation(self):
        """Тест автоматического создания профиля пользователя"""
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsInstance(self.user.profile, UserProfile)

    def test_profile_str(self):
        """Тест строкового представления профиля"""
        expected = f'Профиль пользователя {self.user.phone}'
        self.assertEqual(str(self.user.profile), expected)

class SellerProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123',
            is_seller=True
        )
        self.seller_profile = SellerProfile.objects.create(
            user=self.user,
            seller_type='individual',
            description='Test seller'
        )

    def test_seller_profile_creation(self):
        """Тест создания профиля продавца"""
        self.assertTrue(hasattr(self.user, 'seller_profile'))
        self.assertEqual(self.seller_profile.seller_type, 'individual')
        self.assertEqual(self.seller_profile.description, 'Test seller')

    def test_seller_profile_str(self):
        """Тест строкового представления профиля продавца"""
        expected = f'Профиль продавца {self.user.phone}'
        self.assertEqual(str(self.seller_profile), expected)

    def test_seller_rating_calculation(self):
        """Тест расчета рейтинга продавца"""
        # Создаем отзывы
        other_user = User.objects.create_user(
            phone='+79991234568',
            password='testpass123'
        )
        Review.objects.create(
            author=other_user,
            seller=self.user,
            rating=5,
            comment='Excellent'
        )
        Review.objects.create(
            author=other_user,
            seller=self.user,
            rating=4,
            comment='Good'
        )
        
        self.assertEqual(self.seller_profile.rating, 4.5)

class SpecialistProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123',
            is_specialist=True
        )
        self.specialist_profile = SpecialistProfile.objects.create(
            user=self.user,
            specialization='veterinarian',
            experience_years=5,
            services='Test services'
        )

    def test_specialist_profile_creation(self):
        """Тест создания профиля специалиста"""
        self.assertTrue(hasattr(self.user, 'specialist_profile'))
        self.assertEqual(self.specialist_profile.specialization, 'veterinarian')
        self.assertEqual(self.specialist_profile.experience_years, 5)

    def test_specialist_profile_str(self):
        """Тест строкового представления профиля специалиста"""
        expected = f'Профиль специалиста {self.user.phone}'
        self.assertEqual(str(self.specialist_profile), expected)

    def test_specialist_rating_calculation(self):
        """Тест расчета рейтинга специалиста"""
        # Создаем отзывы
        other_user = User.objects.create_user(
            phone='+79991234568',
            password='testpass123'
        )
        Review.objects.create(
            author=other_user,
            specialist=self.user,
            rating=5,
            comment='Excellent'
        )
        Review.objects.create(
            author=other_user,
            specialist=self.user,
            rating=3,
            comment='Average'
        )
        
        self.assertEqual(self.specialist_profile.rating, 4.0)

class VerificationDocumentTests(TestCase):
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

    def test_document_creation(self):
        """Тест создания документа верификации"""
        test_image = self.create_test_image()
        document = VerificationDocument.objects.create(
            user=self.user,
            document=test_image,
            document_type='passport',
            comment='Test document'
        )
        
        self.assertTrue(document.document)
        self.assertEqual(document.document_type, 'passport')
        self.assertEqual(document.status, 'pending')

    def test_document_str(self):
        """Тест строкового представления документа"""
        test_image = self.create_test_image()
        document = VerificationDocument.objects.create(
            user=self.user,
            document=test_image,
            document_type='passport'
        )
        expected = f'Документ {document.document_type} пользователя {self.user.phone}'
        self.assertEqual(str(document), expected)

class ReviewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123'
        )
        self.seller = User.objects.create_user(
            phone='+79991234568',
            password='testpass123',
            is_seller=True
        )
        self.specialist = User.objects.create_user(
            phone='+79991234569',
            password='testpass123',
            is_specialist=True
        )
        SellerProfile.objects.create(
            user=self.seller,
            seller_type='individual'
        )
        SpecialistProfile.objects.create(
            user=self.specialist,
            specialization='veterinarian'
        )

    def test_review_creation(self):
        """Тест создания отзыва"""
        review = Review.objects.create(
            author=self.user,
            seller=self.seller,
            rating=5,
            comment='Excellent service'
        )
        
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, 'Excellent service')
        self.assertEqual(review.author, self.user)
        self.assertEqual(review.seller, self.seller)

    def test_review_str(self):
        """Тест строкового представления отзыва"""
        review = Review.objects.create(
            author=self.user,
            specialist=self.specialist,
            rating=4,
            comment='Good service'
        )
        expected = f'Отзыв от {self.user.phone}'
        self.assertEqual(str(review), expected)

    def test_review_validation(self):
        """Тест валидации отзыва"""
        # Тест создания отзыва с невалидным рейтингом
        with self.assertRaises(ValueError):
            Review.objects.create(
                author=self.user,
                seller=self.seller,
                rating=6,  # Невалидное значение
                comment='Invalid rating'
            ) 