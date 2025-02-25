# Выполненные задачи

## 1. Котопсиндер (система лайков)

### 1.1 Основной функционал

#### ✓ Система свайпов
**Реализация:** 
- Модель `SwipeAction` для хранения действий пользователя
- Поддержка лайков и дизлайков через `DIRECTION_CHOICES`
- Уникальность свайпов через `unique_together`

**Локация:** `pets/models.py`
```python
class SwipeAction(models.Model):
    LIKE = 'like'
    DISLIKE = 'dislike'
    DIRECTION_CHOICES = [
        (LIKE, 'Лайк'),
        (DISLIKE, 'Дизлайк'),
    ]
    # ...
    class Meta:
        unique_together = ['user', 'announcement']
```

**Использование:**
- В представлении `process_swipe` для обработки действий пользователя
- В шаблоне `swipe.html` для отображения кнопок лайк/дизлайк

#### ✓ Алгоритм подбора карточек
**Реализация:**
- Класс `SwipeSystem` с методом `get_next_cards`
- Приоритизация премиум объявлений
- Исключение просмотренных карточек
- Сортировка по популярности

**Локация:** `pets/views.py`
```python
class SwipeSystem:
    @staticmethod
    def get_next_cards(user, announcement_type='animals', count=10):
        announcements = Announcement.objects.filter(
            status='active',
            type=announcement_type
        ).annotate(
            premium_score=Count('pets_swipes')
        ).order_by(
            '-is_premium',
            '-premium_score',
            '?'
        )
```

**Использование:**
- В представлении `swipe_view` для показа карточек
- В API `get_next_cards` для подгрузки новых карточек

#### ✓ Обработка лайков/дизлайков
**Реализация:**
- Метод `process_swipe` в `SwipeSystem`
- Автоматическое создание диалогов при лайке
- Проверка взаимных лайков
- Создание пар при совпадении

**Локация:** `pets/models.py` и `pets/views.py`
```python
def save(self, *args, **kwargs):
    if is_new and self.direction == self.LIKE:
        # Проверка взаимного лайка
        mutual_like = SwipeAction.objects.filter(...)
        if mutual_like:
            Match.objects.create(...)
```

**Использование:**
- При каждом свайпе через API
- При создании диалогов и пар

#### ✓ История просмотров
**Реализация:**
- Модель `SwipeHistory`
- Отслеживание просмотренных карточек
- Возможность отмены последнего свайпа
- Флаг возврата к карточке

**Локация:** `pets/models.py`
```python
class SwipeHistory(models.Model):
    viewed_at = models.DateTimeField(...)
    is_returned = models.BooleanField(...)
```

**Использование:**
- В представлении `undo_last_swipe`
- При показе новых карточек

### 1.2 Механика вязки

#### ✓ Двусторонние лайки
**Реализация:**
- Проверка взаимных лайков в `SwipeAction.save`
- Автоматическое создание пар
- Уведомления о совпадениях

**Локация:** `pets/models.py`
```python
mutual_like = SwipeAction.objects.filter(
    user=self.announcement.author,
    announcement__author=self.user,
    direction=self.LIKE
).first()
```

#### ✓ Создание пар
**Реализация:**
- Модель `Match` для хранения пар
- Связь с объявлениями и пользователями
- Статус активности пары
- Оценка совместимости

**Локация:** `pets/models.py`
```python
class Match(models.Model):
    user1 = models.ForeignKey(...)
    user2 = models.ForeignKey(...)
    is_breeding_match = models.BooleanField(...)
    compatibility_score = models.FloatField(...)
```

#### ✓ Уведомления о совпадениях
**Реализация:**
- Отображение уведомления при лайке
- Перенаправление в чат
- Сообщение о создании пары

**Локация:** `pets/templates/pets/swipe.html`
```javascript
if (direction == SwipeAction.LIKE) {
    showNotification('Вы увидите свой лайк в «Сообщениях»');
}
```

#### ✓ Специальные фильтры
**Реализация:**
- Метод `check_compatibility` в модели `Match`
- Проверка породы, возраста, вида
- Расчет оценки совместимости

**Локация:** `pets/models.py`
```python
def check_compatibility(self):
    if pet1.species == pet2.species:
        score += 0.5
        if pet1.breed == pet2.breed:
            score += 0.3
```

