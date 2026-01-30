import os
import random
import re
from typing import Optional

import tempfile
from pathlib import Path
from uuid import uuid4

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.keyboards import (
    MAIN_MENU_HELP,
    MAIN_MENU_MY_STATE,
    MAIN_MENU_SETTINGS,
    MAIN_MENU_CHAT,
    main_menu_keyboard,
    my_state_keyboard,
    settings_and_data_keyboard,
    reset_confirm_keyboard,
)
from flows.checkin import handle_checkin_callback, start_checkin, handle_checkin_message
from flows.crisis import handle_crisis_message
from flows.export import export_chat
from flows.help import send_help
from flows.onboarding import (
    confirm_consent,
    decline_consent,
    handle_onboarding_callback,
    start_onboarding,
)
from flows.offer import handle_offer_callback, send_offer
from flows.profile import (
    handle_about_message,
    handle_about_skip,
    handle_age_message,
    handle_gender_callback,
    handle_name_message,
    start_profile,
)
from flows.preferences import handle_focus_callback, prompt_focus
from flows.support import handle_support_callback, send_support_menu
from flows.therapy import handle_therapy_message
from services.analytics import log_event
from services.crisis import detect_crisis
from services.messages import send_message, edit_message, send_message_from_callback
from services.message_service import add_message
from services.memory import get_memory_store
from services.stt import stt_is_available, stt_status_message, transcribe_audio
from services.user_service import (
    get_or_create_user,
    touch_user,
    is_rate_limited,
    increment_user_message_counter,
    set_user_awaiting,
    set_user_text_field,
    update_distress,
    update_user_focus,
    delete_user_data,
)


router = Router()
START_CHAT_TEXT = "Расскажите, что происходит сейчас и что вас беспокоит."
GREETING_RESPONSES = (
    "Привет! Если хотите, расскажите, что сейчас важно.",
    "Здравствуйте. Если есть тема для разговора, я слушаю.",
    "Привет. О чем хотите поговорить сегодня?",
    "Здравствуйте! С чего бы вы хотели начать?",
)
GREETING_STATUS_RESPONSES = (
    "Спасибо, что спросили. Я здесь. Как вы себя сейчас чувствуете?",
    "Я на связи. Как у вас сегодня?",
    "Я здесь. Что у вас сейчас на душе?",
)
GREETING_STEMS = ("привет", "здравств", "добро", "hello", "hi", "hey")
SMALLTALK_TOKENS = {
    "как",
    "дела",
    "ты",
    "вы",
    "самочувствие",
    "настроение",
    "поживаешь",
    "поживаете",
}
GREETING_STATUS_PHRASES = (
    "как дела",
    "как ты",
    "как вы",
    "как поживаешь",
    "как поживаете",
)
CAPABILITIES_RESPONSES = (
    "Могу говорить про стресс, тревогу, выгорание, отношения, самооценку, работу, цели, привычки. Что сейчас ближе?",
    "Можем обсудить работу, отношения, тревогу, усталость, сомнения, самооценку. С чего начнем?",
    "Готов говорить о сложных чувствах, выгорании, мотивации, решениях, отношениях, границах. Какая тема важнее?",
    "Я могу помочь с разбором ситуации, чувств, выбора, конфликтов, усталости и тревоги. Что сейчас актуальнее?",
)
TOPIC_INTENT_PATTERNS = (
    re.compile(
        r"^(?:давай|давайте)\s+(?:поговорим|обсудим)\s+"
        r"((?:о|об|про|насчет|на тему)\s+.+)$"
    ),
    re.compile(
        r"^(?:хочу|хотела|хотел|хотел бы|хотела бы|можно|можем|могу)\s+"
        r"(?:поговорить|обсудить)\s+((?:о|об|про|насчет|на тему)\s+.+)$"
    ),
    re.compile(
        r"^(?:поговорим|обсудим)\s+((?:о|об|про|насчет|на тему)\s+.+)$"
    ),
    re.compile(r"^тема\s*[:\-]?\s*(.+)$"),
)
TOPIC_FALLBACK_RESPONSES = (
    "Давайте. С чего бы вы хотели начать?",
    "Хорошо, давайте. Что именно важно обсудить?",
    "Ок, могу помочь. В какой части темы хотите начать?",
)


# --- Command Handlers ---


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    if message.from_user:
        get_or_create_user(message.from_user.id, message.from_user.username)
        get_memory_store().set_chat_ready(message.from_user.id, False)
    await start_onboarding(message)


@router.message(Command("checkin"))
async def cmd_checkin(message: Message) -> None:
    await start_checkin(message)


@router.message(Command("reset"))
async def cmd_reset_prompt(message: Message) -> None:
    await send_message(
        message,
        "Вы уверены, что хотите сбросить всю историю? Это действие необратимо.",
        reply_markup=reset_confirm_keyboard(),
    )


