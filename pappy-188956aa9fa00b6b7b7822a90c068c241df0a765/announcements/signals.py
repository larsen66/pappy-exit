from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .models import Announcement
from notifications.models import Notification

@receiver(pre_save, sender=Announcement)
def handle_announcement_status_change(sender, instance, **kwargs):
    """Handle announcement status changes"""
    if not instance.pk:  # New announcement
        return
    
    try:
        old_instance = Announcement.objects.get(pk=instance.pk)
        if old_instance.status != instance.status:
            # Status changed
            if instance.status == 'active':
                instance.published_at = timezone.now()
                
                # Create notification for the author
                Notification.objects.create(
                    recipient=instance.author,
                    type='product_status',
                    title=_('Announcement Approved'),
                    text=_('Your announcement "{}" has been approved and is now live.').format(instance.title),
                    link=f'/announcements/{instance.id}/'
                )
            elif instance.status == 'blocked':
                # Create notification for the author
                Notification.objects.create(
                    recipient=instance.author,
                    type='product_status',
                    title=_('Announcement Blocked'),
                    text=_('Your announcement "{}" has been blocked. Please contact support for more information.').format(instance.title),
                    link=f'/announcements/{instance.id}/'
                )
    except Announcement.DoesNotExist:
        pass

@receiver(post_save, sender=Announcement)
def handle_new_announcement(sender, instance, created, **kwargs):
    """Handle new announcement creation"""
    if created:
        # Create notification for moderators
        if instance.status == 'pending':
            # You might want to create a notification for moderators here
            # This depends on how you've implemented the moderation system
            pass
        
        # Create notification for the author
        Notification.objects.create(
            recipient=instance.author,
            type='product_status',
            title=_('Announcement Created'),
            text=_('Your announcement "{}" has been created and is pending review.').format(instance.title),
            link=f'/announcements/{instance.id}/'
        ) 