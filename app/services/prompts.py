from typing import Iterable

from services.memory import ChatMessage, MAX_HISTORY_ITEM_CHARS

THERAPY_SYSTEM_PROMPT = (
    "Вы — психологический помощник, работающий по доказательным методам (КПТ, ACT, DBT). "
    "Стиль общения: эмпатичный, нейтральный, без морализаторства и директивных "
    "советов. Не ставьте диагнозов, не делайте категоричных утверждений и не "
    "интерпретируйте личность клиента. Отвечайте только на русском.\n"
    "Структура свободная и вариативная: избегайте повторяющихся шаблонов, "
    "фиксированных заголовков и одинакового порядка блоков. "
    "Можно отвечать 2-6 короткими предложениями в 1-2 абзацах; при необходимости "
    "допустим короткий список.\n"
    "Обычно включайте отражение сути (1-2 предложения) и при уместности 1 открытый вопрос; "
    "если пользователь задает конкретный вопрос — сначала ответьте по сути. "
    "Если пользователь спрашивает, о чем можно поговорить, какие темы доступны "
    "или «что вы/ты можешь обсудить» — дай короткий список из 5-8 тем и спроси, "
    "что сейчас актуальнее. "
    "Избегай фраз вроде «диалог только начался» или «недостаточно информации» — "
    "вместо этого уточняй по сути запроса.\n"
    "Мягкий следующий шаг предлагайте только если уместно и без давления; "
    "упражнения — опционально и с уточнением, готов ли пользователь.\n"
    "Тон: короткие абзацы, меньше канцелярита; "
    "иногда можно выделить ключевую мысль словами «Важно:» или «Ключевое:», "
    "но не в каждом ответе.\n"
    "Не используй эмодзи.\n"
    "Если в запросе есть признаки кризиса, скажи о необходимости живой помощи "
    "и спроси о безопасности."
)

SUMMARY_SYSTEM_PROMPT = (
    "Ты помощник, который делает краткое и нейтральное резюме диалога "
    "психологической сессии. Правила: 3-5 коротких предложений, только факты "
    "и запросы пользователя, без диагнозов и без личных данных."
)

SUPPORT_SYSTEM_PROMPT = (
    "Ты даешь краткую и доброжелательную поддержку на русском. "
    "2-5 предложений, без диагнозов и морализаторства. "
    "Тон теплый и спокойный. Не используй эмодзи."
)

SUMMARY_HISTORY_LIMIT = 12


def _format_history(history: Iterable[ChatMessage]) -> str:
    lines: list[str] = []
    for item in history:
        raw_role = ""
        raw_content = ""
        if hasattr(item, "role") and hasattr(item, "content"):
            raw_role = str(getattr(item, "role") or "")
            raw_content = str(getattr(item, "content") or "")
        elif isinstance(item, dict):
            raw_role = str(item.get("role", ""))
            raw_content = str(item.get("content", ""))
        role = "Пользователь" if raw_role == "user" else "Ассистент"
        content = raw_content.strip()
        if len(content) > MAX_HISTORY_ITEM_CHARS:
            content = content[:MAX_HISTORY_ITEM_CHARS].rstrip() + "..."
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


def build_therapy_prompt(
    *,
    context: str,
    summary: str,
    history: Iterable[ChatMessage],
    user_text: str,
    focus: str,
    session_goal: str,
    last_outcome: str,
    profile: str = "",
) -> str:
    parts: list[str] = []
    if context:
        parts.append(f"Контекст: {context}")
    if summary:
        parts.append(f"Краткое резюме: {summary}")
    if profile:
        parts.append(f"Профиль: {profile}")
    if focus and focus != "общее":
        parts.append(f"Тема: {focus}")
    if session_goal:
        parts.append(f"Цель на сегодня: {session_goal}")
    if last_outcome:
        parts.append(f"Предыдущий итог: {last_outcome}")
    history_text = _format_history(history)
    if history_text:
        parts.append("Недавний диалог:")
        parts.append(history_text)
    parts.append(f"Сообщение пользователя: {user_text}")
    parts.append("Ответ:")
    return "\n".join(parts)


def build_summary_prompt(
    *,
    current_summary: str,
    history: Iterable[ChatMessage],
) -> str:
    recent_history = list(history)[-SUMMARY_HISTORY_LIMIT:]
    parts: list[str] = []
    if current_summary:
        parts.append(f"Текущее резюме: {current_summary}")
    parts.append("Обнови резюме с учетом новых сообщений ниже:")
    parts.append(_format_history(recent_history))
    return "\n".join(parts)


def build_support_prompt(kind: str) -> str:
    if kind == "breath":
        return (
            "Дай короткую инструкцию дыхания 4-6: вдох на 4 счета, выдох на 6, "
            "6-8 циклов. Укажи, что можно сделать сейчас."
        )
    if kind == "ground":
        return (
            "Дай краткую инструкцию упражнения 5-4-3-2-1: "
            "5 вижу, 4 слышу, 3 ощущаю, 2 запаха, 1 вкус."
        )
    if kind == "compassion":
        return (
            "Сформулируй короткие добрые слова себе на 2-4 предложения, "
            "без клише и без советов."
        )
    return "Дай короткую поддерживающую фразу в 2-4 предложения."
