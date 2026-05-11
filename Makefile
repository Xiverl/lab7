# Makefile
.PHONY: help build up down restart logs init shell dumpdata loaddata clean

help: ## Показать справку
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Сборка образов
	docker compose build

up: ## Запуск проекта
	docker compose up -d

down: ## Остановка проекта
	docker compose down

restart: ## Перезапуск проекта
	docker compose restart

logs: ## Просмотр логов веб-приложения
	docker compose logs -f web

logs-db: ## Просмотр логов БД
	docker compose logs -f db

init: ## Инициализация базы данных (миграции, роли, фикстуры)
	docker compose --profile init run --rm init

shell: ## Django shell в контейнере
	docker compose exec web python manage.py shell

createsuperuser: ## Создание суперпользователя вручную
	docker compose exec web python manage.py createsuperuser

dumpdata: ## Создать дамп данных в fixtures
	docker compose exec web python manage.py dumpdata blog --indent 2 > blog_project/blog/fixtures/initial_data.json

loaddata: ## Загрузить фикстуры
	docker compose exec web python manage.py loaddata blog_project/blog/fixtures/initial_data.json

init-roles: ## Инициализация ролей
	docker compose exec web python manage.py init_roles

clean: ## Полная очистка
	docker compose down -v
	docker system prune -f

clean-db: ## Очистить только БД
	docker compose down
	docker volume rm blog_postgres_data