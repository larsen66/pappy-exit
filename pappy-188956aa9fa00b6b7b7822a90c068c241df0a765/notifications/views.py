from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from .models import Notification

@login_required
def notifications_list(request):
    """Список уведомлений пользователя"""
    notifications = Notification.objects.filter(recipient=request.user)
    return render(request, 'notifications/list.html', {
        'notifications': notifications
    })

@login_required
def mark_all_as_read(request):
    """Отметить все уведомления как прочитанные"""
    if request.method == 'POST':
        Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).update(is_read=True)
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'error': 'Метод не поддерживается'}, status=405)

@login_required
def clear_all_notifications(request):
    """Удалить все уведомления"""
    if request.method == 'POST':
        Notification.objects.filter(recipient=request.user).delete()
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'error': 'Метод не поддерживается'}, status=405)

@login_required
def mark_as_read(request, notification_id=None):
    """Отмечает уведомление(я) как прочитанное"""
    if notification_id:
        # Отмечаем конкретное уведомление
        notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
        notification.is_read = True
        notification.save()
    else:
        # Отмечаем все уведомления
        request.user.notifications.filter(is_read=False).update(is_read=True)
    
    return JsonResponse({'status': 'ok'})

@login_required
def get_unread_count(request):
    """Возвращает количество непрочитанных уведомлений"""
    count = request.user.notifications.filter(is_read=False).count()
    return JsonResponse({'count': count})

@login_required
def delete_notification(request, notification_id):
    """Удаляет уведомление"""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.delete()
    return JsonResponse({'status': 'ok'}) 