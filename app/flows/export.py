import time
from datetime import timezone
from pathlib import Path
from typing import Optional

from aiogram.types import FSInputFile, Message

from services.analytics import log_event
from services.messages import send_document, send_message
from services.message_service import get_all_messages


def _role_label(role: str) -> str:
    if role == "user":
        return "Пользователь"
    if role == "assistant":
        return "Ассистент"
    return role or "Сообщение"


def _format_ts(value) -> str:
    if hasattr(value, "astimezone") and value.tzinfo is not None:
        return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return str(value)


async def export_chat(message: Message, *, user_id: Optional[int] = None) -> None:
    resolved_user_id = user_id
    if resolved_user_id is None:
        if message.from_user is None:
            await send_message(message, "Не получилось сформировать экспорт.")
            return
        resolved_user_id = message.from_user.id
    if resolved_user_id is None:
        await send_message(message, "Не получилось сформировать экспорт.")
        return

    messages = get_all_messages(resolved_user_id)
    if not messages:
        await send_message(message, "Пока нет данных для экспорта.")
        return

    lines: list[str] = []
    for item in messages:
        ts = _format_ts(item.created_at)
        role = _role_label(item.role)
        lines.append(f"[{ts}] {role}:")
        lines.append(item.content)
        lines.append("")
    export_text = "\n".join(lines).strip() + "\n"

    root_dir = Path(__file__).resolve().parents[2]
    export_dir = root_dir / "data" / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    filename = f"chat_{resolved_user_id}_{int(time.time())}.txt"
    path = export_dir / filename
    path.write_text(export_text, encoding="utf-8")

    await send_document(message, FSInputFile(path))
    log_event("export_chat", resolved_user_id)
