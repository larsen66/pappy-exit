# Руководство по развертыванию

## Требования к системе

### Программное обеспечение
- Python 3.13+
- PostgreSQL 15+
- Redis 6+
- Nginx (для production)
- Git

### Системные требования
- CPU: 2+ ядра
- RAM: 4+ GB
- Диск: 20+ GB

## Локальное развертывание

### 1. Клонирование репозитория
```bash
git clone https://github.com/larsen66/pappy.git
cd pappy
```

### 2. Создание виртуального окружения
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

### 3. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 4. Настройка базы данных
```bash
# Создание базы данных
createdb pappi_db

# Создание пользователя
psql postgres -c "CREATE USER pappi_user WITH PASSWORD 'pappi_password';"
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE pappi_db TO pappi_user;"

# Применение миграций
python manage.py migrate
```

### 5. Настройка переменных окружения
Создайте файл `.env` в корневой директории:
```
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# База данных
DB_NAME=pappi_db
DB_USER=pappi_user
DB_PASSWORD=pappi_password
DB_HOST=localhost
DB_PORT=5432

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# SMS
SMS_API_KEY=your-sms-api-key
SMS_SENDER=PAPPI

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 6. Создание суперпользователя
```bash
python manage.py createsuperuser
```

### 7. Сбор статических файлов
```bash
python manage.py collectstatic
```

### 8. Запуск сервера разработки
```bash
python manage.py runserver
```

## Production развертывание

### 1. Настройка сервера

#### Установка зависимостей (Ubuntu)
```bash
# Обновление системы
sudo apt update
sudo apt upgrade -y

# Установка необходимых пакетов
sudo apt install -y python3-pip python3-venv postgresql nginx redis-server

# Установка зависимостей для psycopg2
sudo apt install -y python3-dev libpq-dev
```

#### Создание пользователя
```bash
sudo adduser pappi
sudo usermod -aG sudo pappi
```

### 2. Настройка PostgreSQL
```bash
# Создание базы данных и пользователя
sudo -u postgres psql -c "CREATE DATABASE pappi_db;"
sudo -u postgres psql -c "CREATE USER pappi_user WITH PASSWORD 'pappi_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE pappi_db TO pappi_user;"
```

### 3. Настройка Nginx
Создайте файл `/etc/nginx/sites-available/pappi`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /home/pappi/pappy;
    }

    location /media/ {
        root /home/pappi/pappy;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }
}
```

Активация конфигурации:
```bash
sudo ln -s /etc/nginx/sites-available/pappi /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

### 4. Настройка Gunicorn
Создайте файл `/etc/systemd/system/gunicorn.service`:
```ini
[Unit]
Description=gunicorn daemon
Requires=gunicorn.socket
After=network.target

[Service]
User=pappi
Group=www-data
WorkingDirectory=/home/pappi/pappy
ExecStart=/home/pappi/pappy/venv/bin/gunicorn \
    --access-logfile - \
    --workers 3 \
    --bind unix:/run/gunicorn.sock \
    config.wsgi:application

[Install]
WantedBy=multi-user.target
```

### 5. Настройка Redis
```bash
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### 6. Настройка Celery
Создайте файл `/etc/systemd/system/celery.service`:
```ini
[Unit]
Description=Celery Service
After=network.target

[Service]
User=pappi
Group=pappi
WorkingDirectory=/home/pappi/pappy
ExecStart=/home/pappi/pappy/venv/bin/celery -A config worker -l info

[Install]
WantedBy=multi-user.target
```

### 7. Запуск служб
```bash
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
sudo systemctl start celery
sudo systemctl enable celery
```

### 8. SSL сертификат (Let's Encrypt)
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## Обновление приложения

### 1. Получение изменений
```bash
cd /home/pappi/pappy
git pull origin main
```

### 2. Обновление зависимостей
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Применение миграций
```bash
python manage.py migrate
```

### 4. Сбор статических файлов
```bash
python manage.py collectstatic --noinput
```

### 5. Перезапуск служб
```bash
sudo systemctl restart gunicorn
sudo systemctl restart celery
```

## Мониторинг

### Логи
- Nginx: `/var/log/nginx/error.log`
- Gunicorn: `/var/log/gunicorn/error.log`
- Django: `/home/pappi/pappy/logs/django.log`
- Celery: `/var/log/celery/worker.log`

### Проверка статуса
```bash
sudo systemctl status nginx
sudo systemctl status gunicorn
sudo systemctl status redis
sudo systemctl status celery
```

## Резервное копирование

### База данных
```bash
# Создание бэкапа
pg_dump pappi_db > backup.sql

# Восстановление из бэкапа
psql pappi_db < backup.sql
```

### Медиафайлы
```bash
# Создание архива
tar -czf media_backup.tar.gz /home/pappi/pappy/media/

# Восстановление
tar -xzf media_backup.tar.gz -C /home/pappi/pappy/
```

## Безопасность

### Файрвол (UFW)
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Настройка прав доступа
```bash
sudo chown -R pappi:www-data /home/pappi/pappy
sudo chmod -R 755 /home/pappi/pappy
sudo chmod -R 770 /home/pappi/pappy/media
```

## Troubleshooting

### Проверка логов
```bash
# Nginx
sudo tail -f /var/log/nginx/error.log

# Gunicorn
sudo tail -f /var/log/gunicorn/error.log

# Django
tail -f /home/pappi/pappy/logs/django.log

# Celery
sudo tail -f /var/log/celery/worker.log
```

### Частые проблемы

#### 502 Bad Gateway
1. Проверьте статус Gunicorn
2. Проверьте права доступа к сокету
3. Проверьте логи Nginx и Gunicorn

#### Статические файлы не отображаются
1. Проверьте настройки STATIC_ROOT
2. Выполните collectstatic
3. Проверьте права доступа к папке static

#### Ошибки с базой данных
1. Проверьте подключение к PostgreSQL
2. Проверьте права пользователя базы данных
3. Проверьте настройки в .env файле 