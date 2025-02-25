from django import forms
from django.utils.translation import gettext_lazy as _
from .models import (
    Announcement,
    AnnouncementCategory,
    AnimalAnnouncement,
    ServiceAnnouncement,
    MatingAnnouncement,
    LostFoundAnnouncement,
    AnnouncementImage,
    LostPetAnnouncement
)

class BaseAnnouncementForm(forms.ModelForm):
    """Base form for the main Announcement model"""
    class Meta:
        model = Announcement
        fields = ['title', 'description', 'price', 'location', 'category', 'type']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }

class AnimalAnnouncementForm(forms.ModelForm):
    """Form for animal announcements"""
    class Meta:
        model = AnimalAnnouncement
        fields = [
            'species', 'breed', 'age', 'gender', 'size', 'color',
            'pedigree', 'vaccinated', 'passport', 'microchipped'
        ]

class ServiceAnnouncementForm(forms.ModelForm):
    """Form for service announcements"""
    class Meta:
        model = ServiceAnnouncement
        fields = ['service_type', 'experience', 'certificates', 'schedule']
        widgets = {
            'certificates': forms.Textarea(attrs={'rows': 3}),
            'schedule': forms.Textarea(attrs={'rows': 3}),
        }

class MatingAnnouncementForm(forms.ModelForm):
    """Form for mating announcements"""
    class Meta:
        model = MatingAnnouncement
        fields = ['requirements', 'achievements']
        widgets = {
            'requirements': forms.Textarea(attrs={'rows': 3}),
            'achievements': forms.Textarea(attrs={'rows': 3}),
        }

class LostFoundAnnouncementForm(forms.ModelForm):
    """Форма для объявлений о потерянных/найденных животных"""
    
    class Meta:
        model = LostFoundAnnouncement
        fields = [
            'type',
            'date_lost_found',
            'last_seen_location',
            'latitude',
            'longitude',
            'animal_type',
            'breed',
            'color',
            'color_pattern',
            'distinctive_features',
            'size',
            'health_status',
            'has_microchip',
            'has_collar',
            'has_tag',
            'temperament',
            'contact_phone',
            'contact_email',
            'reward_amount',
            'search_radius',
            'last_seen_details'
        ]
        widgets = {
            'date_lost_found': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'last_seen_location': forms.TextInput(
                attrs={'class': 'location-autocomplete'}
            ),
            'distinctive_features': forms.Textarea(
                attrs={'rows': 3, 'placeholder': _('Опишите особые приметы питомца')}
            ),
            'last_seen_details': forms.Textarea(
                attrs={'rows': 3, 'placeholder': _('Опишите обстоятельства пропажи/находки')}
            ),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Делаем некоторые поля необязательными для найденных животных
        if self.data.get('type') == LostFoundAnnouncement.TYPE_FOUND:
            self.fields['contact_email'].required = False
            self.fields['reward_amount'].required = False
            self.fields['search_radius'].required = False

    def clean(self):
        cleaned_data = super().clean()
        announcement_type = cleaned_data.get('type')
        reward_amount = cleaned_data.get('reward_amount')

        # Проверяем, что вознаграждение указано только для потерянных животных
        if announcement_type == LostFoundAnnouncement.TYPE_FOUND and reward_amount:
            self.add_error('reward_amount', _('Вознаграждение можно указать только для потерянных животных'))

        return cleaned_data

class AnnouncementImageForm(forms.ModelForm):
    """Form for announcement images"""
    class Meta:
        model = AnnouncementImage
        fields = ['image', 'is_main']

class AnnouncementSearchForm(forms.Form):
    """Form for searching announcements"""
    query = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'placeholder': _('Поиск по объявлениям...'),
        'class': 'form-control'
    }))
    category = forms.ModelChoiceField(
        queryset=AnnouncementCategory.objects.all(),
        required=False,
        empty_label=_('Все категории')
    )
    type = forms.ChoiceField(
        choices=[('', _('Все типы'))] + Announcement.ANNOUNCEMENT_TYPE_CHOICES,
        required=False
    )
    min_price = forms.DecimalField(required=False, min_value=0)
    max_price = forms.DecimalField(required=False, min_value=0)
    location = forms.CharField(required=False)
    
    def clean(self):
        cleaned_data = super().clean()
        min_price = cleaned_data.get('min_price')
        max_price = cleaned_data.get('max_price')
        
        if min_price and max_price and min_price > max_price:
            raise forms.ValidationError(_('Минимальная цена не может быть больше максимальной'))

class LostPetAnnouncementForm(forms.ModelForm):
    """Форма для создания объявления о пропаже животного"""
    
    last_seen_date = forms.DateTimeField(
        label=_('Дата и время пропажи'),
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})
    )
    
    last_seen_location = forms.CharField(
        label=_('Место последней встречи'),
        widget=forms.TextInput(attrs={
            'class': 'location-autocomplete',
            'placeholder': _('Введите адрес или выберите на карте')
        })
    )
    
    latitude = forms.DecimalField(
        widget=forms.HiddenInput(),
        required=False
    )
    
    longitude = forms.DecimalField(
        widget=forms.HiddenInput(),
        required=False
    )
    
    notification_radius = forms.IntegerField(
        label=_('Радиус уведомлений (км)'),
        min_value=1,
        max_value=50,
        initial=5,
        help_text=_('Пользователи в этом радиусе получат уведомление')
    )
    
    pet_photos = forms.ImageField(
        label=_('Фотографии питомца'),
        widget=forms.ClearableFileInput(attrs={'multiple': True}),
        required=True,
        help_text=_('Загрузите хотя бы одну фотографию')
    )
    
    distinctive_features = forms.CharField(
        label=_('Отличительные черты'),
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': _('Опишите особые приметы, ошейник, чип и т.д.')
        })
    )
    
    reward = forms.DecimalField(
        label=_('Вознаграждение'),
        required=False,
        min_value=0,
        help_text=_('Оставьте пустым, если не предполагается')
    )
    
    contact_phone = forms.CharField(
        label=_('Контактный телефон'),
        required=True
    )
    
    contact_time = forms.CharField(
        label=_('Удобное время для связи'),
        required=False,
        help_text=_('Например: с 9:00 до 21:00')
    )
    
    additional_contacts = forms.CharField(
        label=_('Дополнительные контакты'),
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 2,
            'placeholder': _('Другие способы связи: WhatsApp, Telegram и т.д.')
        })
    )

    class Meta:
        model = LostPetAnnouncement
        fields = [
            'pet_type', 'breed', 'name', 'age',
            'last_seen_date', 'last_seen_location',
            'latitude', 'longitude', 'notification_radius',
            'pet_photos', 'distinctive_features',
            'reward', 'contact_phone', 'contact_time',
            'additional_contacts'
        ]
        
    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('latitude') or not cleaned_data.get('longitude'):
            raise forms.ValidationError(
                _('Пожалуйста, укажите местоположение на карте')
            )
        return cleaned_data 