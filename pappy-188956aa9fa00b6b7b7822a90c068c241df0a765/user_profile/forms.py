from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from .models import UserProfile, SellerProfile, SpecialistProfile, VerificationDocument

User = get_user_model()

class UserSettingsForm(forms.ModelForm):
    """Форма для редактирования основных настроек пользователя"""
    class Meta:
        model = User
        fields = ['phone', 'email', 'is_specialist', 'is_shelter']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_specialist': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_shelter': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'location']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
        }

class SellerProfileForm(forms.ModelForm):
    """Форма для редактирования профиля продавца"""
    class Meta:
        model = SellerProfile
        fields = ['seller_type', 'company_name', 'inn', 'description', 'website']
        widgets = {
            'seller_type': forms.Select(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'inn': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['company_name'].required = False
        self.fields['inn'].required = False
        self.fields['website'].required = False

class SpecialistProfileForm(forms.ModelForm):
    """Форма для редактирования профиля специалиста"""
    class Meta:
        model = SpecialistProfile
        fields = ['specialization', 'experience_years', 'services', 'price_range']
        widgets = {
            'specialization': forms.Select(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'services': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'price_range': forms.TextInput(attrs={'class': 'form-control'}),
        }

class VerificationDocumentForm(forms.ModelForm):
    class Meta:
        model = VerificationDocument
        fields = ['document', 'comment']
        widgets = {
            'document': forms.FileInput(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
        help_texts = {
            'document': _('Загрузите документ, подтверждающий ваш статус'),
            'comment': _('Дополнительная информация о вашем статусе'),
        }

class SellerVerificationForm(forms.ModelForm):
    """Форма для подачи заявки на верификацию продавца"""
    class Meta:
        model = SellerProfile
        fields = ['seller_type', 'company_name', 'inn']
        widgets = {
            'seller_type': forms.Select(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'inn': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Делаем поля обязательными в зависимости от типа продавца
        if self.instance and self.instance.seller_type in ['entrepreneur', 'company']:
            self.fields['company_name'].required = True
            self.fields['inn'].required = True

class SpecialistVerificationForm(forms.ModelForm):
    """Форма для подачи заявки на верификацию специалиста"""
    class Meta:
        model = SpecialistProfile
        fields = ['specialization', 'experience_years', 'services', 'certificates']
        widgets = {
            'specialization': forms.Select(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'services': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['certificates'].required = True

class VerificationRequestForm(forms.Form):
    documents = forms.FileField(
        label=_('Документы'),
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        help_text=_('Загрузите документ, подтверждающий ваш статус')
    )
    comment = forms.CharField(
        label=_('Комментарий'),
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        required=False,
        help_text=_('Дополнительная информация о вашем статусе')
    ) 