# Pappi - Платформа для владельцев домашних животных

## О проекте

Pappi - это многофункциональная платформа для владельцев домашних животных, заводчиков, ветеринаров и других специалистов по уходу за животными. Проект объединяет функционал маркетплейса, социальной сети и сервиса для поиска потерянных животных.

### Основные возможности
- 🐾 Размещение и поиск объявлений о продаже/покупке животных
- 👨‍⚕️ Поиск специалистов по уходу за животными
- 🔍 Сервис для поиска потерянных животных
- 💝 Тиндер-механика для подбора питомцев
- 💬 Чат между пользователями
- ✅ Система верификации пользователей
- ⭐ Рейтинги и отзывы

## Документация

### Для разработчиков
- [Общая документация проекта](docs/project_documentation.md)
- [Модели и форматы данных](docs/models_and_data.md)
- [API документация](docs/api.md)
- [Руководство по тестированию](docs/testing.md)
- [Руководство по развертыванию](docs/deployment.md)

## Быстрый старт

### Требования
- Python 3.13+
- PostgreSQL 15+
- Redis 6+

### Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/larsen66/pappy.git
cd pappy
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Настройте базу данных:
```bash
createdb pappi_db
psql postgres -c "CREATE USER pappi_user WITH PASSWORD 'pappi_password';"
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE pappi_db TO pappi_user;"
```

5. Создайте файл `.env` в корневой директории:
```
DEBUG=True
SECRET_KEY=your-secret-key-here
DB_NAME=pappi_db
DB_USER=pappi_user
DB_PASSWORD=pappi_password
DB_HOST=localhost
DB_PORT=5432
```

6. Примените миграции:
```bash
python manage.py migrate
```

7. Создайте суперпользователя:
```bash
python manage.py createsuperuser
```

8. Запустите сервер разработки:
```bash
python manage.py runserver
```

## Тестирование

Запуск всех тестов:
```bash
python manage.py test
```

Запуск тестов конкретного приложения:
```bash
python manage.py test announcements
```

## Лицензия

MIT License - см. [LICENSE](LICENSE) файл для подробностей.

## Авторы

- [Давид Акопян](https://github.com/dav-hakobian)

## Поддержка

Если у вас возникли вопросы или проблемы:
1. Проверьте [документацию](docs/)
2. Создайте [issue](https://github.com/larsen66/pappy/issues)
3. Свяжитесь с командой разработки
