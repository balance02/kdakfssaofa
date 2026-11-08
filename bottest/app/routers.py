from aiogram import Router

from app.handlers import admin, chat, errors, menu, payment, start


def build() -> Router:
    root = Router()
    root.include_router(start.router)
    root.include_router(menu.router)
    root.include_router(payment.router)
    root.include_router(admin.router)
    root.include_router(chat.router)
    root.include_router(errors.router)
    return root