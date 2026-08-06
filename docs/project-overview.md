# Invoice Checker — обзор проекта

## Назначение

**Invoice Checker** — внутренний инструмент для учёта банковских транзакций нескольких компаний (Cubetag, Hipcrate, Doorz) и контроля, по каким операциям нужны инвойсы.

Основной сценарий:

1. Загрузить выписки (CSV/XLS/XLSX) с разных банков.
2. Автоматически распарсить и классифицировать транзакции.
3. Просмотреть, отфильтровать, вручную поправить категорию / провайдера / владельца инвойса.
4. Экспортировать список «нужен инвойс» в XLSX.

Проект на стадии **MVP**: есть рабочий web UI, API, классификатор и справочники; LLM-классификация пока заглушка.

## Стек

| Слой | Технологии |
|------|------------|
| Backend | Python 3.12+, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2 |
| БД | PostgreSQL 16, Alembic |
| UI | Jinja2 + vanilla JS/CSS (без фреймворка) |
| Парсинг | pandas, openpyxl, xlrd |
| Инструменты | uv, ruff, pytest, docker compose |

## Структура репозитория

```
invoice_checker/
├── app/
│   ├── main.py                 # FastAPI, lifespan (seed), роутеры
│   ├── models/                 # SQLAlchemy-модели
│   ├── schemas/                # Pydantic-схемы
│   ├── services/
│   │   ├── parser/             # Парсинг выписок, пресеты банков
│   │   ├── classifier/         # Пайплайн классификации
│   │   ├── transaction_service.py
│   │   ├── export_service.py
│   │   ├── reference_data_backup.py
│   │   └── *_service.py        # CRUD справочников
│   ├── routers/                # API + web-страницы
│   ├── templates/              # Jinja2 HTML
│   └── static/                 # CSS, JS
├── alembic/versions/           # Миграции 001–003
├── data/reference_data.json    # Бэкап справочников (ручные вносы)
├── docs/                       # Документация
├── scripts/                    # CLI: import_statements, reference_data
├── statements/                 # Примеры выписок по компаниям
├── tests/                      # pytest (in-memory SQLite)
├── docker-compose.yml
├── Makefile
└── pyproject.toml
```

## Доменные сущности

### Транзакции (операционные данные)

- **Transaction** — строка выписки: дата, сумма, описание, категория, флаг инвойса, провайдер, владелец инвойса, источник классификации, статус.
- **StatementFile** — загруженный файл выписки.
- **Feedback** — история ручных правок классификации.

### Справочники (настраиваемые данные)

- **Category** — категории с slug, label, цветами badge (`badge_bg` / `badge_text`).
- **Bank**, **Company** — ключи для загрузки и фильтров.
- **InvoiceOwner** — люди, ответственные за получение инвойса.
- **Vendor** — известные контрагенты с дефолтной классификацией и aliases.
- **ClassificationRule** — паттерн-правила (exact / contains / regex).

Memory (обучение) **не хранится отдельно** — строится из подтверждённых транзакций с `classification_source=manual`.

## Пайплайн классификации

```
Описание транзакции
       ↓
1. Memory     — похожие подтверждённые ручные правки (Jaccard + amount/card)
       ↓
2. Rules      — активные правила (exact → regex → contains, priority)
       ↓
3. Vendors    — совпадение имени/alias в описании
       ↓
4. LLM        — MockLLMClassifier (возвращает None)
       ↓
5. Unknown    — status=needs_review
```

Поля результата: `category`, `requires_invoice`, `invoice_provider`, `invoice_owner`, `confidence`, `classification_source`, `status`.

**Invoice owner в memory:** копируется только если однозначно (описание + сумма; при нескольких владельцах — уточнение по last4 карты).

## Web UI (основные страницы)

| URL | Назначение |
|-----|------------|
| `/` | Dashboard |
| `/upload` | Загрузка выписки |
| `/transactions` | Список, фильтры, bulk reclassify/delete, ручная правка |
| `/rules` | CRUD правил |
| `/categories` | CRUD категорий + цвета |
| `/vendors` | CRUD вендоров |
| `/invoice-owners` | CRUD владельцев инвойсов |
| `/banks` | CRUD банков |
| `/exports/invoice-requests.xlsx` | Экспорт |
| `/docs` | OpenAPI |

## API (ключевое)

- `POST /statements/upload` — загрузка и классификация
- `GET /transactions`, `PATCH /transactions/{id}/classification`
- `POST /transactions/reclassify`, `POST /transactions/delete`
- `GET /invoice-requests`, `GET /exports/invoice-requests.xlsx`
- `CRUD /rules`

## Поддерживаемые банки (парсер)

Amex, HSBC, HSBC CSV/Loan, Revolut, Revolut Savings, PayPal, Barclays, Capital on Tap, generic fallback. Детали пресетов — `app/services/parser/bank_presets.py`.

## Бэкап справочников

Ручные вносы (категории, вендоры, правила и т.д.) можно выгрузить/загрузить без транзакций:

```bash
make backup-data    # → data/reference_data.json
make restore-data   # ← из data/reference_data.json
```

Сценарий «чистая БД с вашими справочниками»: `make down-v && make up-develop && make migrate && make restore-data`.
