#!/bin/bash
# docker/entrypoint.sh

set -e

echo "========================================="
echo "  Инициализация базы данных блога"
echo "========================================="

cd /app/blog_project

wait_for_db() {
    echo "Ожидание готовности PostgreSQL..."
    while ! nc -z db 5432; do
        sleep 1
    done
    echo "PostgreSQL готов!"
}

run_migrations() {
    echo "Выполнение миграций..."
    python manage.py makemigrations blog
    python manage.py migrate
    echo "Миграции выполнены успешно!"
}

load_fixtures() {
    echo "Загрузка фикстур..."
    
    if [ -f "blog/fixtures/initial_data.json" ]; then
        python manage.py loaddata blog/fixtures/initial_data.json
        echo "Фикстуры загружены успешно!"
    else
        echo "ВНИМАНИЕ: Фикстуры не найдены"
        return 1
    fi
}

set_passwords() {
    echo "Установка паролей пользователей..."
    python manage.py shell << END
from django.contrib.auth.models import User

users_passwords = {
    'admin': 'admin123',
    'moderator': 'moderator123',
    'kirill': 'user123',
    'lera': 'user123',
}

for username, password in users_passwords.items():
    try:
        user = User.objects.get(username=username)
        user.set_password(password)
        user.save()
        print(f'Пароль для {username} установлен')
    except User.DoesNotExist:
        print(f'Пользователь {username} не найден')
END
}

init_roles() {
    echo "Инициализация ролей..."
    python manage.py init_roles
}

main() {
    wait_for_db
    run_migrations
    load_fixtures
    set_passwords
    init_roles
    
    echo ""
    echo "========================================="
    echo "  Инициализация завершена успешно!"
    echo "========================================="
    echo ""
    echo "Данные для входа:"
    echo "  admin / admin123 (администратор)"
    echo "  moderator / moderator123 (модератор)"
    echo "  kirill / user123 (пользователь)"
    echo "  lera / user123 (пользователь)"
    echo ""
}

main

exit 0