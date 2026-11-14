from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class TrackingResult:
    frame: np.ndarray
    landmarks: np.ndarray | None
    hand_count: int
    available: bool
    status: str


class HandTracker:
    """Optional MediaPipe tracker. Missing dependencies degrade safely."""

    def __init__(self):
        self._hands = None
        self._drawing = None
        self._connections = None
        self.available = False
        self.status = "MediaPipe unavailable"
        try:
            import mediapipe as mp

            self._hands = mp.solutions.hands.Hands(
                static_image_mode=False,
                max_num_hands=2,
                min_detection_confidence=0.55,
                min_tracking_confidence=0.55,
            )
            self._drawing = mp.solutions.drawing_utils
            self._connections = mp.solutions.hands.HAND_CONNECTIONS
            self.available = True
            self.status = "Hand landmark tracking active"
        except Exception as exc:
            self.status = f"MediaPipe unavailable: {exc.__class__.__name__}"

    def process(self, frame: np.ndarray) -> TrackingResult:
        if not self.available or self._hands is None:
            return TrackingResult(frame, None, 0, False, self.status)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self._hands.process(rgb)
        all_landmarks: list[float] = []
        hands = result.multi_hand_landmarks or []
        for hand in hands:
            self._drawing.draw_landmarks(frame, hand, self._connections)
            for landmark in hand.landmark:
                all_landmarks.extend((landmark.x, landmark.y, landmark.z))
        normalized = np.asarray(all_landmarks, dtype=np.float32) if all_landmarks else None
        return TrackingResult(frame, normalized, len(hands), True, self.status)

    def close(self) -> None:
        if self._hands is not None:
            self._hands.close()
