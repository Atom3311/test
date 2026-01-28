import sys
from pathlib import Path
import unittest

sys.path.append(str(Path(__file__).resolve().parents[1] / "app"))

from services.checkin import parse_checkin


class TestCheckinParsing(unittest.TestCase):
    def test_parse_slash_format(self) -> None:
        self.assertEqual(parse_checkin("6/4/5"), (6, 4, 5))

    def test_parse_text_format(self) -> None:
        self.assertEqual(
            parse_checkin("настроение 7 тревога 3 энергия 5"),
            (7, 3, 5),
        )

    def test_parse_invalid(self) -> None:
        self.assertIsNone(parse_checkin("не знаю"))


if __name__ == "__main__":
    unittest.main()
