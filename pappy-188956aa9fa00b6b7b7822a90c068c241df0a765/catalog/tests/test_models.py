from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.text import slugify
from django.db import transaction
from django.core.exceptions import ValidationError
from catalog.models import Category, Product, ProductImage, Favorite
from login_auth.models import User
from django.db.utils import IntegrityError

User = get_user_model()

class CategoryModelTest(TransactionTestCase):
    def setUp(self):
        self.animal_category = Category.objects.create(
            name='Животные',
            description='Все животные'
        )
        self.dogs = Category.objects.create(
            name='Собаки',
            description='Собаки всех пород',
            parent=self.animal_category
        )
        self.cats = Category.objects.create(
            name='Кошки',
            description='Кошки всех пород',
            parent=self.animal_category
        )

    def test_category_hierarchy(self):
        """Test category hierarchy structure"""
        self.assertEqual(self.dogs.parent, self.animal_category)
        self.assertEqual(self.cats.parent, self.animal_category)
        self.assertIn(self.dogs, self.animal_category.children.all())
        self.assertIn(self.cats, self.animal_category.children.all())

    def test_category_str_representation(self):
        """Test string representation of categories"""
        self.assertEqual(str(self.animal_category), 'Животные')
        self.assertEqual(str(self.dogs), 'Собаки')
        self.assertEqual(str(self.cats), 'Кошки')

    def test_category_slug_generation(self):
        """Test automatic slug generation for Russian names"""
        self.assertEqual(self.animal_category.slug, 'zhivotnye')
        self.assertEqual(self.dogs.slug, 'sobaki')
        self.assertEqual(self.cats.slug, 'koshki')

class ProductModelTest(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123'
        )
        self.animal_category = Category.objects.create(
            name='Животные'
        )
        self.dogs = Category.objects.create(
            name='Собаки',
            parent=self.animal_category
        )
        self.product = Product.objects.create(
            seller=self.user,
            category=self.dogs,
            title='Щенок хаски',
            description='Красивый щенок хаски, 3 месяца',
            price=15000,
            condition='new',
            status='active',
            breed='Хаски',
            age=3,
            size='medium'
        )

    def test_product_creation(self):
        """Test product creation with all required fields"""
        self.assertEqual(self.product.seller, self.user)
        self.assertEqual(self.product.category, self.dogs)
        self.assertEqual(self.product.title, 'Щенок хаски')
        self.assertEqual(self.product.price, 15000)
        self.assertEqual(self.product.status, 'active')

    def test_product_status_workflow(self):
        """Test product status transitions according to TZ"""
        # Test initial status
        self.assertEqual(self.product.status, 'active')
        
        # Test status transitions
        self.product.status = 'pending'
        self.product.save()
        self.assertEqual(self.product.status, 'pending')
        
        self.product.status = 'blocked'
        self.product.save()
        self.assertEqual(self.product.status, 'blocked')
        
        self.product.status = 'archived'
        self.product.save()
        self.assertEqual(self.product.status, 'archived')

class ProductImageModelTest(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Тест')
        self.product = Product.objects.create(
            seller=self.user,
            category=self.category,
            title='Тест',
            price=100,
            condition='new',
            status='active'
        )

    def test_multiple_images_handling(self):
        """Test handling of multiple product images according to TZ"""
        # Create test images
        image1 = ProductImage.objects.create(
            product=self.product,
            image='test1.jpg',
            is_main=True
        )
        image2 = ProductImage.objects.create(
            product=self.product,
            image='test2.jpg'
        )
        
        # Test that only one image can be main
        self.assertTrue(image1.is_main)
        self.assertFalse(image2.is_main)
        
        # Test setting another image as main
        image2.is_main = True
        image2.save()
        
        # Refresh from database
        image1.refresh_from_db()
        image2.refresh_from_db()
        
        # Verify that old main image is no longer main
        self.assertFalse(image1.is_main)
        self.assertTrue(image2.is_main)

class FavoriteModelTest(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123'
        )
        self.seller = User.objects.create_user(
            phone='+79997654321',
            password='seller123'
        )
        self.category = Category.objects.create(name='Тест')
        self.product = Product.objects.create(
            seller=self.seller,
            category=self.category,
            title='Тест',
            price=100,
            condition='new',
            status='active'
        )

    @transaction.atomic
    def test_favorite_functionality(self):
        """Test favorite functionality according to TZ"""
        # Add to favorites
        favorite = Favorite.objects.create(user=self.user, product=self.product)
        self.assertTrue(
            Favorite.objects.filter(user=self.user, product=self.product).exists()
        )
        
        # Remove from favorites
        favorite.delete()
        self.assertFalse(
            Favorite.objects.filter(user=self.user, product=self.product).exists()
        )
        
        # Test unique constraint
        Favorite.objects.create(user=self.user, product=self.product)
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                Favorite.objects.create(user=self.user, product=self.product) 