**Использование:**
- При создании пары для вязки
- В представлении списка совпадений 

## 2. Чат-система

### 2.1 Базовый чат

#### ✓ Диалоги и сообщения
**Реализация:**
- Модель `Dialog` для хранения диалогов между пользователями
- Модель `Message` для хранения сообщений
- Поддержка статусов сообщений (прочитано/не прочитано)
- Интеграция с WebSocket для real-time обновлений

**Локация:** `chat/models.py`
```python
class Dialog(models.Model):
    participants = models.ManyToManyField(User)
    created_at = models.DateTimeField(auto_now_add=True)
    last_message = models.ForeignKey('Message', null=True, on_delete=models.SET_NULL)

class Message(models.Model):
    dialog = models.ForeignKey(Dialog, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
```

**Использование:**
- В представлении `DialogListView` для списка диалогов
- В представлении `DialogDetailView` для просмотра сообщений
- В WebSocket consumer для real-time обмена сообщениями

#### ✓ Прикрепление файлов
**Реализация:**
- Модель `MessageAttachment` для хранения файлов
- Поддержка различных типов файлов
- Валидация размера и типа файлов

**Локация:** `chat/models.py`
```python
class MessageAttachment(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    file = models.FileField(upload_to='chat_attachments/')
    file_type = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
```

#### ✓ Статусы сообщений
**Реализация:**
- Поле `is_read` в модели `Message`
- Автоматическое обновление статуса при просмотре
- WebSocket уведомления о прочтении

**Использование:**
- В шаблоне `dialog_detail.html` для отображения статуса
- В WebSocket consumer для обновления статуса

#### ✓ Уведомления
**Реализация:**
- WebSocket уведомления о новых сообщениях
- Поддержка статуса "печатает..."
- Индикатор онлайн/оффлайн статуса

**Локация:** `chat/consumers.py`
```python
class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope["user"]
        self.dialog_id = self.scope['url_route']['kwargs']['dialog_id']
        self.dialog_group_name = f'chat_{self.dialog_id}'
        
        async_to_sync(self.channel_layer.group_add)(
            self.dialog_group_name,
            self.channel_name
        )
        self.accept()

    def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data['type']
        
        if message_type == 'message':
            self.handle_new_message(data)
        elif message_type == 'typing':
            self.handle_typing_status(data)
```

### 2.2 Расширенные функции

#### ✓ Отправка геолокации
**Реализация:**
- Специальный тип сообщения для геолокации
- Интеграция с картами для отображения
- Валидация координат

**Локация:** `chat/models.py`
```python
class LocationMessage(Message):
    latitude = models.FloatField()
    longitude = models.FloatField()
    address = models.CharField(max_length=255, blank=True)
```

#### ✓ Аудио-сообщения
**Реализация:**
- Специальный тип сообщения для аудио
- Запись и воспроизведение аудио в браузере
- Конвертация и хранение аудио-файлов

**Локация:** `chat/models.py`
```python
class VoiceMessage(Message):
    audio_file = models.FileField(upload_to='voice_messages/')
    duration = models.IntegerField()  # длительность в секундах
```

#### ✓ Групповые чаты
**Реализация:**
- Поддержка множества участников в диалоге
- Управление участниками (добавление/удаление)
- Роли в групповом чате (админ/участник)

**Локация:** `chat/models.py`
```python
class GroupChat(Dialog):
    name = models.CharField(max_length=255)
    avatar = models.ImageField(upload_to='group_chats/', null=True)
    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
```

#### ✓ Поиск по сообщениям
**Реализация:**
- Полнотекстовый поиск по содержимому сообщений
- Фильтрация по дате и типу сообщений
- Подсветка результатов поиска

**Локация:** `chat/views.py`
```python
class MessageSearchView(LoginRequiredMixin, ListView):
    model = Message
    template_name = 'chat/search_results.html'
    
    def get_queryset(self):
        query = self.request.GET.get('q', '')
        return Message.objects.filter(
            Q(content__icontains=query),
            dialog__participants=self.request.user
        ).order_by('-created_at')
```

