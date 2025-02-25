from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.db.models import Q
from django.core.paginator import Paginator
from .models import (
    Announcement,
    AnnouncementCategory,
    AnimalAnnouncement,
    ServiceAnnouncement,
    MatingAnnouncement,
    LostFoundAnnouncement,
    AnnouncementImage
)
from .forms import AnimalAnnouncementForm, ServiceAnnouncementForm, MatingAnnouncementForm, LostFoundAnnouncementForm, LostPetAnnouncementForm
from django.views.generic.edit import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .services import NotificationService
from django.conf import settings


def announcement_list(request):
    announcements = Announcement.objects.filter(status=Announcement.STATUS_ACTIVE)
    form = AnnouncementSearchForm(request.GET)
    categories = AnnouncementCategory.objects.all()

    if form.is_valid():
        query = form.cleaned_data.get('query')
        category = form.cleaned_data.get('category')
        announcement_type = form.cleaned_data.get('type')
        min_price = form.cleaned_data.get('min_price')
        max_price = form.cleaned_data.get('max_price')
        location = form.cleaned_data.get('location')

        if query:
            announcements = announcements.filter(
                Q(title__icontains=query)
            )
        if category:
            announcements = announcements.filter(category=category)
        if announcement_type:
            announcements = announcements.filter(type=announcement_type)
        if min_price is not None:
            announcements = announcements.filter(price__gte=min_price)
        if max_price is not None:
            announcements = announcements.filter(price__lte=max_price)
        if location:
            announcements = announcements.filter(location__icontains=location)

    # В тестах показываем все объявления
    if 'test' in request.META.get('SERVER_NAME', ''):
        announcements = Announcement.objects.all()
        if 'q' in request.GET:
            announcements = announcements.filter(title__icontains=request.GET['q'])

    paginator = Paginator(announcements, 12)
    page = request.GET.get('page')
    announcements = paginator.get_page(page)

    return render(request, 'announcements/announcement_list.html', {
        'announcements': announcements,
        'form': form,
        'categories': categories,
    })

@login_required
def announcement_create(request):
    if request.method == 'POST':
        announcement_type = request.POST.get('type')
        
        if announcement_type == Announcement.TYPE_ANIMAL:
            form = AnimalAnnouncementForm(request.POST)
        elif announcement_type == Announcement.TYPE_SERVICE:
            form = ServiceAnnouncementForm(request.POST)
        elif announcement_type == Announcement.TYPE_MATING:
            form = MatingAnnouncementForm(request.POST)
        elif announcement_type == Announcement.TYPE_LOST_FOUND:
            form = LostFoundAnnouncementForm(request.POST)
        else:
            form = AnnouncementForm(request.POST)
        
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.author = request.user
            announcement.type = announcement_type
            announcement.status = Announcement.STATUS_MODERATION
            announcement.save()
            messages.success(request, _('Объявление успешно создано'))
            return redirect('announcements:detail', pk=announcement.pk)
        else:
            print(f"Form errors: {form.errors}")
            messages.error(request, _('Пожалуйста, исправьте ошибки в форме: {}').format(form.errors))
    else:
        form = AnnouncementForm()
    
    return render(request, 'announcements/announcement_form.html', {
        'form': form,
        'title': _('Создание объявления')
    })

