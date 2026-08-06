# Текущее состояние и планы

*Актуально: июль 2026, версия 0.1.0 (MVP)*

## Что уже работает

### Ядро

- [x] Парсинг выписок 9+ банковых пресетов (CSV/XLS/XLSX)
- [x] Дедупликация транзакций по fingerprint
- [x] Пайплайн классификации: memory → rules → vendors → LLM stub → unknown
- [x] Ручная правка классификации + feedback
- [x] Экспорт «нужен инвойс» в XLSX
- [x] Bulk reclassify по текущим фильтрам (skip manual, опция skip memory)
- [x] Bulk delete транзакций по фильтрам

### Справочники (CRUD в UI)

- [x] Categories — slug, label, sort, requires_invoice_default, **цвета badge**
- [x] Banks, Companies
- [x] Invoice Owners
- [x] Vendors (aliases, default category/provider/owner)
- [x] Classification Rules

### UI/UX

- [x] Web UI: dashboard, upload, transactions, rules, справочники
- [x] Фильтры транзакций (банк, месяц, даты, категория, статус, поиск…)
- [x] Модалки подтверждения bulk delete/reclassify
- [x] Auto-dismiss success alerts (~4 сек)
- [x] Truncate + tooltip для длинных колонок

### Инфраструктура

- [x] Docker PostgreSQL, Alembic (3 миграции)
- [x] Makefile (lint, test, coverage, backup/restore)
- [x] **35 тестов**, покрытие `app/` ~**76%**
- [x] Бэкап справочников: `data/reference_data.json` (17 categories, 10 vendors, 7 owners, 29 rules, …)

### Что сознательно не в scope MVP

- Реальная LLM-классификация (интерфейс готов, `MockLLMClassifier`)
- Аутентификация / multi-tenant
- CI/CD pipeline
- Отдельная таблица memory (сейчас — derived from transactions)

## Известные ограничения

- Memory работает только после накопления подтверждённых ручных транзакций.
- `company_name` в фильтрах — из distinct по statement files, не жёсткий FK.
- Bank list в фильтрах — distinct из transactions + справочник banks.
- Покрытие web-роутеров низкое — регрессии UI ловятся в основном вручную.
- Seed rules/categories при первом старте может частично пересечься с restore-data (restore безопасен после migrate).

## Ближайшие направления (приоритет)

### 1. Операционная работа с транзакциями

- [ ] Массовый импорт выписок за период (скрипт `import-statements` уже есть)
- [ ] Dashboard со статистикой: needs_review, pending invoices, по компаниям
- [ ] Улучшение UX review-потока (быстрое подтверждение, hotkeys)

### 2. Качество классификации

- [ ] Интеграция реального LLM (OpenAI / local) в `LLMClassifier`
- [ ] Предложение «создать vendor/rule» из транзакции one-click
- [ ] Метрики качества: % auto-classified, % manual override

### 3. Тесты и CI

- [ ] HTTP-тесты web-роутов (transactions filters, bulk actions)
- [ ] GitHub Actions / pre-commit: `make lint && make test`
- [ ] Порог покрытия (например ≥80% для services)

### 4. Справочники и данные

- [ ] Расширение vendor matching (fuzzy / normalized aliases)
- [ ] Версионирование `reference_data.json` или несколько профилей
- [ ] Экспорт/импорт rules отдельно от остальных справочников

### 5. Продуктовые фичи

- [ ] Связь транзакция ↔ загруженный инвойс (файл/ссылка)
- [ ] Напоминания / отчёт «просроченные инвойсы»
- [ ] Multi-currency отчёты

## Долгосрочно

- Auth (OAuth / basic) для команды
- Audit log изменений справочников
- API versioning
- Отдельный frontend (если UI outgrow Jinja)

## Как обновлять этот документ

После значимых фич:

1. Отметить пункт в «Что уже работает».
2. Обновить цифры тестов/покрытия (`make coverage`).
3. Сдвинуть приоритеты в «Ближайшие направления».
