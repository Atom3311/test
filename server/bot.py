from __future__ import annotations

import os
import asyncio
from pathlib import Path

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv

env_paths = [
    Path(__file__).with_name(".env"),
    Path.cwd() / ".env",
]
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)


def load_env_fallback(paths: list[Path]) -> None:
    for path in paths:
        if not path.exists():
            continue
        for raw in path.read_text(encoding="utf-8-sig").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


load_env_fallback(env_paths)

def clean_env(value: str | None) -> str:
    if not value:
        return ""
    return value.strip().strip("\"'").strip()


TOKEN = clean_env(os.getenv("TELEGRAM_BOT_TOKEN"))
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
    if not TOKEN or ":" not in TOKEN:
        raise RuntimeError("Invalid TELEGRAM_BOT_TOKEN in server/.env")

    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    dp.message.register(start_handler, Command("start", "menu"))
    dp.message.register(fallback_handler)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
