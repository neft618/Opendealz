# Opendealz

Маркетплейс заказов с FastAPI backend, React frontend и Nginx.

## Быстрый старт (Docker)

```bash
docker compose build --no-cache
docker compose up
```

После старта:
- фронт: http://localhost
- API health: http://localhost/health
- API docs: http://localhost/docs

> `backend/.env` и `frontend/.env` необязательны.  
> Если их нет, используются `backend/.env.example` и `frontend/.env.example`.

## Локальные env-файлы (опционально)

Если хотите свои настройки:

```bash
cp ./backend/.env.example ./backend/.env
cp ./frontend/.env.example ./frontend/.env
```

`SECRET_KEY` при Docker-запуске генерируется автоматически, если не задан вручную.  
Для продакшена обязательно задайте `SECRET_KEY` и `POSTGRES_PASSWORD` через `backend/.env`.

## Как проверить, что все поднялось

1. Откройте http://localhost  
2. Зарегистрируйте аккаунт на `/register`  
3. После логина откроется `/orders`  
4. Кнопка **Post Order** доступна в роли `customer`

## Тестовые данные (для ручной проверки UI)

Создание заказа:
- **Title**: `Landing page redesign`
- **Description**: `Need redesign of landing page with mobile-first layout and React implementation`
- **Budget**: `1200`
- **Deadline**: выберите дату в будущем

Что открыть после создания:
- список заказов: `/orders`
- карточка заказа: `/orders/<order_id>`
- контракт (после принятия заявки): `/contracts/<contract_id>`
- конструктор контракта: `/contracts/<contract_id>/build`

## Полезные команды

Остановить контейнеры:

```bash
docker compose down
```

Пересобрать и запустить:

```bash
docker compose up --build
```
