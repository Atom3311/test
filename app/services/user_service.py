from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

from postgrest import APIResponse
from services.db import get_db_client, disable_db
from services.datetime_utils import parse_db_datetime


@dataclass
class User:
    id: int
    created_at: datetime
    username: Optional[str] = None
    summary: str = ""
    focus: str = "общее"
    session_goal: str = ""
    last_outcome: str = ""
    awaiting_checkin: bool = False
    awaiting_goal: bool = False
    awaiting_outcome: bool = False
    distress_streak: int = 0
    last_distress_at: Optional[datetime] = None
    last_support_offer_at: Optional[datetime] = None
    last_checkin_prompt_at: Optional[datetime] = None
    last_message_at: Optional[datetime] = None
    messages_since_summary: int = 0
    last_summary_at: Optional[datetime] = None

    @staticmethod
    def from_db(data: Dict[str, Any]) -> "User":
        """Maps a dictionary from the database to a User dataclass instance."""
        for key in [
            "created_at",
            "last_distress_at",
            "last_support_offer_at",
            "last_checkin_prompt_at",
            "last_message_at",
            "last_summary_at",
        ]:
            if data.get(key):
                data[key] = parse_db_datetime(data[key])
        return User(**data)


def _log_db_error(message: str, exc: Exception) -> None:
    print(f"{message}: {exc}")
    disable_db(exc)


def get_or_create_user(user_id: int, username: Optional[str] = None) -> User:
    client = get_db_client()

    # 1. Пытаемся найти пользователя (безопасно)
    try:
        response = (
            client.table("users")
            .select("*")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
    except Exception as e:
        _log_db_error("Ошибка при запросе к БД", e)
        raise

    # 2. Проверяем, получили ли мы данные
    if response is None:
        raise RuntimeError("Supabase returned empty response for user lookup")
    user_data = getattr(response, "data", None)
    if isinstance(user_data, list):
        user_data = user_data[0] if user_data else None

    # 3. Если пользователя нет — создаем его
    if not user_data or "created_at" not in user_data:
        insert_data = {"id": user_id}
        if username:
            insert_data["username"] = username

        try:
            insert_builder = client.table("users").insert(insert_data)
            try:
                insert_builder = insert_builder.select("*")
            except AttributeError:
                pass
            insert_response = insert_builder.execute()
            user_data = getattr(insert_response, "data", None)
            if isinstance(user_data, list):
                user_data = user_data[0] if user_data else None
        except Exception as e:
            _log_db_error("Ошибка при создании пользователя в БД", e)
            raise

        if not user_data or "created_at" not in user_data:
            raise RuntimeError("Supabase insert did not return user data")
        return User.from_db(user_data)

    # 4. Если пользователь есть — возвращаем его
    return User.from_db(user_data)


async def touch_user(user_id: int) -> Optional[APIResponse]:
    """Updates the last_message_at timestamp for a user."""
    client = get_db_client()
    try:
        return client.table("users").update(
            {"last_message_at": datetime.now(timezone.utc).isoformat()}
        ).eq("id", user_id).execute()
    except Exception as e:
        _log_db_error("Ошибка при обновлении пользователя", e)
        raise


def is_rate_limited(user: User, min_interval_seconds: float) -> bool:
    if not user.last_message_at:
        return False
    return (datetime.now(timezone.utc) - user.last_message_at) < timedelta(seconds=min_interval_seconds)


def update_user_focus(user_id: int, new_focus: str) -> Optional[APIResponse]:
    """Updates the focus for a specific user."""
    client = get_db_client()
    try:
        return client.table("users").update({"focus": new_focus}).eq("id", user_id).execute()
    except Exception as e:
        _log_db_error("Ошибка при обновлении темы", e)
        raise


async def update_user_summary(user_id: int, summary: str) -> Optional[APIResponse]:
    """Updates the user's summary, resets the message counter, and updates the timestamp."""
    client = get_db_client()
    try:
        return client.table("users").update(
            {
                "summary": summary,
                "messages_since_summary": 0,
                "last_summary_at": datetime.now(timezone.utc).isoformat(),
            }
        ).eq("id", user_id).execute()
    except Exception as e:
        _log_db_error("Ошибка при обновлении резюме", e)
        raise


async def increment_user_message_counter(user_id: int) -> Optional[APIResponse]:
    """Increments the messages_since_summary counter for a user via RPC."""
    client = get_db_client()
    try:
        return client.rpc("increment_messages_counter", {"user_id_param": user_id}).execute()
    except Exception as e:
        _log_db_error("Ошибка при инкременте счетчика сообщений", e)
        raise


async def set_user_awaiting(user_id: int, field: str, value: bool) -> Optional[APIResponse]:
    """Sets a boolean 'awaiting' field for a user."""
    client = get_db_client()
    try:
        return client.table("users").update({field: value}).eq("id", user_id).execute()
    except Exception as e:
        _log_db_error("Ошибка при обновлении статуса ожидания", e)
        raise


async def set_user_text_field(user_id: int, field: str, value: str) -> Optional[APIResponse]:
    """Sets a text field for a user."""
    client = get_db_client()
    try:
        return client.table("users").update({field: value}).eq("id", user_id).execute()
    except Exception as e:
        _log_db_error("Ошибка при обновлении текстового поля", e)
        raise


def delete_user_data(user_id: int) -> None:
    """Deletes all data associated with a user."""
    client = get_db_client()
    # This will cascade and delete messages as well
    try:
        client.table("users").delete().eq("id", user_id).execute()
    except Exception as e:
        _log_db_error("Ошибка при удалении данных пользователя", e)
        raise


async def update_distress(user_id: int, user: User, is_distress: bool) -> bool:
    """Updates distress streak and returns if support should be offered."""
    client = get_db_client()
    now = datetime.now(timezone.utc)
    
    if not is_distress:
        if user.last_distress_at and (now - user.last_distress_at) > timedelta(hours=12):
            try:
                client.table("users").update({"distress_streak": 0}).eq("id", user_id).execute()
            except Exception as e:
                _log_db_error("Ошибка при обновлении стресса", e)
                raise
        return False

    new_streak = user.distress_streak + 1
    if user.last_distress_at and (now - user.last_distress_at) > timedelta(hours=6):
        new_streak = 1
    
    should_offer = (
        new_streak >= 3
        and (not user.last_support_offer_at or (now - user.last_support_offer_at) > timedelta(hours=12))
    )
    
    update_payload = {
        "distress_streak": new_streak,
        "last_distress_at": now.isoformat(),
    }
    if should_offer:
        update_payload["last_support_offer_at"] = now.isoformat()
        
    try:
        client.table("users").update(update_payload).eq("id", user_id).execute()
        return should_offer
    except Exception as e:
        _log_db_error("Ошибка при обновлении стресса", e)
        raise
