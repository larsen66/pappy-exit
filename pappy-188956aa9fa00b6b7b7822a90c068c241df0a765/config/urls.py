from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('announcements/', include('announcements.urls')),
    path('', include('catalog.urls')),
    path('auth/', include('login_auth.urls')),
    path('profile/', include('user_profile.urls', namespace='profile')),
    path('chat/', include('chat.urls')),
    path('notifications/', include('notifications.urls')),
    path('pets/', include('pets.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) 