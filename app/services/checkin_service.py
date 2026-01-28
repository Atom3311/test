from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict

from services.db import get_db_client, disable_db


@dataclass
class Checkin:
    id: str
    user_id: int
    created_at: datetime
    mood: int
    anxiety: int
    energy: int

    @staticmethod
    def from_db(data: Dict[str, Any]) -> "Checkin":
        if data.get("created_at") and isinstance(data["created_at"], str):
            val = data["created_at"]
            if not val.endswith("+00:00"):
                val += "+00:00"
            data["created_at"] = datetime.fromisoformat(val)
        return Checkin(**data)


def add_checkin(user_id: int, mood: int, anxiety: int, energy: int) -> Checkin:
    client = get_db_client()
    try:
        builder = client.table("checkins").insert(
            {
                "user_id": user_id,
                "mood": mood,
                "anxiety": anxiety,
                "energy": energy,
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
    if isinstance(data, list):
        data = data[0] if data else None
    if not data:
        raise RuntimeError("Supabase insert did not return checkin data")
    return Checkin.from_db(data)
