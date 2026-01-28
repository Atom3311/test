from __future__ import annotations

import random
import unicodedata
from typing import Dict, List, Optional

from services.emoji_pool import SUPPORT_EMOJIS as EMOJI_POOL
from services.memory import get_memory_store

BAD_KEYWORDS = [
    "GUN",
    "PISTOL",
    "KNIFE",
    "DAGGER",
    "BOMB",
    "SKULL",
    "COFFIN",
    "TOMB",
    "CIGARETTE",
    "ALCOHOL",
    "BEER",
    "WINE",
    "SYRINGE",
    "PILL",
    "VOMITING",
    "POOP",
    "MIDDLE FINGER",
    "ANGER",
    "RAGE",
    "WEARY",
    "CRYING",
    "PUNCH",
    "WEAPON",
    "BLOOD",
]

CATEGORY_KEYWORDS = {
    "support": [
        "HEART",
        "HUGGING",
        "DOVE",
        "RAINBOW",
        "SUN",
        "STAR",
        "SPARKLE",
        "BLOSSOM",
        "FLOWER",
        "SEEDLING",
        "LEAF",
        "LOTUS",
    ],
    "calm": [
        "CLOUD",
        "MOON",
        "WAVE",
        "DROPLET",
        "WATER",
        "LEAF",
        "LOTUS",
        "CANDLE",
        "SHELL",
        "STAR",
        "SPARKLE",
    ],
    "positive": [
        "SMILING FACE",
        "SMILE",
        "GRIN",
        "STAR",
        "SPARKLE",
        "SUN",
        "RAINBOW",
        "BALLOON",
        "CONFETTI",
    ],
    "warning": [
        "WARNING",
        "SOS",
        "EXCLAMATION",
        "STOP SIGN",
        "NO ENTRY",
        "CROSS MARK",
    ],
    "question": ["QUESTION MARK", "THINKING FACE", "MAGNIFYING"],
    "info": ["INFORMATION", "LIGHT BULB", "BOOK", "PENCIL", "GEAR"],
}

DECOR_PATTERNS = [
    "{emoji} {text}",
    "{text} {emoji}",
    "{emoji}\n{text}",
    "{text}\n{emoji}",
]


def _name(emoji: str) -> str:
    try:
        return unicodedata.name(emoji)
    except ValueError:
        return ""


def _is_safe(emoji: str) -> bool:
    name = _name(emoji)
    if not name:
        return False
    return not any(bad in name for bad in BAD_KEYWORDS)


SAFE_POOL = [emoji for emoji in EMOJI_POOL if _is_safe(emoji)]


def _build_category_pool(keywords: List[str]) -> List[str]:
    pool: List[str] = []
    for emoji in SAFE_POOL:
        name = _name(emoji)
        if any(word in name for word in keywords):
            pool.append(emoji)
    return pool


CATEGORY_POOLS: Dict[str, List[str]] = {
    category: _build_category_pool(words)
    for category, words in CATEGORY_KEYWORDS.items()
}


def _category_from_text(text: str, kind: Optional[str]) -> str:
    lowered = (text or "").lower()
    if kind:
        if kind.startswith("support:"):
            if kind.endswith("breath") or kind.endswith("ground"):
                return "calm"
            if kind.endswith("compassion"):
                return "support"
            return "support"
        if kind == "warning":
            return "warning"
        if kind == "checkin":
            return "calm"
        if kind == "info":
            return "info"

    if any(word in lowered for word in ["экстренн", "опасн", "служб", "112", "911"]):
        return "warning"
    if any(word in lowered for word in ["оцените", "оценка", "настроени", "тревог", "энерг"]):
        return "calm"
    if "?" in text:
        return "question"
    if any(word in lowered for word in ["спасибо", "получилось", "рад", "хорошо"]):
        return "positive"
    return "support"


def select_emoji(user_id: int, text: str, kind: Optional[str] = None) -> str:
    category = _category_from_text(text, kind)
    preferred = CATEGORY_POOLS.get(category) or SAFE_POOL
    store = get_memory_store()
    return store.next_emoji(user_id, preferred, SAFE_POOL)


def decorate_text(user_id: int, text: str, kind: Optional[str] = None) -> str:
    emoji = select_emoji(user_id, text, kind)
    pattern = random.choice(DECOR_PATTERNS)
    return pattern.format(emoji=emoji, text=text)
