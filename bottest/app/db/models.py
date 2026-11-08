from datetime import date, datetime

from sqlalchemy import (BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, JSON,
                        Numeric, String, Text, func)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(64))
    first_name: Mapped[str | None] = mapped_column(String(128))
    lang: Mapped[str] = mapped_column(String(8), default="ru")
    lang_chosen: Mapped[bool] = mapped_column(Boolean, default=False)
    age_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    subscribed: Mapped[bool] = mapped_column(Boolean, default=False)
    mode: Mapped[str] = mapped_column(String(16), default="default")
    model: Mapped[str | None] = mapped_column(String(64))
    persona: Mapped[str | None] = mapped_column(Text)
    banned: Mapped[bool] = mapped_column(Boolean, default=False)
    trial_used: Mapped[bool] = mapped_column(Boolean, default=False)
    free_used: Mapped[int] = mapped_column(Integer, default=0)
    strong_used_today: Mapped[int] = mapped_column(Integer, default=0)
    strong_warned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    referrer: Mapped[int] = mapped_column(BigInteger, default=0)
    ref_balance: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    ref_by: Mapped[int] = mapped_column(Integer, default=0)


class Subscription(Base):
    __tablename__ = "subscriptions"
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    invoice_id: Mapped[str] = mapped_column(String(64), unique=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    asset: Mapped[str] = mapped_column(String(16), default="USDT")
    days: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    refunded: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UsageDaily(Base):
    __tablename__ = "usage_daily"
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    day: Mapped[date] = mapped_column(Date, primary_key=True)
    messages: Mapped[int] = mapped_column(Integer, default=0)
    tokens_in: Mapped[int] = mapped_column(Integer, default=0)
    tokens_out: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Numeric(12, 6), default=0)


class Context(Base):
    __tablename__ = "contexts"
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    seq: Mapped[int] = mapped_column(Integer, primary_key=True)
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Summary(Base):
    __tablename__ = "summaries"
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    text: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Event(Base):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger)
    kind: Mapped[str] = mapped_column(String(32))
    meta: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())