from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Dialog, Message, MessageAttachment, LocationMessage, VoiceMessage, GroupChat
from decimal import Decimal
import json

User = get_user_model()

class ChatTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create test users
        self.user1 = User.objects.create(phone='+79991234567')
        self.user2 = User.objects.create(phone='+79991234568')
        self.user3 = User.objects.create(phone='+79991234569')
        
        # Create test dialog
        self.dialog = Dialog.objects.create()
        self.dialog.participants.add(self.user1, self.user2)
        
        # Create test group chat
        self.group_chat = GroupChat.objects.create(
            name='Test Group',
            admin=self.user1,
            description='Test group chat'
        )
        self.group_chat.participants.add(self.user1, self.user2, self.user3)
        
        # Login as user1
        self.client.force_login(self.user1)

    def test_dialog_creation(self):
        """Test dialog creation between two users"""
        response = self.client.post(reverse('chat:create_dialog'), {
            'participant_id': self.user3.id
        })
        self.assertEqual(response.status_code, 201)
        dialog = Dialog.objects.latest('id')
        self.assertIn(self.user1, dialog.participants.all())
        self.assertIn(self.user3, dialog.participants.all())

    def test_message_sending(self):
        """Test sending text messages in dialog"""
        response = self.client.post(reverse('chat:send_message', args=[self.dialog.id]), {
            'content': 'Test message'
        })
        self.assertEqual(response.status_code, 201)
        message = Message.objects.latest('id')
        self.assertEqual(message.content, 'Test message')
        self.assertEqual(message.sender, self.user1)
        self.assertEqual(message.dialog, self.dialog)

    def test_file_attachment(self):
        """Test sending messages with file attachments"""
        file_content = b'Test file content'
        test_file = SimpleUploadedFile('test.txt', file_content)
        response = self.client.post(reverse('chat:send_message', args=[self.dialog.id]), {
            'content': 'Message with attachment',
            'attachment': test_file
        })
        self.assertEqual(response.status_code, 201)
        attachment = MessageAttachment.objects.latest('id')
        self.assertEqual(attachment.message.content, 'Message with attachment')
        self.assertTrue(attachment.file.name.endswith('test.txt'))

    def test_location_message(self):
        """Test sending location messages"""
        location_data = {
            'latitude': 55.7558,
            'longitude': 37.6173,
            'address': 'Test Address'
        }
        response = self.client.post(reverse('chat:send_location', args=[self.dialog.id]), 
                                  location_data)
        self.assertEqual(response.status_code, 201)
        location = LocationMessage.objects.latest('id')
        self.assertEqual(float(location.latitude), location_data['latitude'])
        self.assertEqual(float(location.longitude), location_data['longitude'])
        self.assertEqual(location.address, location_data['address'])

    def test_message_read_status(self):
        """Test message read status functionality"""
        # Send message as user2
        self.client.force_login(self.user2)
        response = self.client.post(reverse('chat:send_message', args=[self.dialog.id]), {
            'content': 'Test unread message'
        })
        message_id = json.loads(response.content)['id']
        
        # Check message is unread
        message = Message.objects.get(id=message_id)
        self.assertFalse(message.is_read)
        
        # Read message as user1
        self.client.force_login(self.user1)
        response = self.client.post(reverse('chat:mark_read', args=[message_id]))
        self.assertEqual(response.status_code, 200)
        
        # Verify message is now read
        message.refresh_from_db()
        self.assertTrue(message.is_read)

    def test_group_chat_functionality(self):
        """Test group chat functionality"""
        # Send message to group
        response = self.client.post(reverse('chat:send_group_message', args=[self.group_chat.id]), {
            'content': 'Test group message'
        })
        self.assertEqual(response.status_code, 201)
        
        # Add new participant
        response = self.client.post(reverse('chat:add_participant', args=[self.group_chat.id]), {
            'user_id': self.user3.id
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.user3, self.group_chat.participants.all())
        
        # Remove participant
        response = self.client.post(reverse('chat:remove_participant', args=[self.group_chat.id]), {
            'user_id': self.user3.id
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.user3, self.group_chat.participants.all())

    def test_message_search(self):
        """Test message search functionality"""
        # Create test messages
        Message.objects.create(dialog=self.dialog, sender=self.user1, content='Test search message 1')
        Message.objects.create(dialog=self.dialog, sender=self.user2, content='Test search message 2')
        Message.objects.create(dialog=self.dialog, sender=self.user1, content='Different content')
        
        response = self.client.get(reverse('chat:message_search'), {'q': 'search message'})
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)
        self.assertEqual(len(results['messages']), 2)

    def test_dialog_permissions(self):
        """Test dialog access permissions"""
        # Try to access dialog as non-participant
        self.client.force_login(self.user3)
        response = self.client.get(reverse('chat:dialog_detail', args=[self.dialog.id]))
        self.assertEqual(response.status_code, 403)
        
        # Try to send message as non-participant
        response = self.client.post(reverse('chat:send_message', args=[self.dialog.id]), {
            'content': 'Unauthorized message'
        })
        self.assertEqual(response.status_code, 403)

    def test_group_chat_permissions(self):
        """Test group chat permissions"""
        # Create new user who is not in the group
        new_user = User.objects.create(phone='+79991234570')
        self.client.force_login(new_user)
        
        # Try to access group chat
        response = self.client.get(reverse('chat:group_chat_detail', args=[self.group_chat.id]))
        self.assertEqual(response.status_code, 403)
        
        # Try to send message to group
        response = self.client.post(reverse('chat:send_group_message', args=[self.group_chat.id]), {
            'content': 'Unauthorized group message'
        })
        self.assertEqual(response.status_code, 403)