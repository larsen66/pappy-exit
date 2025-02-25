from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

User = get_user_model()

class DialogManager(models.Manager):
    def get_or_create_for_users(self, user1, user2):
        """
        Получает или создает диалог между двумя пользователями
        """
        dialog = self.filter(participants=user1).filter(participants=user2).first()
        if dialog:
            return dialog, False
        
        dialog = self.create()
        dialog.participants.add(user1, user2)
        return dialog, True

class Dialog(models.Model):
    """Модель диалога между пользователями"""
    participants = models.ManyToManyField(User, related_name='dialogs')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    last_message = models.ForeignKey(
        'Message',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='last_message_dialog'
    )
    
    objects = DialogManager()
    
    class Meta:
        verbose_name = 'Диалог'
        verbose_name_plural = 'Диалоги'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)

    def get_messages(self):
        return self.messages.all()

    def get_opponent(self, user):
        return self.participants.exclude(id=user.id).first()

    @staticmethod
    def get_or_create_dialog(user1, user2):
        dialog = Dialog.objects.filter(
            participants=user1
        ).filter(
            participants=user2
        ).first()
        
        if dialog is None:
            dialog = Dialog.objects.create()
            dialog.participants.add(user1, user2)
            
        return dialog

    def __str__(self):
        return f'Dialog {self.id} between {", ".join(str(p) for p in self.participants.all())}'

class GroupChat(models.Model):
    """Модель группового чата"""
    
    PRIVACY_CHOICES = [
        ('public', _('Публичный')),
        ('private', _('Приватный')),
        ('secret', _('Секретный')),
    ]
    
    name = models.CharField(_('название'), max_length=100)
    description = models.TextField(_('описание'), blank=True)
    avatar = models.ImageField(_('аватар'), upload_to='chat/avatars/', null=True, blank=True)
    created_at = models.DateTimeField(_('создан'), auto_now_add=True)
    
    privacy = models.CharField(
        _('приватность'),
        max_length=20,
        choices=PRIVACY_CHOICES,
        default='private'
    )
    
    invite_link = models.CharField(_('ссылка-приглашение'), max_length=100, unique=True, null=True, blank=True)
    max_members = models.PositiveIntegerField(_('максимум участников'), default=100)
    
    class Meta:
        verbose_name = _('групповой чат')
        verbose_name_plural = _('групповые чаты')

class GroupChatMember(models.Model):
    """Модель участника группового чата"""
    
    ROLE_CHOICES = [
        ('owner', _('Владелец')),
        ('admin', _('Администратор')),
        ('moderator', _('Модератор')),
        ('member', _('Участник')),
    ]
    
    chat = models.ForeignKey(
        GroupChat,
        on_delete=models.CASCADE,
        related_name='members',
        verbose_name=_('чат')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='group_chats',
        verbose_name=_('пользователь')
    )
    role = models.CharField(
        _('роль'),
        max_length=20,
        choices=ROLE_CHOICES,
        default='member'
    )
    joined_at = models.DateTimeField(_('присоединился'), auto_now_add=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='invited_members',
        verbose_name=_('пригласил')
    )
    
    class Meta:
        verbose_name = _('участник группового чата')
        verbose_name_plural = _('участники группового чата')
        unique_together = ['chat', 'user']
    
    def clean(self):
        # Проверка на максимальное количество участников
        if self.chat.members.count() >= self.chat.max_members:
            raise ValidationError(_('Достигнуто максимальное количество участников'))
        
        # Проверка на единственного владельца
        if self.role == 'owner' and \
           self.chat.members.filter(role='owner').exists() and \
           not self.pk:
            raise ValidationError(_('У чата уже есть владелец'))

class GroupChatInvite(models.Model):
    """Модель приглашения в групповой чат"""
    
    chat = models.ForeignKey(
        GroupChat,
        on_delete=models.CASCADE,
        related_name='invites',
        verbose_name=_('чат')
    )
    inviter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_invites',
        verbose_name=_('пригласивший')
    )
    invitee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_invites',
        verbose_name=_('приглашенный')
    )
    created_at = models.DateTimeField(_('создано'), auto_now_add=True)
    expires_at = models.DateTimeField(_('истекает'))
    is_accepted = models.BooleanField(_('принято'), default=False)
    
    class Meta:
        verbose_name = _('приглашение в чат')
        verbose_name_plural = _('приглашения в чат')
        unique_together = ['chat', 'invitee']

