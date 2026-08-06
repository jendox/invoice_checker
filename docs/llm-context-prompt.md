# Стартовый промпт для LLM

Скопируйте блок ниже в начало новой сессии с ассистентом, чтобы быстро передать контекст проекта.

---

```
Ты помогаешь с проектом Invoice Checker — внутренний MVP для анализа банковских выписок и учёта инвойсов (Python/FastAPI).

## Что делает проект
- Загружает CSV/XLS/XLSX выписки (Amex, HSBC, Revolut, PayPal, Barclays и др.)
- Парсит транзакции, классифицирует (категория, нужен ли инвойс, провайдер, invoice_owner)
- Web UI (Jinja2): transactions, rules, categories, vendors, invoice-owners, banks, upload, export XLSX
- API: FastAPI + OpenAPI на /docs

## Стек
Python 3.12+, FastAPI, SQLAlchemy 2 async, PostgreSQL, Alembic, Pydantic v2, pandas, uv, ruff, pytest.
Тесты — in-memory SQLite (tests/conftest.py), не требуют PostgreSQL.

## Классификация (app/services/classifier/)
1. MemoryMatcher — по подтверждённым manual-транзакциям (Jaccard + amount + card last4 для owner)
2. RuleEngine — exact/regex/contains, priority, bank/direction filters
3. VendorMatcher — имя/alias в описании
4. MockLLMClassifier — заглушка (returns None)
5. unknown → needs_review

## Ключевые модели
Transaction, StatementFile, Feedback, ClassificationRule, Category, Bank, Company, InvoiceOwner, Vendor.

## Важные файлы
- app/main.py — lifespan seed
- app/services/transaction_service.py — upload, filters, reclassify, delete
- app/routers/web.py, web_reference.py — HTML UI
- app/services/reference_data_backup.py — backup/restore справочников
- data/reference_data.json — снимок ручных справочников (без транзакций)
- Makefile — lint, test, coverage, migrate, backup-data, restore-data

## Команды
make install && make up-develop && make migrate && make restore-data && make runserver
make lint && make test && make coverage
make backup-data / make restore-data

## Правила разработки
- Минимальный diff, не трогать лишнее
- Следовать паттернам: routers → services → models/schemas
- Комментарии только для неочевидного; код на английском
- Тесты для нового поведения; перед финишем: make lint && make test
- Коммиты только по запросу пользователя
- Документация: docs/ (overview, development, roadmap)

## Текущее состояние MVP (июль 2026)
- CRUD справочников + цвета категорий
- Bulk reclassify/delete на /transactions
- Auto-dismiss alerts
- 35 тестов, ~76% coverage app/
- LLM и auth — не реализованы

## Документация в репозитории
Прочитай при необходимости:
- docs/project-overview.md
- docs/development.md
- docs/roadmap.md

Отвечай на языке пользователя. При изменениях кода запускай lint/test сам.
```

---

## Вариант для узкой задачи

Добавьте к промпту одну строку с задачей, например:

```
Задача: добавить фильтр по invoice_owner на странице transactions.
Не ломай существующие bulk actions. Покрой тестом parse/filter логику.
```

## Вариант после сброса БД

```
Нужно поднять чистую БД с сохранёнными справочниками:
make down-v && make up-develop && make migrate && make restore-data
Транзакций нет — memory пустая, это ожидаемо.
```
