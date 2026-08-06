# Invoice Checker

Backend MVP для анализа банковских выписок и контроля инвойсов по транзакциям нескольких компаний.

**Документация:** [docs/](docs/README.md) — обзор, разработка, roadmap, LLM-промпт.

## Quick Start

```bash
make install
make up-develop
cp .env.example .env   # при необходимости
make migrate
make restore-data      # опционально: справочники из data/reference_data.json
make runserver         # http://localhost:8000
```

Web UI: http://localhost:8000 · API docs: http://localhost:8000/docs

## Основные команды

```bash
make list              # все команды
make lint && make test # проверка перед коммитом
make coverage          # покрытие app/ (~76%)
make backup-data       # выгрузить справочники
make import-statements MONTH=2026-06
```

## Возможности

- Парсинг выписок (Amex, HSBC, Revolut, PayPal, Barclays, …)
- Классификация: memory → rules → vendors → LLM stub
- CRUD: categories, rules, vendors, invoice owners, banks
- Transactions: фильтры, ручная правка, bulk reclassify/delete
- Export XLSX: транзакции, требующие инвойс

## Структура

```
app/          FastAPI, models, services, routers, templates
alembic/      миграции
data/         reference_data.json (бэкап справочников)
docs/         документация
scripts/      CLI-утилиты
statements/   примеры выписок
tests/        pytest (35 тестов)
```

Подробнее: [docs/project-overview.md](docs/project-overview.md)