@router.message(Command("export"))
async def cmd_export(message: Message) -> None:
    await export_chat(message)


@router.message(Command("focus"))
async def cmd_focus(message: Message) -> None:
    await prompt_focus(message)


@router.message(Command("support"))
async def cmd_support(message: Message) -> None:
    await send_support_menu(message)


@router.message(Command("tariffs"))
async def cmd_tariffs(message: Message) -> None:
    await send_offer(message)


@router.message(Command("info"))
async def cmd_info(message: Message) -> None:
    await start_profile(message)


# --- Main Menu Button Handlers ---


@router.message(F.text == MAIN_MENU_HELP)
async def on_help_button(message: Message) -> None:
    await send_support_menu(message)


@router.message(F.text == MAIN_MENU_MY_STATE)
async def on_my_state_button(message: Message) -> None:
    await send_message(message, "Выберите действие:", reply_markup=my_state_keyboard())


@router.message(F.text == MAIN_MENU_SETTINGS)
async def on_settings_data_button(message: Message) -> None:
    await send_message(
        message, "Управление данными:", reply_markup=settings_and_data_keyboard()
    )


@router.message(F.text == MAIN_MENU_CHAT)
async def on_chat_button(message: Message) -> None:
    if message.from_user:
        update_user_focus(message.from_user.id, "общее")
        await set_user_awaiting(message.from_user.id, "awaiting_goal", False)
        await set_user_awaiting(message.from_user.id, "awaiting_outcome", False)
        await set_user_awaiting(message.from_user.id, "awaiting_checkin", False)
        get_memory_store().set_chat_ready(message.from_user.id, True)
    await send_message(message, START_CHAT_TEXT, reply_markup=main_menu_keyboard())


# --- Callback Handlers ---


@router.callback_query(F.data == "consent_yes")
async def on_consent_yes(callback: CallbackQuery) -> None:
    if callback.message and callback.from_user:
        await confirm_consent(
            callback.message, user_id=callback.from_user.id
        )
    await callback.answer()


@router.callback_query(F.data == "consent_no")
async def on_consent_no(callback: CallbackQuery) -> None:
    if callback.message:
        await decline_consent(callback.message)
    await callback.answer()


@router.callback_query(F.data.startswith("onboard:"))
async def on_onboard_callback(callback: CallbackQuery) -> None:
    await handle_onboarding_callback(callback)


@router.callback_query(F.data.startswith("offer:"))
async def on_offer_callback(callback: CallbackQuery) -> None:
    await handle_offer_callback(callback)


@router.callback_query(F.data.startswith("profile:gender:"))
async def on_profile_gender(callback: CallbackQuery) -> None:
    parts = (callback.data or "").split(":")
    gender = parts[-1] if len(parts) >= 3 else ""
    if gender not in {"male", "female"}:
        await callback.answer()
        return
    await handle_gender_callback(callback, gender)


@router.callback_query(F.data == "profile:start")
async def on_profile_start(callback: CallbackQuery) -> None:
    if callback.message:
        await start_profile(callback.message)
    await callback.answer()


@router.callback_query(F.data == "profile:skip_about")
async def on_profile_skip_about(callback: CallbackQuery) -> None:
    await handle_about_skip(callback)


@router.callback_query(F.data.startswith("checkin:"))
async def on_checkin_callback(callback: CallbackQuery) -> None:
    if callback.data == "checkin:prompt":
        if callback.message:
            await start_checkin(callback.message)
        await callback.answer()
        return
    await handle_checkin_callback(callback)


@router.callback_query(F.data == "export:start")
async def on_export_callback(callback: CallbackQuery) -> None:
    if callback.message and callback.from_user:
        await export_chat(callback.message, user_id=callback.from_user.id)
    await callback.answer()


@router.callback_query(F.data == "reset:prompt")
async def on_reset_prompt_callback(callback: CallbackQuery) -> None:
    if callback.message:
        await edit_message(
            callback.message,
            "Вы уверены, что хотите сбросить всю историю? Это действие необратимо.",
            reply_markup=reset_confirm_keyboard(),
        )
    await callback.answer()


@router.callback_query(F.data == "reset:do")
async def on_reset_do_callback(callback: CallbackQuery) -> None:
    if callback.from_user:
        delete_user_data(callback.from_user.id)
        log_event("reset", callback.from_user.id)
    if callback.message:
        await edit_message(callback.message, "Контекст сброшен.")
    await callback.answer()


@router.callback_query(F.data == "menu:cancel")
async def on_menu_cancel(callback: CallbackQuery) -> None:
    if callback.message:
        await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data.startswith("support:"))
