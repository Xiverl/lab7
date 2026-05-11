from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from .models import Post, Comment, Tag, UserProfile
from .forms import UserRegisterForm, PostForm, CommentForm, UserProfileForm
from .decorators import role_required, can_edit_post, can_delete_post

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Создаем профиль для нового пользователя
            UserProfile.objects.create(user=user, role='user')
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('post_list')
    else:
        form = UserRegisterForm()
    return render(request, 'registration/register.html', {'form': form})

def post_list(request):
    posts = Post.objects.filter(is_published=True, published_date__lte=timezone.now())
    
    # Поиск
    query = request.GET.get('q')
    if query:
        posts = posts.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct()
    
    # Фильтрация по тегам
    tag_slug = request.GET.get('tag')
    if tag_slug:
        posts = posts.filter(tags__slug=tag_slug)
    
    # Пагинация
    paginator = Paginator(posts, 6)
    page_number = request.GET.get('page')
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    tags = Tag.objects.all()
    
    context = {
        'page_obj': page_obj,
        'tags': tags,
        'current_tag': tag_slug,
        'query': query,
    }
    return render(request, 'blog/post_list.html', context)

def post_detail(request, slug):
    # Ищем пост
    post = get_object_or_404(Post, slug=slug)
    
    # Если пост не опубликован, проверяем права доступа
    if not post.is_published:
        if not request.user.is_authenticated:
            raise PermissionDenied("Этот пост не опубликован.")
        
        try:
            profile = request.user.profile
            if not (profile.is_admin() or profile.is_moderator() or post.author == request.user):
                raise PermissionDenied("У вас нет доступа к этому черновику.")
        except UserProfile.DoesNotExist:
            if post.author != request.user:
                raise PermissionDenied("У вас нет доступа к этому черновику.")
    
    comments = post.comments.filter(is_approved=True)
    
    # Проверяем права на редактирование/удаление
    can_edit = False
    can_delete = False
    user_role = None
    
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
            user_role = profile.role
            
            # Админ может всё
            if profile.is_admin():
                can_edit = True
                can_delete = True
                print(f"User {request.user.username} is ADMIN - can_edit: {can_edit}, can_delete: {can_delete}")
            
            # Модератор может редактировать всё, удалять только своё
            elif profile.is_moderator():
                can_edit = True
                can_delete = (post.author == request.user)
                print(f"User {request.user.username} is MODERATOR - can_edit: {can_edit}, can_delete: {can_delete}")
            
            # Обычный пользователь может управлять только своими постами
            elif profile.is_user():
                can_edit = (post.author == request.user)
                can_delete = (post.author == request.user)
                print(f"User {request.user.username} is USER - can_edit: {can_edit}, can_delete: {can_delete}")
                
        except UserProfile.DoesNotExist:
            # Если профиль не существует, создаем его
            UserProfile.objects.create(user=request.user)
            user_role = 'user'
            if post.author == request.user:
                can_edit = True
                can_delete = True
            print(f"User {request.user.username} has NO PROFILE - created new one")
    
    # Отладочный вывод
    print(f"Final permissions - can_edit: {can_edit}, can_delete: {can_delete}, user_role: {user_role}")
    print(f"Post author: {post.author.username}, Current user: {request.user.username}")
    
    if request.method == 'POST' and request.user.is_authenticated:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            messages.success(request, 'Комментарий добавлен!')
            return redirect('post_detail', slug=post.slug)
    else:
        comment_form = CommentForm()
    
    context = {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'can_edit': can_edit,
        'can_delete': can_delete,
        'user_role': user_role,
    }
    return render(request, 'blog/post_detail.html', context)

@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(author=request.user)
            if post.is_published:
                post.publish()
                messages.success(request, 'Пост успешно создан и опубликован!')
                return redirect('post_detail', slug=post.slug)
            else:
                messages.success(request, 'Пост сохранен как черновик. Вы можете опубликовать его позже.')
                return redirect('post_update', slug=post.slug)
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = PostForm()
    
    return render(request, 'blog/post_create.html', {'form': form})

@login_required
@can_edit_post
def post_update(request, slug):
    post = get_object_or_404(Post, slug=slug)
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save(author=request.user if post.author == request.user else post.author)
            if post.is_published and not post.published_date:
                post.publish()
            messages.success(request, 'Пост успешно обновлен!')
            return redirect('post_detail', slug=post.slug)
    else:
        # Заполняем поле тегов
        initial_tags = ', '.join([tag.name for tag in post.tags.all()])
        form = PostForm(instance=post, initial={'tags': initial_tags})
    
    return render(request, 'blog/post_create.html', {'form': form, 'post': post})

@login_required
@can_delete_post
def post_delete(request, slug):
    post = get_object_or_404(Post, slug=slug)
    
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Пост успешно удален!')
        return redirect('post_list')
    
    return render(request, 'blog/post_confirm_delete.html', {'post': post})

@login_required
def my_posts(request):
    posts = Post.objects.filter(author=request.user).order_by('-created_date')
    
    # Пагинация для своих постов
    paginator = Paginator(posts, 6)
    page_number = request.GET.get('page')
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    context = {
        'page_obj': page_obj,
        'is_my_posts': True,
    }
    return render(request, 'blog/my_posts.html', context)

@login_required
def profile(request):
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)
    
    # Получаем статистику
    posts_count = Post.objects.filter(author=request.user).count()
    comments_count = Comment.objects.filter(author=request.user).count()
    
    context = {
        'form': form,
        'profile': profile,
        'posts_count': posts_count,
        'comments_count': comments_count,
    }
    return render(request, 'blog/profile.html', context)

@login_required
@role_required(['admin'])
def user_management(request):
    """Управление пользователями (только для админов)"""
    users = User.objects.all().select_related('profile')
    
    context = {
        'users': users,
    }
    return render(request, 'blog/user_management.html', context)

@login_required
@role_required(['admin'])
def change_user_role(request, user_id):
    """Изменение роли пользователя (только для админов)"""
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        new_role = request.POST.get('role')
        
        if new_role in dict(UserProfile.ROLE_CHOICES):
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.role = new_role
            profile.save()
            messages.success(request, f'Роль пользователя {user.username} изменена на {profile.get_role_display()}')
        else:
            messages.error(request, 'Некорректная роль')
    
    return redirect('user_management')
