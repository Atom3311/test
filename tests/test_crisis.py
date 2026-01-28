import sys
from pathlib import Path
import unittest

sys.path.append(str(Path(__file__).resolve().parents[1] / "app"))

from services.crisis import detect_crisis, detect_distress


class TestCrisisDetection(unittest.TestCase):
    def test_high_risk_phrase(self) -> None:
        self.assertTrue(detect_crisis("Хочу покончить с собой."))

    def test_medium_with_intensifier(self) -> None:
        self.assertTrue(detect_crisis("Нет смысла жить, сейчас все плохо."))

    def test_non_crisis(self) -> None:
        self.assertFalse(detect_crisis("Мне грустно, но я держусь."))


class TestDistressDetection(unittest.TestCase):
    def test_distress_phrase(self) -> None:
        self.assertTrue(detect_distress("Мне очень плохо и тревожно."))

    def test_not_distress(self) -> None:
        self.assertFalse(detect_distress("Сегодня хорошая погода."))


if __name__ == "__main__":
    unittest.main()
