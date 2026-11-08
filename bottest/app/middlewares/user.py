from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, User as TgUser

from app.db.models import User
from app.db.session import SessionMaker
from app.services.i18n import resolve_lang


class UserMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[[TelegramObject, dict], Awaitable[Any]],
                       event: TelegramObject, data: dict) -> Any:
        tg: TgUser | None = data.get("event_from_user")
        if tg is None:
            return await handler(event, data)
        async with SessionMaker() as session:
            user = await session.get(User, tg.id)
            if user is None:
                user = User(id=tg.id, username=tg.username, first_name=tg.first_name,
                            lang=resolve_lang(tg.language_code))
                session.add(user)
            else:
                user.username, user.first_name = tg.username, tg.first_name
            await session.commit()
            data["user"] = user
            data["session"] = session
            data["lang"] = user.lang
            return await handler(event, data)