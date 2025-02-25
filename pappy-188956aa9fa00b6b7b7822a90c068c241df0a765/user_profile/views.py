from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.db.models import Q
from django.contrib import messages
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from .forms import (
    UserSettingsForm, UserProfileForm, SellerProfileForm, SpecialistProfileForm,
    VerificationDocumentForm
)
from .models import (
    SellerProfile, SpecialistProfile, VerificationDocument
)
from notifications.models import Notification

@login_required
def profile_settings(request):
    if request.method == 'POST':
        user_form = UserSettingsForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, instance=request.user.profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, _('Настройки профиля успешно обновлены'))
            return redirect('user_profile:settings')
    else:
        user_form = UserSettingsForm(instance=request.user)
        profile_form = UserProfileForm(instance=request.user.profile)
    
    return render(request, 'user_profile/settings.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })

@login_required
def seller_profile(request):
    """Страница настроек профиля продавца"""
    try:
        profile = request.user.seller_profile
        if isinstance(profile, SpecialistProfile):
            return redirect('user_profile:specialist_profile')
    except SellerProfile.DoesNotExist:
        profile = None
    
    if request.method == 'POST':
        form = SellerProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, _('Профиль продавца успешно обновлен'))
            return redirect('user_profile:seller_profile')
    else:
        form = SellerProfileForm(instance=profile)
    
    return render(request, 'user_profile/seller_profile.html', {
        'form': form,
        'profile': profile
    })

@login_required
def specialist_profile(request):
    """Страница настроек профиля специалиста"""
    try:
        profile = request.user.specialist_profile
    except SpecialistProfile.DoesNotExist:
        profile = None
    
    if request.method == 'POST':
        form = SpecialistProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, _('Профиль специалиста успешно обновлен'))
            return redirect('user_profile:specialist_profile')
    else:
        form = SpecialistProfileForm(instance=profile)
    
    return render(request, 'user_profile/specialist_profile.html', {
        'form': form,
        'profile': profile
    })

@login_required
def verification_request(request):
    if request.method == 'POST':
        form = VerificationDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.user = request.user
            document.save()
            messages.success(request, _('Заявка на верификацию успешно отправлена'))
            return redirect('user_profile:verification_status')
    else:
        form = VerificationDocumentForm()
    
    return render(request, 'user_profile/verification_request.html', {
        'form': form,
    })

@login_required
def verification_status(request):
    documents = VerificationDocument.objects.filter(user=request.user).order_by('-uploaded_at')
    return render(request, 'user_profile/verification_status.html', {
        'documents': documents,
    })

@login_required
def public_profile(request, user_id):
    """Публичная страница профиля пользователя"""
    user = get_object_or_404(get_user_model(), id=user_id)
    try:
        seller_profile = user.seller_profile
        is_specialist = isinstance(seller_profile, SpecialistProfile)
    except SellerProfile.DoesNotExist:
        seller_profile = None
        is_specialist = False
    
    return render(request, 'user_profile/public_profile.html', {
        'profile_user': user,
        'seller_profile': seller_profile,
        'is_specialist': is_specialist
    })

@login_required
def create_seller_profile(request):
    if hasattr(request.user, 'sellerprofile'):
        return redirect('user_profile:update_seller_profile')
        
    if request.method == 'POST':
        form = SellerProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, 'Профиль продавца успешно создан')
            return redirect('catalog:home')
    else:
        form = SellerProfileForm()
    
    return render(request, 'user_profile/seller_profile_form.html', {'form': form})

@login_required
def update_seller_profile(request, user_id=None):
    if user_id and user_id != request.user.id:
        return HttpResponseForbidden()
    
    profile = get_object_or_404(SellerProfile, user=request.user)
    
    if request.method == 'POST':
        form = SellerProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлен')
            return redirect('catalog:home')
    else:
        form = SellerProfileForm(instance=profile)
    
    return render(request, 'user_profile/seller_profile_form.html', {'form': form})

@login_required
def delete_profile(request):
    if request.method == 'POST':
        profile = get_object_or_404(SellerProfile, user=request.user)
        profile.delete()
        messages.success(request, 'Профиль успешно удален')
        return redirect('catalog:home')
    return redirect('user_profile:update_seller_profile')

@login_required
def request_verification(request):
    profile = get_object_or_404(SellerProfile, user=request.user)
    
    if request.method == 'POST':
        if 'document_scan' in request.FILES:
            profile.document_scan = request.FILES['document_scan']
            profile.save()
            messages.success(request, 'Документы отправлены на проверку')
            return redirect('catalog:home')
    
    return render(request, 'user_profile/verification_form.html')

@login_required
def create_specialist_profile(request):
    if hasattr(request.user, 'specialistprofile'):
        return redirect('user_profile:specialist_detail', pk=request.user.specialistprofile.pk)
        
    if request.method == 'POST':
        form = SpecialistProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, 'Профиль специалиста успешно создан')
            return redirect('catalog:home')
    else:
        form = SpecialistProfileForm()
    
    return render(request, 'user_profile/specialist_profile_form.html', {'form': form})

def specialist_list(request):
    specialists = SpecialistProfile.objects.filter(is_verified=True)
    specialization = request.GET.get('specialization')
    query = request.GET.get('q')
    
    if specialization:
        specialists = specialists.filter(specialization=specialization)
    if query:
        specialists = specialists.filter(
            Q(user__phone__icontains=query) |
            Q(services__icontains=query)
        )
    
    paginator = Paginator(specialists, 12)
    page = request.GET.get('page')
    specialists = paginator.get_page(page)
    
    return render(request, 'user_profile/specialist_list.html', {
        'specialists': specialists,
        'specialization_choices': SpecialistProfile.SPECIALIZATION_CHOICES,
    })

def specialist_detail(request, pk):
    specialist = get_object_or_404(SpecialistProfile, pk=pk, is_verified=True)
    return render(request, 'user_profile/specialist_detail.html', {
        'specialist': specialist,
    })

@login_required
def become_seller(request):
    """View for handling seller registration process"""
    if hasattr(request.user, 'seller_verification'):
        if request.user.seller_verification.status == 'PE':
            messages.info(request, _('Your seller verification is pending review.'))
            return redirect('user_profile:verification_pending')
        elif request.user.seller_verification.status == 'AP':
            messages.success(request, _('You are already a verified seller.'))
            return redirect('user_profile:profile')
    
    if request.method == 'POST':
        form = SellerVerificationForm(request.POST, request.FILES)
        if form.is_valid():
            verification = form.save(commit=False)
            verification.user = request.user
            verification.save()
            messages.success(request, _('Your seller verification request has been submitted.'))
            return redirect('user_profile:verification_pending')
    else:
        form = SellerVerificationForm()
    
    return render(request, 'user_profile/become_seller.html', {'form': form})

@login_required
def verification_pending(request):
    """View for showing verification pending status"""
    if not hasattr(request.user, 'seller_verification'):
        return redirect('user_profile:become_seller')
    
    verification = request.user.seller_verification
    return render(request, 'user_profile/verification_pending.html', {
        'verification': verification
    }) 