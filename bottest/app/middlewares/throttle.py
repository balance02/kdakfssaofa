import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from app.services import i18n

WINDOW = 2.0
NOTICE_EVERY = 10.0


class ThrottleMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self.last: dict[int, float] = {}
        self.notified: dict[int, float] = {}

    async def __call__(self, handler: Callable[[TelegramObject, dict], Awaitable[Any]],
                       event: TelegramObject, data: dict) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)
        if event.text and event.text.startswith("/"):
            return await handler(event, data)
        uid = data["event_from_user"].id
        now = time.monotonic()
        if now - self.last.get(uid, 0) < WINDOW:
            if now - self.notified.get(uid, 0) > NOTICE_EVERY:
                self.notified[uid] = now
                await event.answer(i18n.t(data.get("lang", "ru"), "throttle"))
            return None
        self.last[uid] = now
        return await handler(event, data)