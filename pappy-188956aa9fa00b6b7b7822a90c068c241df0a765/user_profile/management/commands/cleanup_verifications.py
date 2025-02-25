from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import timedelta
from user_profile.models import SellerVerification

class Command(BaseCommand):
    help = 'Clean up expired seller verification requests'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help=_('Number of days after which to delete rejected verifications')
        )

    def handle(self, *args, **options):
        days = options['days']
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Delete old rejected verifications
        expired = SellerVerification.objects.filter(
            status='RE',
            reviewed_at__lt=cutoff_date
        )
        
        count = expired.count()
        expired.delete()
        
        self.stdout.write(
            self.style.SUCCESS(
                _('Successfully deleted {} expired verification requests').format(count)
            )
        ) 