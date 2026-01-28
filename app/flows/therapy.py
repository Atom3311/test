from aiogram.types import Message

from bot.keyboards import checkin_start_keyboard
from services.analytics import log_event
from services.llm import generate_response, generate_summary
from services.messages import send_message
from services.message_service import add_message, get_last_n_messages
from services.emoji import decorate_text, select_emoji
from services.user_service import (
    get_or_create_user,
    increment_user_message_counter,
    update_user_summary,
    User,
)
from services.prompts import (
    SUMMARY_SYSTEM_PROMPT,
    THERAPY_SYSTEM_PROMPT,
    build_summary_prompt,
    build_therapy_prompt,
)
from services.rag import build_context

SUMMARY_EVERY_N_MESSAGES = 6
CHECKIN_INTERVAL_DAYS = 3
CHECKIN_PROMPT_COOLDOWN_HOURS = 12
HISTORY_LIMIT = 10


def _decorate_therapy_response(user_id: int, text: str) -> str:
    labels = [
        ("Что я понял", "info"),
        ("Вопрос", "question"),
        ("Следующий шаг", "support:general"),
        ("Мини-упражнение", "checkin"),
    ]
    updated = text
    replaced = False
    for label, kind in labels:
        needle = f"{label}:"
        if needle in updated:
            emoji = select_emoji(user_id, label, kind=kind)
            updated = updated.replace(needle, f"{emoji} {needle}")
            replaced = True
    if not replaced:
        updated = decorate_text(user_id, text, kind="support:general")
    return updated


async def handle_therapy_message(message: Message) -> None:
    user_id = message.from_user.id if message.from_user else 0
    text = (message.text or "").strip()

    # Get user state and history from DB
    user = get_or_create_user(user_id)
    history = get_last_n_messages(user_id, n=HISTORY_LIMIT)

    # Append user message to history
    add_message(user_id, "user", text)
    log_event("message_user", user_id, length=len(text))
    await increment_user_message_counter(user_id)
    # Manually increment counter on the user object to avoid another DB call
    user.messages_since_summary += 1

    # Convert Message objects to dictionaries for the prompt builder
    history_for_prompt = [
        {"role": msg.role, "content": msg.content} for msg in history
    ]

    # RAG context is not yet migrated, so it will not work correctly
    # context = build_context(user) # This needs to be adapted for the User object
    context = ""

    prompt = build_therapy_prompt(
        context=context,
        summary=user.summary,
        history=history_for_prompt,
        user_text=text,
        focus=user.focus,
        session_goal=user.session_goal,
        last_outcome=user.last_outcome,
    )
    response = await generate_response(prompt=prompt, system_prompt=THERAPY_SYSTEM_PROMPT)
    if message.from_user:
        response = _decorate_therapy_response(message.from_user.id, response)
    await send_message(message, response)

    # Append assistant message to history
    add_message(user_id, "assistant", response)
    log_event("message_bot", user_id, length=len(response))

    await _maybe_update_summary(user_id, user)
    # await _maybe_prompt_checkin(message, user) # TODO: Migrate check-in logic


async def _maybe_update_summary(user_id: int, user: User) -> None:
    if user.messages_since_summary < SUMMARY_EVERY_N_MESSAGES:
        return

    history = get_last_n_messages(user_id, n=HISTORY_LIMIT)
    history_for_prompt = [
        {"role": msg.role, "content": msg.content} for msg in history
    ]

    prompt = build_summary_prompt(
        current_summary=user.summary,
        history=history_for_prompt,
    )
    summary = await generate_summary(
        prompt=prompt,
        system_prompt=SUMMARY_SYSTEM_PROMPT,
    )
    if summary:
        await update_user_summary(user_id, summary)


# TODO: Migrate check-in logic from MemoryStore to user_service
# async def _maybe_prompt_checkin(message: Message, user: User) -> None:
#     if not should_prompt_checkin(
#         user,
#         interval_days=CHECKIN_INTERVAL_DAYS,
#         prompt_cooldown_hours=CHECKIN_PROMPT_COOLDOWN_HOURS,
#     ):
#         return
#     mark_checkin_prompted(user.id)
#     await send_message(
#         message,
#         "Кажется, давно не было оценки состояния. Хотите быстро оценить самочувствие?",
#         reply_markup=checkin_start_keyboard(),
#     )
