UV ?= uv

# Ruff
lint: ## Проверяет линтерами код в репозитории
	$(UV) run ruff check .

fix: ## Запуск автоформатера
	$(UV) run ruff check --fix .

# Docker / PostgreSQL
up-develop: ## Запустить окружение (PostgreSQL)
	$(UV) run docker compose up -d

down-develop: ## Остановить окружение
	$(UV) run docker compose down

down-v: ## Остановить окружение с очисткой хранилищ
	$(UV) run docker compose down -v

# Alembic
makemigrations: ## Сделать миграции (MSG=описание, по умолчанию auto)
	$(UV) run alembic revision --autogenerate -m "$(or $(MSG),auto)"

migrate: ## Применить миграции
	$(UV) run alembic upgrade head

# App
runserver: ## Запустить FastAPI (http://localhost:8000)
	$(UV) run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

test: ## Запустить тесты
	$(UV) run pytest -v

coverage: ## Тесты с отчётом покрытия app/
	$(UV) run pytest --cov=app --cov-report=term-missing -q

import-statements: ## Импортировать выписки из statements
	$(UV) run python scripts/import_statements.py $(MONTH)

backup-data: ## Выгрузить справочники в data/reference_data.json (FILE=...)
	$(UV) run python scripts/reference_data.py export --file $(or $(FILE),data/reference_data.json)

restore-data: ## Загрузить справочники из data/reference_data.json (FILE=...)
	$(UV) run python scripts/reference_data.py restore --file $(or $(FILE),data/reference_data.json)

install: ## Установить зависимости (dev)
	$(UV) sync --extra dev

list: ## Отображает список доступных команд и их описания
	@echo "Cписок доступных команд:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
