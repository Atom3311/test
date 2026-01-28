from __future__ import annotations

import logging
from typing import Optional

from supabase import Client, create_client

from config import load_settings

_db_client: Optional[Client] = None
_db_error: Optional[Exception] = None


def get_db_client() -> Client:
    client = get_db_client_optional()
    if client is None:
        raise RuntimeError("Supabase client is not available") from _db_error
    return client


def get_db_client_optional() -> Optional[Client]:
    global _db_client, _db_error
    if _db_client is not None:
        return _db_client
    if _db_error is not None:
        return None
    settings = load_settings()
    if not settings.supabase_url or not settings.supabase_key:
        _db_error = RuntimeError("Supabase credentials are missing")
        return None
    try:
        _db_client = create_client(settings.supabase_url, settings.supabase_key)
    except Exception as exc:
        _db_error = exc
        logging.getLogger(__name__).warning("Supabase disabled: %s", exc)
        return None
    return _db_client


def disable_db(exc: Exception) -> None:
    global _db_client, _db_error
    _db_client = None
    _db_error = exc
    logging.getLogger(__name__).warning("Supabase disabled after error: %s", exc)
