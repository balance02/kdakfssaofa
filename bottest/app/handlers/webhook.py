import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Event, Payment
from app.services import access

log = logging.getLogger(__name__)


async def fulfil(session: AsyncSession, payment: Payment) -> None:
    if payment.status == "paid":
        return
    payment.status = "paid"
    payment.paid_at = datetime.now(UTC)
    await access.extend(session, payment.user_id, payment.days)
    if payment.days == 7:
        from app.db.models import User
        u = await session.get(User, payment.user_id)
        if u:
            u.trial_used = True
    session.add(Event(user_id=payment.user_id, kind="paid", meta={"days": payment.days,
                                                                 "amount": float(payment.amount)}))
    await session.commit()


async def handle_update(session: AsyncSession, body: dict) -> None:
    if body.get("update_type") != "invoice_paid":
        return
    inv = body["payload"]
    invoice_id = str(inv["invoice_id"])
    payment = await session.scalar(select(Payment).where(Payment.invoice_id == invoice_id))
    if payment is None or payment.status == "paid":
        return
    if float(inv.get("amount", 0)) + 0.01 < float(payment.amount):
        log.warning("underpaid invoice %s", invoice_id)
        return
    await fulfil(session, payment)