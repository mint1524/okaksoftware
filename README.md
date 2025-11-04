# OKAK Software Platform

Комплекс из Telegram-бота, backend API и React-сайта для выдачи цифровых товаров через Digiseller.

## Состав

- `backend/` — FastAPI + PostgreSQL + SQLAlchemy + Alembic. Отвечает за каталог товаров, сессии покупок и выдачу токенов.
- `bot/` — Telegram-бот на Aiogram v3. Позволяет просматривать каталог, оформлять покупку и получать ссылки.
- `web/` — React + Vite. Отрисовывает одноразовые страницы по токену (`gpt` и `vpn` сценарии).
- `infra/` — Dockerfile'ы, конфигурация Nginx и статические файлы (VPN конфиги).
- `docker-compose.yml` — единая оркестрация сервисов.

## Быстрый старт (локально)

```bash
cp .env.example .env
# при необходимости отредактируйте значения (бот-токен, креды БД, домены и т.д.)

docker compose build
# применяем схему БД
docker compose run --rm migrate
# запускаем все сервисы
docker compose up -d
```

После запуска:
- Backend: `http://localhost:8000/api`
- React-просмотрщик (через Nginx): `http://localhost/`
- Телеграм-бот запускается автоматически (long polling).

## Деплой на сервер (Ubuntu 22.04 пример)

```bash
sudo apt update
sudo apt install -y git curl docker.io docker-compose-plugin nginx certbot python3-certbot-nginx postgresql postgresql-contrib
sudo usermod -aG docker $USER
newgrp docker

# подготавливаем PostgreSQL
sudo -u postgres psql <<'SQL'
CREATE ROLE okak WITH LOGIN PASSWORD 'change_me';
CREATE DATABASE okak OWNER okak;
GRANT ALL PRIVILEGES ON DATABASE okak TO okak;
SQL

# деплой кода
sudo mkdir -p /opt/okak && sudo chown $USER:$USER /opt/okak
cd /opt/okak
git clone https://github.com/mint1524/okaksoftware.git .
cp .env.example .env
nano .env   # добавьте реальные токены, пароли и домены

# сборка и запуск
docker compose build
docker compose run --rm migrate
docker compose up -d

# настраиваем nginx certbot
sudo cp infra/nginx/nginx.conf /etc/nginx/nginx.conf
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d gpt.kcbot.ru -d vpn.kcbot.ru --agree-tos -m admin@kcbot.ru
```

> **Важно:** После выдачи сертификатов certbot создаст отдельные серверные блоки. Проверьте что proxy-пути `/api/`, `/static/vpn/` и `/` соответствуют конфигурации из репозитория.

## Настройка VPN файлов

- Положите конфигурации/архивы в `infra/static/vpn/`. Пример структуры:
  ```
  infra/static/vpn/
    windows/openvpn.exe
    macos/client.dmg
    android/app.apk
  ```
- В БД (таблица `file_assets`) создайте записи для каждого файла (`product_type = 'vpn'`, `path = windows/openvpn.exe` и т.д.). В `metadata` токена фронтенд автоматически сформирует прямые ссылки `https://vpn.kcbot.ru/static/vpn/...`.

## Каталог и тарифы

1. Создайте записи в `products` (`type = 'gpt'` или `vpn'`, `metadata` можно использовать для инструкций).
2. Добавьте варианты (`product_variants`) с `digiseller_product_id` и/или статичной ссылкой на оплату (`payment_url`).
3. Подключите Digiseller webhook на `https://<backend-domain>/api/admin/digiseller/webhook` и укажите секрет в `.env` (`OKAK_DIGISELLER_SECRET`).

## Потоки

- Покупатель в боте выбирает товар → бот вызывает `/api/purchases`, получает `payment_url` и отправляет покупателю.
- Digiseller оповещает webhook → backend генерирует `token`, сохраняет ссылку и отправляет в ответе `token_url`.
- Бот по запросу пользователя (`Мои покупки`) показывает активные ссылки.
- Клиент переходит по `https://<domain>/<token>` → React приложение запрашивает `/api/tokens/{token}` и визуализирует сценарий (`gpt`, `vpn` и т.д.).
- После нажатия "Товар получен" / подтверждения автоматикой — backend инвалидирует токен.

## Управление миграциями

```bash
# генерация новой миграции
cd backend
alembic revision --autogenerate -m "comment"

# применение
alembic upgrade head
```

(в Docker окружении используйте `docker compose run --rm migrate`).

## Переменные окружения

Основные переменные — в `.env.example`. Обязательные:

- `OKAK_TELEGRAM_BOT_TOKEN`
- `OKAK_DATABASE_URL`
- `OKAK_DIGISELLER_*` (для рабочей интеграции)
- `OKAK_DOMAIN_GPT`, `OKAK_DOMAIN_VPN`
- `VITE_API_BASE_URL` (обычно `/api` для работы за reverse-proxy)

## Полезные эндпоинты

- `GET /api/healthz` — проверка здоровья backend
- `GET /api/products` — каталог
- `POST /api/purchases` — создать сессию покупки
- `POST /api/admin/digiseller/webhook` — вход Digiseller
- `GET /api/tokens/{token}` — данные токена для фронтенда
- `GET /api/users/{telegram_id}/purchases` — покупки пользователя

## Тестовый сценарий без Digiseller

1. Создайте товар и тариф вручную в БД, задайте `payment_url` на любой URL оплаты.
2. В боте выберите товар → получите ссылку на оплату.
3. Вручную вызовите:
   ```bash
   curl -X POST http://localhost:8000/api/admin/digiseller/webhook \
     -H 'Content-Type: application/json' \
     -d '{"order_id": "test-order", "status": "paid"}'
   ```
4. Токен появится в `Мои покупки`, можно переходить на React страницу.

## Дополнительно

- Планировщик (APScheduler) каждые час помечает просроченные токены и удаляет их.
- Для интеграции с plati.market предусмотрено поле `metadata` и расширяемая структура — добавляйте адаптеры в `backend/app/services/` при необходимости.
