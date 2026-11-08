from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from app.config import get_settings
from app.db.models import Event, User
from app.keyboards.inline import consent, lang_kb, welcome
from app.services import i18n

router = Router()


@router.message(CommandStart())
async def start(message: Message, user, session, lang: str) -> None:
    args = message.text.split(maxsplit=1)
    if len(args) > 1 and args[1].startswith("ref_"):
        ref = int(args[1][4:]) if args[1][4:].isdigit() else 0
        if ref and ref != user.id and not user.referrer:
            user.referrer = ref
            inviter = await session.get(User, ref)
            if inviter:
                inviter.ref_by += 1
            await session.commit()

    if not user.lang_chosen:
        await message.answer(i18n.t(lang, "lang.pick"), reply_markup=lang_kb())
        return

    session.add(Event(user_id=user.id, kind="signup"))
    await session.commit()
    await message.answer(
        i18n.t(lang, "start.welcome", price=int(get_settings().pro_price_usd)),
        reply_markup=welcome(lang, get_settings().trial_price_usd))


@router.message(Command("lang"))
async def lang_cmd(message: Message, lang: str) -> None:
    await message.answer(i18n.t(lang, "lang.pick"), reply_markup=lang_kb())


@router.callback_query(F.data.startswith("lang:set:"))
async def set_lang(cb: CallbackQuery, user, session) -> None:
    user.lang = cb.data.split(":")[2]
    user.lang_chosen = True
    await session.commit()
    await cb.message.edit_text(
        i18n.t(user.lang, "start.welcome", price=int(get_settings().pro_price_usd)),
        reply_markup=welcome(user.lang, get_settings().trial_price_usd))
    await cb.answer()


@router.callback_query(F.data == "nav:lang")
async def nav_lang(cb: CallbackQuery, lang: str) -> None:
    await cb.message.edit_text(i18n.t(lang, "lang.pick"), reply_markup=lang_kb())
    await cb.answer()


@router.callback_query(F.data == "check_subs")
async def check_subs(cb: CallbackQuery, bot, user, session, lang: str) -> None:
    s = get_settings()
    if not s.has_channel:
        user.subscribed = True
        await session.commit()
        await cb.answer()
        return
    ok = False
    try:
        m = await bot.get_chat_member(s.channel_id, cb.from_user.id)
        ok = m.status in ("member", "administrator", "creator")
    except Exception:  # noqa: BLE001
        ok = False
    if not ok:
        await cb.answer(i18n.t(lang, "channels.not_yet"), show_alert=True)
        return
    user.subscribed = True
    await session.commit()
    try:
        await cb.message.edit_text(i18n.t(lang, "channels.ok_text"))
    except Exception:  # noqa: BLE001
        pass
    await cb.answer(i18n.t(lang, "channels.ok"))


@router.callback_query(F.data == "inside")
async def inside(cb: CallbackQuery, lang: str) -> None:
    await cb.message.answer(i18n.t(lang, "start.inside"))
    await cb.answer()


@router.callback_query(F.data == "consent")
async def give_consent(cb: CallbackQuery, user, session, lang: str) -> None:
    user.age_confirmed = True
    await session.commit()
    await cb.message.edit_text(i18n.t(lang, "consent.ok"))
    await cb.answer()


@router.message(Command("help"))
async def help_cmd(message: Message, lang: str) -> None:
    await message.answer(i18n.t(lang, "help"))