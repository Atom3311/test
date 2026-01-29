from aiogram.types import CallbackQuery, Message

from bot.keyboards import checkin_scale_keyboard
from services.messages import send_message
from services.analytics import log_event
from services.checkin import parse_checkin
from services.checkin_service import add_checkin
from services.message_service import add_message
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


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def build_checkin_feedback(mood: int, anxiety: int, energy: int) -> str:
    actions: list[str] = []
    reflections: list[str] = []

    if anxiety >= 7:
        actions.append("2-3 минуты дыхания 4-6 или упражнение 5-4-3-2-1.")
        reflections.append(
            "Что именно сейчас тревожит и что из этого под вашим контролем?"
        )
    if mood <= 3:
        actions.append(
            "Очень маленький шаг заботы о себе: вода, душ, короткая прогулка."
        )
        reflections.append("Что обычно дает вам хоть немного облегчения?")
    if energy <= 3:
        actions.append(
            "Проверьте базовые вещи: сон, еда, вода, короткая пауза 10-15 минут."
        )
        reflections.append(
            "Что сейчас забирает больше всего сил и что можно отложить?"
        )
    if mood >= 7 and anxiety <= 3 and energy >= 7:
        actions.append("Сохраните то, что помогло сегодня, и повторите это завтра.")
        reflections.append("Что из сегодняшнего стоит закрепить как привычку?")

    if not actions:
        actions.append(
            "Сделайте короткую паузу и отметьте дыхание и ощущения в теле."
        )
        reflections.append("Что могло повлиять на эти оценки сегодня?")

    actions = _dedupe(actions)[:2]
    reflections = _dedupe(reflections)[:2]

    parts = [
        f"Записал: настроение {mood}/10, тревога {anxiety}/10, энергия {energy}/10.",
        "Что можно сделать сейчас:",
    ]
    parts.extend(f"- {item}" for item in actions)
    parts.append("О чем подумать:")
    parts.extend(f"- {item}" for item in reflections)
    parts.append("Если хотите, можем обсудить подробнее.")
    return "\n".join(parts)


def _checkin_history_text(mood: int, anxiety: int, energy: int) -> str:
    return (
        f"Чек-ин: настроение {mood}/10, тревога {anxiety}/10, энергия {energy}/10."
    )


def _record_checkin_history(
    user_id: int, mood: int, anxiety: int, energy: int, response_text: str
) -> None:
    add_message(user_id, "user", _checkin_history_text(mood, anxiety, energy))
    add_message(user_id, "assistant", response_text)


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
    response_text = build_checkin_feedback(mood, anxiety, energy)
    await send_message(message, response_text)
    if message.from_user:
        _record_checkin_history(user_id, mood, anxiety, energy, response_text)


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
        response_text = build_checkin_feedback(mood, anxiety, energy)
        await callback.message.edit_text(response_text)
        _record_checkin_history(user_id, mood, anxiety, energy, response_text)
        await callback.answer()
        return

    await callback.answer()
