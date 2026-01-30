from pathlib import Path
from typing import Optional

from aiogram.types import CallbackQuery, Message

from bot.keyboards import consent_keyboard, main_menu_keyboard, onboarding_keyboard
from services.messages import (
    delete_tracked_messages,
    send_message,
    send_message_from_callback,
    send_photo,
    send_photo_from_callback,
)
from flows.profile import start_profile
from flows.offer import send_offer_from_callback

BOT_DISPLAY_NAME = "Аврора"
PRIVACY_POLICY_URL = ""

ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets" / "onboarding"
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")
WHY_IMAGE = "why"
METHODS_IMAGE = "methods"
CRISIS_IMAGE = "crisis"
REVIEW_IMAGES = (
    "review_1",
    "review_2",
    "review_3",
    "review_4",
    "review_5",
)

WELCOME_TEXT = (
    "Привет, {user_name}!\n"
    "Я {bot_name}. Я психолог и создала этот чат, чтобы вы могли "
    "конфиденциально делиться тем, что вас беспокоит.\n\n"
    "Пожалуйста, сохраняйте анонимность: не отправляйте личные данные.\n"
    "Работаем только с вашим запросом.\n"
    "Пишите мне текстом или голосом в любое время."
)

WHY_TEXT = (
    "Я здесь, чтобы помогать тебе с повседневными заботами, "
    "справляться с эмоциями и жить более осознанно.\n\n"
    "Для меня не бывает неважных тем и глупых вопросов. "
    "Ты можешь выговориться и получить поддержку без осуждения."
)

TOPICS_TEXT = (
    "Мы можем обсуждать разные темы, например:\n"
    "✓ Как справляться со стрессом\n"
    "✓ Как принимать себя\n"
    "✓ Личные границы и отношения\n"
    "✓ Выгорание и усталость\n"
    "✓ Самооценка, мотивация, работа и учеба\n"
    "… и многое другое."
)

OFFER_NEXT_TEXT = "Перейти к отзывам пользователей?"

REVIEWS_COUNT_TEXT = "Уже более 37 544 человек попробовали этот формат."
REVIEWS_TEXT = (
    "Ниже — несколько отзывов пользователей.\n"
    f"{REVIEWS_COUNT_TEXT}"
)

METHODS_TEXT = (
    "В диалоге я использую проверенные подходы: КПТ, ACT, DBT, "
    "майндфулнес и другие практики.\n\n"
    "Мы будем вместе отслеживать, что реально помогает именно тебе."
)

CRISIS_TEXT = (
    "Я могу дать базовую поддержку и помочь наметить шаги.\n\n"
    "Если ситуация тяжелая, пожалуйста, обращайся к специалистам "
    "или в службы помощи."
)

PRIVACY_TEXT = (
    "🔒 Твои данные защищены и не передаются третьим лицам.\n"
    "Продолжая, ты соглашаешься с политикой конфиденциальности.\n\n"
    "🧾 Ты можешь в любой момент удалить историю командой /reset "
    "и экспортировать данные через /export."
)

FINISH_TEXT = "Мы почти закончили — жми Далее ✨"


def _asset_path(base_name: str) -> Path:
    candidate = ASSETS_DIR / base_name
    if candidate.suffix:
        return candidate
    for ext in IMAGE_EXTENSIONS:
        candidate = ASSETS_DIR / f"{base_name}{ext}"
        if candidate.exists():
            return candidate
    return ASSETS_DIR / f"{base_name}{IMAGE_EXTENSIONS[0]}"


def _user_name_from_message(message: Message) -> str:
    if message.from_user and message.from_user.first_name:
        return message.from_user.first_name
    return "друг"


def _user_name_from_callback(callback: CallbackQuery) -> str:
    if callback.from_user and callback.from_user.first_name:
        return callback.from_user.first_name
    return "друг"


