from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from functools import wraps
from django.shortcuts import get_object_or_404
from .models import Post

def role_required(allowed_roles):
    """
    Декоратор для проверки роли пользователя
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            try:
                profile = request.user.profile
            except:
                # Если у пользователя нет профиля, создаем его с ролью 'user'
                from .models import UserProfile
                profile = UserProfile.objects.create(user=request.user)
            
            if profile.role not in allowed_roles:
                raise PermissionDenied("У вас недостаточно прав для выполнения этого действия.")
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def can_edit_post(view_func):
    """
    Декоратор для проверки прав на редактирование поста
    """
    @wraps(view_func)
    def _wrapped_view(request, slug, *args, **kwargs):
        post = get_object_or_404(Post, slug=slug)
        profile = request.user.profile
        
        # Админ может редактировать все
        if profile.is_admin():
            return view_func(request, slug, *args, **kwargs)
        
        # Модератор может редактировать все посты
        if profile.is_moderator():
            return view_func(request, slug, *args, **kwargs)
        
        # Пользователь может редактировать только свои посты
        if post.author == request.user:
            return view_func(request, slug, *args, **kwargs)
        
        raise PermissionDenied("У вас нет прав на редактирование этого поста.")
    
    return _wrapped_view

def can_delete_post(view_func):
    """
    Декоратор для проверки прав на удаление поста
    """
    @wraps(view_func)
    def _wrapped_view(request, slug, *args, **kwargs):
        post = get_object_or_404(Post, slug=slug)
        profile = request.user.profile
        
        # Админ может удалять все
        if profile.is_admin():
            return view_func(request, slug, *args, **kwargs)
        
        # Модератор и пользователь могут удалять только свои посты
        if post.author == request.user:
            return view_func(request, slug, *args, **kwargs)
        
        raise PermissionDenied("У вас нет прав на удаление этого поста.")
    
    return _wrapped_view
