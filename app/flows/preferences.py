from aiogram.types import CallbackQuery, Message

from bot.keyboards import focus_keyboard, main_menu_keyboard
from services.messages import send_message, send_message_from_callback
from services.memory import get_memory_store
from services.user_service import update_user_focus

FOCUS_LABELS = {
    "general": "общее",
    "anxiety": "тревога",
    "burnout": "выгорание",
    "relationships": "отношения",
}


async def prompt_focus(message: Message) -> None:
    if message.from_user is None:
        await send_message(message, "Не удалось определить пользователя.")
        return
    await send_message(
        message,
        "Выберите тему разговора.",
        reply_markup=focus_keyboard(),
    )


async def handle_focus_callback(callback: CallbackQuery) -> None:
    data = callback.data or ""
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    parts = data.split(":")
    focus = parts[-1] if parts else ""
    if focus not in FOCUS_LABELS:
        await callback.answer()
        return
    
    update_user_focus(callback.from_user.id, FOCUS_LABELS[focus])
    get_memory_store().set_chat_ready(callback.from_user.id, True)
    await send_message_from_callback(
        callback,
        "Расскажите, что происходит сейчас и что вас беспокоит.",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()
