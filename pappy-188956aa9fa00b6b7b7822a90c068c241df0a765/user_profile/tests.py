from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from PIL import Image
from rest_framework.test import APITestCase
from rest_framework import status
import io

from .models import SellerProfile, SpecialistProfile, VerificationDocument, Review
from .forms import UserProfileForm, SellerProfileForm, SpecialistProfileForm

User = get_user_model()

class UserProfileTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123'
        )
        self.client.login(phone='+79991234567', password='testpass123')

    def test_user_profile_creation(self):
        """Тест автоматического создания профиля пользователя"""
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsInstance(self.user.profile, UserProfile)

    def test_profile_update(self):
        """Тест обновления профиля пользователя"""
        response = self.client.post(reverse('user_profile:settings'), {
            'bio': 'Test bio',
            'location': 'Test City'
        })
        self.assertEqual(response.status_code, 302)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.bio, 'Test bio')
        self.assertEqual(self.user.profile.location, 'Test City')

class SellerProfileTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123'
        )
        self.client.login(phone='+79991234567', password='testpass123')

    def test_seller_profile_creation(self):
        """Тест создания профиля продавца"""
        response = self.client.post(reverse('user_profile:create_seller_profile'), {
            'seller_type': 'individual',
            'description': 'Test seller'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(hasattr(self.user, 'seller_profile'))
        self.assertEqual(self.user.seller_profile.seller_type, 'individual')

    def test_seller_verification(self):
        """Тест процесса верификации продавца"""
        seller_profile = SellerProfile.objects.create(
            user=self.user,
            seller_type='company',
            company_name='Test Company',
            inn='1234567890'
        )
        
        # Создаем тестовый файл для загрузки
        test_file = SimpleUploadedFile(
            "test_doc.pdf",
            b"file_content",
            content_type="application/pdf"
        )
        
        response = self.client.post(reverse('user_profile:verification_request'), {
            'document': test_file,
            'comment': 'Test verification request'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(VerificationDocument.objects.filter(user=self.user).exists())

class SpecialistProfileTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123',
            is_specialist=True
        )
        self.client.login(phone='+79991234567', password='testpass123')

    def test_specialist_profile_creation(self):
        """Тест создания профиля специалиста"""
        response = self.client.post(reverse('user_profile:create_specialist_profile'), {
            'specialization': 'veterinarian',
            'experience_years': 5,
            'services': 'Test services',
            'price_range': '1000-5000'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(hasattr(self.user, 'specialist_profile'))
        self.assertEqual(self.user.specialist_profile.specialization, 'veterinarian')

    def test_specialist_verification(self):
        """Тест процесса верификации специалиста"""
        specialist_profile = SpecialistProfile.objects.create(
            user=self.user,
            specialization='veterinarian',
            experience_years=5,
            services='Test services'
        )
        
        test_file = SimpleUploadedFile(
            "certificate.pdf",
            b"file_content",
            content_type="application/pdf"
        )
        
        response = self.client.post(reverse('user_profile:verification_request'), {
            'document': test_file,
            'comment': 'Test verification request'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(VerificationDocument.objects.filter(user=self.user).exists())

class ProfileFormsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123'
        )

    def test_user_profile_form(self):
        """Тест формы профиля пользователя"""
        form_data = {
            'bio': 'Test bio',
            'location': 'Test City'
        }
        form = UserProfileForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_seller_profile_form(self):
        """Тест формы профиля продавца"""
        form_data = {
            'seller_type': 'individual',
            'description': 'Test seller'
        }
        form = SellerProfileForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_specialist_profile_form(self):
        """Тест формы профиля специалиста"""
        form_data = {
            'specialization': 'veterinarian',
            'experience_years': 5,
            'services': 'Test services',
            'price_range': '1000-5000'
        }
        form = SpecialistProfileForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_seller_profile_update(self):
        """Тест обновления профиля продавца"""
        # Создаем профиль
        profile = SellerProfile.objects.create(
            user=self.user,
            seller_type='individual',
            description='Старое описание'
        )
        
        # Обновляем профиль
        update_data = {
            'seller_type': 'entrepreneur',
            'description': 'Новое описание',
            'inn': '123456789012'
        }
        
        response = self.client.post(
            reverse('user_profile:update_seller_profile'),
            update_data
        )
        self.assertEqual(response.status_code, 302)
        
        # Проверяем обновление
        profile.refresh_from_db()
        self.assertEqual(profile.seller_type, 'entrepreneur')
        self.assertEqual(profile.description, 'Новое описание')
        self.assertEqual(profile.inn, '123456789012')
    
    def test_specialist_profile_update(self):
        """Тест обновления профиля специалиста"""
        # Создаем профиль
        profile = SpecialistProfile.objects.create(
            user=self.user,
            seller_type='individual',
            specialization='groomer',
            experience_years=3
        )
        
        # Обновляем профиль
        update_data = {
            'seller_type': 'entrepreneur',
            'specialization': 'trainer',
            'experience_years': 7,
            'services': 'Дрессировка собак',
            'price_range': '2000-7000 руб.'
        }
        
        response = self.client.post(
            reverse('user_profile:update_specialist_profile'),
            update_data
        )
        self.assertEqual(response.status_code, 302)
        
        # Проверяем обновление
        profile.refresh_from_db()
        self.assertEqual(profile.specialization, 'trainer')
        self.assertEqual(profile.experience_years, 7)
        self.assertEqual(profile.services, 'Дрессировка собак')
    
    def test_profile_verification(self):
        """Тест верификации профиля"""
        # Создаем профиль
        profile = SellerProfile.objects.create(
            user=self.user,
            seller_type='individual'
        )
        
        # Отправляем на верификацию
        response = self.client.post(
            reverse('user_profile:request_verification'),
            {'document_scan': self.document}
        )
        self.assertEqual(response.status_code, 302)
        
        # Проверяем статус верификации
        profile.refresh_from_db()
        self.assertFalse(profile.is_verified)  # Пока не подтверждено модератором
        
        # Подтверждаем верификацию (как модератор)
        admin_user = self.User.objects.create(
            phone='+79991234568',
            is_staff=True
        )
        self.client.force_login(admin_user)
        
        response = self.client.post(
            reverse('user_profile:verify_profile', kwargs={'user_id': self.user.id}),
            {'is_verified': True}
        )
        self.assertEqual(response.status_code, 302)
        
        # Проверяем результат верификации
        profile.refresh_from_db()
        self.assertTrue(profile.is_verified)
        self.assertIsNotNone(profile.verification_date)
    
    def test_profile_access_permissions(self):
        """Тест прав доступа к профилю"""
        # Создаем другого пользователя
        other_user = self.User.objects.create(phone='+79991234569')
        other_profile = SellerProfile.objects.create(
            user=other_user,
            seller_type='individual'
        )
        
        # Пытаемся обновить чужой профиль
        update_data = {'description': 'Попытка взлома'}
        response = self.client.post(
            reverse('user_profile:update_seller_profile', kwargs={'user_id': other_user.id}),
            update_data
        )
        self.assertEqual(response.status_code, 403)  # Доступ запрещен
        
        # Проверяем, что данные не изменились
        other_profile.refresh_from_db()
        self.assertNotEqual(other_profile.description, 'Попытка взлома')
    
    def test_profile_deletion(self):
        """Тест удаления профиля"""
        # Создаем профиль
        profile = SellerProfile.objects.create(
            user=self.user,
            seller_type='individual'
        )
        
        # Удаляем профиль
        response = self.client.post(reverse('user_profile:delete_profile'))
        self.assertEqual(response.status_code, 302)
        
        # Проверяем, что профиль удален
        self.assertFalse(SellerProfile.objects.filter(user=self.user).exists())
    
    def test_profile_type_validation(self):
        """Тест валидации типа профиля"""
        # Пытаемся создать профиль с неверным типом
        profile_data = {
            'seller_type': 'invalid_type',
            'description': 'Тестовое описание'
        }
        
        response = self.client.post(
            reverse('user_profile:create_seller_profile'),
            profile_data
        )
        self.assertEqual(response.status_code, 200)  # Форма с ошибками
        self.assertFalse(SellerProfile.objects.filter(user=self.user).exists())
    
    def test_inn_validation(self):
        """Тест валидации ИНН"""
        # Пытаемся создать профиль с неверным ИНН
        profile_data = {
            'seller_type': 'entrepreneur',
            'inn': '123'  # Слишком короткий ИНН
        }
        
        response = self.client.post(
            reverse('user_profile:create_seller_profile'),
            profile_data
        )
        self.assertEqual(response.status_code, 200)  # Форма с ошибками
        self.assertFalse(SellerProfile.objects.filter(user=self.user).exists())
    
    def test_specialist_experience_validation(self):
        """Тест валидации опыта работы специалиста"""
        # Пытаемся создать профиль с отрицательным опытом
        profile_data = {
            'seller_type': 'individual',
            'specialization': 'veterinarian',
            'experience_years': -1
        }
        
        response = self.client.post(
            reverse('user_profile:create_specialist_profile'),
            profile_data
        )
        self.assertEqual(response.status_code, 200)  # Форма с ошибками
        self.assertFalse(SpecialistProfile.objects.filter(user=self.user).exists())

class ProfilePermissionsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            phone='+79991234568',
            password='testpass123'
        )
        self.admin_user = User.objects.create_user(
            phone='+79991234569',
            password='testpass123',
            is_staff=True
        )

    def test_profile_access_permissions(self):
        """Тест прав доступа к профилю"""
        # Неавторизованный доступ
        response = self.client.get(reverse('user_profile:settings'))
        self.assertEqual(response.status_code, 302)  # Редирект на логин

        # Доступ к своему профилю
        self.client.login(phone='+79991234567', password='testpass123')
        response = self.client.get(reverse('user_profile:settings'))
        self.assertEqual(response.status_code, 200)

        # Попытка доступа к чужому профилю
        response = self.client.get(
            reverse('user_profile:profile_detail', kwargs={'pk': self.other_user.id})
        )
        self.assertEqual(response.status_code, 403)

    def test_seller_profile_permissions(self):
        """Тест прав доступа к профилю продавца"""
        self.client.login(phone='+79991234567', password='testpass123')
        
        # Создание профиля продавца без верификации
        response = self.client.post(reverse('user_profile:create_seller_profile'))
        self.assertEqual(response.status_code, 403)

        # После верификации
        self.user.is_verified = True
        self.user.save()
        response = self.client.post(reverse('user_profile:create_seller_profile'))
        self.assertEqual(response.status_code, 200)

    def test_profile_deletion(self):
        """Тест удаления профиля"""
        self.client.login(phone='+79991234567', password='testpass123')
        
        # Попытка удаления чужого профиля
        response = self.client.post(
            reverse('user_profile:delete_profile', kwargs={'pk': self.other_user.id})
        )
        self.assertEqual(response.status_code, 403)
        
        # Удаление своего профиля
        response = self.client.post(
            reverse('user_profile:delete_profile', kwargs={'pk': self.user.id})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(id=self.user.id).exists())

class VerificationDocumentTests(TestCase):
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

    def test_document_upload(self):
        """Тест загрузки документов"""
        test_image = self.create_test_image()
        response = self.client.post(reverse('user_profile:upload_document'), {
            'document': test_image,
            'document_type': 'passport',
            'comment': 'Test document'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(VerificationDocument.objects.filter(user=self.user).exists())

    def test_document_validation(self):
        """Тест валидации документов"""
        # Тест неверного формата файла
        invalid_file = SimpleUploadedFile(
            'test.txt',
            b'invalid content',
            content_type='text/plain'
        )
        response = self.client.post(reverse('user_profile:upload_document'), {
            'document': invalid_file,
            'document_type': 'passport'
        })
        self.assertEqual(response.status_code, 400)

        # Тест превышения размера файла
        large_file = SimpleUploadedFile(
            'large.jpg',
            b'x' * 5242880,  # 5MB
            content_type='image/jpeg'
        )
        response = self.client.post(reverse('user_profile:upload_document'), {
            'document': large_file,
            'document_type': 'passport'
        })
        self.assertEqual(response.status_code, 400)

class ProfileRatingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123'
        )
        self.seller = User.objects.create_user(
            phone='+79991234568',
            password='testpass123',
            is_seller=True
        )
        self.seller_profile = SellerProfile.objects.create(
            user=self.seller,
            seller_type='individual',
            description='Test seller'
        )
        self.client.login(phone='+79991234567', password='testpass123')

    def test_rating_calculation(self):
        """Тест расчета рейтинга"""
        # Создаем несколько отзывов
        Review.objects.create(
            author=self.user,
            seller=self.seller,
            rating=5,
            comment='Excellent service'
        )
        Review.objects.create(
            author=self.user,
            seller=self.seller,
            rating=4,
            comment='Good service'
        )
        
        # Проверяем расчет среднего рейтинга
        self.seller_profile.refresh_from_db()
        self.assertEqual(self.seller_profile.rating, 4.5)

    def test_rating_validation(self):
        """Тест валидации рейтинга"""
        # Тест невалидного рейтинга
        response = self.client.post(reverse('user_profile:add_review'), {
            'seller_id': self.seller.id,
            'rating': 6,  # Невалидное значение
            'comment': 'Test review'
        })
        self.assertEqual(response.status_code, 400)

        # Тест отзыва на самого себя
        self.client.login(phone='+79991234568', password='testpass123')
        response = self.client.post(reverse('user_profile:add_review'), {
            'seller_id': self.seller.id,
            'rating': 5,
            'comment': 'Self review'
        })
        self.assertEqual(response.status_code, 403)

class ProfileSearchTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Создаем несколько пользователей с разными профилями
        self.vet = User.objects.create_user(
            phone='+79991234567',
            password='testpass123',
            is_specialist=True
        )
        self.groomer = User.objects.create_user(
            phone='+79991234568',
            password='testpass123',
            is_specialist=True
        )
        SpecialistProfile.objects.create(
            user=self.vet,
            specialization='veterinarian',
            experience_years=5,
            services='Ветеринарные услуги'
        )
        SpecialistProfile.objects.create(
            user=self.groomer,
            specialization='groomer',
            experience_years=3,
            services='Груминг собак и кошек'
        )

    def test_profile_search(self):
        """Тест поиска профилей"""
        # Поиск по специализации
        response = self.client.get(reverse('user_profile:search_specialists'), {
            'specialization': 'veterinarian'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['specialists']), 1)
        self.assertEqual(response.context['specialists'][0].user, self.vet)

        # Поиск по услугам
        response = self.client.get(reverse('user_profile:search_specialists'), {
            'q': 'груминг'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['specialists']), 1)
        self.assertEqual(response.context['specialists'][0].user, self.groomer)

    def test_profile_filters(self):
        """Тест фильтрации профилей"""
        # Фильтр по опыту работы
        response = self.client.get(reverse('user_profile:search_specialists'), {
            'min_experience': 4
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['specialists']), 1)
        self.assertEqual(response.context['specialists'][0].user, self.vet)

        # Фильтр по рейтингу
        self.vet.specialist_profile.rating = 4.5
        self.vet.specialist_profile.save()
        self.groomer.specialist_profile.rating = 3.5
        self.groomer.specialist_profile.save()

        response = self.client.get(reverse('user_profile:search_specialists'), {
            'min_rating': 4
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['specialists']), 1)
        self.assertEqual(response.context['specialists'][0].user, self.vet)

class ProfileAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_profile_list_api(self):
        """Тест API списка профилей"""
        url = reverse('api:profile-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_profile_detail_api(self):
        """Тест API деталей профиля"""
        url = reverse('api:profile-detail', kwargs={'pk': self.user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['phone'], self.user.phone)

    def test_profile_update_api(self):
        """Тест API обновления профиля"""
        url = reverse('api:profile-detail', kwargs={'pk': self.user.id})
        data = {
            'bio': 'Updated bio',
            'location': 'New location'
        }
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['bio'], 'Updated bio')

    def test_seller_profile_api(self):
        """Тест API профиля продавца"""
        # Создание профиля продавца
        url = reverse('api:seller-profile-create')
        data = {
            'seller_type': 'individual',
            'description': 'Test seller'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Обновление профиля продавца
        url = reverse('api:seller-profile-detail', kwargs={'pk': self.user.id})
        data = {
            'description': 'Updated description'
        }
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'Updated description')

    def test_specialist_profile_api(self):
        """Тест API профиля специалиста"""
        # Создание профиля специалиста
        url = reverse('api:specialist-profile-create')
        data = {
            'specialization': 'veterinarian',
            'experience_years': 5,
            'services': 'Test services'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Обновление профиля специалиста
        url = reverse('api:specialist-profile-detail', kwargs={'pk': self.user.id})
        data = {
            'services': 'Updated services'
        }
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['services'], 'Updated services')

    def test_profile_search_api(self):
        """Тест API поиска профилей"""
        # Создаем тестовых специалистов
        specialist = User.objects.create_user(
            phone='+79991234568',
            password='testpass123',
            is_specialist=True
        )
        SpecialistProfile.objects.create(
            user=specialist,
            specialization='veterinarian',
            experience_years=5,
            services='Ветеринарные услуги'
        )

        # Тест поиска по специализации
        url = reverse('api:specialist-search')
        response = self.client.get(url, {'specialization': 'veterinarian'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['user']['phone'], specialist.phone)

    def test_profile_filters_api(self):
        """Тест API фильтрации профилей"""
        # Создаем тестовых специалистов с разным опытом
        specialist1 = User.objects.create_user(
            phone='+79991234568',
            password='testpass123',
            is_specialist=True
        )
        specialist2 = User.objects.create_user(
            phone='+79991234569',
            password='testpass123',
            is_specialist=True
        )
        SpecialistProfile.objects.create(
            user=specialist1,
            specialization='veterinarian',
            experience_years=5,
            services='Ветеринарные услуги'
        )
        SpecialistProfile.objects.create(
            user=specialist2,
            specialization='veterinarian',
            experience_years=2,
            services='Ветеринарные услуги'
        )

        # Тест фильтрации по опыту работы
        url = reverse('api:specialist-search')
        response = self.client.get(url, {'min_experience': 4})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['user']['phone'], specialist1.phone)

    def test_profile_image_upload_api(self):
        """Тест API загрузки изображения профиля"""
        # Создаем тестовое изображение
        file = io.BytesIO()
        image = Image.new('RGB', (100, 100), 'white')
        image.save(file, 'JPEG')
        file.seek(0)
        image_file = SimpleUploadedFile('test.jpg', file.getvalue(), content_type='image/jpeg')

        url = reverse('api:profile-upload-image')
        response = self.client.post(url, {'image': image_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('image_url', response.data)

        # Проверка невалидного формата
        invalid_file = SimpleUploadedFile('test.txt', b'invalid content', content_type='text/plain')
        response = self.client.post(url, {'image': invalid_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_api_error_handling(self):
        """Тест обработки ошибок API"""
        # Тест несуществующего профиля
        url = reverse('api:profile-detail', kwargs={'pk': 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Тест неверных данных при обновлении
        url = reverse('api:profile-detail', kwargs={'pk': self.user.id})
        response = self.client.patch(url, {'experience_years': 'invalid'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Тест доступа к чужому профилю
        other_user = User.objects.create_user(
            phone='+79991234570',
            password='testpass123'
        )
        url = reverse('api:profile-detail', kwargs={'pk': other_user.id})
        response = self.client.patch(url, {'bio': 'Try to update'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_api_authentication(self):
        """Тест аутентификации API"""
        # Сбрасываем аутентификацию
        self.client.force_authenticate(user=None)

        # Тест доступа без аутентификации
        url = reverse('api:profile-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Тест с неверными учетными данными
        response = self.client.post(reverse('api:token_obtain'), {
            'phone': '+79991234567',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Тест с верными учетными данными
        response = self.client.post(reverse('api:token_obtain'), {
            'phone': '+79991234567',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_api_permissions(self):
        """Тест прав доступа API"""
        # Создаем обычного пользователя и админа
        regular_user = User.objects.create_user(
            phone='+79991234571',
            password='testpass123'
        )
        admin_user = User.objects.create_user(
            phone='+79991234572',
            password='testpass123',
            is_staff=True
        )

        # Тест доступа обычного пользователя к админ-функциям
        self.client.force_authenticate(user=regular_user)
        url = reverse('api:admin-user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Тест доступа админа
        self.client.force_authenticate(user=admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK) 