async def on_support_callback(callback: CallbackQuery) -> None:
    await handle_support_callback(callback)


@router.callback_query(F.data == "stt:check")
async def on_stt_check(callback: CallbackQuery) -> None:
    ok, message = stt_status_message()
    await send_message_from_callback(callback, message)
    await callback.answer()


@router.callback_query(F.data.startswith("focus:"))
async def on_focus_callback(callback: CallbackQuery) -> None:
    if callback.data == "focus:prompt":
        if callback.message:
            await prompt_focus(callback.message)
        await callback.answer()
        return
    await handle_focus_callback(callback)


# --- Main Message Handler ---


async def _handle_user_text(message: Message, text: str, *, skip_intents: bool = False) -> None:
    user_id = message.from_user.id if message.from_user else 0
    if not user_id:
        return

    text = (text or "").strip()
    if not text:
        return
    if text.startswith("/"):
        return
    if text in {MAIN_MENU_HELP, MAIN_MENU_MY_STATE, MAIN_MENU_SETTINGS, MAIN_MENU_CHAT}:
        return

    if not skip_intents and _is_presence_check(text):
        await send_message(
            message,
            "Да, я на связи. Можете написать, что вас волнует, или задать вопрос — я отвечу.",
        )
        return

    user = get_or_create_user(user_id, message.from_user.username if message.from_user else None)

    if is_rate_limited(user, min_interval_seconds=1.2):
        await send_message(
            message, "Слишком часто. Подождите пару секунд и попробуйте снова."
        )
        return
    await touch_user(user_id)

    if detect_crisis(text):
        log_event("crisis_detected", user_id)
        await handle_crisis_message(message)
        return

    if user.awaiting_gender:
        await start_profile(message)
        return

    if user.awaiting_name:
        await handle_name_message(message, text)
        return

    if user.awaiting_age:
        await handle_age_message(message, text)
        return

    if user.awaiting_about:
        await handle_about_message(message, text)
        return

    if user.awaiting_checkin:
        await handle_checkin_message(message)
        return

    if user.awaiting_goal:
        await set_user_text_field(user_id, "session_goal", text)
        await set_user_awaiting(user_id, "awaiting_goal", False)
        get_memory_store().set_chat_ready(user_id, True)
        add_message(user_id, "user", f"Цель сессии: {text}")
        add_message(user_id, "assistant", START_CHAT_TEXT)
        await send_message(message, START_CHAT_TEXT)
        return

    if user.awaiting_outcome:
        await set_user_text_field(user_id, "last_outcome", text)
        await set_user_awaiting(user_id, "awaiting_outcome", False)
        response_text = "Записал. Мы можем продолжить в любое время."
        add_message(user_id, "user", f"Итог: {text}")
        add_message(user_id, "assistant", response_text)
        await send_message(message, response_text)
        return

    if not skip_intents:
        if _is_capabilities_request(text):
            response_text = _select_capabilities_reply()
            add_message(user_id, "user", text)
            log_event("message_user", user_id, length=len(text))
            await increment_user_message_counter(user_id)
            add_message(user_id, "assistant", response_text)
            log_event("message_bot", user_id, length=len(response_text))
            log_event("capabilities_intent", user_id)
            await send_message(message, response_text)
            return

        topic = _extract_topic_request(text)
        if topic:
            response_text = _select_topic_reply(topic)
            add_message(user_id, "user", text)
            log_event("message_user", user_id, length=len(text))
            await increment_user_message_counter(user_id)
            add_message(user_id, "assistant", response_text)
            log_event("message_bot", user_id, length=len(response_text))
            log_event("topic_intent", user_id, topic=topic)
            await send_message(message, response_text)
            return

        if _is_greeting(text):
            response_text = _select_greeting_reply(text)
            add_message(user_id, "user", text)
            log_event("message_user", user_id, length=len(text))
            await increment_user_message_counter(user_id)
            add_message(user_id, "assistant", response_text)
            log_event("message_bot", user_id, length=len(response_text))
            await send_message(message, response_text)
            return

    is_distress = await update_distress(user_id, user, detect_crisis(text))
    if is_distress:
        await send_message(message, "Похоже, сейчас непросто. Хотите короткую поддержку?")
        await send_support_menu(message)
        return  # Potentially pause the main therapy flow if we offer support

    await handle_therapy_message(message, text_override=text)


def _normalize_intent_text(text: str) -> str:
    raw = (text or "").strip().lower()
    if not raw:
        return ""
    cleaned = re.sub(r"[^\w\s]", "", raw)
    return " ".join(cleaned.split())


