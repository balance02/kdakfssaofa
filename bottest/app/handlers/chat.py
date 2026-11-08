import asyncio
import html
import io
import logging


from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.config import get_settings
from app.db.models import Event
from app.keyboards.inline import channels_kb, modes
from app.prompts.base import BASE
from app.prompts.modes import MAX_TOKENS, MODES, TEMPERATURE
from app.services import context, i18n, modelpool, usage, venice
from app.services.tokens import estimate
from app.services.md import split_html, to_html


router = Router()
log = logging.getLogger(__name__)
locks: dict[int, asyncio.Lock] = {}
MAX_INPUT = 8000


def _lock(uid: int) -> asyncio.Lock:
    return locks.setdefault(uid, asyncio.Lock())

def esc(text: str) -> str:
    return html.escape(text, quote=False)


@router.message(Command("mode"))
async def choose_mode(message: Message, user, lang: str) -> None:
    await message.answer(i18n.t(lang, "mode.choose"), reply_markup=modes(lang, user.mode))


@router.callback_query(F.data.startswith("mode:"))
async def set_mode(cb: CallbackQuery, user, session, lang: str) -> None:
    user.mode = cb.data.split(":")[1]
    await session.commit()
    await cb.message.edit_text(i18n.t(lang, "mode.set", name=i18n.t(lang, f"mode.{user.mode}")),
                               reply_markup=modes(lang, user.mode))
    await cb.answer()


@router.message(Command("reset"))
@router.message(Command("clear_context"))
async def reset(message: Message, user, session, lang: str) -> None:
    await context.clear(session, user.id)
    await message.answer(i18n.t(lang, "reset.done"))


@router.message(Command("usage"))
async def show_usage(message: Message, user, session, lang: str) -> None:
    row = await usage.get_today(session, user.id)
    s = get_settings()
    await message.answer(i18n.t(lang, "usage.text",
                                msgs=row.messages if row else 0, msg_limit=s.daily_msg_limit,
                                tokens=(row.tokens_in + row.tokens_out) if row else 0,
                                token_limit=s.daily_token_limit))


@router.message(Command("cancel"))
async def cancel(message: Message, user, lang: str) -> None:
    lock = locks.get(user.id)
    if lock and lock.locked():
        lock.release()
        await message.answer(i18n.t(lang, "cancel.done"))
    else:
        await message.answer(i18n.t(lang, "cancel.idle"))


async def _read_input(message: Message, lang: str) -> str | None:
    if message.document:
        if message.document.file_size > 10 * 1024 * 1024:
            await message.answer(i18n.t(lang, "file.too_big"))
            return None
        name = (message.document.file_name or "").lower()
        if name.endswith(".pdf"):
            from pypdf import PdfReader
            buf = io.BytesIO()
            await message.bot.download(message.document, destination=buf)
            buf.seek(0)
            text = "\n".join(p.extract_text() or "" for p in PdfReader(buf).pages)
        elif name.endswith(".txt"):
            buf = io.BytesIO()
            await message.bot.download(message.document, destination=buf)
            text = buf.getvalue().decode("utf-8", "ignore")
        else:
            await message.answer(i18n.t(lang, "file.bad_type"))
            return None
        text = text[:30_000]
        caption = (message.caption or "").strip()
        return f"{caption}\n\n--- файл ---\n{text}".strip()
    text = (message.text or "").strip()
    if not text:
        return None
    return text[:MAX_INPUT]


@router.message((F.text & ~F.text.startswith("/")) | F.document)
async def on_message(message: Message, bot: Bot, user, session, lang: str, gate: str | None = None) -> None:
    s = get_settings()

    if gate == "channels":
        await message.answer(i18n.t(lang, "channels.ask"),
                             reply_markup=channels_kb(lang, s.channels))
        return

    limit = await usage.limits_exceeded(session, user.id)
    if limit == "global":
        await message.answer(i18n.t(lang, "limit.global"))
        return
    if limit:
        await message.answer(i18n.t(lang, "limit.daily", limit=limit))
        return

    lock = _lock(user.id)
    if lock.locked():
        await message.answer(i18n.t(lang, "busy"))
        return
    await lock.acquire()
    try:
        text = await _read_input(message, lang)
        if not text:
            return

        model = modelpool.resolve(user.mode)
        if user.mode in ("rp", "code", "hack"):
            if user.strong_used_today >= s.strong_daily_limit:
                model = modelpool.resolve("default")
                if not user.strong_warned:
                    user.strong_warned = True
                    await session.commit()
                    await message.answer(i18n.t(lang, "model.downgraded"))

        history = await context.build(session, user.id)
        system = BASE + ("\n" + MODES[user.mode] if MODES.get(user.mode) else "")
        if user.mode == "rp" and user.persona:
            system += f"\nПерсона: {user.persona}"
        summary = await context.get_summary(session, user.id)
        if summary:
            system += f"\nСводка прошлого разговора: {summary}"

        messages = [{"role": "system", "content": system}, *history, {"role": "user", "content": text}]
        tokens_in_est = sum(estimate(m["content"]) for m in messages)

        try:
            placeholder = await message.answer(
                i18n.t(lang, "thinking"), message_effect_id=s.effect_id or None)
        except TelegramBadRequest:
            placeholder = await message.answer(i18n.t(lang, "thinking"))

        try:
            result = await venice.chat(messages, model, MAX_TOKENS[user.mode], TEMPERATURE[user.mode])
        except venice.VeniceError as exc:
            session.add(Event(user_id=user.id, kind="llm_error", meta={"status": exc.status}))
            await session.commit()
            if exc.status == 402:
                await placeholder.edit_text(i18n.t(lang, "error.balance"))
            else:
                await placeholder.edit_text(i18n.t(lang, "error.llm"))
            return

        answer = to_html(result["text"].strip()) or "…"
        for idx, chunk in enumerate(split_html(answer)):
            if idx == 0:
                await placeholder.edit_text(chunk)
            else:
                await message.answer(chunk)

        await context.add(session, user.id, "user", text)
        await context.add(session, user.id, "assistant", answer)
        await usage.add(session, user.id, result["tokens_in"] or tokens_in_est,
                        result["tokens_out"], modelpool.cost(model, tokens_in_est, result["tokens_out"]))
        if user.mode in ("rp", "code", "hack"):
            user.strong_used_today += 1
        if not await _is_pro_cached(session, user.id):
            user.free_used += 1
        await session.commit()

        to_summarize = await context.trim_to_summary(session, user.id)
        if to_summarize:
            await _summarize(session, user, to_summarize, lang)
    finally:
        if lock.locked():
            lock.release()


async def _is_pro_cached(session, user_id: int) -> bool:
    from app.services import access
    return await access.is_pro(session, user_id)


async def _summarize(session, user, pairs: list[dict], lang: str) -> None:
    body = "\n".join(f"{p['role']}: {p['content']}" for p in pairs)[:12_000]
    try:
        res = await venice.chat(
            [{"role": "system", "content": "Сожми диалог в 600 токенов. Только факты, имена, решения."},
             {"role": "user", "content": body}],
            modelpool.resolve("default"), 600, 0.3)
        await context.set_summary(session, user.id, res["text"][:4000])
    except venice.VeniceError:
        pass