from aiogram.types import CallbackQuery, Message

from bot.keyboards import support_menu_keyboard
from services.emoji import decorate_text
from services.llm import generate_response
from services.messages import send_message, send_message_from_callback
from services.message_service import add_message
from services.prompts import SUPPORT_SYSTEM_PROMPT, build_support_prompt

SUPPORT_INTRO = (
    "Вот несколько коротких способов помочь себе прямо сейчас. "
    "Выберите вариант ниже."
)


def _record_support_history(user_id: int, label: str, response_text: str) -> None:
    add_message(user_id, "user", f"Запрос поддержки: {label}.")
    add_message(user_id, "assistant", response_text)


async def send_support_menu(message: Message) -> None:
    await send_message(message, SUPPORT_INTRO, reply_markup=support_menu_keyboard())


async def handle_support_callback(callback: CallbackQuery) -> None:
    data = callback.data or ""
    if callback.message is None:
        await callback.answer()
        return
    if data == "support:breath":
        text = await generate_response(
            prompt=build_support_prompt("breath"),
            system_prompt=SUPPORT_SYSTEM_PROMPT,
            temperature=0.7,
            max_completion_tokens=180,
        )
        if callback.from_user:
            text = decorate_text(callback.from_user.id, text, kind="support:breath")
        await send_message_from_callback(callback, text)
        if callback.from_user:
            _record_support_history(callback.from_user.id, "дыхание 4-6", text)
    elif data == "support:ground":
        text = await generate_response(
            prompt=build_support_prompt("ground"),
            system_prompt=SUPPORT_SYSTEM_PROMPT,
            temperature=0.7,
            max_completion_tokens=180,
        )
        if callback.from_user:
            text = decorate_text(callback.from_user.id, text, kind="support:ground")
        await send_message_from_callback(callback, text)
        if callback.from_user:
            _record_support_history(callback.from_user.id, "упражнение 5-4-3-2-1", text)
    elif data == "support:compassion":
        text = await generate_response(
            prompt=build_support_prompt("compassion"),
            system_prompt=SUPPORT_SYSTEM_PROMPT,
            temperature=0.9,
            max_completion_tokens=180,
        )
        if callback.from_user:
            text = decorate_text(callback.from_user.id, text, kind="support:compassion")
        await send_message_from_callback(callback, text)
        if callback.from_user:
            _record_support_history(callback.from_user.id, "добрые слова себе", text)
    await callback.answer()
