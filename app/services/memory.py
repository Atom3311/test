from __future__ import annotations

import json
import os
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_HISTORY_LIMIT = 8
DEFAULT_METRICS_LIMIT = 50
MAX_MESSAGE_CHARS = 1200
MAX_HISTORY_ITEM_CHARS = 600
DATA_DIR_NAME = "data"
MEMORY_FILE_NAME = "memory.json"
PERSIST_LOCAL_MEMORY = False


@dataclass
class ChatMessage:
    role: str
    content: str
    ts: float

    def to_dict(self) -> Dict[str, object]:
        return {"role": self.role, "content": self.content, "ts": self.ts}

    @staticmethod
    def from_dict(raw: Dict[str, object]) -> "ChatMessage":
        return ChatMessage(
            role=str(raw.get("role", "")),
            content=str(raw.get("content", "")),
            ts=float(raw.get("ts", 0.0)),
        )


@dataclass
class UserMemory:
    summary: str = ""
    history: List[ChatMessage] = field(default_factory=list)
    messages_since_summary: int = 0
    last_message_at: float = 0.0
    awaiting_checkin: bool = False
    awaiting_goal: bool = False
    awaiting_outcome: bool = False
    metrics: List[Dict[str, object]] = field(default_factory=list)
    focus: str = "общее"
    session_goal: str = ""
    last_outcome: str = ""
    distress_streak: int = 0
    last_distress_at: float = 0.0
    last_support_offer_at: float = 0.0
    pending_checkin_stage: str = ""
    pending_checkin_values: Dict[str, int] = field(default_factory=dict)
    last_checkin_prompt_at: float = 0.0
    bot_message_ids: List[int] = field(default_factory=list)
    emoji_pool: List[str] = field(default_factory=list)
    chat_ready: bool = False

    def to_dict(self) -> Dict[str, object]:
        return {
            "summary": self.summary,
            "history": [msg.to_dict() for msg in self.history],
            "messages_since_summary": self.messages_since_summary,
            "last_message_at": self.last_message_at,
            "awaiting_checkin": self.awaiting_checkin,
            "awaiting_goal": self.awaiting_goal,
            "awaiting_outcome": self.awaiting_outcome,
            "metrics": self.metrics,
            "focus": self.focus,
            "session_goal": self.session_goal,
            "last_outcome": self.last_outcome,
            "distress_streak": self.distress_streak,
            "last_distress_at": self.last_distress_at,
            "last_support_offer_at": self.last_support_offer_at,
            "pending_checkin_stage": self.pending_checkin_stage,
            "pending_checkin_values": self.pending_checkin_values,
            "last_checkin_prompt_at": self.last_checkin_prompt_at,
            "bot_message_ids": self.bot_message_ids,
            "emoji_pool": self.emoji_pool,
            "chat_ready": self.chat_ready,
        }

    @staticmethod
    def from_dict(raw: Dict[str, object]) -> "UserMemory":
        history = [ChatMessage.from_dict(item) for item in raw.get("history", [])]
        metrics = list(raw.get("metrics", []))
        return UserMemory(
            summary=str(raw.get("summary", "")),
            history=history,
            messages_since_summary=int(raw.get("messages_since_summary", 0)),
            last_message_at=float(raw.get("last_message_at", 0.0)),
            awaiting_checkin=bool(raw.get("awaiting_checkin", False)),
            awaiting_goal=bool(raw.get("awaiting_goal", False)),
            awaiting_outcome=bool(raw.get("awaiting_outcome", False)),
            metrics=metrics,
            focus=str(raw.get("focus", "общее")),
            session_goal=str(raw.get("session_goal", "")),
            last_outcome=str(raw.get("last_outcome", "")),
            distress_streak=int(raw.get("distress_streak", 0)),
            last_distress_at=float(raw.get("last_distress_at", 0.0)),
            last_support_offer_at=float(raw.get("last_support_offer_at", 0.0)),
            pending_checkin_stage=str(raw.get("pending_checkin_stage", "")),
            pending_checkin_values=dict(raw.get("pending_checkin_values", {})),
            last_checkin_prompt_at=float(raw.get("last_checkin_prompt_at", 0.0)),
            bot_message_ids=list(raw.get("bot_message_ids", [])),
            emoji_pool=list(raw.get("emoji_pool", [])),
            chat_ready=bool(raw.get("chat_ready", False)),
        )


