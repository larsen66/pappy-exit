from django.test import TransactionTestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from login_auth.models import User
from catalog.models import Category, Product, MatingRequest
from chat.models import Dialog

class MatingTest(TransactionTestCase):
    def setUp(self):
        # Create users
        self.male_owner = User.objects.create_user(
            phone='+79991234567',
            password='testpass123',
            is_seller=True
        )
        self.female_owner = User.objects.create_user(
            phone='+79997654321',
            password='testpass123',
            is_seller=True
        )
        
        # Create mating category
        self.category = Category.objects.create(
            name='Вязка',
            slug='mating'
        )
        
        # Create test image
        self.image = SimpleUploadedFile(
            "cat.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        
        # Create male pet
        self.male_pet = Product.objects.create(
            seller=self.male_owner,
            category=self.category,
            title='Кот для вязки',
            description='Породистый кот',
            price=5000,
            condition='new',
            status='active',
            breed='Британская',
            age=2,
            size='medium',
            gender='male'
        )
        
        # Create female pet
        self.female_pet = Product.objects.create(
            seller=self.female_owner,
            category=self.category,
            title='Кошка для вязки',
            description='Породистая кошка',
            price=5000,
            condition='new',
            status='active',
            breed='Британская',
            age=2,
            size='medium',
            gender='female'
        )
    
    def test_mating_request_flow(self):
        """
        Test the complete mating request flow according to TZ:
        1. Female owner likes male pet
        2. Male owner likes female pet
        3. Match is created
        4. Chat is opened
        """
        self.client.login(phone='+79997654321', password='testpass123')
        
        # Female owner likes male pet
        response = self.client.post(reverse('catalog:mating_like'), {
            'product': self.male_pet.id
        })
        self.assertEqual(response.status_code, 200)
        
        # Check request was created
        request = MatingRequest.objects.get(
            from_pet=self.female_pet,
            to_pet=self.male_pet
        )
        self.assertEqual(request.status, 'pending')
        
        # Male owner likes female pet
        self.client.login(phone='+79991234567', password='testpass123')
        response = self.client.post(reverse('catalog:mating_like'), {
            'product': self.female_pet.id
        })
        self.assertEqual(response.status_code, 200)
        
        # Check match was created
        request.refresh_from_db()
        self.assertEqual(request.status, 'matched')
        
        # Check chat was created
        self.assertTrue(
            Dialog.objects.filter(
                participants__in=[self.male_owner, self.female_owner]
            ).exists()
        )
    
    def test_breed_compatibility(self):
        """Test that only compatible breeds can match"""
        # Create pet of different breed
        other_pet = Product.objects.create(
            seller=self.female_owner,
            category=self.category,
            title='Кошка другой породы',
            description='Описание',
            price=5000,
            status='active',
            breed='Сиамская',  # Different breed
            gender='female'
        )
        
        self.client.login(phone='+79991234567', password='testpass123')
        
        # Try to like incompatible pet
        response = self.client.post(reverse('catalog:mating_like'), {
            'product': other_pet.id
        })
        self.assertEqual(response.status_code, 400)
    
    def test_gender_validation(self):
        """Test that only opposite genders can match"""
        # Create another male pet
        other_male = Product.objects.create(
            seller=self.female_owner,
            category=self.category,
            title='Еще один кот',
            description='Описание',
            price=5000,
            status='active',
            breed='Британская',
            gender='male'
        )
        
        self.client.login(phone='+79991234567', password='testpass123')
        
        # Try to like same gender
        response = self.client.post(reverse('catalog:mating_like'), {
            'product': other_male.id
        })
        self.assertEqual(response.status_code, 400)
    
    def test_mating_request_expiry(self):
        """Test that unmatched requests expire after 30 days"""
        self.client.login(phone='+79997654321', password='testpass123')
        
        # Create request
        response = self.client.post(reverse('catalog:mating_like'), {
            'product': self.male_pet.id
        })
        
        request = MatingRequest.objects.get(
            from_pet=self.female_pet,
            to_pet=self.male_pet
        )
        
        # Move time forward 31 days
        from django.utils import timezone
        from datetime import timedelta
        request.created = timezone.now() - timedelta(days=31)
        request.save()
        
        # Check request expired
        self.assertFalse(request.is_valid)
    
    def test_cancel_mating_request(self):
        """Test canceling mating request"""
        self.client.login(phone='+79997654321', password='testpass123')
        
        # Create request
        self.client.post(reverse('catalog:mating_like'), {
            'product': self.male_pet.id
        })
        
        request = MatingRequest.objects.get(
            from_pet=self.female_pet,
            to_pet=self.male_pet
        )
        
        # Cancel request
        response = self.client.post(reverse('catalog:cancel_mating_request'), {
            'request': request.id
        })
        self.assertEqual(response.status_code, 200)
        
        # Check request was canceled
        request.refresh_from_db()
        self.assertEqual(request.status, 'canceled') 