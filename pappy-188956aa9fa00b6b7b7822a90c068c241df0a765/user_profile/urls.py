from django.urls import path
from . import views

app_name = 'user_profile'

urlpatterns = [
    path('settings/', views.profile_settings, name='settings'),
    path('seller/', views.seller_profile, name='seller_profile'),
    path('specialist/', views.specialist_profile, name='specialist_profile'),
    path('verification/request/', views.verification_request, name='verification_request'),
    path('verification/status/', views.verification_status, name='verification_status'),
    path('specialists/', views.specialist_list, name='specialist_list'),
    path('specialists/<int:pk>/', views.specialist_detail, name='specialist_detail'),
    path('user/<int:user_id>/', views.public_profile, name='public_profile'),
    # Seller profile URLs
    path('seller/create/', views.create_seller_profile, name='create_seller_profile'),
    path('seller/update/', views.update_seller_profile, name='update_seller_profile'),
    path('seller/update/<int:user_id>/', views.update_seller_profile, name='update_seller_profile'),
    path('seller/delete/', views.delete_profile, name='delete_profile'),
    path('seller/verify/', views.request_verification, name='request_verification'),
    
    # Specialist profile URLs
    path('specialist/create/', views.create_specialist_profile, name='create_specialist_profile'),
    path('become-seller/', views.become_seller, name='become_seller'),
    path('verification-pending/', views.verification_pending, name='verification_pending'),
] 