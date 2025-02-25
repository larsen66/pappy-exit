from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.translation import gettext as _
from .models import Category, Product, Favorite, ProductImage, MatingRequest
from .forms import ProductForm, ProductFilterForm
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db import transaction
from chat.models import Dialog
from notifications.models import Notification
from login_auth.models import User

def search_products(request):
    query = request.GET.get('q', '')
    products_list = Product.objects.filter(
        Q(title__icontains=query) |
        Q(description__icontains=query) |
        Q(category__name__icontains=query),
        status='active'
    ).select_related('seller', 'category').prefetch_related('images').distinct()
    
    # Фильтрация по состоянию
    conditions = request.GET.getlist('condition')
    if conditions:
        products_list = products_list.filter(condition__in=conditions)
    
    # Фильтрация по цене
    price_min = request.GET.get('price_min')
    if price_min and price_min.isdigit():
        products_list = products_list.filter(price__gte=price_min)
    
    price_max = request.GET.get('price_max')
    if price_max and price_max.isdigit():
        products_list = products_list.filter(price__lte=price_max)
    
    # Фильтрация по категории
    category_id = request.GET.get('category')
    if category_id and category_id.isdigit():
        category = get_object_or_404(Category, id=category_id)
        products_list = products_list.filter(
            Q(category=category) | Q(category__parent=category)
        )
    
    # Фильтрация по местоположению
    location = request.GET.get('location')
    if location:
        products_list = products_list.filter(location__icontains=location)
    
    # Сортировка
    sort = request.GET.get('sort', '-created')
    valid_sort_fields = ['price', '-price', 'created', '-created', 'views', '-views']
    if sort in valid_sort_fields:
        products_list = products_list.order_by(sort)
    
    # Пагинация
    paginator = Paginator(products_list, 24)  # 24 товара на странице
    page = request.GET.get('page')
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    
    # Получаем все категории для фильтра
    categories = Category.objects.filter(parent=None).prefetch_related('children')
    
    context = {
        'query': query,
        'products': products,
        'categories': categories,
        'current_filters': {
            'condition': conditions,
            'price_min': price_min,
            'price_max': price_max,
            'category': category_id,
            'location': location,
            'sort': sort,
        }
    }
    return render(request, 'catalog/search_results.html', context)

def catalog_home(request):
    """Главная страница каталога"""
    featured_products = Product.objects.filter(
        status='active',
        is_featured=True
    ).select_related('seller').prefetch_related('images')[:8]
    
    categories = Category.objects.filter(
        is_active=True,
        parent__isnull=True
    ).prefetch_related('children')
    
    latest_products = Product.objects.filter(
        status='active'
    ).select_related('seller').prefetch_related('images')[:8]
    
    return render(request, 'catalog/home.html', {
        'featured_products': featured_products,
        'categories': categories,
        'latest_products': latest_products
    })

def category_detail(request, slug):
    """Страница категории с фильтрацией товаров"""
    category = get_object_or_404(Category, slug=slug, is_active=True)
    form = ProductFilterForm(request.GET)
    
    # Базовый queryset
    products = Product.objects.filter(
        status='active',
        category=category
    ).select_related('seller').prefetch_related('images')
    
    if form.is_valid():
        # Применяем фильтры
        if form.cleaned_data['condition']:
            products = products.filter(condition__in=form.cleaned_data['condition'])
        
        if form.cleaned_data['min_price']:
            products = products.filter(price__gte=form.cleaned_data['min_price'])
        
        if form.cleaned_data['max_price']:
            products = products.filter(price__lte=form.cleaned_data['max_price'])
        
        if form.cleaned_data['search']:
            query = form.cleaned_data['search']
            products = products.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query)
            )
        
        # Сортировка
        sort = form.cleaned_data['sort']
        if sort == 'oldest':
            products = products.order_by('created')
        elif sort == 'price_low':
            products = products.order_by('price')
        elif sort == 'price_high':
            products = products.order_by('-price')
        elif sort == 'popular':
            products = products.order_by('-views')
        else:  # newest
            products = products.order_by('-created')
    
    # Пагинация
    paginator = Paginator(products, 12)
    page = request.GET.get('page')
    products = paginator.get_page(page)
    
    return render(request, 'catalog/category_detail.html', {
        'category': category,
        'form': form,
        'products': products
    })

