from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from unidecode import unidecode

class Category(models.Model):
    name = models.CharField(_('name'), max_length=200)
    slug = models.SlugField(_('slug'), max_length=200, unique=True)
    parent = models.ForeignKey('self', verbose_name=_('parent category'),
                             on_delete=models.CASCADE, null=True, blank=True,
                             related_name='children')
    description = models.TextField(_('description'), blank=True)
    image = models.ImageField(_('image'), upload_to='categories/', blank=True)
    order = models.IntegerField(_('order'), default=0)
    is_active = models.BooleanField(_('active'), default=True)
    created = models.DateTimeField(_('created'), auto_now_add=True)
    updated = models.DateTimeField(_('updated'), auto_now=True)
    
    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            # Convert Russian text to Latin characters
            base_slug = slugify(unidecode(self.name))
            slug = base_slug
            n = 1
            while Category.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('catalog:category_detail', kwargs={'slug': self.slug})

class Product(models.Model):
    CONDITION_CHOICES = [
        ('new', _('New')),
        ('used', _('Used')),
    ]
    
    STATUS_CHOICES = [
        ('active', _('Active')),
        ('pending', _('Pending')),
        ('blocked', _('Blocked')),
        ('archived', _('Archived')),
    ]
    
    SIZE_CHOICES = [
        ('small', _('Small')),
        ('medium', _('Medium')),
        ('large', _('Large')),
    ]
    
    GENDER_CHOICES = [
        ('male', _('Male')),
        ('female', _('Female')),
    ]
    
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('seller'),
                              on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, verbose_name=_('category'),
                                on_delete=models.CASCADE, related_name='products')
    title = models.CharField(_('title'), max_length=200)
    slug = models.SlugField(_('slug'), max_length=200, unique=True)
    description = models.TextField(_('description'))
    price = models.DecimalField(_('price'), max_digits=10, decimal_places=2, null=True, blank=True)
    condition = models.CharField(_('condition'), max_length=4,
                               choices=CONDITION_CHOICES)
    status = models.CharField(_('status'), max_length=8,
                            choices=STATUS_CHOICES, default='active')
    location = models.CharField(_('location'), max_length=200, blank=True)
    breed = models.CharField(_('breed'), max_length=100, blank=True)
    age = models.PositiveIntegerField(_('age'), null=True, blank=True)
    size = models.CharField(_('size'), max_length=6, choices=SIZE_CHOICES, blank=True)
    gender = models.CharField(_('gender'), max_length=6, choices=GENDER_CHOICES, blank=True)
    created = models.DateTimeField(_('created'), auto_now_add=True)
    updated = models.DateTimeField(_('updated'), auto_now=True)
    views = models.PositiveIntegerField(_('views'), default=0)
    is_featured = models.BooleanField(_('featured'), default=False)
    
    class Meta:
        verbose_name = _('product')
        verbose_name_plural = _('products')
        ordering = ['-created']
        indexes = [
            models.Index(fields=['-created']),
            models.Index(fields=['status']),
            models.Index(fields=['is_featured']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            # Convert Russian text to Latin characters and create base slug
            base_slug = slugify(unidecode(self.title))
            slug = base_slug
            n = 1
            # Keep trying until we find a unique slug
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('catalog:product_detail', kwargs={'slug': self.slug})

class ProductImage(models.Model):
    product = models.ForeignKey(Product, verbose_name=_('product'),
                               on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(_('image'), upload_to='products/')
    is_main = models.BooleanField(_('main image'), default=False)
    order = models.IntegerField(_('order'), default=0)
    
    class Meta:
        verbose_name = _('product image')
        verbose_name_plural = _('product images')
        ordering = ['order']
    
    def save(self, *args, **kwargs):
        if self.is_main:
            # Убираем отметку основного изображения у других изображений продукта
            ProductImage.objects.filter(product=self.product).update(is_main=False)
        elif not ProductImage.objects.filter(product=self.product).exists():
            # Если это первое изображение продукта, делаем его основным
            self.is_main = True
        super().save(*args, **kwargs)

class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('user'),
                            on_delete=models.CASCADE, related_name='favorites')
    product = models.ForeignKey(Product, verbose_name=_('product'),
                               on_delete=models.CASCADE, related_name='favorited_by')
    created = models.DateTimeField(_('created'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('favorite')
        verbose_name_plural = _('favorites')
        ordering = ['-created']
        constraints = [
            models.UniqueConstraint(fields=['user', 'product'],
                                  name='unique_user_product_favorite')
        ]
    
    def __str__(self):
        return f'{self.user} - {self.product}'

class MatingRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('matched', _('Matched')),
        ('rejected', _('Rejected')),
        ('canceled', _('Canceled')),
    ]
    
    from_pet = models.ForeignKey(Product, verbose_name=_('from pet'),
                                on_delete=models.CASCADE, related_name='sent_requests')
    to_pet = models.ForeignKey(Product, verbose_name=_('to pet'),
                              on_delete=models.CASCADE, related_name='received_requests')
    status = models.CharField(_('status'), max_length=8,
                            choices=STATUS_CHOICES, default='pending')
    created = models.DateTimeField(_('created'), auto_now_add=True)
    updated = models.DateTimeField(_('updated'), auto_now=True)
    
    class Meta:
        verbose_name = _('mating request')
        verbose_name_plural = _('mating requests')
        ordering = ['-created']
        constraints = [
            models.UniqueConstraint(fields=['from_pet', 'to_pet'],
                                  name='unique_mating_request')
        ]
    
    def __str__(self):
        return f'{self.from_pet} -> {self.to_pet}'
    
    @property
    def is_valid(self):
        """Check if request is still valid (not expired)"""
        from django.utils import timezone
        from datetime import timedelta
        return self.created > timezone.now() - timedelta(days=30) 