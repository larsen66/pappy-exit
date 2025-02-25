from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UserProfileConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user_profile'
    verbose_name = _('User Profiles')

    def ready(self):
        import user_profile.signals  # noqa 