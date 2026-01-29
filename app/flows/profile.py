import re

from aiogram.types import CallbackQuery, Message

from bot.keyboards import about_skip_keyboard, gender_keyboard, main_menu_keyboard
from services.messages import send_message, send_message_from_callback
from services.memory import get_memory_store
from services.user_service import set_user_awaiting, set_user_text_field

GENDER_QUESTION = "🟢⚪️⚪️⚪️ Выберите пол:"
NAME_QUESTION = "🟢⚪️⚪️⚪️ Как тебя зовут?"
AGE_QUESTION = "🟢🟢⚪️⚪️ Сколько тебе лет?"
ABOUT_QUESTION = (
    "🟢🟢🟢⚪️ Что еще важно о тебе знать? Опиши кто ты, что происходит в твоей жизни.\n\n"
    "Используй не более 3000 символов (это примерно 500–600 слов)."
)
FINAL_TEXT = (
    "Хорошо, отредактировать анкету можно будет позже командой /info.\n\n"
    "Расскажи как у тебя дела, как проходит твой день? "
    "Пришли мне текст, кружок или голосовое."
)


async def start_profile(message: Message) -> None:
    if message.from_user is None:
        await send_message(message, GENDER_QUESTION, reply_markup=gender_keyboard())
        return
    user_id = message.from_user.id
    await set_user_awaiting(user_id, "awaiting_checkin", False)
    await set_user_awaiting(user_id, "awaiting_goal", False)
    await set_user_awaiting(user_id, "awaiting_outcome", False)
    await set_user_awaiting(user_id, "awaiting_gender", True)
    await set_user_awaiting(user_id, "awaiting_name", False)
    await set_user_awaiting(user_id, "awaiting_age", False)
    await set_user_awaiting(user_id, "awaiting_about", False)
    await send_message(message, GENDER_QUESTION, reply_markup=gender_keyboard())


async def handle_gender_callback(callback: CallbackQuery, gender: str) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer()
        return
    user_id = callback.from_user.id
    gender_label = "мужчина" if gender == "male" else "женщина"
    await set_user_text_field(user_id, "gender", gender_label)
    await set_user_awaiting(user_id, "awaiting_gender", False)
    await set_user_awaiting(user_id, "awaiting_name", True)
    await send_message_from_callback(callback, NAME_QUESTION)
    await callback.answer()


async def handle_name_message(message: Message, text: str) -> None:
    if message.from_user is None:
        return
    name = text.strip()
    if not name:
        await send_message(message, NAME_QUESTION)
        return
    user_id = message.from_user.id
    await set_user_text_field(user_id, "display_name", name)
    await set_user_awaiting(user_id, "awaiting_name", False)
    await set_user_awaiting(user_id, "awaiting_age", True)
    await send_message(message, AGE_QUESTION)


async def handle_age_message(message: Message, text: str) -> None:
    if message.from_user is None:
        return
    value = text.strip()
    match = re.search(r"\d{1,3}", value)
    if not match:
        await send_message(message, "Пожалуйста, напиши возраст числом.")
        return
    age = int(match.group(0))
    if age < 8 or age > 120:
        await send_message(message, "Похоже, возраст некорректный. Напиши число от 8 до 120.")
        return
    user_id = message.from_user.id
    await set_user_text_field(user_id, "age", age)
    await set_user_awaiting(user_id, "awaiting_age", False)
    await set_user_awaiting(user_id, "awaiting_about", True)
    await send_message(
        message,
        ABOUT_QUESTION,
        reply_markup=about_skip_keyboard(),
    )


async def handle_about_message(message: Message, text: str) -> None:
    if message.from_user is None:
        return
    user_id = message.from_user.id
    await set_user_text_field(user_id, "about", text.strip())
    await set_user_awaiting(user_id, "awaiting_about", False)
    get_memory_store().set_chat_ready(user_id, True)
    await send_message(message, FINAL_TEXT, reply_markup=main_menu_keyboard())


async def handle_about_skip(callback: CallbackQuery) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer()
        return
    user_id = callback.from_user.id
    await set_user_awaiting(user_id, "awaiting_about", False)
    get_memory_store().set_chat_ready(user_id, True)
    await send_message_from_callback(callback, FINAL_TEXT, reply_markup=main_menu_keyboard())
    await callback.answer()