def product_detail(request, slug):
    """Страница товара"""
    product = get_object_or_404(Product, slug=slug, status='active')
    
    # Увеличиваем счетчик просмотров
    product.views += 1
    product.save()
    
    # Получаем похожие товары
    similar_products = Product.objects.filter(
        status='active',
        category=product.category
    ).exclude(id=product.id)[:4]
    
    return render(request, 'catalog/product_detail.html', {
        'product': product,
        'similar_products': similar_products
    })

@login_required
def my_products(request):
    """Страница с товарами пользователя"""
    products = Product.objects.filter(
        seller=request.user
    ).order_by('-created')
    
    # Фильтр по статусу
    status = request.GET.get('status')
    if status:
        products = products.filter(status=status)
    
    # Пагинация
    paginator = Paginator(products, 10)
    page = request.GET.get('page')
    products = paginator.get_page(page)
    
    return render(request, 'catalog/my_products.html', {
        'products': products,
        'current_status': status
    })

@login_required
def product_create(request):
    """Создание нового товара"""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = request.user
            product.save()
            form.save_m2m()
            return redirect('catalog:product_detail', slug=product.slug)
    else:
        form = ProductForm()
    
    return render(request, 'catalog/product_form.html', {
        'form': form,
        'title': _('New listing')
    })

@login_required
def product_edit(request, slug):
    """Редактирование товара"""
    product = get_object_or_404(Product, slug=slug, seller=request.user)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save()
            return redirect('catalog:product_detail', slug=product.slug)
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'catalog/product_form.html', {
        'form': form,
        'product': product,
        'title': _('Edit listing')
    })

@login_required
def toggle_favorite(request):
    """Добавление/удаление товара из избранного"""
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        if product_id:
            product = get_object_or_404(Product, id=product_id)
            favorite, created = Favorite.objects.get_or_create(
                user=request.user,
                product=product
            )
            
            if not created:
                favorite.delete()
                is_favorite = False
            else:
                is_favorite = True
            
            return JsonResponse({
                'status': 'success',
                'is_favorite': is_favorite
            })
    
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def favorites(request):
    """Страница с избранными товарами"""
    favorites = Favorite.objects.filter(
        user=request.user
    ).select_related('product', 'product__seller').prefetch_related('product__images')
    
    # Пагинация
    paginator = Paginator(favorites, 12)
    page = request.GET.get('page')
    favorites = paginator.get_page(page)
    
    return render(request, 'catalog/favorites.html', {
        'favorites': favorites
    })

@login_required
def update_product_status(request, product_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    product = get_object_or_404(Product, id=product_id, seller=request.user)
    
    try:
        data = json.loads(request.body)
        status = data.get('status')
        
        if status not in dict(Product.STATUS_CHOICES):
            return JsonResponse({'error': 'Invalid status'}, status=400)
        
        product.status = status
        product.save()
        
        return JsonResponse({'status': 'success'})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

@login_required
def delete_product(request, product_id):
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    product = get_object_or_404(Product, id=product_id, seller=request.user)
    product.delete()
    
    return JsonResponse({'status': 'success'})

@login_required
def delete_product_image(request, image_id):
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    image = get_object_or_404(ProductImage, id=image_id, product__seller=request.user)
    
    # Если это главное изображение, сделать следующее изображение главным
    if image.is_main:
        next_image = ProductImage.objects.filter(
            product=image.product
        ).exclude(id=image.id).first()
        if next_image:
            next_image.is_main = True
            next_image.save()
    
    image.delete()
    return JsonResponse({'status': 'success'})

@login_required
def create_lost_pet(request):
    """Create lost pet announcement"""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = request.user
            product.price = 0  # Lost pets are free
            product.status = 'active'  # Auto-activate
            product.save()
            form.save_m2m()  # This will save the images
            
            # Notify nearby users
            notify_nearby_users(product)
            
            messages.success(request, _('Lost pet announcement created successfully'))
            return redirect('catalog:product_detail', slug=product.slug)
        else:
            messages.error(request, _('Please correct the errors below'))
            return render(request, 'catalog/lost_pet_form.html', {'form': form})
    else:
        form = ProductForm(initial={'category': Category.objects.get(slug='lostfound')})
    
    return render(request, 'catalog/lost_pet_form.html', {'form': form})

def lost_pets_search(request):
    """Search for lost pets"""
    query = request.GET.get('q', '')
    location = request.GET.get('location', '')
    
    products = Product.objects.filter(
        category__slug='lostfound',
        status='active'
    )
    
    if query:
        products = products.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(breed__icontains=query)
        )
    
    if location:
        products = products.filter(location__icontains=location)
    
    return JsonResponse({
        'results': [
            {
                'id': p.id,
                'title': p.title,
                'description': p.description,
                'location': p.location,
                'image': p.images.filter(is_main=True).first().image.url if p.images.exists() else None
            }
            for p in products
        ]
    })

