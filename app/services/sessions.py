from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional


@dataclass
class ActiveSession:
    user_id: int
    started_at: datetime
    risk_detected: bool = False


_active_sessions: Dict[int, ActiveSession] = {}


def start_session(user_id: int) -> ActiveSession:
    session = ActiveSession(user_id=user_id, started_at=datetime.utcnow())
    _active_sessions[user_id] = session
    return session


def get_session(user_id: int) -> Optional[ActiveSession]:
    return _active_sessions.get(user_id)


def end_session(user_id: int) -> Optional[ActiveSession]:
    return _active_sessions.pop(user_id, None)
