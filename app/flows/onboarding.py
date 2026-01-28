from typing import Optional

from aiogram.types import Message

from bot.keyboards import consent_keyboard, main_menu_keyboard
from services.messages import delete_tracked_messages, send_message

INTRO_TEXT = (
    "Привет! Я помогу бережно разбирать эмоции и сложные ситуации "
    "на основе доказательных подходов."
)

DISCLAIMER_TEXT = (
    "Важно: я не являюсь экстренной помощью. "
    "Если вам угрожает опасность, пожалуйста, обратитесь в экстренные службы."
)

CONSENT_QUESTION = "Если согласны продолжить, нажмите кнопку ниже."


async def start_onboarding(message: Message) -> None:
    await send_message(message, INTRO_TEXT, reply_markup=main_menu_keyboard())
    await send_message(message, DISCLAIMER_TEXT)
    await send_message(message, CONSENT_QUESTION, reply_markup=consent_keyboard())

async def confirm_consent(message: Message, user_id: Optional[int] = None) -> None:
    await send_message(
        message,
        "Привет! Я готов с тобой пообщаться. Напиши мне.",
        reply_markup=main_menu_keyboard(),
        track=False,
    )
    await delete_tracked_messages(message, user_id=user_id)


async def decline_consent(message: Message) -> None:
    await send_message(
        message,
        "Хорошо. Если захотите вернуться, нажмите /start в любое время.",
        reply_markup=main_menu_keyboard(),
    )
