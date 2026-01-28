import re
from typing import Optional, Tuple


def parse_checkin(text: str) -> Optional[Tuple[int, int, int]]:
    numbers = [int(value) for value in re.findall(r"\b10\b|\b[0-9]\b", text)]
    if len(numbers) < 3:
        return None
    mood, anxiety, energy = numbers[0], numbers[1], numbers[2]
    if any(value < 0 or value > 10 for value in (mood, anxiety, energy)):
        return None
    return mood, anxiety, energy
