from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Context, Summary
from app.services.tokens import estimate, estimate_messages

MAX_CONTEXT_TOKENS = 8000
MAX_PAIRS = 12
SUMMARY_TOKENS = 600


async def add(session: AsyncSession, user_id: int, role: str, content: str) -> None:
    seq = await session.scalar(select(func.coalesce(func.max(Context.seq), 0)).where(Context.user_id == user_id)) + 1
    session.add(Context(user_id=user_id, seq=seq, role=role, content=content))
    await session.commit()


async def get_summary(session: AsyncSession, user_id: int) -> str | None:
    return await session.scalar(select(Summary.text).where(Summary.user_id == user_id))


async def set_summary(session: AsyncSession, user_id: int, text: str) -> None:
    row = await session.scalar(select(Summary).where(Summary.user_id == user_id))
    if row:
        row.text = text
    else:
        session.add(Summary(user_id=user_id, text=text))
    await session.commit()


async def clear(session: AsyncSession, user_id: int) -> None:
    await session.execute(delete(Context).where(Context.user_id == user_id))
    await session.execute(delete(Summary).where(Summary.user_id == user_id))
    await session.commit()


async def build(session: AsyncSession, user_id: int) -> list[dict]:
    rows = list((await session.scalars(
        select(Context).where(Context.user_id == user_id).order_by(Context.seq.desc()).limit(MAX_PAIRS * 2)
    )).all())
    rows.reverse()
    messages = [{"role": r.role, "content": r.content} for r in rows]
    while estimate_messages(messages) > MAX_CONTEXT_TOKENS and messages:
        messages.pop(0)
    return messages


async def trim_to_summary(session: AsyncSession, user_id: int) -> list[dict] | None:
    """Возвращает пары, ушедшие за пределы окна, для пересчёта суммари."""
    rows = list((await session.scalars(
        select(Context).where(Context.user_id == user_id).order_by(Context.seq.asc())
    )).all())
    if len(rows) <= MAX_PAIRS * 2:
        return None
    keep_from = len(rows) - MAX_PAIRS * 2
    cut = rows[:keep_from]
    if sum(estimate(r.content) for r in cut) < SUMMARY_TOKENS:
        return None
    return [{"role": r.role, "content": r.content} for r in cut]