#!/bin/bash

# Проверка наличия Python
if ! command -v python3 &> /dev/null; then
    echo "Python3 не установлен. Пожалуйста, установите Python3"
    exit 1
fi

# Проверка наличия pip
if ! command -v pip3 &> /dev/null; then
    echo "pip3 не установлен. Пожалуйста, установите pip3"
    exit 1
fi

# Удаление старого виртуального окружения, если оно существует
if [ -d "venv" ]; then
    echo "Удаление старого виртуального окружения..."
    rm -rf venv
fi

# Создание нового виртуального окружения
echo "Создание виртуального окружения..."
python3 -m venv venv

# Активация виртуального окружения
echo "Активация виртуального окружения..."
source venv/bin/activate

# Обновление pip до последней версии
echo "Обновление pip..."
pip install --upgrade pip

# Установка wheel (для избежания ошибок сборки)
echo "Установка wheel..."
pip install wheel

# Установка зависимостей
echo "Установка зависимостей..."
pip install -r requirements.txt

# Создание проекта Django, если его нет
if [ ! -f "manage.py" ]; then
    echo "Создание нового проекта Django..."
    django-admin startproject config .
fi

# Создание приложений Django
echo "Создание Django приложений..."
python manage.py startapp login_auth
python manage.py startapp catalog
python manage.py startapp kotopsinder

# Создание необходимых директорий
echo "Создание директорий для медиа и статических файлов..."
mkdir -p media
mkdir -p static
mkdir -p templates

# Применение миграций
echo "Применение миграций..."
python manage.py makemigrations
python manage.py migrate

# Создание суперпользователя
echo "Создание суперпользователя..."
python manage.py createsuperuser

# Сбор статических файлов
echo "Сбор статических файлов..."
python manage.py collectstatic --noinput

# Запуск сервера
echo "Запуск сервера разработки..."
python manage.py runserver 