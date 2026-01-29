from pathlib import Path
from typing import Any, Optional, Union

from aiogram.types import CallbackQuery, Message, FSInputFile

from services.memory import get_memory_store


def _record_message(user_id: Optional[int], message_id: int) -> None:
    if user_id is None:
        return
    store = get_memory_store()
    store.add_bot_message_id(user_id, message_id)


async def send_message(
    message: Message, text: str, *, track: bool = True, **kwargs: Any
) -> Message:
    sent = await message.answer(text, **kwargs)
    if track:
        _record_message(
            message.from_user.id if message.from_user else None, sent.message_id
        )
    return sent


async def send_photo(
    message: Message,
    photo: Union[str, Path],
    *,
    caption: Optional[str] = None,
    track: bool = True,
    **kwargs: Any,
) -> Message:
    path = Path(photo)
    sent = await message.answer_photo(
        FSInputFile(path), caption=caption, **kwargs
    )
    if track:
        _record_message(
            message.from_user.id if message.from_user else None, sent.message_id
        )
    return sent


async def send_message_from_callback(
    callback: CallbackQuery, text: str, *, track: bool = True, **kwargs: Any
) -> Optional[Message]:
    if callback.message is None:
        return None
    sent = await callback.message.answer(text, **kwargs)
    if track:
        _record_message(
            callback.from_user.id if callback.from_user else None, sent.message_id
        )
    return sent


async def send_photo_from_callback(
    callback: CallbackQuery,
    photo: Union[str, Path],
    *,
    caption: Optional[str] = None,
    track: bool = True,
    **kwargs: Any,
) -> Optional[Message]:
    if callback.message is None:
        return None
    path = Path(photo)
    sent = await callback.message.answer_photo(
        FSInputFile(path), caption=caption, **kwargs
    )
    if track:
        _record_message(
            callback.from_user.id if callback.from_user else None, sent.message_id
        )
    return sent


async def send_document(
    message: Message, document: Any, *, track: bool = True, **kwargs: Any
) -> Message:
    sent = await message.answer_document(document, **kwargs)
    if track:
        _record_message(
            message.from_user.id if message.from_user else None, sent.message_id
        )
    return sent


async def delete_tracked_messages(
    message: Message, user_id: Optional[int] = None
) -> None:
    if user_id is None and message.from_user is None:
        return
    resolved_user_id = user_id if user_id is not None else message.from_user.id
    store = get_memory_store()
    memory = store.get(resolved_user_id)
    for msg_id in memory.bot_message_ids:
        try:
            await message.bot.delete_message(message.chat.id, msg_id)
        except Exception:
            continue
    store.clear_bot_message_ids(resolved_user_id)


async def edit_message(
    message: Message, text: str, **kwargs: Any
) -> Message:
    return await message.edit_text(text, **kwargs)
