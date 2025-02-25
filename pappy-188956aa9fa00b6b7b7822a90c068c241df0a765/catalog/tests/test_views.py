from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from catalog.models import Category, Product, ProductImage, Favorite

User = get_user_model()

class CatalogViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create users
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123'
        )
        self.seller = User.objects.create_user(
            phone='+79992345678',
            password='seller123'
        )
        self.buyer = User.objects.create_user(
            phone='+79997654321',
            password='buyer123'
        )
        
        # Create category
        self.category = Category.objects.create(
            name='Test Category',
            description='Test Description'
        )
        
        # Create product
        self.product = Product.objects.create(
            seller=self.seller,
            category=self.category,
            title='Test Product',
            description='Test Description',
            price=99.99,
            condition='new',
            status='active'
        )
        
        # Create product image
        self.image_file = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'',
            content_type='image/jpeg'
        )
        self.product_image = ProductImage.objects.create(
            product=self.product,
            image=self.image_file,
            is_main=True
        )

    def test_catalog_home_view(self):
        response = self.client.get(reverse('catalog:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/home.html')
        self.assertIn('featured_products', response.context)
        self.assertIn('categories', response.context)
        self.assertIn('latest_products', response.context)

    def test_category_detail_view(self):
        response = self.client.get(
            reverse('catalog:category_detail', kwargs={'slug': self.category.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/category_detail.html')
        self.assertEqual(response.context['category'], self.category)
        self.assertIn('products', response.context)
        self.assertIn('form', response.context)

    def test_product_detail_view(self):
        response = self.client.get(
            reverse('catalog:product_detail', kwargs={'slug': self.product.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/product_detail.html')
        self.assertEqual(response.context['product'], self.product)
        
        # Test view counter
        self.product.refresh_from_db()
        self.assertEqual(self.product.views, 1)

    def test_search_products_view(self):
        # Test basic search
        response = self.client.get(reverse('catalog:search'), {'q': 'Test'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/search_results.html')
        self.assertTrue(len(response.context['products']) > 0)
        
        # Test search with filters
        response = self.client.get(reverse('catalog:search'), {
            'q': 'Test',
            'condition': ['new'],
            'price_min': '50',
            'price_max': '150',
            'category': str(self.category.id),
            'sort': '-price'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.context['products']) > 0)

    def test_my_products_view(self):
        # Test unauthorized access
        response = self.client.get(reverse('catalog:my_products'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Test authorized access
        self.client.login(phone='+79992345678', password='seller123')
        response = self.client.get(reverse('catalog:my_products'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/my_products.html')
        self.assertTrue(len(response.context['products']) > 0)

    def test_product_create_view(self):
        # Test unauthorized access
        response = self.client.get(reverse('catalog:product_create'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Test GET request
        self.client.login(phone='+79991234567', password='testpass123')
        response = self.client.get(reverse('catalog:product_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/product_form.html')
        
        # Test POST request
        image_file = SimpleUploadedFile(
            name='test_image.gif',
            content=(
                b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff'
                b'\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44'
                b'\x01\x00\x3b'
            ),
            content_type='image/gif'
        )
        post_data = {
            'title': 'New Product',
            'description': 'New Description',
            'price': '199.99',
            'condition': 'new',
            'category': self.category.id,
            'image_1': image_file
        }
        response = self.client.post(reverse('catalog:product_create'), post_data)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(Product.objects.filter(title='New Product').exists())

    def test_product_edit_view(self):
        # Create a product for the test user
        product = Product.objects.create(
            seller=self.user,
            category=self.category,
            title='User Product',
            description='Test Description',
            price=99.99,
            condition='new'
        )
        
        # Test unauthorized access
        response = self.client.get(
            reverse('catalog:product_edit', kwargs={'slug': product.slug})
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Test access by non-owner
        self.client.login(phone='+79992345678', password='seller123')
        response = self.client.get(
            reverse('catalog:product_edit', kwargs={'slug': product.slug})
        )
        self.assertEqual(response.status_code, 404)
        
        # Test access by owner
        self.client.login(phone='+79991234567', password='testpass123')
        response = self.client.get(
            reverse('catalog:product_edit', kwargs={'slug': product.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/product_form.html')
        
        # Test successful edit
        post_data = {
            'title': 'Updated Product',
            'description': 'Updated Description',
            'price': '299.99',
            'condition': 'used',
            'category': self.category.id
        }
        response = self.client.post(
            reverse('catalog:product_edit', kwargs={'slug': product.slug}),
            post_data
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success
        product.refresh_from_db()
        self.assertEqual(product.title, 'Updated Product')

    def test_toggle_favorite_view(self):
        # Test unauthorized access
        response = self.client.post(reverse('catalog:toggle_favorite'), {
            'product_id': self.product.id
        })
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Test adding to favorites
        self.client.login(phone='+79991234567', password='testpass123')
        response = self.client.post(reverse('catalog:toggle_favorite'), {
            'product_id': self.product.id
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Favorite.objects.filter(user=self.user, product=self.product).exists()
        )
        
        # Test removing from favorites
        response = self.client.post(reverse('catalog:toggle_favorite'), {
            'product_id': self.product.id
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Favorite.objects.filter(user=self.user, product=self.product).exists()
        )

    def test_favorites_view(self):
        # Test unauthorized access
        response = self.client.get(reverse('catalog:favorites'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Add product to favorites
        self.client.login(phone='+79991234567', password='testpass123')
        Favorite.objects.create(user=self.user, product=self.product)
        
        # Test authorized access
        response = self.client.get(reverse('catalog:favorites'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/favorites.html')
        self.assertTrue(len(response.context['favorites']) > 0) 