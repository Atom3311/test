from aiogram.types import CallbackQuery, Message

from bot.keyboards import checkin_scale_keyboard
from services.messages import send_message
from services.analytics import log_event
from services.checkin import parse_checkin
from services.checkin_service import add_checkin
from services.memory import get_memory_store
from services.user_service import set_user_awaiting

CHECKIN_PROMPT = (
    "Давайте короткую оценку состояния. Оцените по шкале 0-10:\n"
    "1) настроение\n"
    "2) тревога\n"
    "3) энергия\n"
    "Можно написать так: 6/4/5"
)

CHECKIN_MOOD_TEXT = "Оцените настроение (0-10)."
CHECKIN_ANXIETY_TEXT = "Оцените тревогу (0-10)."
CHECKIN_ENERGY_TEXT = "Оцените энергию (0-10)."


async def start_checkin(message: Message) -> None:
    store = get_memory_store()
    if message.from_user:
        user_id = message.from_user.id
        store.clear_transient_state(user_id)
        await set_user_awaiting(user_id, "awaiting_checkin", True)
        store.clear_pending_checkin(user_id)
        store.set_pending_checkin_stage(user_id, "mood")
        log_event("checkin_start", user_id)
    await send_message(
        message,
        CHECKIN_MOOD_TEXT,
        reply_markup=checkin_scale_keyboard("mood"),
    )


async def handle_checkin_message(message: Message) -> None:
    text = message.text or ""
    parsed = parse_checkin(text)
    if not parsed:
        await send_message(
            message,
            "Не получилось распознать значения. Напишите три числа от 0 до 10, "
            "например: 6/4/5"
        )
        return
    mood, anxiety, energy = parsed
    store = get_memory_store()
    if message.from_user:
        user_id = message.from_user.id
        add_checkin(user_id, mood=mood, anxiety=anxiety, energy=energy)
        await set_user_awaiting(user_id, "awaiting_checkin", False)
        store.clear_pending_checkin(user_id)
        log_event(
            "checkin_saved",
            user_id,
            mood=mood,
            anxiety=anxiety,
            energy=energy,
        )
    await send_message(
        message,
        "Записал. Хотите обсудить, что повлияло на эти оценки?"
    )


async def handle_checkin_callback(callback: CallbackQuery) -> None:
    data = callback.data or ""
    parts = data.split(":")
    if len(parts) != 3:
        await callback.answer()
        return
    _, metric, value_str = parts
    try:
        value = int(value_str)
    except ValueError:
        await callback.answer()
        return
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return

    store = get_memory_store()
    user_id = callback.from_user.id
    store.set_pending_checkin_value(user_id, metric, value)

    if metric == "mood":
        store.set_pending_checkin_stage(user_id, "anxiety")
        await callback.message.edit_text(
            CHECKIN_ANXIETY_TEXT,
            reply_markup=checkin_scale_keyboard("anxiety"),
        )
        await callback.answer()
        return
    if metric == "anxiety":
        store.set_pending_checkin_stage(user_id, "energy")
        await callback.message.edit_text(
            CHECKIN_ENERGY_TEXT,
            reply_markup=checkin_scale_keyboard("energy"),
        )
        await callback.answer()
        return
    if metric == "energy":
        memory = store.get(user_id)
        mood = int(memory.pending_checkin_values.get("mood", 0))
        anxiety = int(memory.pending_checkin_values.get("anxiety", 0))
        energy = int(memory.pending_checkin_values.get("energy", 0))
        add_checkin(user_id, mood=mood, anxiety=anxiety, energy=energy)
        await set_user_awaiting(user_id, "awaiting_checkin", False)
        store.clear_pending_checkin(user_id)
        log_event(
            "checkin_saved",
            user_id,
            mood=mood,
            anxiety=anxiety,
            energy=energy,
        )
        await callback.message.edit_text(
            "Записал. Хотите обсудить, что повлияло на эти оценки?"
        )
        await callback.answer()
        return

    await callback.answer()
