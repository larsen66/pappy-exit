from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.catalog_home, name='home'),
    path('search/', views.search_products, name='search'),
    path('my-products/', views.my_products, name='my_products'),
    path('product/create/', views.product_create, name='product_create'),
    path('product/<slug:slug>/edit/', views.product_edit, name='product_edit'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('favorites/', views.favorites, name='favorites'),
    path('toggle-favorite/', views.toggle_favorite, name='toggle_favorite'),
    
    # Lost pets
    path('lost-pets/create/', views.create_lost_pet, name='create_lost_pet'),
    path('lost-pets/search/', views.lost_pets_search, name='lost_pets_search'),
    path('lost-pets/<int:pk>/mark-found/', views.mark_as_found, name='mark_as_found'),
    path('lost-pets/contact-owner/', views.contact_owner, name='contact_owner'),
    
    # Mating
    path('mating/like/', views.mating_like, name='mating_like'),
    path('mating/cancel/', views.cancel_mating_request, name='cancel_mating_request'),
    
    # API endpoints
    path('api/products/<int:product_id>/status/', views.update_product_status, name='update_product_status'),
    path('api/products/<int:product_id>/', views.delete_product, name='delete_product'),
    path('api/images/<int:image_id>/', views.delete_product_image, name='delete_product_image'),
] 