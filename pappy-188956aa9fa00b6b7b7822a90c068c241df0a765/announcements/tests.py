from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import (
    Announcement, AnnouncementCategory, AnimalAnnouncement,
    ServiceAnnouncement, MatingAnnouncement, LostFoundAnnouncement
)

User = get_user_model()

class AnnouncementTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123'
        )
        self.client.login(phone='+79991234567', password='testpass123')
        
        # Создаем категорию для тестов
        self.category = AnnouncementCategory.objects.create(
            name='Собаки',
            slug='dogs'
        )

    def test_announcement_creation(self):
        """Тест создания объявления"""
        response = self.client.post(reverse('announcements:create'), {
            'title': 'Test Announcement',
            'description': 'Test Description',
            'price': 1000,
            'category': self.category.id,
            'type': 'animal',
            'location': 'Test City',
            'status': 'moderation',
            'species': 'dog',
            'breed': 'Labrador',
            'age': 2,
            'gender': 'male',
            'size': 'medium',
            'color': 'black',
            'vaccinated': True
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Announcement.objects.filter(title='Test Announcement').exists())

    def test_announcement_update(self):
        """Тест обновления объявления"""
        announcement = Announcement.objects.create(
            title='Original Title',
            description='Original Description',
            price=1000,
            category=self.category,
            author=self.user,
            type='animal',
            location='Test City',
            status='moderation'
        )
        
        response = self.client.post(
            reverse('announcements:update', kwargs={'pk': announcement.pk}),
            {
                'title': 'Updated Title',
                'description': 'Updated Description',
                'price': 2000,
                'category': self.category.id,
                'type': 'animal',
                'location': 'Updated City',
                'status': 'moderation',
                'species': 'dog',
                'breed': 'Labrador',
                'age': 2,
                'gender': 'male',
                'size': 'medium',
                'color': 'black',
                'vaccinated': True
            }
        )
        
        self.assertEqual(response.status_code, 302)
        announcement.refresh_from_db()
        self.assertEqual(announcement.title, 'Updated Title')
        self.assertEqual(announcement.price, 2000)

    def test_announcement_deletion(self):
        """Тест удаления объявления"""
        announcement = Announcement.objects.create(
            title='Test Announcement',
            description='Test Description',
            price=1000,
            category=self.category,
            author=self.user,
            type='animal',
            location='Test City'
        )
        
        response = self.client.post(
            reverse('announcements:delete', kwargs={'pk': announcement.pk})
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Announcement.objects.filter(pk=announcement.pk).exists())

    def test_announcement_listing(self):
        """Тест списка объявлений"""
        Announcement.objects.create(
            title='Test Announcement 1',
            description='Test Description 1',
            price=1000,
            category=self.category,
            author=self.user,
            type='animal',
            location='Test City'
        )
        Announcement.objects.create(
            title='Test Announcement 2',
            description='Test Description 2',
            price=2000,
            category=self.category,
            author=self.user,
            type='service',
            location='Test City'
        )
        
        response = self.client.get(reverse('announcements:list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['announcements']), 2)

    def test_announcement_search(self):
        """Тест поиска объявлений"""
        Announcement.objects.create(
            title='Dog Announcement',
            description='Test Description',
            price=1000,
            category=self.category,
            author=self.user,
            type='animal',
            location='Test City'
        )
        Announcement.objects.create(
            title='Cat Announcement',
            description='Test Description',
            price=2000,
            category=self.category,
            author=self.user,
            type='animal',
            location='Test City'
        )
        
        response = self.client.get(reverse('announcements:list'), {'q': 'dog'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['announcements']), 1)
        self.assertEqual(response.context['announcements'][0].title, 'Dog Announcement')

class AnimalAnnouncementTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123'
        )
        self.client.login(phone='+79991234567', password='testpass123')
        
        self.category = AnnouncementCategory.objects.create(
            name='Собаки',
            slug='dogs'
        )

    def test_animal_announcement_creation(self):
        """Тест создания объявления о животном"""
        response = self.client.post(reverse('announcements:create_animal'), {
            'title': 'Test Animal',
            'description': 'Test Description',
            'price': 1000,
            'category': self.category.id,
            'species': 'dog',
            'breed': 'Labrador',
            'age': 2,
            'gender': 'male',
            'size': 'medium',
            'color': 'black',
            'vaccinated': True,
            'location': 'Test City',
            'status': 'moderation'
        })
        
        self.assertEqual(response.status_code, 302)
        announcement = AnimalAnnouncement.objects.first()
        self.assertEqual(announcement.species, 'dog')
        self.assertEqual(announcement.breed, 'Labrador')

class ServiceAnnouncementTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123',
            is_specialist=True
        )
        self.client.login(phone='+79991234567', password='testpass123')
        
        self.category = AnnouncementCategory.objects.create(
            name='Услуги',
            slug='services'
        )

    def test_service_announcement_creation(self):
        """Тест создания объявления об услуге"""
        response = self.client.post(reverse('announcements:create_service'), {
            'title': 'Test Service',
            'description': 'Test Description',
            'price': 1000,
            'category': self.category.id,
            'service_type': 'grooming',
            'experience': 2,
            'schedule': 'Mon-Fri 9-18',
            'location': 'Test City',
            'status': 'moderation'
        })
        
        self.assertEqual(response.status_code, 302)
        announcement = ServiceAnnouncement.objects.first()
        self.assertEqual(announcement.service_type, 'grooming')
        self.assertEqual(announcement.schedule, 'Mon-Fri 9-18')
