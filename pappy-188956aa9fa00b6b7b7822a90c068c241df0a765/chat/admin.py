from django.contrib import admin
from .models import Dialog, Message, MessageAttachment, LocationMessage, VoiceMessage, GroupChat

@admin.register(Dialog)
class DialogAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_participants', 'last_message', 'created_at']
    list_filter = ['created_at']
    search_fields = ['participants__username', 'participants__email']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    def get_participants(self, obj):
        return ", ".join([user.get_full_name() or user.username for user in obj.participants.all()])
    get_participants.short_description = 'Участники'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'dialog', 'sender', 'content', 'created_at', 'is_read']
    list_filter = ['is_read', 'created_at']
    search_fields = ['content', 'sender__username', 'sender__email']
    readonly_fields = ['dialog', 'sender', 'created_at']
    date_hierarchy = 'created_at'

@admin.register(MessageAttachment)
class MessageAttachmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'message', 'file_type', 'created_at']
    list_filter = ['file_type', 'created_at']
    search_fields = ['message__content', 'file_type']
    readonly_fields = ['created_at']

@admin.register(LocationMessage)
class LocationMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'dialog', 'sender', 'latitude', 'longitude', 'created_at']
    list_filter = ['created_at']
    search_fields = ['address', 'sender__username']
    readonly_fields = ['created_at']

@admin.register(VoiceMessage)
class VoiceMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'dialog', 'sender', 'duration', 'created_at']
    list_filter = ['created_at']
    search_fields = ['sender__username']
    readonly_fields = ['created_at']

@admin.register(GroupChat)
class GroupChatAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'admin', 'get_participants_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description', 'admin__username', 'participants__username']
    readonly_fields = ['created_at']
    
    def get_participants_count(self, obj):
        return obj.participants.count()
    get_participants_count.short_description = 'Количество участников' 