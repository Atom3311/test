from typing import Optional

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
from flows.onboarding import confirm_consent, decline_consent, start_onboarding
from flows.preferences import handle_focus_callback, prompt_focus
from flows.support import handle_support_callback, send_support_menu
from flows.therapy import handle_therapy_message
from services.analytics import log_event
from services.crisis import detect_crisis
from services.messages import send_message, edit_message
from services.memory import get_memory_store
from services.user_service import (
    get_or_create_user,
    touch_user,
    is_rate_limited,
    set_user_awaiting,
    set_user_text_field,
    update_distress,
    update_user_focus,
    delete_user_data,
)


router = Router()
START_CHAT_TEXT = "Расскажите, что происходит сейчас и что вас беспокоит."
CHOOSE_ACTION_TEXT = "Выберите тему разговора или нажмите «Общение»."


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
        await set_user_awaiting(callback.from_user.id, "awaiting_goal", True)
        await confirm_consent(
            callback.message, user_id=callback.from_user.id
        )
    await callback.answer()


@router.callback_query(F.data == "consent_no")
async def on_consent_no(callback: CallbackQuery) -> None:
    if callback.message:
        await decline_consent(callback.message)
    await callback.answer()


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


@router.callback_query(F.data.startswith("focus:"))
async def on_focus_callback(callback: CallbackQuery) -> None:
    if callback.data == "focus:prompt":
        if callback.message:
            await prompt_focus(callback.message)
        await callback.answer()
        return
    await handle_focus_callback(callback)


# --- Main Message Handler ---


@router.message(F.text)
async def on_text_message(message: Message) -> None:
    user_id = message.from_user.id if message.from_user else 0
    if not user_id:
        return

    text = (message.text or "").strip()
    if text.startswith("/"):
        return
    if text in {MAIN_MENU_HELP, MAIN_MENU_MY_STATE, MAIN_MENU_SETTINGS, MAIN_MENU_CHAT}:
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

    if user.awaiting_checkin:
        await handle_checkin_message(message)
        return

    if user.awaiting_goal:
        await set_user_text_field(user_id, "session_goal", text)
        await set_user_awaiting(user_id, "awaiting_goal", False)
        get_memory_store().set_chat_ready(user_id, True)
        await send_message(message, START_CHAT_TEXT)
        return

    if user.awaiting_outcome:
        await set_user_text_field(user_id, "last_outcome", text)
        await set_user_awaiting(user_id, "awaiting_outcome", False)
        await send_message(message, "Записал. Мы можем продолжить в любое время.")
        return

    if not get_memory_store().is_chat_ready(user_id):
        await send_message(
            message,
            CHOOSE_ACTION_TEXT,
            reply_markup=main_menu_keyboard(),
        )
        return

    is_distress = await update_distress(user_id, user, detect_crisis(text))
    if is_distress:
        await send_message(message, "Похоже, сейчас непросто. Хотите короткую поддержку?")
        await send_support_menu(message)
        return  # Potentially pause the main therapy flow if we offer support

    await handle_therapy_message(message)


@router.message()
async def on_non_text_message(message: Message) -> None:
    await send_message(message, "Пожалуйста, отправьте текстовое сообщение.")
