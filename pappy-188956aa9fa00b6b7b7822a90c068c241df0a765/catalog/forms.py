from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Product, Category, ProductImage


class MultipleFileInput(forms.FileInput):
    def __init__(self, attrs=None):
        default_attrs = {'multiple': 'multiple'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

    def value_from_datadict(self, data, files, name):
        if hasattr(files, 'getlist'):
            return files.getlist(name)
        return files.get(name)


class ProductForm(forms.ModelForm):
    image_1 = forms.ImageField(
        label=_('Image 1'),
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    image_2 = forms.ImageField(
        label=_('Image 2'),
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    image_3 = forms.ImageField(
        label=_('Image 3'),
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Product
        fields = ['category', 'title', 'description', 'price', 'condition', 'location', 'breed', 'age', 'size', 'gender']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'condition': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'breed': forms.TextInput(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'size': forms.Select(attrs={'class': 'form-select'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def save(self, commit=True):
        product = super().save(commit=False)
        # Сохраняем изображения даже если commit=False
        if commit:
            product.save()
        
        # Обработка загруженных изображений
        for i in range(1, 4):
            image = self.cleaned_data.get(f'image_{i}')
            if image:
                # Создаем изображение, но не сохраняем если commit=False
                image_obj = ProductImage(
                    product=product,
                    image=image,
                    is_main=(i == 1)  # Первое изображение будет главным
                )
                if commit:
                    image_obj.save()
                else:
                    # Сохраняем для последующего создания
                    if not hasattr(self, '_image_objects'):
                        self._image_objects = []
                    self._image_objects.append(image_obj)
        
        if not commit:
            old_save_m2m = self.save_m2m
            def save_m2m():
                old_save_m2m()
                # Сохраняем отложенные изображения
                if hasattr(self, '_image_objects'):
                    for image_obj in self._image_objects:
                        image_obj.save()
            self.save_m2m = save_m2m
            
        return product

class ProductFilterForm(forms.Form):
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        empty_label=_('All categories'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    condition = forms.MultipleChoiceField(
        choices=Product.CONDITION_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    min_price = forms.DecimalField(
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('Min price')})
    )
    max_price = forms.DecimalField(
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('Max price')})
    )
    sort = forms.ChoiceField(
        choices=[
            ('newest', _('Newest first')),
            ('oldest', _('Oldest first')),
            ('price_low', _('Price: low to high')),
            ('price_high', _('Price: high to low')),
            ('popular', _('Most popular')),
        ],
        required=False,
        initial='newest',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Search products...')
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Получаем только активные категории
        self.fields['category'].queryset = Category.objects.filter(is_active=True) 