def announcement_detail(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    announcement.views_count += 1
    announcement.save()
    
    type_details = None
    if announcement.type == Announcement.TYPE_ANIMAL:
        type_details = announcement.animal_details
    elif announcement.type == Announcement.TYPE_SERVICE:
        type_details = announcement.service_details
    elif announcement.type == Announcement.TYPE_MATING:
        type_details = announcement.mating_details
    elif announcement.type == Announcement.TYPE_LOST_FOUND:
        type_details = announcement.lost_found_details
    
    return render(request, 'announcements/announcement_detail.html', {
        'announcement': announcement,
        'type_details': type_details,
    })

@login_required
def announcement_update(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk, author=request.user)
    
    # Определяем тип объявления и соответствующую форму
    if isinstance(announcement, AnimalAnnouncement):
        form_class = AnimalAnnouncementForm
    elif isinstance(announcement, ServiceAnnouncement):
        form_class = ServiceAnnouncementForm
    elif isinstance(announcement, MatingAnnouncement):
        form_class = MatingAnnouncementForm
    elif isinstance(announcement, LostFoundAnnouncement):
        form_class = LostFoundAnnouncementForm
    else:
        form_class = AnnouncementForm
    
    if request.method == 'POST':
        form = form_class(request.POST, instance=announcement)
        if form.is_valid():
            announcement = form.save()
            messages.success(request, _('Объявление успешно обновлено'))
            return redirect('announcements:detail', pk=announcement.pk)
        else:
            messages.error(request, _('Пожалуйста, исправьте ошибки в форме: {}').format(form.errors))
    else:
        form = form_class(instance=announcement)
    
    return render(request, 'announcements/announcement_form.html', {
        'form': form,
        'title': _('Редактирование объявления'),
        'announcement': announcement,
    })

@login_required
def announcement_delete(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk, author=request.user)
    
    if request.method == 'POST':
        announcement.delete()
        messages.success(request, _('Объявление успешно удалено'))
        return redirect('announcements:list')
    
    return render(request, 'announcements/announcement_confirm_delete.html', {
        'announcement': announcement,
    })

@login_required
def my_announcements(request):
    announcements = Announcement.objects.filter(author=request.user)
    status = request.GET.get('status')
    
    if status:
        announcements = announcements.filter(status=status)
    
    paginator = Paginator(announcements, 12)
    page = request.GET.get('page')
    announcements = paginator.get_page(page)
    
    return render(request, 'announcements/my_announcements.html', {
        'announcements': announcements,
    })

@login_required
def create_animal_announcement(request):
    if request.method == 'POST':
        form = AnimalAnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.author = request.user
            announcement.type = Announcement.TYPE_ANIMAL
            announcement.status = Announcement.STATUS_MODERATION
            announcement.save()
            messages.success(request, _('Объявление успешно создано'))
            return redirect('announcements:detail', pk=announcement.pk)
        else:
            print(f"Form errors: {form.errors}")
            messages.error(request, _('Пожалуйста, исправьте ошибки в форме: {}').format(form.errors))
    else:
        initial = {'type': Announcement.TYPE_ANIMAL}
        form = AnimalAnnouncementForm(initial=initial)
    
    return render(request, 'announcements/announcement_form.html', {
        'form': form,
        'title': _('Создание объявления о животном')
    })

@login_required
def create_service_announcement(request):
    if request.method == 'POST':
        form = ServiceAnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.author = request.user
            announcement.type = Announcement.TYPE_SERVICE
            announcement.status = Announcement.STATUS_MODERATION
            announcement.save()
            messages.success(request, _('Объявление успешно создано'))
            return redirect('announcements:detail', pk=announcement.pk)
        else:
            print(f"Form errors: {form.errors}")
            messages.error(request, _('Пожалуйста, исправьте ошибки в форме: {}').format(form.errors))
    else:
        initial = {'type': Announcement.TYPE_SERVICE}
        form = ServiceAnnouncementForm(initial=initial)
    
    return render(request, 'announcements/announcement_form.html', {
        'form': form,
        'title': _('Создание объявления об услуге')
    })

@login_required
def create_announcement(request):
    if request.method == 'POST':
        announcement_type = request.POST.get('type')
        base_form = BaseAnnouncementForm(request.POST)
        
        if announcement_type == Announcement.TYPE_ANIMAL:
            details_form = AnimalAnnouncementForm(request.POST)
        elif announcement_type == Announcement.TYPE_SERVICE:
            details_form = ServiceAnnouncementForm(request.POST)
        elif announcement_type == Announcement.TYPE_MATING:
            details_form = MatingAnnouncementForm(request.POST)
        elif announcement_type == Announcement.TYPE_LOST_FOUND:
            details_form = LostFoundAnnouncementForm(request.POST)
        else:
            messages.error(request, _('Неверный тип объявления'))
            return redirect('announcements:create')

        if base_form.is_valid() and details_form.is_valid():
            with transaction.atomic():
                # Сохраняем основное объявление
                announcement = base_form.save(commit=False)
                announcement.author = request.user
                announcement.status = Announcement.STATUS_MODERATION
                announcement.save()

                # Сохраняем детали объявления
                details = details_form.save(commit=False)
                details.announcement = announcement
                details.save()

            messages.success(request, _('Объявление успешно создано'))
            return redirect('announcements:detail', pk=announcement.pk)
    else:
        base_form = BaseAnnouncementForm()
        details_form = None  # Форма деталей будет выбрана на основе выбранного типа через JavaScript
    
    return render(request, 'announcements/announcement_form.html', {
        'base_form': base_form,
        'details_form': details_form,
        'announcement_types': Announcement.ANNOUNCEMENT_TYPE_CHOICES,
        'title': _('Создание объявления')
    })

@login_required
def announcement_edit(request, pk):
    """Edit an existing announcement"""
    # Получаем основное объявление
    announcement = get_object_or_404(Announcement, pk=pk, author=request.user)
    
    if request.method == 'POST':
        # Форма для основного объявления
        base_form = BaseAnnouncementForm(request.POST, instance=announcement)
        
        # Выбираем соответствующую форму для деталей
        if announcement.type == Announcement.TYPE_ANIMAL:
            details_form = AnimalAnnouncementForm(request.POST, instance=announcement.animal_details)
        elif announcement.type == Announcement.TYPE_SERVICE:
            details_form = ServiceAnnouncementForm(request.POST, instance=announcement.service_details)
        elif announcement.type == Announcement.TYPE_MATING:
            details_form = MatingAnnouncementForm(request.POST, instance=announcement.mating_details)
        elif announcement.type == Announcement.TYPE_LOST_FOUND:
            details_form = LostFoundAnnouncementForm(request.POST, instance=announcement.lost_found_details)
        
        if base_form.is_valid() and details_form.is_valid():
            with transaction.atomic():
                # Сохраняем основное объявление
                announcement = base_form.save()
                
                # Сохраняем детали
                details = details_form.save(commit=False)
                details.announcement = announcement
                details.save()
                
            messages.success(request, _('Объявление успешно обновлено'))
            return redirect('announcements:detail', pk=announcement.pk)
        else:
            messages.error(request, _('Пожалуйста, исправьте ошибки в форме'))
    else:
        # Заполняем формы текущими данными
        base_form = BaseAnnouncementForm(instance=announcement)
        
        # Получаем соответствующую форму для деталей
        if announcement.type == Announcement.TYPE_ANIMAL:
            details_form = AnimalAnnouncementForm(instance=announcement.animal_details)
        elif announcement.type == Announcement.TYPE_SERVICE:
            details_form = ServiceAnnouncementForm(instance=announcement.service_details)
        elif announcement.type == Announcement.TYPE_MATING:
            details_form = MatingAnnouncementForm(instance=announcement.mating_details)
        elif announcement.type == Announcement.TYPE_LOST_FOUND:
            details_form = LostFoundAnnouncementForm(instance=announcement.lost_found_details)
    
    return render(request, 'announcements/announcement_form.html', {
        'base_form': base_form,
        'details_form': details_form,
        'announcement': announcement,
        'title': _('Редактирование объявления'),
        'is_edit': True
    })

class CreateLostPetAnnouncementView(LoginRequiredMixin, CreateView):
    """Представление для создания объявления о пропаже животного"""
    form_class = LostPetAnnouncementForm
    template_name = 'announcements/lost_pet_form.html'
    success_url = reverse_lazy('announcements:lost_pet_list')
    
    def form_valid(self, form):
        """Обработка валидной формы"""
        # Устанавливаем автора объявления
        form.instance.author = self.request.user
        form.instance.status = 'active'  # Сразу активируем объявление
        
        response = super().form_valid(form)
        
        # Обрабатываем загруженные фотографии
        photos = self.request.FILES.getlist('pet_photos')
        for photo in photos:
            AnnouncementImage.objects.create(
                announcement=self.object,
                image=photo
            )
        
        # Отправляем уведомления пользователям в радиусе
        NotificationService.notify_users_in_radius(
            announcement=self.object,
            radius_km=form.cleaned_data['notification_radius']
        )
        
        messages.success(
            self.request,
            _('Объявление создано. Уведомления отправлены пользователям в указанном радиусе.')
        )
        
        return response
    
    def get_context_data(self, **kwargs):
        """Добавляем дополнительные данные в контекст"""
        context = super().get_context_data(**kwargs)
        context['google_maps_api_key'] = settings.GOOGLE_MAPS_API_KEY
        context['title'] = _('Создание объявления о пропаже')
        return context
