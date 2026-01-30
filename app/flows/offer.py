import os

from aiogram.types import CallbackQuery, Message

from bot.keyboards import offer_keyboard
from services.messages import send_message, send_message_from_callback

OFFER_TEXT = (
    "🌿 Поддержка для разных ситуаций и эмоций.\n"
    "Чтобы чувствовать себя лучше здесь и сейчас.\n\n"
    "📘 ПЕРСОНАЛЬНАЯ ПРОГРАММА.\n"
    "В зависимости от запроса я предлагаю задания, упражнения или мини-сессию.\n\n"
    "💬 НЕОГРАНИЧЕННЫЕ РАЗГОВОРЫ И СОВЕТЫ.\n"
    "Подстраиваюсь под твою жизнь и цели.\n\n"
    "🧘 ПРАКТИКИ ДЛЯ СТРЕССА, ТРЕВОГИ, ВЫГОРАНИЯ, ОТНОШЕНИЙ.\n"
    "Короткие упражнения, чтобы стабилизироваться в моменте.\n\n"
    "👩‍⚕️ В некоторых тарифах доступна консультация психолога в чате.\n\n"
    "🎙 Голосовые сообщения доступны только в платной версии.\n\n"
    "🔥 После оплаты придет код активации — отправь его мне."
)


def _get_offer_urls() -> dict[str, str]:
    return {
        "ru": os.getenv("OFFER_PAY_RU_URL", "").strip(),
        "intl": os.getenv("OFFER_PAY_INTL_URL", "").strip(),
        "support": os.getenv("OFFER_SUPPORT_URL", "").strip(),
    }


def _link_or_fallback(label: str, url: str, support_url: str) -> str:
    if url:
        return f"{label}\n{url}"
    if support_url:
        return (
            "Ссылка пока не настроена.\n"
            f"Напишите в поддержку: {support_url}"
        )
    return "Ссылка пока не настроена."


async def send_offer(message: Message) -> None:
    urls = _get_offer_urls()
    await send_message(
        message,
        OFFER_TEXT,
        reply_markup=offer_keyboard(
            pay_ru_url=urls["ru"],
            pay_intl_url=urls["intl"],
            support_url=urls["support"],
        ),
    )


async def send_offer_from_callback(callback: CallbackQuery) -> None:
    urls = _get_offer_urls()
    await send_message_from_callback(
        callback,
        OFFER_TEXT,
        reply_markup=offer_keyboard(
            pay_ru_url=urls["ru"],
            pay_intl_url=urls["intl"],
            support_url=urls["support"],
        ),
    )


async def handle_offer_callback(callback: CallbackQuery) -> None:
    data = callback.data or ""
    urls = _get_offer_urls()
    if data == "offer:pay:ru":
        await send_message_from_callback(
            callback,
            _link_or_fallback("Ссылка для оплаты из России:", urls["ru"], urls["support"]),
        )
    elif data == "offer:pay:intl":
        await send_message_from_callback(
            callback,
            _link_or_fallback(
                "Ссылка для оплаты из других стран:", urls["intl"], urls["support"]
            ),
        )
    elif data == "offer:support":
        await send_message_from_callback(
            callback,
            _link_or_fallback("Контакт поддержки:", urls["support"], urls["support"]),
        )
    await callback.answer()
