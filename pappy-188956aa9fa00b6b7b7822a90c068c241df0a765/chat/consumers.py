import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Dialog, Message, User, GroupChat

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.dialog_id = self.scope['url_route']['kwargs']['dialog_id']
        self.room_group_name = f'chat_{self.dialog_id}'
        self.user = self.scope['user']
        
        # Проверка доступа к диалогу
        if not await self.has_dialog_access():
            await self.close()
            return
        
        # Присоединение к группе чата
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Обновление статуса пользователя
        await self.update_user_status(True)
        
        # Отправка уведомления другим участникам
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'user': {
                    'id': self.user.id,
                    'is_online': True
                }
            }
        )
    
    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            # Обновление статуса пользователя
            await self.update_user_status(False)
            
            # Отправка уведомления другим участникам
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_status',
                    'user': {
                        'id': self.user.id,
                        'is_online': False
                    }
                }
            )
            
            # Отключение от группы чата
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'typing':
            # Обработка статуса печати
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_status',
                    'user': {
                        'id': self.user.id,
                        'typing': data.get('typing', False)
                    }
                }
            )
        elif message_type == 'read':
            # Обработка прочтения сообщений
            message_ids = data.get('message_ids', [])
            await self.mark_messages_read(message_ids)
            
            # Отправка уведомления о прочтении
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'messages_read',
                    'message_ids': message_ids,
                    'user_id': self.user.id
                }
            )
    
    async def new_message(self, event):
        """Отправка нового сообщения клиенту"""
        message = event['message']
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'message': message
        }))
    
    async def typing_status(self, event):
        """Отправка статуса печати клиенту"""
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user': event['user']
        }))
    
    async def user_status(self, event):
        """Отправка статуса пользователя клиенту"""
        await self.send(text_data=json.dumps({
            'type': 'user_status',
            'user': event['user']
        }))
    
    async def messages_read(self, event):
        """Отправка статуса прочтения сообщений клиенту"""
        await self.send(text_data=json.dumps({
            'type': 'messages_read',
            'message_ids': event['message_ids'],
            'user_id': event['user_id']
        }))
    
    @database_sync_to_async
    def has_dialog_access(self):
        """Проверка доступа пользователя к диалогу"""
        try:
            dialog = Dialog.objects.get(id=self.dialog_id)
            return self.user in dialog.participants.all()
        except Dialog.DoesNotExist:
            return False
    
    @database_sync_to_async
    def update_user_status(self, is_online):
        """Обновление статуса пользователя"""
        User.objects.filter(id=self.user.id).update(
            is_online=is_online,
            last_activity=timezone.now()
        )
    
    @database_sync_to_async
    def mark_messages_read(self, message_ids):
        """Отметка сообщений как прочитанных"""
        Message.objects.filter(
            id__in=message_ids,
            dialog_id=self.dialog_id
        ).exclude(
            sender=self.user
        ).update(
            is_read=True,
            read_at=timezone.now()
        )


class GroupChatConsumer(ChatConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f'group_chat_{self.chat_id}'
        self.user = self.scope['user']
        
        # Проверка доступа к групповому чату
        if not await self.has_group_chat_access():
            await self.close()
            return
        
        # Присоединение к группе чата
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Обновление статуса пользователя
        await self.update_user_status(True)
        
        # Отправка уведомления другим участникам
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'user': {
                    'id': self.user.id,
                    'is_online': True
                }
            }
        )
    
    @database_sync_to_async
    def has_group_chat_access(self):
        """Проверка доступа пользователя к групповому чату"""
        try:
            group_chat = GroupChat.objects.get(id=self.chat_id)
            return self.user in group_chat.participants.all()
        except GroupChat.DoesNotExist:
            return False

    async def handle_new_message(self, data):
        """Обработка нового сообщения в групповом чате"""
        content = data.get('content')
        if not content:
            return
            
        # Создаем новое сообщение
        message = Message.objects.create(
            dialog_id=self.chat_id,  # GroupChat наследуется от Dialog
            sender=self.user,
            content=content
        )
        
        # Обновляем последнее сообщение
        chat = GroupChat.objects.get(id=self.chat_id)
        chat.last_message = message
        chat.save()
        
        # Отправляем сообщение всем участникам
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': {
                    'id': message.id,
                    'content': message.content,
                    'sender_id': message.sender.id,
                    'sender_name': message.sender.get_full_name() or message.sender.username,
                    'created_at': message.created_at.isoformat()
                }
            }
        ) 