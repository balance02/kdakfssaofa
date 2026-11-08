import logging
import time

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.config import get_settings
from app.db.models import Event, Payment
from app.keyboards.inline import invoice
from app.services import access, crypto, i18n

router = Router()
log = logging.getLogger(__name__)
last_invoice: dict[int, float] = {}


@router.message(Command("buy"))
@router.message(Command("plans"))
@router.callback_query(F.data.startswith("buy:"))
async def buy(event: Message | CallbackQuery, user, session, lang: str) -> None:
    s = get_settings()
    is_trial = isinstance(event, CallbackQuery) and event.data == "buy:trial"
    if is_trial and (s.trial_price_usd <= 0 or user.trial_used):
        if isinstance(event, CallbackQuery):
            await event.answer(i18n.t(lang, "buy.trial_unavailable"), show_alert=True)
        return
    if time.monotonic() - last_invoice.get(user.id, 0) < 60:
        text = i18n.t(lang, "buy.too_often")
        target = event.message if isinstance(event, CallbackQuery) else event
        await target.answer(text)
        return
    last_invoice[user.id] = time.monotonic()

    amount = s.trial_price_usd if is_trial else s.pro_price_usd
    days = 7 if is_trial else 30
    try:
        invoice_id, url = await crypto.create_invoice(user.id, amount, days)
    except Exception as exc:  # noqa: BLE001
        log.exception("invoice failed")
        session.add(Event(user_id=user.id, kind="pay_error", meta={"err": str(exc)[:200]}))
        await session.commit()
        target = event.message if isinstance(event, CallbackQuery) else event
        await target.answer(i18n.t(lang, "buy.error"))
        return

    session.add(Payment(user_id=user.id, invoice_id=invoice_id, amount=amount, days=days))
    await session.commit()
    target = event.message if isinstance(event, CallbackQuery) else event
    await target.answer(i18n.t(lang, "buy.invoice", days=days, amount=amount),
                        reply_markup=invoice(lang, url))
    if isinstance(event, CallbackQuery):
        await event.answer()


@router.message(Command("sub"))
async def sub_status(message: Message, user, session, lang: str) -> None:
    exp = await access.expires_at(session, user.id)
    if exp:
        await message.answer(i18n.t(lang, "sub.active", date=exp.strftime("%Y-%m-%d %H:%M UTC")))
    else:
        await message.answer(i18n.t(lang, "sub.none"))


@router.callback_query(F.data == "pay:check")
async def check(cb: CallbackQuery, user, session, lang: str) -> None:
    from sqlalchemy import select
    rows = (await session.scalars(
        select(Payment).where(Payment.user_id == user.id, Payment.status == "pending"))).all()
    for p in rows:
        inv = await crypto.get_invoice(p.invoice_id)
        if inv and inv.get("status") == "paid":
            from app.handlers.webhook import fulfil
            await fulfil(session, p)
            await cb.message.edit_text(i18n.t(lang, "pay.done"))
            await cb.answer()
            return
    await cb.answer(i18n.t(lang, "pay.pending"), show_alert=True)