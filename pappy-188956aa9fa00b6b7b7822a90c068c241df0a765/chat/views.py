from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q, Max, Prefetch
from django.utils import timezone
from .models import Dialog, Message, MessageAttachment, LocationMessage, VoiceMessage, GroupChat
from catalog.models import Product
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, View

@login_required
def dialogs_list(request):
    """Список диалогов пользователя"""
    dialogs = Dialog.objects.filter(participants=request.user)\
        .select_related('product')\
        .prefetch_related('participants')\
        .annotate(last_message_time=Max('messages__created'))\
        .order_by('-last_message_time')
    
    return render(request, 'chat/dialogs_list.html', {'dialogs': dialogs})

@login_required
def dialog_detail(request, dialog_id):
    """Детальная страница диалога с сообщениями"""
    dialog = get_object_or_404(Dialog, id=dialog_id)
    
    # Проверяем права доступа
    if request.user not in dialog.participants.all():
        return HttpResponseForbidden('У вас нет доступа к этому диалогу')
    
    # Отмечаем сообщения как прочитанные
    Message.objects.filter(dialog=dialog)\
        .exclude(sender=request.user)\
        .filter(is_read=False)\
        .update(is_read=True)
    
    messages = dialog.messages.select_related('sender').all()
    
    return render(request, 'chat/dialog_detail.html', {
        'dialog': dialog,
        'messages': messages
    })

