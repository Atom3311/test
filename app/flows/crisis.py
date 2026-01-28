from aiogram.types import Message

from services.messages import send_message

CRISIS_MESSAGE = (
    "Мне очень жаль, что вам так тяжело. Я не могу заменить живую помощь.\n\n"
    "Важно: если вы в непосредственной опасности, обратитесь в экстренные "
    "службы вашей страны (например, 112/911).\n"
    "Если возможно, свяжитесь с человеком из доверенного круга.\n\n"
    "Вы сейчас в безопасности? В какой стране вы находитесь?"
)


async def handle_crisis_message(message: Message) -> None:
    await send_message(message, CRISIS_MESSAGE)
