from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import (
    Announcement,
    AnnouncementCategory,
    AnimalAnnouncement,
    ServiceAnnouncement,
    MatingAnnouncement,
    LostFoundAnnouncement,
    AnnouncementImage
)

class AnnouncementImageInline(admin.TabularInline):
    model = AnnouncementImage
    extra = 1

@admin.register(AnnouncementCategory)
class AnnouncementCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    list_filter = ('parent',)

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'status', 'author', 'created_at', 'views_count')
    list_filter = ('type', 'status', 'created_at')
    search_fields = ('title', 'description', 'author__phone')
    inlines = [AnnouncementImageInline]
    date_hierarchy = 'created_at'

@admin.register(AnimalAnnouncement)
class AnimalAnnouncementAdmin(admin.ModelAdmin):
    list_display = ('announcement', 'species', 'breed', 'age', 'gender')
    list_filter = ('species', 'breed', 'gender')
    search_fields = ('announcement__title', 'breed')

@admin.register(ServiceAnnouncement)
class ServiceAnnouncementAdmin(admin.ModelAdmin):
    list_display = ('announcement', 'service_type', 'experience')
    list_filter = ('service_type',)
    search_fields = ('announcement__title', 'service_type')

@admin.register(MatingAnnouncement)
class MatingAnnouncementAdmin(admin.ModelAdmin):
    list_display = ('announcement', 'requirements')
    search_fields = ('announcement__title', 'requirements')

@admin.register(LostFoundAnnouncement)
class LostFoundAnnouncementAdmin(admin.ModelAdmin):
    list_display = ('announcement', 'type', 'date_lost_found')
    list_filter = ('type', 'date_lost_found')
    search_fields = ('announcement__title', 'distinctive_features')
