import logging

from aiogram import Router
from aiogram.types import ErrorEvent

from app.config import get_settings

router = Router()
log = logging.getLogger(__name__)


@router.error()
async def on_error(event: ErrorEvent) -> bool:
    log.exception("handler error", exc_info=event.exception)
    text = f"error: {type(event.exception).__name__}: {event.exception}"
    for admin in get_settings().admins:
        try:
            await event.update.bot.send_message(admin, text[:1000])
        except Exception:  # noqa: BLE001
            pass
    return True