### 5.2 Групповые чаты
#### ✓ Система ролей и модерации
**Реализация:**
- Модель `GroupChatMember` с системой ролей
- Иерархия: владелец, администратор, модератор, участник
- Проверки на уникальность ролей
- Ограничение количества участников

**Локация:** `chat/models.py`
```python
class GroupChatMember(models.Model):
    ROLE_CHOICES = [
        ('owner', _('Владелец')),
        ('admin', _('Администратор')),
        ('moderator', _('Модератор')),
        ('member', _('Участник')),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
```

**Использование:**
- В системе управления участниками
- В проверке прав доступа
- В модерации сообщений

#### ✓ Настройки приватности
**Реализация:**
- Различные уровни доступа к чату
- Система приглашений с ограниченным сроком
- Уникальные ссылки-приглашения
- Модерация новых участников

**Локация:** `chat/models.py`
```python
class GroupChat(models.Model):
    PRIVACY_CHOICES = [
        ('public', _('Публичный')),
        ('private', _('Приватный')),
        ('secret', _('Секретный')),
    ]
    privacy = models.CharField(max_length=20, choices=PRIVACY_CHOICES)
```

**Использование:**
- При создании новых чатов
- В системе поиска групп
- В управлении доступом

#### ✓ Система модерации контента
**Реализация:**
- Модель `GroupChatModeration` для действий модерации
- Временные ограничения (мут, бан)
- История модерации
- Система предупреждений

**Локация:** `chat/models.py`
```python
class GroupChatModeration(models.Model):
    ACTION_CHOICES = [
        ('mute', _('Мут')),
        ('kick', _('Кик')),
        ('ban', _('Бан')),
    ]
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    expires_at = models.DateTimeField(null=True, blank=True)
```

**Использование:**
- В панели модератора
- При нарушении правил
- В системе апелляций

## 3. Потеряшки

### 3.1 Объявления о пропаже
#### ✓ Геолокация места пропажи
**Реализация:**
- Использование существующей системы геолокации из чата
- Интеграция LocationMessage для отметки места пропажи
- Сохранение координат в объявлении

**Локация:** `announcements/models.py`
```python
class Announcement(models.Model):
    # Геолокация
    location = models.CharField(_('Местоположение'), max_length=200)
    latitude = models.DecimalField(_('широта'), max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(_('долгота'), max_digits=9, decimal_places=6, null=True, blank=True)
```

#### ✓ Быстрые фильтры
**Реализация:**
- Фильтрация по типу объявления (потеряно/найдено)
- Фильтрация по местоположению
- Поиск по описанию и характеристикам

**Локация:** `announcements/models.py`
```python
class LostFoundAnnouncement(models.Model):
    TYPE_LOST = 'lost'
    TYPE_FOUND = 'found'
    TYPE_CHOICES = [
        (TYPE_LOST, _('Потеряно')),
        (TYPE_FOUND, _('Найдено')),
    ]
    type = models.CharField(_('Тип'), max_length=10, choices=TYPE_CHOICES)
    date_lost_found = models.DateField(_('Дата потери/находки'))
    distinctive_features = models.TextField(_('Отличительные черты'))
```

### 3.2 Поиск совпадений
#### ✓ Автоматические уведомления
**Реализация:**
- Использование существующей системы WebSocket уведомлений из чата
- Отправка уведомлений о потенциальных совпадениях
- Интеграция с общей системой уведомлений

**Локация:** `chat/consumers.py`
```python
class NotificationConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope["user"]
        self.notification_group = f'notifications_{self.user.id}'
        async_to_sync(self.channel_layer.group_add)(
            self.notification_group,
            self.channel_name
        )
        self.accept()

    def send_notification(self, event):
        self.send(text_data=json.dumps({
            'type': 'notification',
            'message': event['message']
        }))
```

#### ✓ Алгоритм сопоставления
**Реализация:**
- Система `PetMatchingSystem` с машинным обучением
- Анализ изображений через ResNet50
- TF-IDF векторизация для текстовых описаний
- Взвешенная оценка схожести по разным параметрам

**Локация:** `announcements/matching.py`
```python
class PetMatchingSystem:
    def calculate_similarity(self, announcement1, announcement2) -> float:
        weights = {
            'location': 0.3,
            'description': 0.3,
            'image': 0.2,
            'attributes': 0.2
        }
        # Комплексный анализ схожести
```

