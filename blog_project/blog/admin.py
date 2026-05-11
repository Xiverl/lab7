from django.contrib import admin
from .models import Post, Comment, Tag, UserProfile
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Профиль'

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)

# Перерегистрируем User admin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'author', 'is_published', 'published_date', 'created_date']
    list_filter = ['is_published', 'created_date', 'published_date', 'tags']
    search_fields = ['title', 'content', 'slug']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_date'
    inlines = [CommentInline]
    readonly_fields = ['created_date', 'updated_date']
    
    actions = ['make_published']
    
    def make_published(self, request, queryset):
        for post in queryset:
            post.publish()
    make_published.short_description = "Опубликовать выбранные посты"

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['post', 'author', 'created_date', 'is_approved']
    list_filter = ['is_approved', 'created_date']
    search_fields = ['content', 'author__username', 'post__title']
    
    actions = ['approve_comments']
    
    def approve_comments(self, request, queryset):
        queryset.update(is_approved=True)
    approve_comments.short_description = "Одобрить выбранные комментарии"