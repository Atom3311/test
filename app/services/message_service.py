from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Dict, Any

from services.db import get_db_client, disable_db
from services.datetime_utils import parse_db_datetime

MAX_MESSAGE_CHARS = 1200


@dataclass
class Message:
    id: str  # UUID from the database
    user_id: int
    created_at: datetime
    role: str
    content: str

    @staticmethod
    def from_db(data: Dict[str, Any]) -> "Message":
        """Maps a dictionary from the database to a Message dataclass instance."""
        if data.get("created_at"):
            data["created_at"] = parse_db_datetime(data["created_at"])
        return Message(**data)


def add_message(user_id: int, role: str, content: str) -> Message:
    """Adds a new message to the database for a given user."""
    cleaned_content = (content or "").strip()
    if len(cleaned_content) > MAX_MESSAGE_CHARS:
        cleaned_content = cleaned_content[:MAX_MESSAGE_CHARS].rstrip() + "..."

    client = get_db_client()

    try:
        builder = client.table("messages").insert(
            {
                "user_id": user_id,
                "role": role,
                "content": cleaned_content,
            }
        )
        try:
            builder = builder.select("*")
        except AttributeError:
            pass
        response = builder.execute()
    except Exception as e:
        disable_db(e)
        raise

    data = getattr(response, "data", None) if response is not None else None
    if not data:
        raise RuntimeError("Supabase insert did not return message data")

    return Message.from_db(data[0])


def get_last_n_messages(user_id: int, n: int) -> List[Message]:
    """Retrieves the last N messages for a given user, ordered by creation time."""
    client = get_db_client()
    try:
        response = (
            client.table("messages")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(n)
            .execute()
        )
    except Exception as e:
        disable_db(e)
        raise

    data = getattr(response, "data", None) if response is not None else None
    if not data:
        return []

    # The messages are returned in descending order, so we reverse them
    # to get the correct chronological order for the prompt.
    return [Message.from_db(item) for item in reversed(data)]


def get_all_messages(user_id: int, batch_size: int = 500) -> List[Message]:
    """Retrieves all messages for a given user, ordered by creation time."""
    client = get_db_client()
    all_items: List[Message] = []
    offset = 0
    while True:
        try:
            response = (
                client.table("messages")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=False)
                .range(offset, offset + batch_size)
                .execute()
            )
        except Exception as e:
            disable_db(e)
            raise

        data = getattr(response, "data", None) if response is not None else None
        if not data:
            break
        all_items.extend(Message.from_db(item) for item in data)
        if len(data) < batch_size:
            break
        offset += batch_size
    return all_items
