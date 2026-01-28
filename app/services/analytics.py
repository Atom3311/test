import json
import time
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, Optional

DATA_DIR_NAME = "data"
ANALYTICS_FILE_NAME = "analytics.jsonl"


def _hash_user_id(user_id: Optional[int]) -> Optional[str]:
    if user_id is None:
        return None
    digest = sha256(str(user_id).encode("utf-8")).hexdigest()
    return digest[:12]


def log_event(event: str, user_id: Optional[int] = None, **payload: Any) -> None:
    root_dir = Path(__file__).resolve().parents[2]
    data_dir = root_dir / DATA_DIR_NAME
    data_dir.mkdir(parents=True, exist_ok=True)
    path = data_dir / ANALYTICS_FILE_NAME
    record: Dict[str, Any] = {
        "ts": time.time(),
        "event": event,
        "user": _hash_user_id(user_id),
    }
    record.update(payload)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