@login_required
def send_message(request, dialog_id):
    """API для отправки сообщения"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не поддерживается'}, status=405)
    
    dialog = get_object_or_404(Dialog, id=dialog_id)
    
    # Проверяем права доступа
    if request.user not in dialog.participants.all():
        return HttpResponseForbidden('У вас нет доступа к этому диалогу')
    
    text = request.POST.get('text', '').strip()
    
    if not text:
        return JsonResponse({'error': 'Текст сообщения не может быть пустым'}, status=400)
    
    message = Message.objects.create(
        dialog=dialog,
        sender=request.user,
        text=text
    )
    
    # Обновляем время последнего сообщения в диалоге
    dialog.updated = timezone.now()
    dialog.save()
    
    return JsonResponse({
        'id': message.id,
        'text': message.text,
        'created': message.created.strftime('%Y-%m-%d %H:%M:%S'),
        'sender_name': message.sender.get_full_name(),
        'is_own': True
    })

@login_required
def get_new_messages(request, dialog_id):
    """API для получения новых сообщений"""
    dialog = get_object_or_404(Dialog, id=dialog_id)
    
    # Проверяем права доступа
    if request.user not in dialog.participants.all():
        return HttpResponseForbidden('У вас нет доступа к этому диалогу')
    
    last_message_id = request.GET.get('last_id')
    
    messages_query = dialog.messages.select_related('sender')
    
    if last_message_id:
        messages_query = messages_query.filter(id__gt=last_message_id)
    
    messages = messages_query.all()
    
    # Отмечаем полученные сообщения как прочитанные
    messages.exclude(sender=request.user).filter(is_read=False).update(is_read=True)
    
    return JsonResponse({
        'messages': [{
            'id': msg.id,
            'text': msg.text,
            'created': msg.created.strftime('%Y-%m-%d %H:%M:%S'),
            'sender_name': msg.sender.get_full_name(),
            'is_own': msg.sender == request.user
        } for msg in messages]
    })

@login_required
def create_dialog(request, product_id):
    """Создание нового диалога"""
    product = get_object_or_404(Product, id=product_id)
    
    # Проверяем, не пытается ли пользователь создать диалог с самим собой
    if product.seller == request.user:
        return JsonResponse(
            {'error': 'Нельзя создать диалог с самим собой'},
            status=400
        )
    
    # Проверяем, существует ли уже диалог
    existing_dialog = Dialog.objects.filter(
        participants=request.user,
        product=product
    ).first()
    
    if existing_dialog:
        return JsonResponse(
            {'error': 'Диалог уже существует'},
            status=400
        )
    
    # Создаем новый диалог
    dialog = Dialog.objects.create(product=product)
    dialog.participants.add(request.user, product.seller)
    
    return redirect('chat:dialog_detail', dialog_id=dialog.id)

class DialogListView(LoginRequiredMixin, ListView):
    """Представление для списка диалогов пользователя"""
    model = Dialog
    template_name = 'chat/dialogs_list.html'
    context_object_name = 'dialogs'
    
    def get_queryset(self):
        return Dialog.objects.filter(
            participants=self.request.user
        ).annotate(
            last_message_time=Max('messages__created_at')
        ).order_by('-last_message_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unread_count'] = Message.objects.filter(
            dialog__participants=self.request.user,
            is_read=False
        ).exclude(sender=self.request.user).count()
        return context

class DialogDetailView(LoginRequiredMixin, DetailView):
    """Представление для просмотра конкретного диалога"""
    model = Dialog
    template_name = 'chat/dialog_detail.html'
    context_object_name = 'dialog'
    
    def get_object(self):
        return get_object_or_404(
            Dialog,
            id=self.kwargs['dialog_id'],
            participants=self.request.user
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dialog = self.get_object()
        
        # Получаем сообщения с вложениями
        messages = dialog.messages.select_related('sender').prefetch_related(
            Prefetch('attachments', queryset=MessageAttachment.objects.all())
        )
        
        # Помечаем непрочитанные сообщения как прочитанные
        unread_messages = messages.filter(
            is_read=False
        ).exclude(sender=self.request.user)
        
        for message in unread_messages:
            message.mark_as_read()
            
        context['messages'] = messages
        context['opponent'] = dialog.get_opponent(self.request.user)
        return context

class SendMessageView(LoginRequiredMixin, View):
    """Представление для отправки сообщения"""
    def post(self, request, dialog_id):
        dialog = get_object_or_404(Dialog, id=dialog_id, participants=request.user)
        content = request.POST.get('content')
        
        if not content:
            return JsonResponse({'error': 'Сообщение не может быть пустым'}, status=400)
            
        message = Message.objects.create(
            dialog=dialog,
            sender=request.user,
            content=content
        )
        
        # Обработка вложений
        for file in request.FILES.getlist('attachments'):
            MessageAttachment.objects.create(
                message=message,
                file=file,
                file_type=file.content_type
            )
            
        # Обновляем последнее сообщение в диалоге
        dialog.last_message = message
        dialog.save()
        
        return JsonResponse({
            'message_id': message.id,
            'content': message.content,
            'created_at': message.created_at.isoformat(),
            'sender_name': message.sender.get_full_name() or message.sender.username
        })

class SendLocationView(LoginRequiredMixin, View):
    """Представление для отправки геолокации"""
    def post(self, request, dialog_id):
        dialog = get_object_or_404(Dialog, id=dialog_id, participants=request.user)
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        address = request.POST.get('address', '')
        
        if not all([latitude, longitude]):
            return JsonResponse({'error': 'Не указаны координаты'}, status=400)
            
        message = LocationMessage.objects.create(
            dialog=dialog,
            sender=request.user,
            content=f'Геолокация: {address}' if address else 'Геолокация',
            latitude=float(latitude),
            longitude=float(longitude),
            address=address
        )
        
        dialog.last_message = message
        dialog.save()
        
        return JsonResponse({
            'message_id': message.id,
            'latitude': message.latitude,
            'longitude': message.longitude,
            'address': message.address,
            'created_at': message.created_at.isoformat()
        })

class SendVoiceMessageView(LoginRequiredMixin, View):
    """Представление для отправки голосового сообщения"""
    def post(self, request, dialog_id):
        dialog = get_object_or_404(Dialog, id=dialog_id, participants=request.user)
        audio_file = request.FILES.get('audio')
        duration = request.POST.get('duration')
        
        if not all([audio_file, duration]):
            return JsonResponse({'error': 'Не указан аудио файл или длительность'}, status=400)
            
        message = VoiceMessage.objects.create(
            dialog=dialog,
            sender=request.user,
            content='Голосовое сообщение',
            audio_file=audio_file,
            duration=int(duration)
        )
        
        dialog.last_message = message
        dialog.save()
        
        return JsonResponse({
            'message_id': message.id,
            'audio_url': message.audio_file.url,
            'duration': message.duration,
            'created_at': message.created_at.isoformat()
        })

class MessageSearchView(LoginRequiredMixin, ListView):
    """Представление для поиска по сообщениям"""
    model = Message
    template_name = 'chat/search_results.html'
    context_object_name = 'messages'
    paginate_by = 20
    
    def get_queryset(self):
        query = self.request.GET.get('q', '')
        return Message.objects.filter(
            Q(content__icontains=query),
            dialog__participants=self.request.user
        ).select_related('dialog', 'sender').order_by('-created_at')

class GroupChatView(LoginRequiredMixin, DetailView):
    """Представление для группового чата"""
    model = GroupChat
    template_name = 'chat/group_chat.html'
    context_object_name = 'chat'
    
    def get_object(self):
        return get_object_or_404(
            GroupChat,
            id=self.kwargs['chat_id'],
            participants=self.request.user
        )
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        chat = self.get_object()
        
        context['messages'] = chat.messages.select_related('sender').prefetch_related(
            'attachments'
        ).order_by('created_at')
        context['participants'] = chat.participants.all()
        context['is_admin'] = chat.admin == self.request.user
        
        return context 