# Deribit Price Tracker

Тестовое задание на позицию junior backend разработчика.

Сервис состоит из двух частей:

1. **Клиент для криптобиржи Deribit** — раз в минуту забирает index price для `btc_usd` и `eth_usd` и сохраняет в базу данных: тикер валюты, текущую цену и время в UNIX-формате.
2. **Внешнее API** для обработки сохранённых данных.

## Стек

- **FastAPI** — внешнее API
- **Celery + Redis** — периодический запуск задачи сбора цен (beat + worker)
- **PostgreSQL + asyncpg** — база данных
- **SQLAlchemy 2.0 (async)** — ORM
- **aiohttp** — HTTP-клиент для Deribit API
- **Docker + docker-compose** — развёртывание

## API

Все методы — GET, у каждого обязательный query-параметр `ticker`.

| Метод | Путь | Описание |
|---|---|---|
| GET | `/prices/all?ticker=btc_usd` | Получение всех сохранённых данных по валюте |
| GET | `/prices/last?ticker=btc_usd` | Получение последней цены валюты |
| GET | `/prices/date?ticker=btc_usd&date=2026-10-14` | Получение цены валюты с фильтром по дате (UTC) |

Пример ответа (`/prices/last`):

```json
{
  "ticker": "btc_usd",
  "current_price": 114523.4,
  "time": 1760918400
}
```

Интерактивная документация (Swagger UI): http://localhost:8000/docs

## Разворачивание

Требования: Docker и docker-compose.

1. Создайте `.env` на основе примера:

```bash
cp .env.example .env
```

2. Запустите сервисы:

```bash
docker-compose up --build
```

После запуска:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- PostgreSQL: `localhost:5432`, Redis: `localhost:6379`

### Запуск без Docker (локальная разработка)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Требуются запущенные PostgreSQL и Redis (параметры — в .env)
uvicorn app.main:app --reload                          # API
celery -A app.core.celery_app worker --loglevel=info   # воркер
celery -A app.core.celery_app beat --loglevel=info     # планировщик
```

## Переменные окружения

| Переменная | Описание | Пример |
|---|---|---|
| `DB_NAME` | Имя базы данных | `deribit` |
| `DB_USER` | Пользователь PostgreSQL | `postgres` |
| `DB_PASSWORD` | Пароль PostgreSQL | `postgres` |
| `DB_HOST` | Хост PostgreSQL | `db` (в docker-compose) |
| `DB_PORT` | Порт PostgreSQL | `5432` |
| `REDIS_URL` | URL брокера Celery | `redis://redis:6379/0` |
| `DERIBIT_API_URL` | URL метода `get_index_price` Deribit | `https://test.deribit.com/api/v2/public/get_index_price?index_name=` |

## Design

### Общая схема

```
                        ┌────────────┐   каждую минуту   ┌──────────────────┐
                        │ Celery beat│ ────────────────► │ Celery worker    │
                        └────────────┘                   │ (fetch_prices)   │
                                                         └──────┬───────────┘
                              сохраняет в PostgreSQL          │ aiohttp
                                (тикер, цена, UNIX-время)     ▼
                                                         ┌────────────┐
                                                         │ Deribit API│
                                                         └────────────┘

 ┌──────────┐   GET /prices/*    ┌─────────┐   SQL    ┌────────────┐
 │ Клиент   │ ─────────────────► │ FastAPI │ ───────► │ PostgreSQL │
 └──────────┘                    └─────────┘          └────────────┘
```

### Структура проекта

```
app/
├── api/            # FastAPI-роутеры (эндпоинты /prices/*)
├── core/           # Настройки (pydantic-settings) и конфигурация Celery
├── db/             # Подключение к БД, DeclarativeBase, модели
├── repositories/   # Слой доступа к данным (PriceRepository)
├── schemas/        # Pydantic-схемы ответов API
├── services/       # Клиент к API Deribit (DeribitClient)
└── tasks/          # Celery-задача сбора цен
```

### Принятые решения

**Слои и чистая архитектура.** Код разделён на слои с однонаправленными
зависимостями: роутеры не работают с БД напрямую, а обращаются к репозиторию;
логика работы с внешним API вынесена в отдельный сервис. Благодаря этому
каждый слой можно тестировать и менять независимо (например, заменить
PostgreSQL на другую БД, затронув только `db/` и `repositories/`).

**ООП.** Логика доступа к данным инкапсулирована в классе `PriceRepository`,
работа с Deribit — в классе `DeribitClient`. Состояние (сессия БД, base URL)
передаётся через конструктор (внедрение зависимостей), глобальных переменных
нет — только настройки (`settings`) как единая точка конфигурации.

**Периодический сбор цен — Celery beat.** Задача `fetch_prices` запускается
beat-планировщиком раз в минуту (`beat_schedule` в `app/core/celery_app.py`).
Beat и worker разнесены по отдельным контейнерам: один планирует, другой
выполняет. Брокер и результат — Redis.

**Async стек.** Сбор цен и API — это I/O-bound задачи, поэтому везде
используется асинхронность: `aiohttp` для запросов к Deribit, `asyncpg` +
`AsyncSession` SQLAlchemy для БД, `async`/`await` в роутерах. Одно соединение
с БД обслуживает много запросов без блокировок.

**Модель данных.** Таблица `price_record`: `id` (PK), `ticker` (с индексом —
все запросы фильтруют по нему), `current_price`, `time` (UNIX-timestamp,
целое число). Фильтр по дате реализован как диапазон UNIX-timestamps
(начало и конец дня в UTC), что позволяет использовать индекс и не делать
преобразования на уровне БД.

**Создание таблиц.** Используется `Base.metadata.create_all` на старте
приложения (lifespan) — достаточно для тестового задания. Для продакшена
заменил бы на Alembic-миграции.

**Конфигурация.** Все параметры — через переменные окружения, валидация
и значения по умолчанию — в `app/core/config.py` на pydantic-settings.
Секреты не коммитятся (`.env` в `.gitignore`, в репозитории только
`.env.example`).
