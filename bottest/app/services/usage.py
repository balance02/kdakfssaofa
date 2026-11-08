from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import UsageDaily


def today() -> date:
    return datetime.now(UTC).date()


async def get_today(session: AsyncSession, user_id: int) -> UsageDaily | None:
    return await session.scalar(
        select(UsageDaily).where(UsageDaily.user_id == user_id, UsageDaily.day == today())
    )


async def add(session: AsyncSession, user_id: int, tokens_in: int, tokens_out: int, cost: float) -> None:
    row = await get_today(session, user_id)
    if row:
        row.messages += 1
        row.tokens_in += tokens_in
        row.tokens_out += tokens_out
        row.cost_usd = Decimal(row.cost_usd) + Decimal(str(cost))
    else:
        session.add(UsageDaily(user_id=user_id, day=today(), messages=1,
                               tokens_in=tokens_in, tokens_out=tokens_out, cost_usd=Decimal(str(cost))))
    await session.commit()


async def global_cost_today(session: AsyncSession) -> float:
    total = await session.scalar(
        select(func.coalesce(func.sum(UsageDaily.cost_usd), 0)).where(UsageDaily.day == today())
    )
    return float(total or 0)


async def limits_exceeded(session: AsyncSession, user_id: int) -> str | None:
    s = get_settings()
    row = await get_today(session, user_id)
    if row and row.messages >= s.daily_msg_limit:
        return "messages"
    if row and (row.tokens_in + row.tokens_out) >= s.daily_token_limit:
        return "tokens"
    if await global_cost_today(session) >= s.daily_spend_cap:
        return "global"
    return None