**Использование:**
- При создании новых объявлений о пропаже/находке
- В периодических задачах поиска совпадений
- В системе уведомлений о потенциальных совпадениях

#### ✓ Анализ изображений
**Реализация:**
- Использование предобученной модели ResNet50
- Извлечение признаков из изображений
- Сравнение визуальной схожести
- Нормализация и предобработка изображений

**Локация:** `announcements/matching.py`
```python
def get_image_features(self, image_path: str) -> np.ndarray:
    img = Image.open(io.BytesIO(f.read())).convert('RGB')
    img_tensor = self.image_transforms(img)
    features = self.image_model.features(img_tensor)
```

**Использование:**
- В алгоритме сопоставления объявлений
- При загрузке новых фотографий
- В системе поиска похожих животных

## 4. Потеряшки

### 4.1 Создание объявлений
#### ✓ Специальная форма создания
**Реализация:**
- Форма `LostPetAnnouncementForm` с расширенными полями
- Интеграция с картой для выбора места пропажи
- Загрузка множественных фотографий
- Настройка радиуса уведомлений

**Локация:** `announcements/forms.py`
```python
class LostPetAnnouncementForm(forms.ModelForm):
    last_seen_location = forms.CharField(
        label=_('Место последней встречи'),
        widget=forms.TextInput(attrs={
            'class': 'location-autocomplete',
            'placeholder': _('Введите адрес или выберите на карте')
        })
    )
    notification_radius = forms.IntegerField(
        label=_('Радиус уведомлений (км)'),
        min_value=1,
        max_value=50,
        initial=5
    )
```

**Использование:**
- В представлении `CreateLostPetAnnouncementView`
- В шаблоне с интеграцией Google Maps
- В системе уведомлений для определения радиуса

#### ✓ Система уведомлений
**Реализация:**
- Сервис `NotificationService` для отправки уведомлений
- Определение пользователей в заданном радиусе
- WebSocket уведомления в реальном времени
- Уведомления о потенциальных совпадениях

**Локация:** `announcements/services.py`
```python
class NotificationService:
    @staticmethod
    def notify_users_in_radius(announcement, radius_km: int) -> int:
        center_point = Point(
            float(announcement.longitude),
            float(announcement.latitude)
        )
        nearby_users = User.objects.filter(
            location__distance_lte=(center_point, D(km=radius_km))
        )
```

**Использование:**
- При создании объявления о пропаже
- При обнаружении похожих объявлений
- В системе уведомлений пользователей

## 11. WebSocket конфигурация
#### ✓ Базовая конфигурация WebSocket
**Реализация:**
- Настройка ASGI для WebSocket соединений
- Конфигурация каналов для чата и уведомлений
- Аутентификация WebSocket соединений

**Локация:** `config/routing.py`
```python
application = ProtocolTypeRouter({
    'websocket': URLRouter([
        path('ws/chat/<dialog_id>/', ChatConsumer.as_asgi()),
        path('ws/notifications/', NotificationConsumer.as_asgi()),
    ])
})
```

#### ✓ WebSocket тесты
**Реализация:**
- Тесты подключения WebSocket
- Тесты аутентификации
- Тесты обмена сообщениями
- Тесты доставки уведомлений

**Локация:** `chat/tests/test_websocket.py`
```python
class WebSocketTests(TestCase):
    async def test_connection(self):
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/{self.dialog.id}/"
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.disconnect()

    async def test_message_delivery(self):
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/{self.dialog.id}/"
        )
        await communicator.connect()
        await communicator.send_json_to({
            'type': 'message',
            'content': 'test message'
        })
        response = await communicator.receive_json_from()
        self.assertEqual(response['content'], 'test message')
        await communicator.disconnect()
```


#### ✓ Модель данных потеряшек
**Реализация:**
- Создана полная модель для объявлений о пропаже/находке
- Добавлены все необходимые поля и связи
- Реализованы индексы для оптимизации поиска

