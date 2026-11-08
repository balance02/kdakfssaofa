from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.config import get_settings
from app.keyboards.inline import paywall
from app.services import access, i18n

EXEMPT_COMMANDS = {"start", "buy", "sub", "help", "lang", "admin", "cancel"}
EXEMPT_CALLBACKS = ("buy:", "pay:", "consent", "inside", "lang:", "check_subs", "nav:", "mode:")


class AccessMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[[TelegramObject, dict], Awaitable[Any]],
                       event: TelegramObject, data: dict) -> Any:
        data.setdefault("gate", None)
        user, session = data.get("user"), data.get("session")
        if user is None or user.banned:
            return None
        if isinstance(event, Message) and event.text and event.text.startswith("/"):
            if event.text[1:].split()[0].split("@")[0] in EXEMPT_COMMANDS:
                return await handler(event, data)
        if isinstance(event, CallbackQuery) and event.data and event.data.startswith(EXEMPT_CALLBACKS):
            return await handler(event, data)

        if get_settings().has_channel and not user.subscribed:
            data["gate"] = "channels"
            return await handler(event, data)

        if await access.is_pro(session, user.id):
            return await handler(event, data)
        if user.free_used < get_settings().free_messages:
            data["gate"] = "free"
            return await handler(event, data)

        data["gate"] = "paywall"
        text = i18n.t(data["lang"], "paywall.text", price=int(get_settings().pro_price_usd))
        kb = paywall(data["lang"], get_settings().trial_price_usd)
        if isinstance(event, Message):
            await event.answer(text, reply_markup=kb)
        elif isinstance(event, CallbackQuery):
            await event.message.answer(text, reply_markup=kb)
        return None