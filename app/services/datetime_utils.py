from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

_TZ_RE = re.compile(r"(Z|[+-]\d{2}:?\d{2})$")


def _normalize_iso_datetime(value: str) -> str:
    s = value.strip()
    if not s:
        raise ValueError("Empty datetime string")

    tz_match = _TZ_RE.search(s)
    tz = tz_match.group(1) if tz_match else ""
    base = s[: tz_match.start()] if tz_match else s

    if tz == "Z":
        tz = "+00:00"

    if "." in base:
        head, frac = base.split(".", 1)
        frac_digits = re.sub(r"\D", "", frac)
        if frac_digits:
            if len(frac_digits) < 6:
                frac_digits = frac_digits.ljust(6, "0")
            else:
                frac_digits = frac_digits[:6]
            base = f"{head}.{frac_digits}"
        else:
            base = head

    if not tz:
        tz = "+00:00"
    elif len(tz) == 5 and ":" not in tz:
        tz = f"{tz[:3]}:{tz[3:]}"

    return f"{base}{tz}"


def parse_db_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        raise TypeError(f"Expected datetime string, got {type(value).__name__}")

    normalized = _normalize_iso_datetime(value)
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        # Fallbacks for environments with stricter parsing.
        for fmt in (
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S.%f%z",
            "%Y-%m-%d %H:%M:%S%z",
        ):
            try:
                return datetime.strptime(normalized, fmt)
            except ValueError:
                continue

        try:
            naive = datetime.fromisoformat(normalized.replace("+00:00", ""))
            return naive.replace(tzinfo=timezone.utc)
        except ValueError:
            raise