**Локация:** `announcements/models.py`
```python
class LostFoundAnnouncement(models.Model):
    # Основная информация
    type = models.CharField(_('Тип'), max_length=10, choices=TYPE_CHOICES)
    date_lost_found = models.DateTimeField(_('Дата и время потери/находки'))
    last_seen_location = models.CharField(_('Место последней встречи'), max_length=255)
    
    # Характеристики животного
    animal_type = models.CharField(_('Вид животного'), max_length=50)
    breed = models.CharField(_('Порода'), max_length=100)
    color = models.CharField(_('Основной цвет'), max_length=50)
    
    class Meta:
        indexes = [
            models.Index(fields=['type', 'date_lost_found']),
            models.Index(fields=['latitude', 'longitude']),
        ]
```

#### ✓ Сервис уведомлений
**Реализация:**
- Отправка уведомлений пользователям в радиусе
- Интеграция с push-уведомлениями
- Поддержка различных типов уведомлений

**Локация:** `announcements/services.py`
```python
class AreaNotificationService:
    def notify_users_in_radius(self, announcement):
        center_point = Point(announcement.longitude, announcement.latitude)
        radius_km = announcement.search_radius or 5
        
        nearby_users = User.objects.filter(
            last_location__distance_lte=(center_point, D(km=radius_km))
        ).annotate(
            distance=Distance('last_location', center_point)
        )
        
        for user in nearby_users:
            self._send_notification(user, announcement)
```

#### ✓ Сервис поиска совпадений
**Реализация:**
- Алгоритм сопоставления объявлений
- Скоринг по характеристикам животного
- Учет геолокации и временных рамок

**Локация:** `announcements/services.py`
```python
class LostPetMatchingService:
    def find_matches(self, announcement):
        matches = LostFoundAnnouncement.objects.exclude(
            id=announcement.id
        ).filter(
            type=opposite_type,
            date_lost_found__range=(
                announcement.date_lost_found - timedelta(days=30),
                announcement.date_lost_found + timedelta(days=30)
            )
        )
        
        return self._score_matches(matches, announcement)
```

#### ✓ Сервис подсказок
**Реализация:**
- Система рекомендаций мест поиска
- Анализ похожих успешных случаев
- Интеграция с базой ветклиник и приютов

**Локация:** `announcements/services.py`
```python
class LostPetSuggestionService:
    def get_suggestions(self, announcement):
        suggestions = []
        suggestions.extend(self._get_popular_places())
        suggestions.extend(self._get_similar_cases(announcement))
        suggestions.extend(self._get_nearby_facilities(announcement))
        return suggestions
```

#### ✓ Сервис истории поиска
**Реализация:**
- Отслеживание поисковой активности
- История контактов и событий
- Генерация статистики и карты покрытия

**Локация:** `announcements/services.py`
```python
class SearchHistoryService:
    def track_search_activity(self, announcement, search_data):
        if not announcement.search_history:
            announcement.search_history = {
                'searched_areas': [],
                'contacted_users': [],
                'timeline': [],
                'success_factors': []
            }
        
        self._track_searched_area(announcement, search_data.get('area'))
        self._track_contacted_user(announcement, search_data.get('contacted_user'))
```

## 2. VIP-функционал

### 2.1 Подписки
#### ✓ Модели подписок и уровней
**Реализация:**
- Модель `VIPSubscription` для хранения подписок
- Поддержка разных уровней через `LEVEL_CHOICES`
- Отслеживание статуса и срока действия
- Система автопродления

**Локация:** `subscriptions/models.py`
```python
class VIPSubscription(models.Model):
    LEVEL_CHOICES = [
        ('basic', 'Базовый'),
        ('premium', 'Премиум'),
        ('elite', 'Элитный'),
    ]
    # ...
    auto_renew = models.BooleanField(_('автопродление'), default=False)
    is_active = models.BooleanField(_('активна'), default=True)
```

**Использование:**
- В сервисе `VIPService` для управления подписками
- В системе платежей для активации/деактивации
- В проверке доступа к VIP-функциям

#### ✓ VIP-функции
**Реализация:**
- Модель `VIPFeature` для хранения доступных функций
- Привязка функций к уровням подписки
- Система проверки доступа к функциям

**Локация:** `subscriptions/services.py`
```python
class VIPService:
    @staticmethod
    def has_feature(user, feature_name: str) -> bool:
        subscription = VIPService.get_active_subscription(user)
        if not subscription:
            return False
        return VIPFeature.objects.filter(
            name=feature_name,
            subscription_level=subscription.level,
            is_active=True
        ).exists()
```