@login_required
@require_POST
def mark_as_found(request, pk):
    """Mark lost pet as found"""
    product = get_object_or_404(Product, pk=pk, category__slug='lostfound')
    
    # Check if user is the owner
    if product.seller != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    product.status = 'archived'
    product.save()
    
    messages.success(request, _('Pet marked as found'))
    return JsonResponse({'status': 'ok'})

@login_required
@require_POST
def contact_owner(request):
    """Contact lost pet owner"""
    product = get_object_or_404(Product, pk=request.POST.get('product'))
    
    # Create dialog if doesn't exist
    dialog = Dialog.objects.filter(
        participants=request.user
    ).filter(
        participants=product.seller
    ).filter(
        product=product
    ).first()
    
    if not dialog:
        dialog = Dialog.objects.create(product=product)
        dialog.participants.add(request.user, product.seller)
        dialog.save()
    
    return JsonResponse({'status': 'success', 'dialog_id': dialog.id})

def notify_nearby_users(product):
    """Notify users in the area about lost pet"""
    print(f"Notifying users about lost pet: {product.title}")
    print(f"Product location: {product.location}")
    
    if not product.location:
        print("No location provided")
        return
        
    city = product.location.split(',')[0].strip()  # Get city name, keep original case
    print(f"Searching for users in city: {city}")
    
    nearby_users = User.objects.filter(
        location__iregex=f'^{city}'  # Match city name at start, case-insensitive
    ).exclude(id=product.seller.id)  # Exclude the seller
    
    print(f"Found nearby users: {list(nearby_users.values_list('phone', 'location'))}")
    
    for user in nearby_users:
        print(f"Creating notification for user: {user.phone}")
        notification = Notification.objects.create(
            recipient=user,
            type='lost_pet_nearby',
            title='Потерянный питомец рядом',
            text=f'В вашем районе пропал питомец: {product.title}. Местоположение: {product.location}',
            link=f'/catalog/product/{product.slug}/'
        )
        print(f"Created notification: {notification.id}")

@login_required
@require_POST
def mating_like(request):
    """Like a pet for mating"""
    product = get_object_or_404(Product, pk=request.POST.get('product'))
    
    # Get user's pet in mating category
    user_pet = request.user.products.filter(
        category__slug='mating',
        status='active'
    ).first()
    
    if not user_pet:
        return JsonResponse({
            'status': 'error',
            'message': _('You need to create a mating profile first')
        }, status=400)
    
    # Check breed compatibility
    if user_pet.breed != product.breed:
        return JsonResponse({
            'status': 'error',
            'message': _('Pets must be of the same breed')
        }, status=400)
    
    # Check gender compatibility
    if user_pet.gender == product.gender:
        return JsonResponse({
            'status': 'error',
            'message': _('Pets must be of opposite genders')
        }, status=400)
    
    # Create mating request
    with transaction.atomic():
        request = MatingRequest.objects.create(
            from_pet=user_pet,
            to_pet=product
        )
        
        # Check for mutual like
        mutual_request = MatingRequest.objects.filter(
            from_pet=product,
            to_pet=user_pet,
            status='pending'
        ).first()
        
        if mutual_request:
            # It's a match!
            request.status = 'matched'
            mutual_request.status = 'matched'
            request.save()
            mutual_request.save()
            
            # Create dialog
            dialog = Dialog.objects.create(product=product)
            dialog.participants.add(request.from_pet.seller, request.to_pet.seller)
            dialog.save()
    
    return JsonResponse({'status': 'success'})

@login_required
@require_POST
def cancel_mating_request(request):
    """Cancel mating request"""
    mating_request = get_object_or_404(
        MatingRequest,
        pk=request.POST.get('request'),
        from_pet__seller=request.user,
        status='pending'
    )
    
    mating_request.status = 'canceled'
    mating_request.save()
    
    return JsonResponse({'status': 'success'}) 