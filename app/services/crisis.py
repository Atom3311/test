import re

HIGH_RISK_PATTERNS = [
    r"поконч(ить|у) с собой",
    r"уби(ть|ю) себя",
    r"хочу умереть",
    r"не хочу жить",
    r"жить не хочу",
    r"самоубий",
    r"повес",
    r"спрыгн(уть|у)",
    r"(порез|перерез)[^\\n]{0,12}вен",
    r"передоз",
    r"передозиров",
    r"отрав(иться|люсь)",
    r"вып(ить|ью)[^\\n]{0,12}таблет",
    r"селф[- ]?харм",
    r"self[- ]?harm",
    r"самоповреж",
]

MEDIUM_RISK_PATTERNS = [
    r"нет смысла жить",
    r"жизнь не имеет смысла",
    r"лучше бы меня не было",
    r"не хочу просыпаться",
    r"хочу исчезнуть",
    r"устал(а)? жить",
    r"надоело жить",
]

INTENSIFIERS = [
    r"прямо сейчас",
    r"сегодня",
    r"сейчас",
    r"есть план",
    r"планирую",
    r"сделаю это",
    r"готовлюсь",
]


def _matches_any(patterns: list[str], text: str) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def detect_crisis(text: str) -> bool:
    lowered = text.lower()
    if _matches_any(HIGH_RISK_PATTERNS, lowered):
        return True

    score = 0
    if _matches_any(MEDIUM_RISK_PATTERNS, lowered):
        score += 1
    if _matches_any(INTENSIFIERS, lowered):
        score += 1

    return score >= 2


DISTRESS_PATTERNS = [
    r"очень плохо",
    r"мне плохо",
    r"тяжело",
    r"пустот",
    r"безысход",
    r"паник",
    r"сильн(ая|ое) тревог",
    r"тревожно",
    r"страшно",
    r"выгора",
    r"устал(а)?",
    r"нет сил",
    r"не могу справиться",
    r"невыносимо",
    r"депрессив",
    r"бессонниц",
]


def detect_distress(text: str) -> bool:
    lowered = text.lower()
    return _matches_any(DISTRESS_PATTERNS, lowered)