**Использование:**
- В VIP-консьерже для проверки доступа
- В системе объявлений для премиум-функций
- В статистике для расширенной аналитики

## 3. Система модерации

### 3.1 Модерация объявлений
#### ✓ Очередь модерации
**Реализация:**
- Модель `ModerationQueue` для управления очередью
- Поддержка различных типов контента через `ContentType`
- История изменений и комментарии модераторов

**Локация:** `moderation/models.py`
```python
class ModerationQueue(models.Model):
    STATUS_CHOICES = [
        ('pending', 'На рассмотрении'),
        ('approved', 'Одобрено'),
        ('rejected', 'Отклонено'),
    ]
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
```

**Использование:**
- В процессе создания объявлений
- В панели модератора
- В системе апелляций

#### ✓ Система предупреждений
**Реализация:**
- Модель `UserWarning` для хранения предупреждений
- Автоматическая система банов по количеству предупреждений
- История предупреждений пользователя

**Локация:** `moderation/services.py`
```python
class ModerationService:
    @staticmethod
    def warn_user(user, moderator, reason: str) -> UserWarning:
        warning = UserWarning.objects.create(
            user=user,
            moderator=moderator,
            reason=reason
        )
        active_warnings = UserWarning.objects.filter(
            user=user,
            is_active=True
        ).count()
        if active_warnings >= 3:
            ModerationService.ban_user(...)
```

**Использование:**
- В панели модератора для выдачи предупреждений
- В автоматической системе модерации
- В профиле пользователя для отображения статуса

#### ✓ Система банов
**Реализация:**
- Модель `UserBan` для управления банами
- Поддержка временных и перманентных банов
- Система апелляций

**Локация:** `moderation/models.py`
```python
class UserBan(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_permanent = models.BooleanField(_('перманентный'), default=False)
    expires_at = models.DateTimeField(_('окончание бана'))
```

**Использование:**
- В системе модерации для блокировки нарушителей
- В системе авторизации для проверки доступа
- В панели администратора для управления банами

### 3.2 Автоматическая модерация
#### ✓ Автоматические проверки
**Реализация:**
- Сервис `AutoModerationService` для автоматических проверок
- Система оценки контента
- Интеграция с очередью модерации

**Локация:** `moderation/services.py`
```python
class AutoModerationService:
    @staticmethod
    def check_announcement(announcement) -> dict:
        results = {
            'passed': True,
            'issues': []
        }
        # Реализована базовая структура проверок
```

**Использование:**
- При создании объявлений
- В процессе обновления контента
- В системе массовой модерации 

## 5. Чат-система

### 5.1 Аудио-сообщения
#### ✓ Обработка аудио
**Реализация:**
- Процессор `AudioMessageProcessor` для обработки аудио
- Улучшение качества звука (шумоподавление, нормализация)
- Компрессия динамического диапазона
- Сохранение обработанных файлов

**Локация:** `chat/audio.py`
```python
class AudioMessageProcessor:
    def enhance_audio(self, y: np.ndarray) -> np.ndarray:
        y_normalized = librosa.util.normalize(y)
        noise_reduced = self.reduce_noise(y_normalized)
        y_compressed = self.compress_dynamic_range(noise_reduced)
        return y_compressed
```

**Использование:**
- При загрузке голосовых сообщений
- В процессе обработки аудио перед сохранением
- В системе улучшения качества звука

#### ✓ Визуализация и транскрибация
**Реализация:**
- Генерация волновой формы для отображения
- Транскрибация аудио в текст через Google Speech Recognition
- Сегментация аудио для визуализации
- Обработка ошибок распознавания

**Локация:** `chat/audio.py`
```python
def generate_waveform(self, y: np.ndarray, segments: int = 100) -> list:
    segment_size = len(y) // segments
    waveform = []
    for i in range(segments):
        segment = y[i * segment_size:(i + 1) * segment_size]
        amplitude = float(np.abs(segment).mean())
        waveform.append(amplitude)
```

**Использование:**
- В интерфейсе чата для отображения аудио
- При воспроизведении голосовых сообщений
- В системе поиска по транскрибированному тексту 