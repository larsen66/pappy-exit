from rest_framework import serializers
from announcements.models import Announcement, AnimalAnnouncement
from .models import SwipeAction, Match

class AnimalAnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnimalAnnouncement
        fields = ['species', 'breed', 'age', 'gender', 'size', 'color', 'pedigree', 'vaccinated', 'passport', 'microchipped']

class AnnouncementSerializer(serializers.ModelSerializer):
    animal_details = AnimalAnnouncementSerializer()

    class Meta:
        model = Announcement
        fields = ['id', 'title', 'description', 'animal_details', 'created_at', 'status', 'type', 'location']

class MatchSerializer(serializers.ModelSerializer):
    announcement1_details = AnnouncementSerializer(source='announcement1')
    announcement2_details = AnnouncementSerializer(source='announcement2')

    class Meta:
        model = Match
        fields = ['id', 'user1', 'user2', 'announcement1_details', 'announcement2_details', 'created_at', 'is_active'] 