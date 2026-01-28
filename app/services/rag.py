from datetime import datetime

from services.memory import UserMemory


def build_context(
    memory: UserMemory,
    direction: str = "general",
    stage: str = "session",
) -> str:
    parts: list[str] = []
    last_metric = memory.metrics[-1] if memory.metrics else None
    if last_metric:
        ts = datetime.fromtimestamp(last_metric["ts"]).strftime("%Y-%m-%d")
        parts.append(
            "Последняя оценка состояния "
            f"({ts}): настроение {last_metric['mood']}/10, "
            f"тревога {last_metric['anxiety']}/10, "
            f"энергия {last_metric['energy']}/10."
        )
    if not parts:
        return ""
    return " ".join(parts)
