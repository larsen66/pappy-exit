from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .api import SwipeViewSet

router = DefaultRouter()
router.register(r'swipe', SwipeViewSet, basename='swipe')

app_name = 'pets'

urlpatterns = [
    path('api/', include(router.urls)),
    path('swipe/', views.swipe_view, name='swipe'),
    path('swipe/process/', views.process_swipe, name='process_swipe'),
    path('matches/', views.matches_view, name='matches'),
] 