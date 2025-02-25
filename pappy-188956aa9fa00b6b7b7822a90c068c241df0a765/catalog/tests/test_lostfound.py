from django.test import TransactionTestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from login_auth.models import User
from catalog.models import Category, Product
from notifications.models import Notification
from django.utils import timezone
from PIL import Image
import io

class LostFoundTest(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123'
        )
        self.client.login(phone='+79991234567', password='testpass123')
        
        # Create lost pets category
        self.category = Category.objects.create(
            name='Потеряшки',
            slug='lostfound'
        )
        
        # Create test image using PIL
        # Create a new image with a red background
        image = Image.new('RGB', (100, 100), color='red')
        image_io = io.BytesIO()
        image.save(image_io, format='JPEG')
        image_io.seek(0)
        
        self.image = SimpleUploadedFile(
            name='test_image.jpg',
            content=image_io.getvalue(),
            content_type='image/jpeg'
        )
    
    def test_create_lost_pet_ad(self):
        """
        Test creating lost pet announcement according to TZ:
        1. Any user can create (no seller status needed)
        2. No payment required
        3. Automatically becomes active
        """
        response = self.client.post(reverse('catalog:create_lost_pet'), {
            'title': 'Пропал кот',
            'description': 'Рыжий кот, потерялся в районе метро',
            'location': 'Москва, метро Сокол',
            'category': self.category.id,
            'image_1': self.image,
            'breed': 'Рыжий',
            'age': 2,
            'size': 'medium',
            'last_seen': timezone.now(),
            'condition': 'new'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after creation
        
        # Check announcement was created
        product = Product.objects.get(title='Пропал кот')
        self.assertEqual(product.category, self.category)
        self.assertEqual(product.status, 'active')  # Should be active immediately
        self.assertEqual(product.price, 0)  # Should be free
    
    def test_lost_pet_search(self):
        """Test searching for lost pets"""
        # Create some lost pet announcements
        Product.objects.create(
            seller=self.user,
            category=self.category,
            title='Пропала кошка',
            description='Черная кошка',
            location='Москва',
            status='active',
            breed='Черная',
            age=1,
            condition='new'
        )
        Product.objects.create(
            seller=self.user,
            category=self.category,
            title='Пропала собака',
            description='Белая собака',
            location='Москва',
            status='active',
            breed='Белая',
            age=2,
            condition='new'
        )
        
        # Search by type
        response = self.client.get(reverse('catalog:lost_pets_search') + 
                                 '?q=кошка')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['results']), 1)
        
        # Search by location
        response = self.client.get(reverse('catalog:lost_pets_search') + 
                                 '?location=Москва')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['results']), 2)
    
    def test_lost_pet_contact(self):
        """Test contacting lost pet owner"""
        # Create lost pet announcement
        product = Product.objects.create(
            seller=self.user,
            category=self.category,
            title='Пропала собака',
            description='Описание',
            location='Москва',
            status='active',
            condition='new'
        )
        
        # Create another user
        finder = User.objects.create_user(
            phone='+79995555555',
            password='pass123'
        )
        self.client.login(phone='+79995555555', password='pass123')
        
        # Contact owner
        response = self.client.post(reverse('catalog:contact_owner'), {
            'product': product.id,
            'message': 'Возможно, я видел вашу собаку'
        })
        self.assertEqual(response.status_code, 200)
        
        # Check that chat was created
        self.assertTrue(product.dialogs.exists())
    
    def test_mark_as_found(self):
        """Test marking lost pet as found"""
        product = Product.objects.create(
            seller=self.user,
            category=self.category,
            title='Пропала собака',
            description='Описание',
            location='Москва',
            status='active',
            condition='new'
        )
        
        response = self.client.post(reverse('catalog:mark_as_found', 
                                          kwargs={'pk': product.pk}))
        self.assertEqual(response.status_code, 200)
        
        # Check status was updated
        product.refresh_from_db()
        self.assertEqual(product.status, 'archived')
    
    def test_lost_pet_notification_radius(self):
        """Test that users in area get notified about lost pets"""
        # Create users with location
        nearby_user = User.objects.create_user(
            phone='+79995555555',
            password='pass123',
            location='Москва, метро Сокол'
        )
        far_user = User.objects.create_user(
            phone='+79994444444',
            password='pass123',
            location='Санкт-Петербург'
        )
        
        # Create lost pet announcement
        response = self.client.post(reverse('catalog:create_lost_pet'), {
            'title': 'Пропал кот',
            'description': 'Рыжий кот с белой грудкой',
            'location': 'Москва, метро Сокол',
            'category': self.category.id,
            'breed': 'Рыжий',
            'age': 2,
            'size': 'medium',
            'condition': 'new',
            'last_seen': timezone.now(),
            'image_1': self.image
        })
        
        self.assertEqual(response.status_code, 302)  # Should redirect after success
        
        # Check that only nearby user was notified
        self.assertTrue(
            nearby_user.notifications.filter(
                type='lost_pet_nearby'
            ).exists()
        )
        self.assertFalse(
            far_user.notifications.filter(
                type='lost_pet_nearby'
            ).exists()
        )

    def test_lost_pet_validation(self):
        """Test validation rules for lost pet announcements"""
        # Test without required fields
        response = self.client.post(reverse('catalog:create_lost_pet'), {
            'title': '',  # Required field
            'category': self.category.id,
            'condition': 'new'
        })
        self.assertEqual(response.status_code, 200)  # Returns form with errors
        self.assertContains(response, 'Обязательное поле')  # Check error message
        
        # Test with invalid category
        response = self.client.post(reverse('catalog:create_lost_pet'), {
            'title': 'Пропал кот',
            'description': 'Описание',
            'location': 'Москва',
            'category': 999,  # Non-existent category
            'condition': 'new'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Выберите корректный вариант')

    def test_lost_pet_image_handling(self):
        """Test image upload functionality for lost pet announcements"""
        # Create test images using PIL
        image1 = Image.new('RGB', (100, 100), color='red')
        image2 = Image.new('RGB', (100, 100), color='blue')
        
        image1_io = io.BytesIO()
        image2_io = io.BytesIO()
        
        image1.save(image1_io, format='JPEG')
        image2.save(image2_io, format='JPEG')
        
        image1_io.seek(0)
        image2_io.seek(0)
        
        img1 = SimpleUploadedFile(
            name='test_image1.jpg',
            content=image1_io.getvalue(),
            content_type='image/jpeg'
        )
        img2 = SimpleUploadedFile(
            name='test_image2.jpg',
            content=image2_io.getvalue(),
            content_type='image/jpeg'
        )
        
        # Create announcement with multiple images
        response = self.client.post(reverse('catalog:create_lost_pet'), {
            'title': 'Пропал кот',
            'description': 'Описание',
            'location': 'Москва',
            'category': self.category.id,
            'condition': 'new',
            'image_1': img1,
            'image_2': img2
        })
        
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        product = Product.objects.get(title='Пропал кот')
        self.assertEqual(product.images.count(), 2)
        self.assertTrue(product.images.filter(is_main=True).exists())

    def test_lost_pet_search_filters(self):
        """Test advanced search filters for lost pets"""
        # Create test data
        Product.objects.create(
            seller=self.user,
            category=self.category,
            title='Пропал кот',
            description='Рыжий кот',
            location='Москва, Сокол',
            breed='Рыжий',
            age=2,
            status='active',
            condition='new'
        )
        Product.objects.create(
            seller=self.user,
            category=self.category,
            title='Пропала собака',
            description='Белая собака',
            location='Москва, Аэропорт',
            breed='Белая',
            age=3,
            status='active',
            condition='new'
        )
        
        # Test search by breed
        response = self.client.get(reverse('catalog:lost_pets_search') + 
                                 '?q=Рыжий')
        data = response.json()
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['title'], 'Пропал кот')
        
        # Test search by location district
        response = self.client.get(reverse('catalog:lost_pets_search') + 
                                 '?location=Сокол')
        data = response.json()
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['location'], 'Москва, Сокол')

    def test_lost_pet_notification_content(self):
        """Test the content of notifications sent for lost pets"""
        nearby_user = User.objects.create_user(
            phone='+79995555555',
            password='pass123',
            location='Москва, метро Сокол'
        )
        
        # Create lost pet announcement
        response = self.client.post(reverse('catalog:create_lost_pet'), {
            'title': 'Пропал кот Барсик',
            'description': 'Рыжий кот с белой грудкой',
            'location': 'Москва, метро Сокол',
            'category': self.category.id,
            'breed': 'Рыжий',
            'age': 2,
            'size': 'medium',
            'condition': 'new',
            'last_seen': timezone.now(),
            'image_1': self.image
        })
        
        self.assertEqual(response.status_code, 302)  # Should redirect after success
        
        # Check notification content
        notification = nearby_user.notifications.filter(
            type='lost_pet_nearby'
        ).first()
        self.assertIsNotNone(notification)
        self.assertEqual(notification.title, 'Потерянный питомец рядом')
        self.assertIn('Пропал кот Барсик', notification.text)
        self.assertIn('Москва, метро Сокол', notification.text)

    def test_mark_as_found_permissions(self):
        """Test that only the owner can mark a pet as found"""
        # Create another user
        other_user = User.objects.create_user(
            phone='+79995555555',
            password='pass123'
        )
        
        # Create lost pet announcement
        product = Product.objects.create(
            seller=self.user,
            category=self.category,
            title='Пропала собака',
            description='Описание',
            location='Москва',
            status='active',
            condition='new'
        )
        
        # Try to mark as found with other user
        self.client.login(phone='+79995555555', password='pass123')
        response = self.client.post(reverse('catalog:mark_as_found', 
                                          kwargs={'pk': product.pk}))
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Check status wasn't changed
        product.refresh_from_db()
        self.assertEqual(product.status, 'active') 