from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class LoginAuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'login_auth'
    verbose_name = 'Аутентификация' 