from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.config import get_settings
from app.db.models import Event, User
from app.services import access

router = Router()


def _admin(message: Message) -> bool:
    return message.from_user.id in get_settings().admins


@router.message(Command("admin"))
async def admin(message: Message, session) -> None:
    if not _admin(message):
        return
    total = await session.scalar(__import__("sqlalchemy").select(__import__("sqlalchemy").func.count(User.id)))
    await message.answer(f"users: {total}\n/grant <id> <days>\n/revoke <id>\n/ban <id>\n/unban <id>")


@router.message(Command("grant"))
async def grant(message: Message, session) -> None:
    if not _admin(message):
        return
    _, uid, days = message.text.split()
    exp = await access.extend(session, int(uid), int(days))
    session.add(Event(user_id=int(uid), kind="grant", meta={"days": int(days)}))
    await session.commit()
    await message.answer(f"granted {days}d until {exp.isoformat()}")


@router.message(Command("revoke"))
async def revoke(message: Message, session) -> None:
    if not _admin(message):
        return
    uid = int(message.text.split()[1])
    from datetime import UTC, datetime
    from sqlalchemy import select
    from app.db.models import Subscription
    row = await session.scalar(select(Subscription).where(Subscription.user_id == uid))
    if row:
        row.expires_at = datetime.now(UTC)
        await session.commit()
    await message.answer("revoked")


@router.message(Command("ban"))
async def ban(message: Message, session) -> None:
    if not _admin(message):
        return
    u = await session.get(User, int(message.text.split()[1]))
    if u:
        u.banned = True
        await session.commit()
    await message.answer("banned")


@router.message(Command("unban"))
async def unban(message: Message, session) -> None:
    if not _admin(message):
        return
    u = await session.get(User, int(message.text.split()[1]))
    if u:
        u.banned = False
        await session.commit()
    await message.answer("unbanned")