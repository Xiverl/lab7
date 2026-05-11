from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from blog.models import UserProfile

class Command(BaseCommand):
    help = 'Инициализация ролей пользователей'

    def handle(self, *args, **kwargs):
        # Назначаем роль admin всем суперпользователям
        for user in User.objects.filter(is_superuser=True):
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.role = 'admin'
            profile.save()
            self.stdout.write(f'User {user.username} is now admin')
        
        # Назначаем роль user всем остальным пользователям без профиля
        for user in User.objects.filter(profile__isnull=True):
            UserProfile.objects.create(user=user, role='user')
            self.stdout.write(f'Created profile for {user.username} as user')
