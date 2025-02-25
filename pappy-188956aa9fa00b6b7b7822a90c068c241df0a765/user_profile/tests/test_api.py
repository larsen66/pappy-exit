from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from PIL import Image
from rest_framework.test import APITestCase
from rest_framework import status
import io

from ..models import UserProfile, SellerProfile, SpecialistProfile, VerificationDocument

User = get_user_model()

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