from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # Список диалогов
    path('', views.DialogListView.as_view(), name='dialogs_list'),
    
    # Детальная страница диалога
    path('<int:dialog_id>/', views.DialogDetailView.as_view(), name='dialog_detail'),
    
    # Отправка сообщений
    path('<int:dialog_id>/send/', views.SendMessageView.as_view(), name='send_message'),
    path('<int:dialog_id>/send-location/', views.SendLocationView.as_view(), name='send_location'),
    path('<int:dialog_id>/send-voice/', views.SendVoiceMessageView.as_view(), name='send_voice'),
    
    # Поиск по сообщениям
    path('search/', views.MessageSearchView.as_view(), name='message_search'),
    
    # Групповые чаты
    path('group/<int:chat_id>/', views.GroupChatView.as_view(), name='group_chat'),
] 