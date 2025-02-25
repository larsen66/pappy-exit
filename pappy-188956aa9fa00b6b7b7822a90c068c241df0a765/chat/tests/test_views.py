from django.test import TransactionTestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from login_auth.models import User
from catalog.models import Category, Product
from chat.models import Dialog, Message
from decimal import Decimal

class ChatTest(TransactionTestCase):
    def setUp(self):
        # Create users
        self.buyer = User.objects.create_user(
            phone='+79991234567',
            password='testpass123'
        )
        self.seller = User.objects.create_user(
            phone='+79997654321',
            password='seller123',
            is_seller=True
        )
        self.client.login(phone='+79991234567', password='testpass123')
        
        # Create category and product
        self.category = Category.objects.create(name='Кошки')
        self.product = Product.objects.create(
            seller=self.seller,
            category=self.category,
            title='Британский котенок',
            price=15000,
            condition='new',
            status='active'
        )
        
        # Create dialog
        self.dialog = Dialog.objects.create()
        self.dialog.participants.add(self.buyer, self.seller)
    
    def test_send_message(self):
        """Test sending text messages in dialog"""
        response = self.client.post(reverse('chat:send_message'), {
            'dialog': self.dialog.id,
            'text': 'Здравствуйте! Котенок еще доступен?'
        })
        self.assertEqual(response.status_code, 200)
        
        # Check message was created
        message = Message.objects.get(dialog=self.dialog)
        self.assertEqual(message.sender, self.buyer)
        self.assertEqual(message.text, 'Здравствуйте! Котенок еще доступен?')
    
    def test_send_attachment(self):
        """Test sending file attachments in dialog"""
        image = SimpleUploadedFile(
            "photo.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        
        response = self.client.post(reverse('chat:send_message'), {
            'dialog': self.dialog.id,
            'text': 'Вот фото моего дома',
            'attachment': image
        })
        self.assertEqual(response.status_code, 200)
        
        # Check message was created with attachment
        message = Message.objects.get(dialog=self.dialog)
        self.assertTrue(message.attachment)
        self.assertEqual(message.attachment.name.split('/')[-1], 'photo.jpg')
    
    def test_send_invoice(self):
        """Test that seller can send invoice to buyer"""
        # Login as seller
        self.client.login(phone='+79997654321', password='seller123')
        
        response = self.client.post(reverse('chat:send_invoice'), {
            'dialog': self.dialog.id,
            'amount': '15000.00',
            'description': 'Оплата за котенка'
        })
        self.assertEqual(response.status_code, 200)
        
        # Check invoice message was created
        message = Message.objects.get(dialog=self.dialog, message_type='invoice')
        self.assertEqual(message.sender, self.seller)
        self.assertEqual(message.amount, Decimal('15000.00'))
        self.assertEqual(message.status, 'pending')
    
    def test_pay_invoice(self):
        """Test paying an invoice (mock payment)"""
        # Create invoice first
        invoice = Message.objects.create(
            dialog=self.dialog,
            sender=self.seller,
            message_type='invoice',
            amount=Decimal('15000.00'),
            status='pending'
        )
        
        # Mock payment
        response = self.client.post(reverse('chat:pay_invoice'), {
            'message_id': invoice.id,
            'payment_token': 'mock_token'
        })
        self.assertEqual(response.status_code, 200)
        
        # Check invoice was marked as paid
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, 'paid')
    
    def test_buyer_cant_send_invoice(self):
        """Test that only seller can send invoices"""
        response = self.client.post(reverse('chat:send_invoice'), {
            'dialog': self.dialog.id,
            'amount': '15000.00',
            'description': 'Тестовый счет'
        })
        self.assertEqual(response.status_code, 403)
    
    def test_dialog_messages_pagination(self):
        """Test that messages are properly paginated"""
        # Create 25 messages
        for i in range(25):
            Message.objects.create(
                dialog=self.dialog,
                sender=self.buyer,
                text=f'Message {i}'
            )
        
        # Get first page (20 messages by default)
        response = self.client.get(reverse('chat:dialog_messages', 
                                         kwargs={'dialog_id': self.dialog.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['messages']), 20)
        
        # Get second page
        response = self.client.get(
            reverse('chat:dialog_messages', 
                   kwargs={'dialog_id': self.dialog.id}) + '?page=2'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['messages']), 5)
    
    def test_dialog_participants(self):
        """Test that only dialog participants can access it"""
        # Create another user
        other_user = User.objects.create_user(
            phone='+79995555555',
            password='pass123'
        )
        self.client.login(phone='+79995555555', password='pass123')
        
        # Try to access dialog
        response = self.client.get(reverse('chat:dialog_messages',
                                         kwargs={'dialog_id': self.dialog.id}))
        self.assertEqual(response.status_code, 403) 