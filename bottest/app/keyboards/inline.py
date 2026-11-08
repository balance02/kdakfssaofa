from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.services import i18n
from app.config import get_settings


def lang_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:set:ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:set:en")],
    ])


def channels_kb(lang: str, channels: list[str]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for ch in channels:
        kb.button(text=i18n.t(lang, "btn.sub_channel", name=ch), url=f"https://t.me/{ch}")
    kb.button(text=i18n.t(lang, "btn.subscribed"), callback_data="check_subs")
    kb.adjust(1, 2)
    return kb.as_markup()


def welcome(lang: str, trial: float) -> InlineKeyboardMarkup:
    s = get_settings()
    rows = [[
        InlineKeyboardButton(text=i18n.t(lang, "btn.profile"), callback_data="nav:profile",
                             style="success"),
        InlineKeyboardButton(text=i18n.t(lang, "btn.ref"), callback_data="nav:ref",
                             style="success"),
    ]]
    if s.has_channel:
        rows.append([InlineKeyboardButton(text=i18n.t(lang, "btn.sub_channel", name=s.channel_title),
                                          url=s.channel_url)])
    if trial > 0:
        rows.append([InlineKeyboardButton(text=i18n.t(lang, "btn.try"), callback_data="buy:trial")])
    last = []
    if s.has_channel:
        last.append(InlineKeyboardButton(text=i18n.t(lang, "btn.subscribed"),
                                         callback_data="check_subs", style="success"))
    last.append(InlineKeyboardButton(text=i18n.t(lang, "btn.buy"), callback_data="buy:pro",
                                     style="primary"))
    last.append(InlineKeyboardButton(text=i18n.t(lang, "btn.lang"), callback_data="nav:lang"))
    rows.append(last)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def consent(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=i18n.t(lang, "btn.ok"), callback_data="consent")
    ]])


def paywall(lang: str, trial: float) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if trial > 0:
        kb.button(text=i18n.t(lang, "btn.try_price", price=trial), callback_data="buy:trial")
    kb.button(text=i18n.t(lang, "btn.buy"), callback_data="buy:pro")
    kb.adjust(1)
    return kb.as_markup()


def invoice(lang: str, url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=i18n.t(lang, "btn.pay"), url=url)],
        [InlineKeyboardButton(text=i18n.t(lang, "btn.check"), callback_data="pay:check")],
    ])


def modes(lang: str, current: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for code in ("default", "code", "rp", "hack", "brief"):
        mark = "• " if code == current else ""
        kb.button(text=f"{mark}{i18n.t(lang, f'mode.{code}')}", callback_data=f"mode:{code}")
    kb.adjust(2)
    return kb.as_markup()

def back_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=i18n.t(lang, "btn.back"), callback_data="nav:back")]
    ])