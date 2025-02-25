from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, ProductImage, Favorite

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'order', 'is_active', 'created', 'updated']
    list_filter = ['is_active', 'parent']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']
    actions = ['activate_categories', 'deactivate_categories']
    
    def activate_categories(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f'Активировано категорий: {queryset.count()}')
    activate_categories.short_description = 'Активировать выбранные категории'
    
    def deactivate_categories(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f'Деактивировано категорий: {queryset.count()}')
    deactivate_categories.short_description = 'Деактивировать выбранные категории'

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'is_main', 'order', 'preview_image']
    readonly_fields = ['preview_image']
    
    def preview_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px;"/>', obj.image.url)
        return '-'
    preview_image.short_description = 'Предпросмотр'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'seller', 'category', 'price', 'status', 'created', 'views', 'is_featured']
    list_filter = ['status', 'condition', 'is_featured', 'created', 'category']
    search_fields = ['title', 'description', 'seller__first_name', 'seller__last_name', 'seller__phone']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ProductImageInline]
    actions = ['mark_as_featured', 'unmark_as_featured', 'block_products']
    date_hierarchy = 'created'
    list_per_page = 20
    
    def mark_as_featured(self, request, queryset):
        from notifications.models import Notification
        
        for product in queryset:
            if not product.is_featured:
                product.is_featured = True
                product.save()
                
                # Создаем уведомление
                Notification.create_product_status_notification(
                    product.seller,
                    'Объявление в рекомендуемых',
                    f'Ваше объявление "{product.title}" теперь отображается в рекомендуемых.'
                )
        
        self.message_user(request, f'Добавлено в рекомендуемые: {queryset.count()}')
    mark_as_featured.short_description = 'Добавить в рекомендуемые'
    
    def unmark_as_featured(self, request, queryset):
        queryset.update(is_featured=False)
        self.message_user(request, f'Удалено из рекомендуемых: {queryset.count()}')
    unmark_as_featured.short_description = 'Удалить из рекомендуемых'
    
    def block_products(self, request, queryset):
        from notifications.models import Notification
        
        for product in queryset:
            if product.status != 'blocked':
                product.status = 'blocked'
                product.save()
                
                # Создаем уведомление
                Notification.create_product_status_notification(
                    product.seller,
                    'Объявление заблокировано',
                    f'Ваше объявление "{product.title}" было заблокировано. Пожалуйста, обратитесь в поддержку.'
                )
        
        self.message_user(request, f'Заблокировано объявлений: {queryset.count()}')
    block_products.short_description = 'Заблокировать выбранные объявления'

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'created']
    list_filter = ['created']
    search_fields = ['user__first_name', 'user__last_name', 'user__phone', 'product__title']
    date_hierarchy = 'created' 