def unread_notifications_count(request):
    """Добавляет количество непрочитанных уведомлений в контекст шаблона"""
    if request.user.is_authenticated:
        count = request.user.notifications.filter(is_read=False).count()
        return {'unread_notifications_count': count}
    return {'unread_notifications_count': 0} 