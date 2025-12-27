from __future__ import annotations

import os
import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://YOUR_SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "YOUR_SUPABASE_ANON_KEY")


async def upsert_user(user: types.User) -> None:
    if "YOUR_" in SUPABASE_URL or "YOUR_" in SUPABASE_ANON_KEY:
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
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Prefer": "resolution=merge-duplicates",
    }

    import aiohttp

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{SUPABASE_URL}/rest/v1/users", json=payload, headers=headers) as resp:
            if resp.status >= 400:
                text = await resp.text()
                print("Supabase error", resp.status, text)


async def start_handler(message: types.Message) -> None:
    if message.from_user:
        await upsert_user(message.from_user)
    await message.answer("Открыть Снежный Кликер через меню бота.")


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
