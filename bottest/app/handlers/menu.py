from datetime import UTC, datetime

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.config import get_settings
from app.keyboards.inline import back_kb, welcome
from app.services import access, i18n

router = Router()
REF_BONUS = 10.0


@router.callback_query(F.data == "nav:back")
async def back(cb: CallbackQuery, user, lang: str) -> None:
    await cb.message.edit_text(
        i18n.t(lang, "start.welcome", price=int(get_settings().pro_price_usd)),
        reply_markup=welcome(lang, get_settings().trial_price_usd))
    await cb.answer()


@router.callback_query(F.data == "nav:profile")
async def profile(cb: CallbackQuery, user, session, lang: str) -> None:
    exp = await access.expires_at(session, user.id)
    active = bool(exp and exp > datetime.now(UTC))
    if active:
        sub = i18n.t(lang, "profile.sub_active", date=exp.strftime("%d.%m.%Y %H:%M"))
    else:
        sub = i18n.t(lang, "profile.sub_none")
    left = "∞" if active else str(max(0, get_settings().free_messages - user.free_used))
    text = (i18n.t(lang, "profile.title") + "\n"
            + sub + "\n"
            + i18n.t(lang, "profile.free", left=left) + "\n\n"
            + i18n.t(lang, "profile.balance", amount=f"{float(user.ref_balance):.2f}"))
    await cb.message.edit_text(text, reply_markup=back_kb(lang))
    await cb.answer()


@router.callback_query(F.data == "nav:ref")
async def referral(cb: CallbackQuery, user, bot, lang: str) -> None:
    me = await bot.get_me()
    link = f"https://t.me/{me.username}?start=ref_{user.id}"
    text = (i18n.t(lang, "ref.title") + "\n\n"
            + i18n.t(lang, "ref.link") + f"\n<code>{link}</code>\n\n"
            + i18n.t(lang, "ref.rules", bonus=int(REF_BONUS)) + "\n\n"
            + i18n.t(lang, "ref.stats", amount=f"{float(user.ref_balance):.2f}", count=user.ref_by))
    await cb.message.edit_text(text, reply_markup=back_kb(lang), disable_web_page_preview=True)
    await cb.answer()