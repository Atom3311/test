from aiogram.types import Message

from bot.keyboards import main_menu_keyboard
from services.messages import send_message

HELP_TEXT = (
    "Я помогу обсудить эмоции и сложные ситуации.\n\n"
    "Команды:\n"
    "/start — начать\n"
    "/checkin — оценка состояния\n"
    "/support — быстрая помощь\n"
    "/focus — выбрать тему\n"
    "/export — экспорт переписки\n"
    "/reset — сбросить контекст\n\n"
    "Кнопки: Моё состояние, Быстрая помощь, Общение, Настройки и данные.\n"
    "В настройках: Экспорт данных, Сбросить переписку.\n\n"
    "Важно: я не являюсь экстренной помощью. "
    "Если вам угрожает опасность, обратитесь в службы экстренной помощи "
    "вашей страны."
)


async def send_help(message: Message) -> None:
    await send_message(message, HELP_TEXT, reply_markup=main_menu_keyboard())
