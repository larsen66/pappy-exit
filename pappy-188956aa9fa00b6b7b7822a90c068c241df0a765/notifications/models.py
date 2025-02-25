from django.db import models
from django.conf import settings

class Notification(models.Model):
    TYPES = (
        ('message', 'Новое сообщение'),
        ('match', 'Взаимный лайк'),
        ('product_status', 'Изменение статуса объявления'),
        ('verification', 'Статус верификации'),
        ('lost_pet_nearby', 'Потерянный питомец рядом'),
    )
    
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Получатель'
    )
    type = models.CharField('Тип', max_length=20, choices=TYPES)
    title = models.CharField('Заголовок', max_length=255)
    text = models.TextField('Текст')
    link = models.CharField('Ссылка', max_length=255, blank=True)
    is_read = models.BooleanField('Прочитано', default=False)
    created = models.DateTimeField('Создано', auto_now_add=True)
    
    class Meta:
        ordering = ['-created']
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
    
    def __str__(self):
        return f'{self.get_type_display()} для {self.recipient.get_full_name()}'
    
    @classmethod
    def create_message_notification(cls, recipient, dialog):
        """Создает уведомление о новом сообщении"""
        last_message = dialog.messages.last()
        if last_message and last_message.sender != recipient:
            return cls.objects.create(
                recipient=recipient,
                type='message',
                title='Новое сообщение',
                text=f'Новое сообщение от {last_message.sender.get_full_name()} по объявлению "{dialog.product.title}"',
                link=f'/chat/dialog/{dialog.id}/'
            )
    
    @classmethod
    def create_match_notification(cls, recipient, product):
        """Создает уведомление о взаимном лайке"""
        return cls.objects.create(
            recipient=recipient,
            type='match',
            title='Новый матч!',
            text=f'Взаимный интерес к объявлению "{product.title}"',
            link=f'/chat/create/{product.id}/'
        )
    
    @classmethod
    def create_product_status_notification(cls, recipient, product, status):
        """Создает уведомление об изменении статуса объявления"""
        status_choices = {
            'active': 'активный',
            'archived': 'в архиве',
            'draft': 'черновик',
            'moderation': 'на модерации',
            'rejected': 'отклонен'
        }
        status_display = status_choices.get(status, status)
        return cls.objects.create(
            recipient=recipient,
            type='product_status',
            title='Статус объявления изменен',
            text=f'Статус вашего объявления "{product.title}" изменен на "{status_display}"',
            link=f'/catalog/product/{product.slug}/'
        )
    
    @classmethod
    def create_verification_notification(cls, recipient, is_verified):
        """Создает уведомление о результате верификации"""
        status = 'подтвержден' if is_verified else 'отклонен'
        return cls.objects.create(
            recipient=recipient,
            type='verification',
            title='Результат верификации',
            text=f'Ваш аккаунт {status}',
            link='/profile/verification/'
        )
    
    @classmethod
    def create_lost_pet_notification(cls, recipient, product):
        """Создает уведомление о потерянном питомце поблизости"""
        return cls.objects.create(
            recipient=recipient,
            type='lost_pet_nearby',
            title='Потерянный питомец рядом',
            text=f'В вашем районе пропал питомец: {product.title}. Местоположение: {product.location}',
            link=f'/catalog/product/{product.slug}/'
        ) 