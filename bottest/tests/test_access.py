import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.models import Base, Subscription
from app.services import access


def run(coro):
    return asyncio.run(coro)


def test_expiry_flow():
    async def scenario():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        maker = async_sessionmaker(engine, expire_on_commit=False)
        async with maker() as s:
            assert not await access.is_pro(s, 1)
            exp = await access.extend(s, 1, 30)
            assert exp > datetime.now(UTC)
            assert await access.is_pro(s, 1)
            row = await s.get(Subscription, 1)
            row.expires_at = datetime.now(UTC) - timedelta(seconds=1)
            await s.commit()
            assert not await access.is_pro(s, 1)
    run(scenario())