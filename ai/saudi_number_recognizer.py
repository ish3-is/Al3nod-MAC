from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass

import numpy as np


ARABIC_DIGITS = "\u0660\u0661\u0662\u0663\u0664\u0665\u0666\u0667\u0668\u0669"


@dataclass(frozen=True)
class NumberPrediction:
    value: int | None
    pattern: tuple[bool, bool, bool, bool, bool]
    quality: float


def _distance(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a - b))


def _angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    ba = a - b
    bc = c - b
    denom = float(np.linalg.norm(ba) * np.linalg.norm(bc))
    if denom < 1e-8:
        return 0.0
    cosine = float(np.clip(np.dot(ba, bc) / denom, -1.0, 1.0))
    return float(np.degrees(np.arccos(cosine)))


class SaudiNumberRecognizer:
    """Static Saudi Arabic digit recognizer for the documented 0-9 poses.

    The classifier uses MediaPipe's 21 hand landmarks. It intentionally
    supports only the static 0-9 poses from the supplied Saudi sign-language
    number reference; larger numbers require movement or two-hand composition.
    """

    PATTERN_TO_DIGIT = {
        (False, False, False, False, False): 0,
        (False, True, False, False, False): 1,
        (False, True, True, False, False): 2,
        (False, True, True, True, False): 3,
        (False, True, True, True, True): 4,
        (True, True, True, True, True): 5,
        (True, False, False, False, False): 6,
        (True, True, False, False, False): 7,
        (True, True, True, False, False): 8,
        (True, True, True, True, False): 9,
    }

    @staticmethod
    def _finger_extended(points: np.ndarray, mcp: int, pip: int, dip: int, tip: int) -> tuple[bool, float]:
        wrist = points[0]
        bend = _angle(points[mcp], points[pip], points[tip])
        reach_ratio = _distance(wrist, points[tip]) / max(_distance(wrist, points[pip]), 1e-6)
        chain = (
            _distance(points[mcp], points[pip])
            + _distance(points[pip], points[dip])
            + _distance(points[dip], points[tip])
        )
        straight_ratio = _distance(points[mcp], points[tip]) / max(chain, 1e-6)
        extended = bend >= 145.0 and reach_ratio >= 1.08 and straight_ratio >= 0.72
        quality = min(1.0, max(0.0, (bend - 110.0) / 60.0))
        return extended, quality

    @staticmethod
    def _thumb_extended(points: np.ndarray) -> tuple[bool, float]:
        wrist = points[0]
        bend = _angle(points[2], points[3], points[4])
        reach_ratio = _distance(wrist, points[4]) / max(_distance(wrist, points[3]), 1e-6)
        palm_width = max(_distance(points[5], points[17]), 1e-6)
        lateral_reach = _distance(points[4], points[5]) / palm_width
        extended = bend >= 140.0 and reach_ratio >= 1.04 and lateral_reach >= 0.55
        quality = min(1.0, max(0.0, (bend - 105.0) / 65.0))
        return extended, quality

    def predict(self, landmarks: np.ndarray) -> NumberPrediction:
        points = np.asarray(landmarks, dtype=np.float32)
        if points.shape not in {(21, 2), (21, 3)}:
            return NumberPrediction(None, (False,) * 5, 0.0)
        points = points[:, :2]
        thumb, tq = self._thumb_extended(points)
        index, iq = self._finger_extended(points, 5, 6, 7, 8)
        middle, mq = self._finger_extended(points, 9, 10, 11, 12)
        ring, rq = self._finger_extended(points, 13, 14, 15, 16)
        pinky, pq = self._finger_extended(points, 17, 18, 19, 20)
        pattern = (thumb, index, middle, ring, pinky)
        return NumberPrediction(
            self.PATTERN_TO_DIGIT.get(pattern),
            pattern,
            float(np.mean([tq, iq, mq, rq, pq])),
        )


class NumberStabilizer:
    """Accept a digit only after it remains stable across camera frames."""

    def __init__(self, window: int = 12, minimum_votes: int = 8):
        self.values: deque[int | None] = deque(maxlen=window)
        self.minimum_votes = minimum_votes

    def reset(self) -> None:
        self.values.clear()

    def update(self, value: int | None) -> tuple[int | None, float]:
        self.values.append(value)
        valid = [item for item in self.values if item is not None]
        if not valid:
            return None, 0.0
        digit, votes = Counter(valid).most_common(1)[0]
        confidence = votes / max(len(self.values), 1)
        if votes < self.minimum_votes or confidence < 0.66:
            return None, confidence
        return digit, confidence


def format_digit(value: int | None) -> str:
    return ARABIC_DIGITS[value] if value is not None and 0 <= value <= 9 else "?"
