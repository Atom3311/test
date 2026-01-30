from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

# --- Reply Keyboard (Main Menu) ---
MAIN_MENU_MY_STATE = "🧠 Моё состояние"
MAIN_MENU_HELP = "🚑 Быстрая помощь"
MAIN_MENU_SETTINGS = "⚙️ Настройки и данные"
MAIN_MENU_CHAT = "💬 Беседа"

# --- Inline Keyboard Actions & Labels ---
SUPPORT_MENU_BREATH = "Дыхание 4-6"
SUPPORT_MENU_GROUND = "Упражнение 5-4-3-2-1"
SUPPORT_MENU_COMPASSION = "Добрые слова себе"
CONSENT_YES_TEXT = "Далее"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """A single, stable main menu for the bot."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=MAIN_MENU_MY_STATE),
                KeyboardButton(text=MAIN_MENU_HELP),
            ],
            [
                KeyboardButton(text=MAIN_MENU_CHAT),
                KeyboardButton(text=MAIN_MENU_SETTINGS),
            ],
        ],
        resize_keyboard=True,
    )


def my_state_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard for state-related actions."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Оценить состояние", callback_data="checkin:prompt"
                )
            ],
        ]
    )


def settings_and_data_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard for settings and data management."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Анкета", callback_data="profile:start")],
            [InlineKeyboardButton(text="Изменить тему", callback_data="focus:prompt")],
            [InlineKeyboardButton(text="Проверить голосовые", callback_data="stt:check")],
            [InlineKeyboardButton(text="Экспорт данных", callback_data="export:start")],
            [
                InlineKeyboardButton(
                    text="Сбросить переписку", callback_data="reset:prompt"
                )
            ],
        ]
    )


def reset_confirm_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard to confirm a destructive reset action."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔴 Да, сбросить", callback_data="reset:do"),
                InlineKeyboardButton(text="Отмена", callback_data="menu:cancel"),
            ]
        ]
    )


def consent_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=CONSENT_YES_TEXT, callback_data="consent_yes")],
        ]
    )


def onboarding_keyboard(
    primary_text: str,
    primary_callback: str,
    *,
    skip_text: str = "Пропустить",
    skip_callback: str = "onboard:skip",
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=primary_text, callback_data=primary_callback)],
            [InlineKeyboardButton(text=skip_text, callback_data=skip_callback)],
        ]
    )


def checkin_scale_keyboard(metric: str) -> InlineKeyboardMarkup:
    rows = []
    current_row = []
    for value in range(0, 11):
        current_row.append(
            InlineKeyboardButton(
                text=str(value),
                callback_data=f"checkin:{metric}:{value}",
            )
        )
        if len(current_row) == 6:
            rows.append(current_row)
            current_row = []
    if current_row:
        rows.append(current_row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def checkin_start_keyboard() -> InlineKeyboardMarkup:
    """Offers to start a check-in flow via an inline button."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Оценить состояние",
                    callback_data="checkin:prompt",
                )
            ]
        ]
    )


def focus_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Тревога", callback_data="focus:select:anxiety")],
            [InlineKeyboardButton(text="Выгорание", callback_data="focus:select:burnout")],
            [
                InlineKeyboardButton(
                    text="Отношения", callback_data="focus:select:relationships"
                )
            ],
            [InlineKeyboardButton(text="Общее", callback_data="focus:select:general")],
        ]
    )


def support_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=SUPPORT_MENU_BREATH, callback_data="support:breath")],
            [InlineKeyboardButton(text=SUPPORT_MENU_GROUND, callback_data="support:ground")],
            [
                InlineKeyboardButton(
                    text=SUPPORT_MENU_COMPASSION, callback_data="support:compassion"
                )
            ],
        ]
    )


def gender_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Мужчина", callback_data="profile:gender:male"),
                InlineKeyboardButton(text="Женщина", callback_data="profile:gender:female"),
            ],
        ]
    )


def about_skip_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Заполню позже 🙂", callback_data="profile:skip_about")]
        ]
    )


def offer_keyboard(
    *,
    pay_ru_url: str = "",
    pay_intl_url: str = "",
    support_url: str = "",
) -> InlineKeyboardMarkup:
    rows = []
    if pay_ru_url:
        rows.append(
            [InlineKeyboardButton(text="Купить (из России)", url=pay_ru_url)]
        )
    else:
        rows.append(
            [InlineKeyboardButton(text="Купить (из России)", callback_data="offer:pay:ru")]
        )
    if pay_intl_url:
        rows.append(
            [InlineKeyboardButton(text="Купить (не из России)", url=pay_intl_url)]
        )
    else:
        rows.append(
            [
                InlineKeyboardButton(
                    text="Купить (не из России)", callback_data="offer:pay:intl"
                )
            ]
        )
    if support_url:
        rows.append([InlineKeyboardButton(text="Техподдержка", url=support_url)])
    else:
        rows.append(
            [InlineKeyboardButton(text="Техподдержка", callback_data="offer:support")]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)
