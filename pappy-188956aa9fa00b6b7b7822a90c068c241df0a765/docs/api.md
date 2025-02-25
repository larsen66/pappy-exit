# API Documentation

## Общая информация

### Базовый URL
```
https://api.pappi.com/v1
```

### Аутентификация
Все запросы (кроме регистрации и авторизации) должны содержать заголовок:
```
Authorization: Bearer <token>
```

### Формат ответа
Все ответы возвращаются в формате JSON.

## Endpoints

### Аутентификация

#### Регистрация
```
POST /auth/register/
```
Request:
```json
{
    "phone": "+79991234567",
    "password": "secure_password",
    "email": "user@example.com"
}
```
Response (200 OK):
```json
{
    "id": 1,
    "phone": "+79991234567",
    "token": "jwt_token_here"
}
```

#### Авторизация
```
POST /auth/login/
```
Request:
```json
{
    "phone": "+79991234567",
    "password": "secure_password"
}
```
Response (200 OK):
```json
{
    "token": "jwt_token_here"
}
```

### Пользователи

#### Получение профиля
```
GET /users/profile/
```
Response (200 OK):
```json
{
    "id": 1,
    "phone": "+79991234567",
    "email": "user@example.com",
    "is_verified": true,
    "is_specialist": false,
    "is_shelter": false,
    "rating": 4.5,
    "created_at": "2024-01-01T00:00:00Z"
}
```

#### Обновление профиля
```
PATCH /users/profile/
```
Request:
```json
{
    "email": "new.email@example.com"
}
```
Response (200 OK):
```json
{
    "id": 1,
    "email": "new.email@example.com",
    "phone": "+79991234567"
}
```

### Объявления

#### Список объявлений
```
GET /announcements/
```
Query Parameters:
- `category` (int): ID категории
- `type` (string): Тип объявления (sale, service, lost_found)
- `price_min` (decimal): Минимальная цена
- `price_max` (decimal): Максимальная цена
- `page` (int): Номер страницы
- `per_page` (int): Количество объявлений на странице

Response (200 OK):
```json
{
    "count": 100,
    "next": "/api/v1/announcements/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "title": "Котята Maine Coon",
            "description": "Продаются котята",
            "price": 50000.00,
            "category": {
                "id": 1,
                "name": "Кошки"
            },
            "type": "sale",
            "status": "active",
            "author": {
                "id": 1,
                "phone": "+79991234567",
                "rating": 4.5
            },
            "images": [
                {
                    "id": 1,
                    "url": "/media/announcements/1/image1.jpg"
                }
            ],
            "created_at": "2024-01-25T10:30:00Z",
            "updated_at": "2024-01-25T10:30:00Z"
        }
    ]
}
```

#### Создание объявления
```
POST /announcements/
```
Request:
```json
{
    "title": "Котята Maine Coon",
    "description": "Продаются котята",
    "price": 50000.00,
    "category": 1,
    "type": "sale",
    "images": [
        {
            "file": "base64_encoded_image"
        }
    ]
}
```
Response (201 Created):
```json
{
    "id": 1,
    "title": "Котята Maine Coon",
    "description": "Продаются котята",
    "price": 50000.00,
    "category": {
        "id": 1,
        "name": "Кошки"
    },
    "type": "sale",
    "status": "pending",
    "images": [
        {
            "id": 1,
            "url": "/media/announcements/1/image1.jpg"
        }
    ]
}
```

### Чат

#### Список диалогов
```
GET /chat/dialogs/
```
Response (200 OK):
```json
{
    "count": 10,
    "results": [
        {
            "id": 1,
            "participant": {
                "id": 2,
                "phone": "+79997654321",
                "rating": 4.8
            },
            "last_message": {
                "id": 100,
                "text": "Здравствуйте, котята еще доступны?",
                "created_at": "2024-01-25T12:30:00Z",
                "is_read": false
            },
            "unread_count": 1
        }
    ]
}
```

#### Отправка сообщения
```
POST /chat/dialogs/{dialog_id}/messages/
```
Request:
```json
{
    "text": "Да, котята все еще доступны"
}
```
Response (201 Created):
```json
{
    "id": 101,
    "text": "Да, котята все еще доступны",
    "created_at": "2024-01-25T12:35:00Z",
    "is_read": false,
    "author": {
        "id": 1,
        "phone": "+79991234567"
    }
}
```

## Коды ошибок

### 400 Bad Request
```json
{
    "error": "validation_error",
    "message": "Validation failed",
    "details": {
        "field": ["error message"]
    }
}
```

### 401 Unauthorized
```json
{
    "error": "unauthorized",
    "message": "Authentication credentials were not provided"
}
```

### 403 Forbidden
```json
{
    "error": "forbidden",
    "message": "You do not have permission to perform this action"
}
```

### 404 Not Found
```json
{
    "error": "not_found",
    "message": "Requested resource was not found"
}
```

## Ограничения

### Запросы
- Максимум 100 запросов в минуту с одного IP
- Максимум 1000 запросов в час с одного пользователя

### Данные
- Максимальный размер изображения: 5MB
- Максимальное количество изображений в объявлении: 10
- Максимальная длина сообщения в чате: 1000 символов 