async def _send_photo_or_text(
    message: Message,
    filename: str,
    text: str,
    *,
    reply_markup=None,
) -> None:
    path = _asset_path(filename)
    if path.exists():
        await send_photo(message, path, caption=text, reply_markup=reply_markup)
    else:
        await send_message(message, text, reply_markup=reply_markup)


async def _send_photo_or_text_from_callback(
    callback: CallbackQuery,
    filename: str,
    text: str,
    *,
    reply_markup=None,
) -> None:
    path = _asset_path(filename)
    if path.exists():
        await send_photo_from_callback(
            callback, path, caption=text, reply_markup=reply_markup
        )
    else:
        await send_message_from_callback(callback, text, reply_markup=reply_markup)


async def _send_review_images_from_callback(callback: CallbackQuery) -> None:
    for idx, name in enumerate(REVIEW_IMAGES, start=1):
        path = _asset_path(name)
        if path.exists():
            await send_photo_from_callback(callback, path)
        else:
            await send_message_from_callback(callback, f"Отзыв {idx}")


async def start_onboarding(message: Message) -> None:
    user_name = _user_name_from_message(message)
    text = WELCOME_TEXT.format(user_name=user_name, bot_name=BOT_DISPLAY_NAME)
    await send_message(
        message,
        text,
        reply_markup=onboarding_keyboard(
            "Зачем мне это?", "onboard:why", skip_text="Пропустить знакомство"
        ),
    )


async def handle_onboarding_callback(callback: CallbackQuery) -> None:
    data = callback.data or ""
    if data == "onboard:why":
        await _send_photo_or_text_from_callback(
            callback,
            WHY_IMAGE,
            WHY_TEXT,
            reply_markup=onboarding_keyboard(
                "Что мы можем обсудить?", "onboard:topics"
            ),
        )
    elif data == "onboard:topics":
        await send_message_from_callback(
            callback,
            TOPICS_TEXT,
            reply_markup=onboarding_keyboard(
                "Тарифы и оплата", "onboard:offer"
            ),
        )
    elif data == "onboard:offer":
        await send_offer_from_callback(callback)
        await send_message_from_callback(
            callback,
            OFFER_NEXT_TEXT,
            reply_markup=onboarding_keyboard(
                "Отзывы пользователей", "onboard:reviews"
            ),
        )
    elif data == "onboard:reviews":
        await send_message_from_callback(callback, REVIEWS_TEXT)
        await _send_review_images_from_callback(callback)
        await send_message_from_callback(
            callback,
            "Продолжим?",
            reply_markup=onboarding_keyboard(
                "Какие методики ты используешь?", "onboard:methods"
            ),
        )
    elif data == "onboard:methods":
        await _send_photo_or_text_from_callback(
            callback,
            METHODS_IMAGE,
            METHODS_TEXT,
            reply_markup=onboarding_keyboard(
                "А если у меня тяжелая ситуация?", "onboard:crisis"
            ),
        )
    elif data in {"onboard:crisis", "onboard:ai"}:
        await _send_photo_or_text_from_callback(
            callback,
            CRISIS_IMAGE,
            CRISIS_TEXT,
            reply_markup=onboarding_keyboard(
                "Ок. А мои данные в безопасности?", "onboard:privacy"
            ),
        )
    elif data in {"onboard:privacy", "onboard:skip"}:
        await send_message_from_callback(callback, PRIVACY_TEXT)
        if PRIVACY_POLICY_URL:
            await send_message_from_callback(callback, PRIVACY_POLICY_URL)
        await send_message_from_callback(
            callback, FINISH_TEXT, reply_markup=consent_keyboard()
        )
    await callback.answer()


async def confirm_consent(message: Message, user_id: Optional[int] = None) -> None:
    await start_profile(message)
    await delete_tracked_messages(message, user_id=user_id)


async def decline_consent(message: Message) -> None:
    await send_message(
        message,
        "Хорошо. Если захотите вернуться, нажмите /start в любое время.",
        reply_markup=main_menu_keyboard(),
    )
