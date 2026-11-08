import asyncio
import contextlib
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, Update
from fastapi import FastAPI, Header, HTTPException, Request
from sqlalchemy import text

from app.config import get_settings
from app.db.models import Base
from app.db.session import SessionMaker, engine
from app.handlers.webhook import handle_update
from app.middlewares.access import AccessMiddleware
from app.middlewares.throttle import ThrottleMiddleware
from app.middlewares.user import UserMiddleware
from app.routers import build
from app.services import crypto

logging.basicConfig(level=get_settings().log_level,
                    format='{"lvl":"%(levelname)s","mod":"%(name)s","msg":"%(message)s"}')
log = logging.getLogger(__name__)
settings = get_settings()

bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
dp.message.middleware(UserMiddleware())
dp.message.middleware(ThrottleMiddleware())
dp.message.middleware(AccessMiddleware())
dp.callback_query.middleware(UserMiddleware())
dp.callback_query.middleware(AccessMiddleware())
dp.include_router(build())

app = FastAPI(docs_url=None, redoc_url=None)

RU_COMMANDS = [
    BotCommand(command="start", description="Запустить бота/вернуться в главное меню"),
    BotCommand(command="plans", description="Купить подписку"),
    BotCommand(command="clear_context", description="Очистить историю запросов"),
]
EN_COMMANDS = [
    BotCommand(command="start", description="Start the bot / back to main menu"),
    BotCommand(command="plans", description="Buy a subscription"),
    BotCommand(command="clear_context", description="Clear request history"),
]


@app.on_event("startup")
async def on_startup() -> None:
    if settings.auto_create_schema:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    with contextlib.suppress(Exception):
        await bot.set_my_commands(RU_COMMANDS)
        await bot.set_my_commands(EN_COMMANDS, language_code="en")

    if settings.use_polling:
        await bot.delete_webhook(drop_pending_updates=True)
        asyncio.create_task(dp.start_polling(bot, allowed_updates=["message", "callback_query"]))
        log.info("polling started")
    else:
        url = f"{settings.webhook_base_url}/tg/{settings.webhook_path}"
        await bot.set_webhook(url, secret_token=settings.webhook_secret,
                              drop_pending_updates=True,
                              allowed_updates=["message", "callback_query"])
        log.info("webhook set: %s", url)
    asyncio.create_task(poller())


@app.on_event("shutdown")
async def on_shutdown() -> None:
    if not settings.use_polling:
        await bot.delete_webhook()
    await engine.dispose()


@app.get("/healthz")
async def healthz() -> dict:
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return {"ok": True}


@app.post("/tg/{path}")
async def telegram(path: str, request: Request,
                   x_telegram_bot_api_secret_token: str = Header(default="")) -> dict:
    if path != settings.webhook_path or x_telegram_bot_api_secret_token != settings.webhook_secret:
        raise HTTPException(403)
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}


@app.post("/crypto/webhook")
async def crypto_webhook(request: Request, crypto_pay_api_signature: str = Header(default="")) -> dict:
    raw = await request.body()
    if not crypto.verify_signature(raw, crypto_pay_api_signature):
        raise HTTPException(403)
    body = await request.json()
    async with SessionMaker() as session:
        await handle_update(session, body)
    return {"ok": True}


async def poller() -> None:
    from sqlalchemy import select

    from app.db.models import Payment

    while True:
        await asyncio.sleep(120)
        try:
            async with SessionMaker() as session:
                rows = (await session.scalars(select(Payment).where(Payment.status == "pending"))).all()
                for p in rows:
                    inv = await crypto.get_invoice(p.invoice_id)
                    if inv and inv.get("status") == "paid":
                        await handle_update(session, {"update_type": "invoice_paid", "payload": inv})
        except Exception:  # noqa: BLE001
            log.exception("poller")