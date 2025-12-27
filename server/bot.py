from __future__ import annotations

import os
import asyncio
from typing import Optional

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://YOUR_SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "YOUR_SUPABASE_SERVICE_ROLE_KEY")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://YOUR_WEBAPP_URL")


async def upsert_user(user: types.User) -> None:
    if "YOUR_" in SUPABASE_URL:
        return

    payload = {
        "id": str(user.id),
        "username": user.username,
        "display_name": user.first_name or "Игрок",
        "photo_url": None,
        "badges": ["Новичок"],
        "season": "Зима 2025",
        "achievements": "0/30",
    }

    headers = {
        "Content-Type": "application/json",
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Prefer": "resolution=merge-duplicates",
    }

    import aiohttp

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{SUPABASE_URL}/rest/v1/users", json=payload, headers=headers) as resp:
            if resp.status >= 400:
                text = await resp.text()
                print("Supabase error", resp.status, text)


def build_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Открыть Mini App", web_app=types.WebAppInfo(url=WEBAPP_URL))]
        ]
    )


async def start_handler(message: types.Message) -> None:
    if message.from_user:
        await upsert_user(message.from_user)
    await message.answer("Открыть Снежный Кликер", reply_markup=build_menu())


async def fallback_handler(message: types.Message) -> None:
    if message.text and message.text.startswith("/"):
        return
    await message.answer("Нажми кнопку, чтобы открыть игру.")


async def main() -> None:
    if "YOUR_" in TOKEN:
        print("Set TELEGRAM_BOT_TOKEN before запуск")

    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    dp.message.register(start_handler, Command("start", "menu"))
    dp.message.register(fallback_handler)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
