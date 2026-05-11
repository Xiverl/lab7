from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('user', 'Пользователь'),
        ('moderator', 'Модератор'),
        ('admin', 'Администратор'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user', verbose_name='Роль')
    bio = models.TextField(max_length=500, blank=True, verbose_name='О себе')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='Аватар')
    
    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'
    
    def __str__(self):
        return f'{self.user.username} - {self.get_role_display()}'
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_moderator(self):
        return self.role == 'moderator'
    
    def is_user(self):
        return self.role == 'user'

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='Название')
    slug = models.SlugField(max_length=50, unique=True, blank=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Post(models.Model):
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='blog_posts',
        verbose_name='Автор'
    )
    content = models.TextField(verbose_name='Содержание')
    created_date = models.DateTimeField(
        default=timezone.now, 
        verbose_name='Дата создания'
    )
    published_date = models.DateTimeField(
        blank=True, 
        null=True, 
        verbose_name='Дата публикации'
    )
    updated_date = models.DateTimeField(
        auto_now=True, 
        verbose_name='Дата обновления'
    )
    tags = models.ManyToManyField(
        Tag, 
        related_name='posts', 
        blank=True,
        verbose_name='Теги'
    )
    image = models.ImageField(
        upload_to='post_images/', 
        blank=True, 
        null=True,
        verbose_name='Изображение'
    )
    is_published = models.BooleanField(
        default=False, 
        verbose_name='Опубликовано'
    )

    class Meta:
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'
        ordering = ['-published_date', '-created_date']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Проверяем уникальность slug
        original_slug = self.slug
        counter = 1
        while Post.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
            self.slug = f"{original_slug}-{counter}"
            counter += 1
            
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('post_detail', kwargs={'slug': self.slug})

    def publish(self):
        self.published_date = timezone.now()
        self.is_published = True
        self.save()

class Comment(models.Model):
    post = models.ForeignKey(
        Post, 
        on_delete=models.CASCADE, 
        related_name='comments'
    )
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='comments'
    )
    content = models.TextField(verbose_name='Комментарий')
    created_date = models.DateTimeField(
        default=timezone.now, 
        verbose_name='Дата создания'
    )
    is_approved = models.BooleanField(
        default=True, 
        verbose_name='Одобрен'
    )

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['created_date']

    def __str__(self):
        return f'Комментарий от {self.author.username} к {self.post.title}'