class MemoryStore:
    def __init__(
        self,
        path: Path,
        history_limit: int = DEFAULT_HISTORY_LIMIT,
        metrics_limit: int = DEFAULT_METRICS_LIMIT,
    ) -> None:
        self._path = path
        self._history_limit = history_limit
        self._metrics_limit = metrics_limit
        self._cache: Dict[str, UserMemory] = {}
        self._loaded = False

    def _load(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        if not PERSIST_LOCAL_MEMORY:
            return
        if not self._path.exists():
            return
        try:
            with self._path.open("r", encoding="utf-8") as fh:
                raw = json.load(fh)
        except Exception:
            return
        if not isinstance(raw, dict):
            return
        for user_id, data in raw.items():
            if isinstance(data, dict):
                self._cache[str(user_id)] = UserMemory.from_dict(data)

    def _save(self) -> None:
        if not PERSIST_LOCAL_MEMORY:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {user_id: memory.to_dict() for user_id, memory in self._cache.items()}
        tmp_path = self._path.with_suffix(".tmp")
        with tmp_path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False)
        os.replace(tmp_path, self._path)

    def _get(self, user_id: int) -> UserMemory:
        self._load()
        key = str(user_id)
        if key not in self._cache:
            self._cache[key] = UserMemory()
        return self._cache[key]

    def get(self, user_id: int) -> UserMemory:
        return self._get(user_id)

    def clear(self, user_id: int) -> None:
        self._load()
        self._cache.pop(str(user_id), None)
        self._save()

    def touch(self, user_id: int) -> None:
        memory = self._get(user_id)
        memory.last_message_at = time.time()
        self._save()

    def is_rate_limited(self, user_id: int, min_interval_seconds: float) -> bool:
        memory = self._get(user_id)
        if memory.last_message_at <= 0:
            return False
        return (time.time() - memory.last_message_at) < min_interval_seconds

    def set_awaiting_checkin(self, user_id: int, awaiting: bool) -> None:
        memory = self._get(user_id)
        memory.awaiting_checkin = awaiting
        self._save()

    def set_awaiting_goal(self, user_id: int, awaiting: bool) -> None:
        memory = self._get(user_id)
        memory.awaiting_goal = awaiting
        self._save()

    def set_awaiting_outcome(self, user_id: int, awaiting: bool) -> None:
        memory = self._get(user_id)
        memory.awaiting_outcome = awaiting
        self._save()

    def set_focus(self, user_id: int, focus: str) -> None:
        memory = self._get(user_id)
        memory.focus = focus
        self._save()

    def set_session_goal(self, user_id: int, goal: str) -> None:
        memory = self._get(user_id)
        memory.session_goal = (goal or "").strip()
        self._save()

    def set_last_outcome(self, user_id: int, outcome: str) -> None:
        memory = self._get(user_id)
        memory.last_outcome = (outcome or "").strip()
        self._save()

    def set_pending_checkin_stage(self, user_id: int, stage: str) -> None:
        memory = self._get(user_id)
        memory.pending_checkin_stage = stage
        self._save()

    def set_pending_checkin_value(self, user_id: int, key: str, value: int) -> None:
        memory = self._get(user_id)
        memory.pending_checkin_values[key] = value
        self._save()

    def clear_pending_checkin(self, user_id: int) -> None:
        memory = self._get(user_id)
        memory.pending_checkin_stage = ""
        memory.pending_checkin_values = {}
        self._save()

    def clear_transient_state(self, user_id: int) -> None:
        memory = self._get(user_id)
        memory.awaiting_checkin = False
        memory.awaiting_goal = False
        memory.awaiting_outcome = False
        memory.pending_checkin_stage = ""
        memory.pending_checkin_values = {}
        self._save()

    def set_chat_ready(self, user_id: int, ready: bool) -> None:
        memory = self._get(user_id)
        memory.chat_ready = ready
        self._save()

    def is_chat_ready(self, user_id: int) -> bool:
        return self._get(user_id).chat_ready

    def add_bot_message_id(self, user_id: int, message_id: int) -> None:
        memory = self._get(user_id)
        memory.bot_message_ids.append(message_id)
        self._save()

    def clear_bot_message_ids(self, user_id: int) -> None:
        memory = self._get(user_id)
        memory.bot_message_ids = []
        self._save()

    def next_emoji(
        self, user_id: int, preferred: List[str], all_emojis: List[str]
    ) -> str:
        memory = self._get(user_id)
        if not memory.emoji_pool:
            pool = list(all_emojis)
            random.shuffle(pool)
            memory.emoji_pool = pool

        pool = memory.emoji_pool
        preferred_set = set(preferred)
        chosen = None
        for idx, emoji in enumerate(pool):
            if emoji in preferred_set:
                chosen = emoji
                del pool[idx]
                break

        if chosen is None:
            chosen = pool.pop(0)

        if not pool:
            pool = list(all_emojis)
            random.shuffle(pool)
            if pool and pool[0] == chosen and len(pool) > 1:
                pool.append(pool.pop(0))
        memory.emoji_pool = pool
        self._save()
        return chosen

    def next_support_emoji(self, user_id: int, emojis: List[str]) -> str:
        if not emojis:
            return "✨"
        return self.next_emoji(user_id, emojis, emojis)

    def append_message(self, user_id: int, role: str, content: str) -> None:
        memory = self._get(user_id)
        cleaned = (content or "").strip()
        if len(cleaned) > MAX_MESSAGE_CHARS:
            cleaned = cleaned[:MAX_MESSAGE_CHARS].rstrip() + "..."
        memory.history.append(
            ChatMessage(role=role, content=cleaned, ts=time.time())
        )
        if role == "user":
            memory.messages_since_summary += 1
        if len(memory.history) > self._history_limit:
            memory.history = memory.history[-self._history_limit :]
        self._save()

    def set_summary(self, user_id: int, summary: str) -> None:
        memory = self._get(user_id)
        memory.summary = (summary or "").strip()
        memory.messages_since_summary = 0
        self._save()

    def reset_summary_counter(self, user_id: int) -> None:
        memory = self._get(user_id)
        memory.messages_since_summary = 0
        self._save()

    def update_distress(self, user_id: int, is_distress: bool) -> bool:
        memory = self._get(user_id)
        now = time.time()
        if not is_distress:
            if now - memory.last_distress_at > 12 * 3600:
                memory.distress_streak = 0
            self._save()
            return False
        if now - memory.last_distress_at > 6 * 3600:
            memory.distress_streak = 0
        memory.distress_streak += 1
        memory.last_distress_at = now
        should_offer = (
            memory.distress_streak >= 3
            and (now - memory.last_support_offer_at) > 12 * 3600
        )
        if should_offer:
            memory.last_support_offer_at = now
        self._save()
        return should_offer

    def should_prompt_checkin(
        self, user_id: int, interval_days: int, prompt_cooldown_hours: int
    ) -> bool:
        memory = self._get(user_id)
        now = time.time()
        if memory.awaiting_checkin or memory.pending_checkin_stage:
            return False
        if memory.last_checkin_prompt_at > 0:
            if (now - memory.last_checkin_prompt_at) < (prompt_cooldown_hours * 3600):
                return False
        last_metric = memory.metrics[-1] if memory.metrics else None
        if not last_metric:
            return True
        return (now - float(last_metric["ts"])) > (interval_days * 86400)

    def mark_checkin_prompted(self, user_id: int) -> None:
        memory = self._get(user_id)
        memory.last_checkin_prompt_at = time.time()
        self._save()

    def add_metric(
        self,
        user_id: int,
        mood: int,
        anxiety: int,
        energy: int,
    ) -> None:
        memory = self._get(user_id)
        memory.metrics.append(
            {
                "mood": mood,
                "anxiety": anxiety,
                "energy": energy,
                "ts": time.time(),
            }
        )
        if len(memory.metrics) > self._metrics_limit:
            memory.metrics = memory.metrics[-self._metrics_limit :]
        self._save()

    def get_last_metric(self, user_id: int) -> Optional[Dict[str, object]]:
        memory = self._get(user_id)
        if not memory.metrics:
            return None
        return memory.metrics[-1]


_store: Optional[MemoryStore] = None


def get_memory_store() -> MemoryStore:
    global _store
    if _store is None:
        root_dir = Path(__file__).resolve().parents[2]
        data_dir = root_dir / DATA_DIR_NAME
        path = data_dir / MEMORY_FILE_NAME
        _store = MemoryStore(path=path)
    return _store
