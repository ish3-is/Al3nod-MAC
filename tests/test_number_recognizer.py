from __future__ import annotations

import unittest

from ai.saudi_number_recognizer import (
    ARABIC_DIGITS,
    NumberStabilizer,
    SaudiNumberRecognizer,
    format_digit,
)


class SaudiNumberRecognizerTests(unittest.TestCase):
    def test_reference_patterns_cover_digits_zero_to_nine_once(self):
        mapping = SaudiNumberRecognizer.PATTERN_TO_DIGIT
        self.assertEqual(set(mapping.values()), set(range(10)))
        self.assertEqual(len(mapping), 10)

    def test_documented_static_patterns(self):
        mapping = SaudiNumberRecognizer.PATTERN_TO_DIGIT
        self.assertEqual(mapping[(False, False, False, False, False)], 0)
        self.assertEqual(mapping[(False, True, False, False, False)], 1)
        self.assertEqual(mapping[(True, True, True, True, True)], 5)
        self.assertEqual(mapping[(True, False, False, False, False)], 6)
        self.assertEqual(mapping[(True, True, True, True, False)], 9)

    def test_stabilizer_rejects_a_single_or_changing_frame(self):
        stabilizer = NumberStabilizer(window=6, minimum_votes=4)
        self.assertIsNone(stabilizer.update(5)[0])
        for value in (1, 5, 1, 5):
            digit, _ = stabilizer.update(value)
        self.assertIsNone(digit)

    def test_stabilizer_accepts_a_consistent_digit(self):
        stabilizer = NumberStabilizer(window=6, minimum_votes=4)
        result = (None, 0.0)
        for _ in range(4):
            result = stabilizer.update(7)
        self.assertEqual(result[0], 7)
        self.assertGreaterEqual(result[1], 0.66)

    def test_arabic_digit_format(self):
        self.assertEqual("".join(format_digit(i) for i in range(10)), ARABIC_DIGITS)
        self.assertEqual(format_digit(None), "?")


if __name__ == "__main__":
    unittest.main()
