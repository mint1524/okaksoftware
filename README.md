# OKAK Software Platform

Комплекс из Telegram-бота, backend API и React-сайта для выдачи цифровых товаров с оплатой через YooMoney.

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
- Админ-панель: `http://localhost:4174` (в продакшене через `shop.kcbot.ru`)
- Телеграм-бот запускается автоматически (long polling).

## Деплой на сервер (Ubuntu 22.04 пример)

```bash
sudo apt update
sudo apt install -y git curl docker.io docker-compose-plugin postgresql postgresql-contrib
sudo usermod -aG docker $USER
newgrp docker

# если на сервере уже запущен nginx/apache, освободите порт 80
sudo systemctl stop nginx || true
sudo systemctl disable nginx || true

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

# сборка и запуск (nginx стартует в http-режиме, пока нет сертификатов)
docker compose build
docker compose run --rm migrate
docker compose up -d

# первичная выдача сертификатов Let's Encrypt (nginx уже слушает 80 порт)
docker compose run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  -d gpt.kcbot.ru -d vpn.kcbot.ru -d shop.kcbot.ru \
  --agree-tos -m admin@kcbot.ru --no-eff-email

# переключаем nginx в https-режим
docker compose restart nginx

# пример cron-задачи для автообновления сертификатов
# 0 5 * * * cd /opt/okak && docker compose run --rm certbot renew --webroot -w /var/www/certbot \\
#   && docker compose exec nginx nginx -s reload
```

## Настройка VPN файлов

- Положите конфигурации/архивы в `infra/static/vpn/`. Пример структуры:
  ```
  infra/static/vpn/
    windows/openvpn.exe
    macos/client.dmg
    android/app.apk
  ```
- В БД (таблица `file_assets`) создайте записи для каждого файла (`product_type = 'vpn'`, `path = windows/openvpn.exe` и т.д.). В `metadata` токена фронтенд автоматически сформирует прямые ссылки `https://vpn.kcbot.ru/static/vpn/...`.

## Админ-панель (shop.kcbot.ru)

- Домен `shop.kcbot.ru` проксируется на отдельный React-приложение (`admin/`).
- Аутентификация по паролю, JWT хранится в localStorage. Сбросить пароль можно только вручную: сгенерируйте новый хэш и обновите `.env`.
  ```bash
  docker compose run --rm backend python -m app.scripts.hash_admin_password
  ```
  Скрипт выводит исходный хэш и строку с экранированными `$` (для `.env` в docker compose используйте вариант с `$$`). После обновления `.env` перезапустите бэкенд.
- Остальные переменные:
  - `OKAK_ADMIN_JWT_SECRET` — секрет для подписания админских токенов (замените на случайный).
  - `OKAK_ADMIN_TOKEN_EXPIRE_MINUTES` — время жизни токена (по умолчанию 60 минут).
- В админке доступны:
  - управление товарами и тарифами (CRUD, JSON metadata);
  - список покупок с фильтрами по статусу и типу товара;
  - управление файлами VPN (привязка к `file_assets`).
- API админки: `/api/admin/panel/*`. Для интеграции используйте Bearer-токен, полученный на `/api/admin/panel/auth/login`.

## Каталог и тарифы

1. Создайте записи в `products` (`type = 'gpt'` или `vpn'`, `metadata` можно использовать для инструкций).
2. Добавьте варианты (`product_variants`) с основной информацией (цена, валюта). При необходимости можно указать статичную ссылку на оплату (`payment_url`) — тогда YooMoney не будет задействован.
3. Настройте YooMoney webhook на `https://<backend-domain>/api/admin/payments/yoomoney/webhook` и передавайте секрет из `.env` (`OKAK_YOOMONEY_WEBHOOK_SECRET`).

## Потоки

- Покупатель в боте выбирает товар → бот вызывает `/api/purchases`, получает `payment_url` и отправляет покупателю.
- YooMoney оповещает webhook → backend генерирует `token`, сохраняет ссылку и отправляет в ответе `token_url`.
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
- `POST /api/admin/payments/yoomoney/webhook` — вход событий YooMoney
- `GET /api/tokens/{token}` — данные токена для фронтенда
- `GET /api/users/{telegram_id}/purchases` — покупки пользователя

## Тестовый сценарий без YooMoney

1. Создайте товар и тариф вручную в БД, оставьте `payment_url` пустым, чтобы задействовать YooMoney (или укажите тестовую ссылку, если хотите обойти YooMoney).
2. В боте выберите товар → получите ссылку на оплату.
3. Для эмуляции вебхука выполните:
   ```bash
   curl -X POST http://localhost:8000/api/admin/payments/yoomoney/webhook \
     -H 'Content-Type: application/json' \
     -d '{"event":"payment.succeeded","object":{"id":"test-payment","metadata":{"purchase_id":1}}}'
   ```
4. После подтверждения токен появится в разделе «Мои покупки».

## Дополнительно

- Планировщик (APScheduler) каждые час помечает просроченные токены и удаляет их.
- Для интеграции с plati.market предусмотрено поле `metadata` и расширяемая структура — добавляйте адаптеры в `backend/app/services/` при необходимости.
