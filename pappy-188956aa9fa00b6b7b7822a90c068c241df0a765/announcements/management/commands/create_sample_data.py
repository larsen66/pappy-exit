from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from announcements.models import Announcement, AnimalAnnouncement, AnnouncementCategory
from pets.models import SwipeAction, Match

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates sample announcements for testing'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating users...')
        
        # Create admin users
        admin_user1 = User.objects.create_user(
            email='admin1@example.com',
            phone='+79001234567',
            password='admin',
            first_name='First',
            last_name='Admin',
            is_staff=True,
            is_superuser=True
        )
        
        admin_user2 = User.objects.create_user(
            email='admin2@example.com',
            phone='+79001234568',
            password='admin2',
            first_name='Second',
            last_name='Admin',
            is_staff=True,
            is_superuser=True
        )

        self.stdout.write('Creating categories...')
        # Create categories
        cats_category = AnnouncementCategory.objects.create(
            name='Кошки',
            slug='cats'
        )
        
        dogs_category = AnnouncementCategory.objects.create(
            name='Собаки',
            slug='dogs'
        )

        self.stdout.write('Creating announcements...')
        # Create announcements for first admin
        admin1_pets = [
            {
                'title': 'Красивый рыжий кот',
                'description': 'Очень ласковый и добрый кот ищет новый дом.',
                'category': cats_category,
                'breed': 'Сибирская',
                'age': 2,
                'gender': 'M',
                'color': 'Рыжий',
                'size': 'medium',
                'pedigree': True,
                'vaccinated': True,
                'passport': True,
                'microchipped': False
            },
            {
                'title': 'Щенок лабрадора',
                'description': 'Активный и игривый щенок ищет семью.',
                'category': dogs_category,
                'breed': 'Лабрадор',
                'age': 1,
                'gender': 'M',
                'color': 'Золотистый',
                'size': 'medium',
                'pedigree': True,
                'vaccinated': True,
                'passport': True,
                'microchipped': False
            }
        ]

        # Create announcements for second admin
        admin2_pets = [
            {
                'title': 'Британская кошечка',
                'description': 'Спокойная британская кошка ищет дом.',
                'category': cats_category,
                'breed': 'Британская',
                'age': 3,
                'gender': 'F',
                'color': 'Серый',
                'size': 'medium',
                'pedigree': True,
                'vaccinated': True,
                'passport': True,
                'microchipped': False
            },
            {
                'title': 'Хаски ищет дом',
                'description': 'Энергичный хаски ищет активную семью.',
                'category': dogs_category,
                'breed': 'Хаски',
                'age': 2,
                'gender': 'F',
                'color': 'Черно-белый',
                'size': 'large',
                'pedigree': True,
                'vaccinated': True,
                'passport': True,
                'microchipped': False
            }
        ]

        admin1_announcements = []
        # Create first admin's announcements
        for pet in admin1_pets:
            announcement = Announcement.objects.create(
                title=pet['title'],
                description=pet['description'],
                author=admin_user1,
                category=pet['category'],
                type='animal',
                status='active',
                location='Москва'
            )
            
            AnimalAnnouncement.objects.create(
                announcement=announcement,
                species='Кошка' if pet['category'] == cats_category else 'Собака',
                breed=pet['breed'],
                age=pet['age'],
                gender=pet['gender'],
                size=pet['size'],
                color=pet['color'],
                pedigree=pet['pedigree'],
                vaccinated=pet['vaccinated'],
                passport=pet['passport'],
                microchipped=pet['microchipped']
            )
            admin1_announcements.append(announcement)

        admin2_announcements = []
        # Create second admin's announcements
        for pet in admin2_pets:
            announcement = Announcement.objects.create(
                title=pet['title'],
                description=pet['description'],
                author=admin_user2,
                category=pet['category'],
                type='animal',
                status='active',
                location='Москва'
            )
            
            AnimalAnnouncement.objects.create(
                announcement=announcement,
                species='Кошка' if pet['category'] == cats_category else 'Собака',
                breed=pet['breed'],
                age=pet['age'],
                gender=pet['gender'],
                size=pet['size'],
                color=pet['color'],
                pedigree=pet['pedigree'],
                vaccinated=pet['vaccinated'],
                passport=pet['passport'],
                microchipped=pet['microchipped']
            )
            admin2_announcements.append(announcement)

        self.stdout.write('Creating matches...')
        # Create mutual likes between the first announcements (cats)
        SwipeAction.objects.create(
            user=admin_user1,
            announcement=admin2_announcements[0],  # British cat
            direction='LIKE'
        )

        SwipeAction.objects.create(
            user=admin_user2,
            announcement=admin1_announcements[0],  # Ginger cat
            direction='LIKE'
        )

        # Create a match for the cats
        Match.objects.create(
            user1=admin_user1,
            user2=admin_user2,
            announcement1=admin1_announcements[0],  # Ginger cat
            announcement2=admin2_announcements[0],   # British cat
            is_breeding_match=False
        )

        # Create one-sided like for dogs (no match)
        SwipeAction.objects.create(
            user=admin_user1,
            announcement=admin2_announcements[1],  # Husky
            direction='LIKE'
        )

        self.stdout.write('\nLogin Credentials:')
        self.stdout.write('-' * 50)
        self.stdout.write('First Admin:')
        self.stdout.write(f'Phone: {admin_user1.phone}')
        self.stdout.write('Password: admin')
        self.stdout.write('-' * 50)
        self.stdout.write('Second Admin:')
        self.stdout.write(f'Phone: {admin_user2.phone}')
        self.stdout.write('Password: admin2')
        self.stdout.write('-' * 50)
        
        self.stdout.write(self.style.SUCCESS('\nSuccessfully created sample data with match scenario')) 