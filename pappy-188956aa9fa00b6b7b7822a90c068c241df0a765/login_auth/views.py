from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .models import PhoneVerification
from django.utils.crypto import get_random_string
from django.conf import settings

User = get_user_model()

def login(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        user = User.objects.filter(phone=phone).first()
        
        if not user:
            messages.error(request, 'Пользователь с таким номером не найден')
            return render(request, 'login_auth/login.html')
        
        verification = PhoneVerification.objects.create(phone=phone)
        code = verification.generate_code()
        
        # TODO: Отправить SMS с кодом
        
        request.session['phone'] = phone
        return redirect('login_auth:sms_validation')
    
    return render(request, 'login_auth/login.html')

@require_http_methods(['GET', 'POST'])
def sms_validation(request):
    phone = request.session.get('phone')
    print(f"Phone from session: {phone}")
    
    if not phone:
        print("No phone in session")
        return redirect('login_auth:login')
    
    if request.method == 'POST':
        code = request.POST.get('code')
        print(f"Received code: {code}")
        
        try:
            verification = PhoneVerification.objects.filter(
                phone=phone,
                is_verified=False
            ).latest('created')
            print(f"Found verification: {verification.code}, attempts: {verification.attempts}")
            
            if verification.verify(code):
                print("Code verified successfully")
                # Если это регистрация, создаем пользователя
                user = User.objects.filter(phone=phone).first()
                if not user:
                    print("Creating new user")
                    user = User.objects.create_user(phone=phone)
                else:
                    print("Found existing user")
                
                auth_login(request, user)
                del request.session['phone']
                return redirect('catalog:home')
            else:
                print("Code verification failed")
                if verification.is_blocked:
                    messages.error(request, 'Слишком много попыток. Запросите новый код.')
                elif verification.is_expired():
                    messages.error(request, 'Код истек. Запросите новый код.')
                else:
                    messages.error(request, 'Неверный код. Осталось попыток: ' + 
                                 str(settings.MAX_VERIFICATION_ATTEMPTS - verification.attempts))
        except PhoneVerification.DoesNotExist:
            print("Verification not found")
            messages.error(request, 'Код подтверждения не найден. Запросите новый код.')
    
    return render(request, 'login_auth/sms_validation.html')

def signup(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        
        if User.objects.filter(phone=phone).exists():
            messages.error(request, 'Пользователь с таким номером уже существует')
            return render(request, 'login_auth/signup.html')
        
        verification = PhoneVerification.objects.create(phone=phone)
        code = verification.generate_code()
        
        # TODO: Отправить SMS с кодом
        
        request.session['phone'] = phone
        return redirect('login_auth:sms_validation')
    
    return render(request, 'login_auth/signup.html')

def signup_success(request):
    return render(request, 'login_auth/signup_success.html') 