class GroupChatMessage(models.Model):
    """Модель сообщения в групповом чате"""
    
    chat = models.ForeignKey(
        GroupChat,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_('чат')
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='group_messages',
        verbose_name=_('отправитель')
    )
    content = models.TextField(_('содержание'))
    created_at = models.DateTimeField(_('создано'), auto_now_add=True)
    edited_at = models.DateTimeField(_('изменено'), null=True, blank=True)
    is_system = models.BooleanField(_('системное'), default=False)
    reply_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name=_('ответ на')
    )
    
    class Meta:
        verbose_name = _('сообщение группового чата')
        verbose_name_plural = _('сообщения группового чата')
        ordering = ['created_at']

class GroupChatModeration(models.Model):
    """Модель модерации в групповом чате"""
    
    ACTION_CHOICES = [
        ('mute', _('Мут')),
        ('kick', _('Кик')),
        ('ban', _('Бан')),
    ]
    
    chat = models.ForeignKey(
        GroupChat,
        on_delete=models.CASCADE,
        related_name='moderation_actions',
        verbose_name=_('чат')
    )
    moderator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='moderation_actions',
        verbose_name=_('модератор')
    )
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_actions',
        verbose_name=_('цель')
    )
    action = models.CharField(_('действие'), max_length=20, choices=ACTION_CHOICES)
    reason = models.TextField(_('причина'))
    created_at = models.DateTimeField(_('создано'), auto_now_add=True)
    expires_at = models.DateTimeField(_('истекает'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('действие модерации')
        verbose_name_plural = _('действия модерации')
        ordering = ['-created_at']

class Message(models.Model):
    """Базовая модель сообщения"""
    dialog = models.ForeignKey(
        Dialog,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='messages'
    )
    group_chat = models.ForeignKey(
        GroupChat,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='messages'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.dialog and not self.group_chat:
            raise ValidationError('Message must belong to either a dialog or a group chat')
        if self.dialog and self.group_chat:
            raise ValidationError('Message cannot belong to both dialog and group chat')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        ordering = ['created_at']

    def __str__(self):
        chat_type = 'dialog' if self.dialog else 'group'
        chat_id = self.dialog.id if self.dialog else self.group_chat.id
        return f'Message in {chat_type} {chat_id} from {self.sender}'

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.save()

class MessageAttachment(models.Model):
    """Модель для хранения файлов, прикрепленных к сообщениям"""
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(upload_to='chat_attachments/')
    file_type = models.CharField(max_length=50)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f'Attachment {self.file_type} for message {self.message.id}'

class LocationMessage(models.Model):
    """Модель для сообщений с геолокацией"""
    dialog = models.ForeignKey(
        Dialog,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    group_chat = models.ForeignKey(
        GroupChat,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='location_messages'
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    address = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.dialog and not self.group_chat:
            raise ValidationError('Location message must belong to either a dialog or a group chat')
        if self.dialog and self.group_chat:
            raise ValidationError('Location message cannot belong to both dialog and group chat')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        chat_type = 'dialog' if self.dialog else 'group'
        chat_id = self.dialog.id if self.dialog else self.group_chat.id
        return f'Location in {chat_type} {chat_id} from {self.sender}'

class VoiceMessage(models.Model):
    """Модель для голосовых сообщений"""
    dialog = models.ForeignKey(
        Dialog,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    group_chat = models.ForeignKey(
        GroupChat,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='voice_messages'
    )
    audio_file = models.FileField(upload_to='voice_messages/')
    duration = models.IntegerField()  # длительность в секундах
    created_at = models.DateTimeField(default=timezone.now)
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.dialog and not self.group_chat:
            raise ValidationError('Voice message must belong to either a dialog or a group chat')
        if self.dialog and self.group_chat:
            raise ValidationError('Voice message cannot belong to both dialog and group chat')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        chat_type = 'dialog' if self.dialog else 'group'
        chat_id = self.dialog.id if self.dialog else self.group_chat.id
        return f'Voice message in {chat_type} {chat_id} from {self.sender}' 