from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import Subscription


async def expires_at(session: AsyncSession, user_id: int) -> datetime | None:
    row = await session.scalar(select(Subscription).where(Subscription.user_id == user_id))
    return row.expires_at if row else None


async def is_pro(session: AsyncSession, user_id: int) -> bool:
    exp = await expires_at(session, user_id)
    return bool(exp and exp > datetime.now(UTC))


async def extend(session: AsyncSession, user_id: int, days: int) -> datetime:
    now = datetime.now(UTC)
    current = await expires_at(session, user_id)
    base = max(now, current) if current else now
    new_exp = base + timedelta(days=days)
    row = await session.scalar(select(Subscription).where(Subscription.user_id == user_id))
    if row:
        row.expires_at, row.updated_at = new_exp, now
    else:
        session.add(Subscription(user_id=user_id, expires_at=new_exp, updated_at=now))
    await session.commit()
    return new_exp