def _is_presence_check(text: str) -> bool:
    cleaned = _normalize_intent_text(text)
    if not cleaned:
        return False
    if len(cleaned) > 80:
        return False
    direct_phrases = (
        "ты работаешь",
        "ты тут",
        "ты здесь",
        "ты на связи",
        "ты онлайн",
        "ты живой",
        "бот работает",
        "ты слышишь",
        "ты отвечаешь",
    )
    if any(phrase in cleaned for phrase in direct_phrases):
        return True
    if cleaned in {"проверка", "тест", "алло", "ало", "есть кто"}:
        return True
    return False


def _is_greeting(text: str) -> bool:
    cleaned = _normalize_intent_text(text)
    if not cleaned or len(cleaned) > 60:
        return False
    tokens = cleaned.split()
    if not tokens:
        return False
    has_greeting = any(token.startswith(GREETING_STEMS) for token in tokens)
    for token in tokens:
        if token.startswith(GREETING_STEMS):
            continue
        if token in SMALLTALK_TOKENS:
            continue
        return False
    if has_greeting:
        return True
    return cleaned in GREETING_STATUS_PHRASES


def _select_greeting_reply(text: str) -> str:
    cleaned = _normalize_intent_text(text)
    if any(phrase in cleaned for phrase in GREETING_STATUS_PHRASES):
        return random.choice(GREETING_STATUS_RESPONSES)
    return random.choice(GREETING_RESPONSES)


def _is_capabilities_request(text: str) -> bool:
    cleaned = _normalize_intent_text(text)
    if not cleaned or len(cleaned) > 160:
        return False
    if any(
        phrase in cleaned
        for phrase in (
            "какие темы",
            "на какие темы",
            "темы для разговора",
            "темы для беседы",
            "о чем можем поговорить",
            "о чем можно поговорить",
            "о чем вы можете поговорить",
            "о чем ты можешь поговорить",
        )
    ):
        return True
    if "на тему" in cleaned and any(
        phrase in cleaned
        for phrase in (
            "можешь поговорить",
            "можете поговорить",
            "можем поговорить",
            "можно поговорить",
            "можешь обсудить",
            "можете обсудить",
            "можем обсудить",
            "можно обсудить",
        )
    ):
        return True
    if any(
        phrase in cleaned
        for phrase in (
            "что ты можешь",
            "что вы можете",
            "что ты умеешь",
            "что вы умеете",
        )
    ) and any(word in cleaned for word in ("поговорить", "обсудить", "помочь")):
        return True
    return False


def _select_capabilities_reply() -> str:
    return random.choice(CAPABILITIES_RESPONSES)


def _extract_topic_request(text: str) -> Optional[str]:
    cleaned = _normalize_intent_text(text)
    if not cleaned or len(cleaned) > 180:
        return None
    for pattern in TOPIC_INTENT_PATTERNS:
        match = pattern.match(cleaned)
        if match:
            topic = (match.group(1) or "").strip()
            topic = topic.strip(" .!?\"'“”«»")
            if topic:
                if len(topic) > 120:
                    topic = topic[:120].rstrip()
                return topic
    return None


def _select_topic_reply(topic: Optional[str]) -> str:
    if topic:
        options = (
            f"Давайте. {topic} — что в этом сейчас самое важное?",
            f"Ок, можем. Что именно {topic} хочется обсудить в первую очередь?",
            f"Хорошо. В теме «{topic}» что больше всего беспокоит или занимает?",
            f"Давайте поговорим. С какой стороны {topic} хочется начать?",
        )
        return random.choice(options)
    return random.choice(TOPIC_FALLBACK_RESPONSES)


@router.message(F.text)
async def on_text_message(message: Message) -> None:
    await _handle_user_text(message, message.text or "", skip_intents=False)


@router.message(F.voice)
async def on_voice_message(message: Message) -> None:
    if message.voice is None:
        return
    if not stt_is_available():
        await send_message(
            message,
            "Голосовые пока не подключены. Нужны ffmpeg и модель Vosk (VOSK_MODEL_PATH).",
        )
        return
    tmp_dir = Path(tempfile.gettempdir()) / "psiholog_voice"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tmp_path = tmp_dir / f"voice_{uuid4().hex}.ogg"
    try:
        await message.bot.download(message.voice, destination=tmp_path)
        text = await transcribe_audio(tmp_path, language="ru")
    finally:
        try:
            tmp_path.unlink()
        except OSError:
            pass
    if not text:
        await send_message(
            message,
            "Не получилось распознать голосовое. Попробуйте еще раз или напишите текстом.",
        )
        return
    cleaned = text.strip()
    if os.getenv("STT_ECHO", "").strip() == "1":
        await send_message(message, f"🎤 Я услышал: «{cleaned}»")
    await _handle_user_text(message, text, skip_intents=True)


@router.message()
async def on_non_text_message(message: Message) -> None:
    await send_message(message, "Пожалуйста, отправьте текстовое сообщение.")
