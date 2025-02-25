from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'type', 'title', 'is_read', 'created']
    list_filter = ['type', 'is_read', 'created']
    search_fields = ['recipient__first_name', 'recipient__last_name', 'recipient__phone', 'title', 'text']
    readonly_fields = ['recipient', 'type', 'title', 'text', 'link', 'created']
    date_hierarchy = 'created'
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, f'Отмечено прочитанными: {queryset.count()}')
    mark_as_read.short_description = 'Отметить как прочитанные'
    
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
        self.message_user(request, f'Отмечено непрочитанными: {queryset.count()}')
    mark_as_unread.short_description = 'Отметить как непрочитанные'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False 