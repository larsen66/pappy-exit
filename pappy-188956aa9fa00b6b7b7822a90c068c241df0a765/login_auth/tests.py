from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.template.loader import get_template
from .models import PhoneVerification
from unittest.mock import patch, Mock

User = get_user_model()

# Мок-шаблон для тестов
MOCK_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>SMS Validation</title></head>
<body>
    <form method="post">
        {% csrf_token %}
        <input type="text" name="code">
        <button type="submit">Verify</button>
    </form>
    {% if messages %}
    <ul class="messages">
        {% for message in messages %}
        <li>{{ message }}</li>
        {% endfor %}
    </ul>
    {% endif %}
</body>
</html>
"""

@override_settings(
    CODE_EXPIRY_MINUTES=10,
    MAX_VERIFICATION_ATTEMPTS=3
)
class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.phone = '+79991234567'
        self.password = 'testpass123'
        
        # Подменяем шаблон для тестов
        self.template_mock = Mock()
        self.template_mock.render = Mock(return_value=MOCK_TEMPLATE)
        self.get_template_patcher = patch('django.template.loader.get_template', 
                                        return_value=self.template_mock)
        self.get_template_patcher.start()
    
    def tearDown(self):
        self.get_template_patcher.stop()
    
    def test_registration(self):
        """Тест регистрации по номеру телефона"""
        # Шаг 1: Запрос кода подтверждения
        response = self.client.post(reverse('login_auth:signup'), {
            'phone': self.phone
        })
        self.assertEqual(response.status_code, 302)  # Редирект на страницу ввода кода
        
        # Проверяем, что верификация создана
        verification = PhoneVerification.objects.get(phone=self.phone)
        self.assertFalse(verification.is_verified)
        
        # Шаг 2: Подтверждение кода
        self.client.session['phone'] = self.phone  # Добавляем телефон в сессию
        response = self.client.post(reverse('login_auth:sms_validation'), {
            'code': verification.code
        })
        self.assertEqual(response.status_code, 302)  # Редирект на главную
        
        # Проверяем, что пользователь создан
        user = User.objects.get(phone=self.phone)
        self.assertTrue(user.is_authenticated)
    
    def test_login(self):
        """Тест входа в систему"""
        # Создаем пользователя
        user = User.objects.create_user(phone=self.phone, password=self.password)
        
        # Шаг 1: Запрос кода подтверждения
        response = self.client.post(reverse('login_auth:login'), {
            'phone': self.phone
        })
        self.assertEqual(response.status_code, 302)
        
        # Проверяем, что верификация создана
        verification = PhoneVerification.objects.get(phone=self.phone)
        
        # Шаг 2: Подтверждение кода
        self.client.session['phone'] = self.phone  # Добавляем телефон в сессию
        response = self.client.post(reverse('login_auth:sms_validation'), {
            'code': verification.code
        })
        self.assertEqual(response.status_code, 302)
        
        # Проверяем, что пользователь вошел в систему
        self.assertTrue('_auth_user_id' in self.client.session)
    
    def test_sms_verification(self):
        """Тест верификации через SMS"""
        # Создаем пользователя
        user = User.objects.create_user(phone=self.phone, password=self.password)
        
        # Создаем верификацию
        verification = PhoneVerification.objects.create(phone=self.phone)
        code = verification.generate_code()
        
        # Добавляем телефон в сессию
        session = self.client.session
        session['phone'] = self.phone
        session.save()
        
        # Пробуем неверный код
        response = self.client.post(reverse('login_auth:sms_validation'), {
            'code': '000000'
        })
        self.assertEqual(response.status_code, 200)  # Остаемся на странице
        verification.refresh_from_db()
        self.assertEqual(verification.attempts, 1)
        self.assertFalse(verification.is_verified)
        
        # Пробуем верный код
        response = self.client.post(reverse('login_auth:sms_validation'), {
            'code': code
        })
        self.assertEqual(response.status_code, 302)  # Редирект после успеха
        verification.refresh_from_db()
        self.assertTrue(verification.is_verified) 