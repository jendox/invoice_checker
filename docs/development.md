# Руководство разработчика

## Первый запуск

```bash
make install          # uv sync --extra dev
make up-develop       # PostgreSQL в docker
cp .env.example .env  # при необходимости
make migrate
make restore-data     # опционально: загрузить справочники из data/reference_data.json
make runserver        # http://localhost:8000
```

Переменные окружения (`.env`):

- `DATABASE_URL` — async PostgreSQL URL (`postgresql+asyncpg://...`)
- `SECRET_KEY`, `DEBUG`

## Makefile — все команды

```bash
make list             # список команд
```

| Команда | Описание |
|---------|----------|
| `install` | Установка зависимостей (dev) |
| `up-develop` / `down-develop` / `down-v` | Docker PostgreSQL |
| `migrate` / `makemigrations MSG=...` | Alembic |
| `runserver` | FastAPI с reload |
| `lint` | Ruff check |
| `fix` | Ruff auto-fix |
| `test` | pytest -v |
| `coverage` | pytest + отчёт покрытия `app/` |
| `import-statements MONTH=2026-06` | Bulk-импорт из `statements/` |
| `backup-data` / `restore-data` | Экспорт/импорт справочников |

## Линтер (Ruff)

Конфигурация: [ruff.toml](../ruff.toml).

```bash
make lint    # проверка
make fix     # автоисправление (импорты, часть E/W/F)
```

**Включено:** E/W/F (PEP8), isort (I), pyupgrade (UP), bugbear (B), comprehensions (C), pylint-сложность (PL), return (RET), builtins (A).

**Ограничения сложности:**

- max complexity (McCabe): 7
- max args: 6, max branches: 10, max statements: 50

**Исключения per-file:** тесты (`PLR2004`, длинные функции), роутеры web/deps (много query-параметров).

Alembic и `.venv` исключены из проверки.

Перед коммитом: `make lint && make test`.

## Тесты

```bash
make test       # 35 тестов, verbose
make coverage   # с отчётом по строкам
```

**Фреймворк:** pytest + pytest-asyncio (`asyncio_mode = auto`).

**Fixtures** ([tests/conftest.py](../tests/conftest.py)):

- In-memory SQLite (`aiosqlite`) — быстрые unit/integration тесты без PostgreSQL.
- При создании сессии автоматически вызываются `seed_reference_data` и `seed_default_rules`.

**Покрытие (на момент актуализации):** ~**76%** по `app/` (35 тестов).

| Область | Покрытие | Комментарий |
|---------|----------|-------------|
| models, schemas | ~100% | |
| classifier (core) | 79–92% | memory, rules, vendor, normalizer |
| parser | 79–87% | + real files parametrized |
| transaction_service | ~72% | upload, filters, reclassify, delete |
| reference_data_backup | ~96% | export/restore roundtrip |
| routers (web, API) | 45–58% | мало HTTP-тестов UI |
| *_service (CRUD) | 28–52% | частично через integration |

**Файлы тестов:**

| Файл | Что проверяет |
|------|---------------|
| `test_classifier.py` | Amazon, Google, unknown |
| `test_rule_engine.py` | приоритет, bank filter |
| `test_memory / feedback / reference_data` | invoice_owner, feedback |
| `test_reclassify.py` | bulk reclassify, skip manual |
| `test_delete_transactions.py` | bulk delete |
| `test_transaction_filters.py` | даты, пустые фильтры |
| `test_parser_real_files.py` | реальные выписки из `statements/` |
| `test_export.py` | XLSX |
| `test_reference_data_backup.py` | backup/restore |
| `test_normalizer.py`, `test_fingerprint.py` | утилиты |

Целевое направление: поднять покрытие роутеров и CRUD-сервисов HTTP-тестами через `AsyncClient`.

## Миграции

```bash
make makemigrations MSG="add foo"
make migrate
```

Текущие ревизии:

1. `001_initial_schema` — transactions, rules, feedback, vendors
2. `002_reference_tables` — categories, banks, companies, invoice_owners, invoice_owner на transactions
3. `003_category_badge_colors` — badge_bg, badge_text

Seed при старте приложения (`lifespan` в `main.py`) заполняет **только пустые** таблицы categories/banks/companies/rules.

## Правила разработки

### Общие

1. **Минимальный diff** — не рефакторить и не трогать несвязанный код.
2. **Следовать существующим паттернам** — async SQLAlchemy, Pydantic schemas, service layer, Jinja templates.
3. **Комментарии** — только для неочевидной бизнес-логики; код на английском.
4. **Тесты** — добавлять для нового поведения; не писать тривиальные assert-ы.
5. **Миграции** — через Alembic, не править БД вручную.

### Backend

- Роутеры тонкие: валидация → service → response/redirect.
- Web-формы и API делят сервисы (`TransactionService`, `CategoryService`, …).
- Фильтры транзакций — через `TransactionFilters` + `parse_optional_date` (пустая строка = None).
- Классификация только через `TransactionClassifier`; ручные правки → `classification_source=manual`, feedback запись.

### Frontend (Jinja + JS)

- Статика: `app/static/`, общий `ui.js` (модалки, auto-dismiss alerts).
- Макросы: `_macros.html` (`category_badge`).
- Bulk-действия на transactions синхронизируют hidden fields из текущих фильтров через JS.

### Данные

- Справочники пользователя бэкапить: `make backup-data` после значимых правок.
- `data/reference_data.json` — можно хранить в git (без секретов и транзакций).

### Git

- Коммиты только по запросу.
- `.env` не коммитить.

## Отладка

- SQL echo: `DEBUG=true` в `.env`
- API: http://localhost:8000/docs
- Health: `GET /health`
