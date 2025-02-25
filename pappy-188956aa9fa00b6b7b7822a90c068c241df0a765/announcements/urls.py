from django.urls import path
from . import views

app_name = 'announcements'

urlpatterns = [
    path('', views.announcement_list, name='list'),
    path('create/', views.announcement_create, name='create'),
    path('<int:pk>/', views.announcement_detail, name='detail'),
    path('<int:pk>/edit/', views.announcement_edit, name='edit'),
    path('<int:pk>/delete/', views.announcement_delete, name='delete'),
    path('my/', views.my_announcements, name='my_list'),
] 