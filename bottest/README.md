# Uncensored AI Bot

Telegram-бот с подпиской в USDT. Python 3.12, aiogram 3, FastAPI, PostgreSQL.

## Запуск

1. VPS Ubuntu 24.04, домен `bot.<domain>` с A-записью на IP, Cloudflare proxy выключен.
2. `apt install docker.io docker-compose-plugin`, `ufw allow 22,80,443`.
3. `git clone` в `/opt/uncensored-ai`, `cp .env.example .env`, заполнить.
4. В Caddyfile вписать домен.
5. `docker compose up -d --build`.
6. В @CryptoBot: создать приложение, включить webhook на `https://bot.<domain>/crypto/webhook`.
7. В @BotFather: `setWebhook` не нужен, ставится автоматически при старте.
8. Проверить `/healthz`, затем `/start` в боте.
9. Cron: `cp deploy/cronexpr /etc/cron.d/uncensored-ai`.

## Переменные

`ADMIN_IDS` — числовые ID через запятую (узнать в @userinfobot).
`TRIAL_PRICE_USD=0` — тариф на 7 дней выключен.
`AUTO_CREATE_SCHEMA=false` после первого запуска, дальше `alembic revision --autogenerate`.

## Экономика

Дефолт — `olafangensan-glm-4.7-flash-heretic` ($0.07/$0.40 за 1M). Тяжёлые модели ограничены
60 сообщениями в сутки на пользователя, дальше авто-даунгрейд.