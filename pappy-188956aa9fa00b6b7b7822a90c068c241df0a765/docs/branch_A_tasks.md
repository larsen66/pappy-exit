# Ветка А: Базовый функционал и безопасность

## 1. Система аутентификации и авторизации

### 1.1 Госуслуги OAuth
- [ ] Интеграция с API Госуслуг
- [ ] Создание middleware для OAuth
- [ ] Обработка callback и токенов
- [ ] Сохранение данных пользователя

```python
class GosuslugiAuth:
    def initialize_auth(self) -> str:
        """Инициализация OAuth flow"""
        pass

    def handle_callback(self, code: str) -> dict:
        """Обработка ответа от Госуслуг"""
        pass

    def get_user_data(self, token: str) -> dict:
        """Получение данных пользователя"""
        pass
```

### 1.2 Верификация продавцов
- [ ] Система загрузки документов
- [ ] Очередь модерации документов
- [ ] Уведомления о статусе проверки
- [ ] Автоматическое обновление статуса

```python
class SellerVerification:
    def upload_documents(self, user_id: int, files: List[File]) -> bool:
        """Загрузка документов на верификацию"""
        pass

    def verify_documents(self, verification_id: int) -> bool:
        """Проверка документов модератором"""
        pass

    def notify_user(self, user_id: int, status: str) -> None:
        """Отправка уведомления о статусе"""
        pass
```

## 2. VIP-функционал

### 2.1 Подписки
- [ ] Модели подписок и уровней
- [ ] Система оплаты
- [ ] Автопродление
- [ ] Уведомления об окончании

```python
class VIPSubscription(models.Model):
    user = models.ForeignKey(User)
    level = models.CharField(choices=VIP_LEVELS)
    starts_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    auto_renew = models.BooleanField(default=False)
    
    def extend_subscription(self, days: int) -> None:
        """Продление подписки"""
        pass

    def cancel_subscription(self) -> bool:
        """Отмена автопродления"""
        pass
```

### 2.2 VIP-функции
- [ ] Приоритетное размещение
- [ ] Расширенная статистика
- [ ] VIP-поддержка
- [ ] Специальные бейджи

```python
class VIPFeatures:
    def boost_announcement(self, announcement_id: int) -> bool:
        """Поднятие объявления в топ"""
        pass

    def get_extended_stats(self, user_id: int) -> dict:
        """Получение расширенной статистики"""
        pass
```

## 3. Система модерации

### 3.1 Модерация объявлений
- [ ] Очередь модерации
- [ ] Автоматические проверки
- [ ] История изменений
- [ ] Система апелляций

```python
class ModerationSystem:
    def check_announcement(self, announcement_id: int) -> dict:
        """Автоматическая проверка объявления"""
        pass

    def moderate_announcement(self, announcement_id: int, action: str, reason: str = None) -> bool:
        """Модерация объявления"""
        pass

    def appeal_decision(self, announcement_id: int, reason: str) -> bool:
        """Подача апелляции"""
        pass
```

### 3.2 Модерация пользователей
- [ ] Система предупреждений
- [ ] Временные баны
- [ ] История нарушений
- [ ] Автоматические санкции

```python
class UserModeration:
    def warn_user(self, user_id: int, reason: str) -> bool:
        """Выдача предупреждения"""
        pass

    def ban_user(self, user_id: int, duration: int, reason: str) -> bool:
        """Временная блокировка"""
        pass
```

## 4. Тесты

### 4.1 Unit Tests
```python
class AuthTests(TestCase):
    def test_gosuslugi_auth_flow(self):
        pass
    
    def test_seller_verification(self):
        pass

class VIPTests(TestCase):
    def test_subscription_creation(self):
        pass
    
    def test_subscription_renewal(self):
        pass

class ModerationTests(TestCase):
    def test_auto_moderation(self):
        pass
    
    def test_appeal_process(self):
        pass
```

### 4.2 Integration Tests
```python
class AuthIntegrationTests(TestCase):
    def test_complete_auth_flow(self):
        pass
    
    def test_seller_verification_flow(self):
        pass

class VIPIntegrationTests(TestCase):
    def test_subscription_purchase_flow(self):
        pass
    
    def test_vip_features_access(self):
        pass
```

## 5. Миграции

```python
# migrations/0001_auth_system.py
class Migration(migrations.Migration):
    dependencies = []
    operations = [
        migrations.AddField(
            model_name='user',
            name='gosuslugi_id',
            field=models.CharField(max_length=100, null=True)
        ),
        # Другие операции...
    ]

# migrations/0002_vip_system.py
class Migration(migrations.Migration):
    dependencies = ['0001_auth_system']
    operations = [
        migrations.CreateModel(
            name='VIPSubscription',
            fields=[
                # Поля модели...
            ]
        ),
        # Другие операции...
    ]
```

## 6. Зависимости

```
# requirements_branch_a.txt
django-oauth-toolkit==2.3.0
django-moderation==0.8.0
stripe==5.4.0
```

## 7. Тестирование SMS-верификации

### 7.1 Основной функционал
- [ ] Генерация кода подтверждения
- [ ] Подсчет попыток ввода
- [ ] Блокировка после превышения лимита
- [ ] Проверка срока действия кода

```python
class PhoneVerification(models.Model):
    CODE_EXPIRY_MINUTES = 10
    MAX_VERIFICATION_ATTEMPTS = 3

    phone = models.CharField(max_length=15)
    code = models.CharField(max_length=6)
    attempts = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)

    def verify_code(self, input_code: str) -> bool:
        """Проверка кода подтверждения"""
        pass

    def is_blocked(self) -> bool:
        """Проверка блокировки"""
        pass
```

### 7.2 Дополнительные тесты
```python
class PhoneVerificationTests(TestCase):
    def test_code_generation(self):
        """Тест генерации кода"""
        pass

    def test_verification_attempts(self):
        """Тест подсчета попыток"""
        pass

    def test_expiry_check(self):
        """Тест срока действия"""
        pass
```

## 8. Расширенные тесты безопасности

### 8.1 Тесты прав доступа
```python
class PermissionTests(TestCase):
    def test_profile_permissions(self):
        """Проверка прав доступа к профилю"""
        pass

    def test_announcement_permissions(self):
        """Проверка прав доступа к объявлениям"""
        pass

    def test_verification_document_upload(self):
        """Проверка загрузки документов"""
        pass
```

### 8.2 Тесты валидации
```python
class ValidationTests(TestCase):
    def test_phone_validation(self):
        """Проверка валидации телефона"""
        pass

    def test_document_validation(self):
        """Проверка валидации документов"""
        pass

    def test_subscription_validation(self):
        """Проверка валидации подписки"""
        pass
```

## 9. Зависимости

```
# Дополнительные зависимости
python-jose==3.3.0
django-phonenumber-field==7.1.0
django-storages[google]==1.13.2
django-cleanup==8.0.0
``` 