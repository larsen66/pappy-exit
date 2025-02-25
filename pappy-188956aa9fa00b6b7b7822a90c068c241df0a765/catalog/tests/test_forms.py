from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from catalog.forms import ProductForm, ProductFilterForm
from catalog.models import Category, Product

User = get_user_model()

class ProductFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone='+79991234567',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Test Category',
            description='Test Description'
        )
        # Create a small test image
        image_content = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff'
            b'\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44'
            b'\x01\x00\x3b'
        )
        self.image_file = SimpleUploadedFile(
            name='test_image.gif',
            content=image_content,
            content_type='image/gif'
        )

    def test_valid_product_form(self):
        form_data = {
            'title': 'Test Product',
            'description': 'Test Description',
            'price': '99.99',
            'condition': 'new',
            'category': self.category.id,
            'location': 'Test Location'
        }
        form_files = {
            'image_1': self.image_file
        }
        form = ProductForm(data=form_data, files=form_files)
        if not form.is_valid():
            print("Form errors:", form.errors)
        self.assertTrue(form.is_valid())

    def test_invalid_product_form(self):
        # Test with empty data
        form = ProductForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 4)  # title, description, price, category are required
        
        # Test with invalid price
        form_data = {
            'title': 'Test Product',
            'description': 'Test Description',
            'price': 'invalid',
            'condition': 'new',
            'category': self.category.id
        }
        form = ProductForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('price', form.errors)

    def test_product_form_save(self):
        """Test saving product with images"""
        form_data = {
            'title': 'Test Product',
            'description': 'Test Description',
            'price': '100.00',
            'category': self.category.id,
            'condition': 'new',
            'location': 'Test Location'
        }
        form_files = {
            'image_1': self.image_file
        }
        form = ProductForm(data=form_data, files=form_files)
        self.assertTrue(form.is_valid())
        product = form.save(commit=False)
        product.seller = self.user  # Set the seller
        product.save()
        form.save_m2m()  # Save many-to-many relationships
        
        # Check that product was created
        self.assertEqual(Product.objects.count(), 1)
        saved_product = Product.objects.first()
        self.assertEqual(saved_product.title, 'Test Product')
        self.assertEqual(saved_product.seller, self.user)
        
        # Check that image was saved
        self.assertEqual(saved_product.images.count(), 1)
        self.assertTrue(saved_product.images.first().is_main)

class ProductFilterFormTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name='Test Category',
            description='Test Description'
        )

    def test_valid_filter_form(self):
        form_data = {
            'category': self.category.id,
            'condition': ['new', 'used'],
            'min_price': '50',
            'max_price': '500',
            'sort': 'newest',
            'search': 'test'
        }
        form = ProductFilterForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_empty_filter_form(self):
        # All fields are optional
        form = ProductFilterForm(data={})
        self.assertTrue(form.is_valid())

    def test_invalid_filter_form(self):
        # Test with invalid price values
        form_data = {
            'min_price': 'invalid',
            'max_price': 'invalid'
        }
        form = ProductFilterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('min_price', form.errors)
        self.assertIn('max_price', form.errors)
        
        # Test with invalid sort value
        form_data = {
            'sort': 'invalid_sort'
        }
        form = ProductFilterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('sort', form.errors)

    def test_filter_form_initial_values(self):
        form = ProductFilterForm()
        self.assertEqual(form.fields['sort'].initial, 'newest')
        self.assertTrue(form.fields['category'].queryset.filter(id=self.category.id).exists()) 