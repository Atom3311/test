import asyncio

from aiogram import Bot, Dispatcher

from config import load_settings
from utils.logger import setup_logging
from services.db import get_db_client
from bot.handlers import router


async def main() -> None:
    setup_logging()
    settings = load_settings()
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is not set")
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY is not set")
    if not settings.supabase_url or not settings.supabase_key:
        raise RuntimeError("SUPABASE_URL or SUPABASE_KEY is not set")

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    dp.include_router(router)

    get_db_client()
    await dp.start_polling(bot)




if __name__ == "__main__":
    asyncio.run(main())

