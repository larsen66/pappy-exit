from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from chat.models import Dialog, Message, MessageAttachment, LocationMessage, VoiceMessage, GroupChat
from django.utils import timezone
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates test chat data'

    def handle(self, *args, **options):
        # Create test admin users
        users = []
        for i in range(5):
            phone = f'+7900123456{i+1}'  # Sequential numbers from +79001234561 to +79001234565
            user, created = User.objects.get_or_create(
                phone=phone,
                defaults={
                    'email': f'admin{i+1}@example.com',
                    'first_name': f'Admin{i+1}',
                    'last_name': f'User',
                    'is_active': True,
                    'is_staff': True,
                    'is_superuser': True,
                    'password': 'admin'  # Note: This won't hash the password
                }
            )
            if created:
                user.set_password('admin')  # This properly hashes the password
                user.save()
                self.stdout.write(f'Created admin user with phone {phone} and password: admin')
            users.append(user)

        # Create dialogs with messages
        for i in range(3):
            # Select two random users
            participants = random.sample(users, 2)
            dialog = Dialog.objects.create(
                created_at=timezone.now(),
                updated_at=timezone.now()
            )
            dialog.participants.add(*participants)
            self.stdout.write(f'Created dialog between {participants[0].phone} and {participants[1].phone}')

            # Add messages to dialog
            for j in range(5):
                message = Message.objects.create(
                    dialog=dialog,
                    sender=random.choice(participants),
                    content=f'Test message {j} in dialog {i}',
                    is_read=random.choice([True, False]),
                    created_at=timezone.now()
                )
                self.stdout.write(f'Created message in dialog {i}')

                # Randomly add attachments
                if random.choice([True, False]):
                    attachment = MessageAttachment.objects.create(
                        message=message,
                        file='test.txt',
                        file_type='text/plain',
                        created_at=timezone.now()
                    )
                    self.stdout.write(f'Added attachment to message {message.id}')

                # Randomly add location messages
                if random.choice([True, False]):
                    location = LocationMessage.objects.create(
                        dialog=dialog,
                        sender=random.choice(participants),
                        latitude=random.uniform(-90, 90),
                        longitude=random.uniform(-180, 180),
                        address='Test address',
                        created_at=timezone.now()
                    )
                    self.stdout.write(f'Added location message to dialog {i}')

        # Create group chats
        for i in range(2):
            group = GroupChat.objects.create(
                name=f'Test Group {i}',
                description=f'Test group chat {i}',
                admin=random.choice(users),
                created_at=timezone.now(),
                updated_at=timezone.now()
            )
            # Add 3-4 random participants
            participants = random.sample(users, random.randint(3, 4))
            group.participants.add(*participants)
            self.stdout.write(f'Created group chat {group.name}')

            # Add messages to group chat
            for j in range(5):
                message = Message.objects.create(
                    group_chat=group,
                    sender=random.choice(participants),
                    content=f'Test message {j} in group {i}',
                    is_read=random.choice([True, False]),
                    created_at=timezone.now()
                )
                self.stdout.write(f'Created message in group chat {i}')

                # Randomly add attachments
                if random.choice([True, False]):
                    attachment = MessageAttachment.objects.create(
                        message=message,
                        file='test.txt',
                        file_type='text/plain',
                        created_at=timezone.now()
                    )
                    self.stdout.write(f'Added attachment to message {message.id}')

                # Randomly add voice messages
                if random.choice([True, False]):
                    voice = VoiceMessage.objects.create(
                        group_chat=group,
                        sender=random.choice(participants),
                        audio_file='test.mp3',
                        duration=random.randint(10, 60),
                        created_at=timezone.now()
                    )
                    self.stdout.write(f'Added voice message to group chat {i}')

        self.stdout.write(self.style.SUCCESS('Successfully created test chat data')) 