# Ветка Б: Пользовательские функции

## 1. Котопсиндер (система лайков)

### 1.1 Основной функционал
- [x] Система свайпов
- [x] Алгоритм подбора карточек
- [x] Обработка лайков/дизлайков
- [x] История просмотров

```python
class SwipeSystem:
    def get_next_cards(self, user_id: int, count: int = 10) -> List[Announcement]:
        """Получение следующих карточек для показа"""
        pass

    def process_swipe(self, user_id: int, announcement_id: int, direction: str) -> bool:
        """Обработка свайпа"""
        pass

    def get_matches(self, user_id: int) -> List[Match]:
        """Получение списка совпадений"""
        pass
```

### 1.2 Механика вязки
- [x] Двусторонние лайки
- [x] Создание пар
- [x] Уведомления о совпадениях
- [x] Специальные фильтры

```python
class BreedingMatch:
    def check_compatibility(self, pet1_id: int, pet2_id: int) -> bool:
        """Проверка совместимости животных"""
        pass

    def create_match(self, pet1_id: int, pet2_id: int) -> Match:
        """Создание пары для вязки"""
        pass
```

## 2. Чат-система

### 2.1 Базовый чат
- [x] Диалоги и сообщения
- [x] Прикрепление файлов
- [x] Статусы сообщений
- [x] Уведомления

```python
class ChatSystem:
    class Dialog(models.Model):
        participants = models.ManyToManyField(User)
        created_at = models.DateTimeField(auto_now_add=True)
        last_message = models.ForeignKey('Message', null=True)

    class Message(models.Model):
        dialog = models.ForeignKey(Dialog)
        sender = models.ForeignKey(User)
        content = models.TextField()
        created_at = models.DateTimeField(auto_now_add=True)
        is_read = models.BooleanField(default=False)
```

### 2.2 Расширенные функции
- [x] Отправка геолокации
- [x] Аудио-сообщения
- [x] Групповые чаты
- [x] Поиск по сообщениям

```python
class ChatFeatures:
    def send_location(self, dialog_id: int, location: dict) -> Message:
        """Отправка геолокации"""
        pass

    def send_voice(self, dialog_id: int, audio_file: File) -> Message:
        """Отправка голосового сообщения"""
        pass
```

## 3. Потеряшки

### 3.1 Объявления о пропаже
- [ ] Специальная форма создания
- [ ] Геолокация места пропажи
- [ ] Быстрые фильтры
- [ ] Уведомления в районе

```python
class LostPetSystem:
    def create_lost_announcement(self, data: dict) -> Announcement:
        """Создание объявления о пропаже"""
        pass

    def notify_area(self, announcement_id: int, radius: float) -> int:
        """Уведомление пользователей в радиусе"""
        pass
```

### 3.2 Поиск совпадений
- [ ] Алгоритм сопоставления
- [ ] Система подсказок
- [ ] Автоматические уведомления
- [ ] История поиска

```python
class LostPetMatcher:
    def find_matches(self, lost_pet_id: int) -> List[Announcement]:
        """Поиск похожих объявлений"""
        pass

    def suggest_locations(self, lost_pet_id: int) -> List[Location]:
        """Предложение мест для поиска"""
        pass
```

## 4. Тесты

### 4.1 Unit Tests
```python
class SwipeTests(TestCase):
    def test_swipe_processing(self):
        pass
    
    def test_match_creation(self):
        pass

class ChatTests(TestCase):
    def test_message_sending(self):
        pass
    
    def test_file_attachment(self):
        pass

class LostPetTests(TestCase):
    def test_announcement_creation(self):
        pass
    
    def test_matching_algorithm(self):
        pass
```

### 4.2 Integration Tests
```python
class SwipeIntegrationTests(TestCase):
    def test_complete_match_flow(self):
        pass
    
    def test_breeding_match_flow(self):
        pass

class ChatIntegrationTests(TestCase):
    def test_dialog_creation_flow(self):
        pass
    
    def test_media_sharing_flow(self):
        pass
```

## 5. Миграции

```python
# migrations/0001_chat_system.py
class Migration(migrations.Migration):
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='Dialog',
            fields=[
                # Поля модели...
            ]
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                # Поля модели...
            ]
        ),
    ]

# migrations/0002_swipe_system.py
class Migration(migrations.Migration):
    dependencies = ['0001_chat_system']
    operations = [
        migrations.CreateModel(
            name='SwipeAction',
            fields=[
                # Поля модели...
            ]
        ),
        migrations.CreateModel(
            name='Match',
            fields=[
                # Поля модели...
            ]
        ),
    ]
```

## 6. WebSocket конфигурация

```python
# routing.py
application = ProtocolTypeRouter({
    'websocket': URLRouter([
        path('ws/chat/<dialog_id>/', ChatConsumer.as_asgi()),
        path('ws/notifications/', NotificationConsumer.as_asgi()),
    ])
})
```

## 7. Зависимости

```
# requirements_branch_b.txt
channels==3.0.4
channels-redis==3.4.0
django-storages==1.13.2
Pillow==9.5.0
```

## 8. Расширенные тесты чата

### 8.1 Тесты диалогов
```python
class DialogTests(TestCase):
    def test_dialog_creation(self):
        """Проверка создания диалога"""
        pass

    def test_duplicate_dialog_prevention(self):
        """Проверка предотвращения дублей диалогов"""
        pass

    def test_dialog_participants(self):
        """Проверка участников диалога"""
        pass
```

### 8.2 Тесты сообщений
```python
class MessageTests(TestCase):
    def test_message_ordering(self):
        """Проверка порядка сообщений"""
        pass

    def test_read_status(self):
        """Проверка статуса прочтения"""
        pass

    def test_file_attachments(self):
        """Проверка вложений"""
        pass
```

## 9. Тесты потеряшек

### 9.1 Тесты объявлений
```python
class LostPetAnnouncementTests(TestCase):
    def test_announcement_creation(self):
        """Проверка создания объявления"""
        pass

    def test_location_validation(self):
        """Проверка валидации локации"""
        pass

    def test_notification_radius(self):
        """Проверка радиуса уведомлений"""
        pass
```

### 9.2 Тесты поиска
```python
class LostPetSearchTests(TestCase):
    def test_search_filters(self):
        """Проверка фильтров поиска"""
        pass

    def test_location_search(self):
        """Проверка поиска по локации"""
        pass

    def test_breed_matching(self):
        """Проверка сопоставления пород"""
        pass
```

## 10. WebSocket тесты

### 10.1 Тесты подключения
```python
class WebSocketTests(TestCase):
    async def test_connection(self):
        """Проверка подключения"""
        pass

    async def test_authentication(self):
        """Проверка аутентификации"""
        pass
```

### 10.2 Тесты обмена сообщениями
```python
class WebSocketMessageTests(TestCase):
    async def test_message_delivery(self):
        """Проверка доставки сообщений"""
        pass

    async def test_notification_delivery(self):
        """Проверка доставки уведомлений"""
        pass
```

## 11. Дополнительные зависимости

```
# Дополнительные зависимости
django-channels-presence==1.0.0
channels-redis==4.1.0
django-eventstream==4.5.1
django-notifications-hq==1.8.0
``` 