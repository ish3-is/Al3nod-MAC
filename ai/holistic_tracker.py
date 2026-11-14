from __future__ import annotations

import time
from dataclasses import dataclass

import cv2
import numpy as np

from ai.models.feats import from_holistic
from ai.saudi_number_recognizer import SaudiNumberRecognizer


@dataclass
class HolisticTrackingResult:
    frame: np.ndarray
    feature: np.ndarray | None
    digit: int | None
    timestamp_ms: float
    available: bool
    status: str


class HolisticTracker:
    """MediaPipe Holistic adapter producing the model's official SF1 frame."""

    def __init__(self):
        self.available = False
        self.status = "MediaPipe Holistic unavailable"
        self._holistic = None
        self._drawing = None
        self._mp_holistic = None
        self._number_recognizer = SaudiNumberRecognizer()
        try:
            import mediapipe as mp

            self._mp_holistic = mp.solutions.holistic
            self._drawing = mp.solutions.drawing_utils
            self._holistic = self._mp_holistic.Holistic(
                static_image_mode=False,
                model_complexity=1,
                smooth_landmarks=True,
                refine_face_landmarks=False,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            self.available = True
            self.status = "MediaPipe Holistic + SF1 tracking active"
        except Exception as exc:
            self.status = f"MediaPipe Holistic unavailable: {exc.__class__.__name__}: {exc}"

    @staticmethod
    def _append_landmarks(target_xyz, target_conf, landmarks, count, width, height, pose=False):
        if landmarks is None:
            target_xyz.extend([[0.0, 0.0, 0.0]] * count)
            target_conf.extend([0.0] * count)
            return
        values = list(landmarks.landmark)[:count]
        for landmark in values:
            target_xyz.append([landmark.x * width, landmark.y * height, landmark.z * width])
            target_conf.append(float(getattr(landmark, "visibility", 1.0)) if pose else 1.0)
        missing = count - len(values)
        if missing:
            target_xyz.extend([[0.0, 0.0, 0.0]] * missing)
            target_conf.extend([0.0] * missing)

    def process(self, frame: np.ndarray) -> HolisticTrackingResult:
        timestamp = time.perf_counter() * 1000.0
        if not self.available or self._holistic is None:
            return HolisticTrackingResult(frame, None, None, timestamp, False, self.status)
        height, width = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        result = self._holistic.process(rgb)
        xyz: list[list[float]] = []
        conf: list[float] = []
        self._append_landmarks(xyz, conf, result.pose_landmarks, 33, width, height, pose=True)
        self._append_landmarks(xyz, conf, result.face_landmarks, 468, width, height)
        self._append_landmarks(xyz, conf, result.left_hand_landmarks, 21, width, height)
        self._append_landmarks(xyz, conf, result.right_hand_landmarks, 21, width, height)
        if self._drawing:
            if result.pose_landmarks:
                self._drawing.draw_landmarks(frame, result.pose_landmarks, self._mp_holistic.POSE_CONNECTIONS)
            if result.left_hand_landmarks:
                self._drawing.draw_landmarks(frame, result.left_hand_landmarks, self._mp_holistic.HAND_CONNECTIONS)
            if result.right_hand_landmarks:
                self._drawing.draw_landmarks(frame, result.right_hand_landmarks, self._mp_holistic.HAND_CONNECTIONS)
        hand = (
            result.right_hand_landmarks
            if result.right_hand_landmarks is not None
            else result.left_hand_landmarks
        )
        digit = None
        if hand is not None:
            hand_points = np.asarray(
                [[item.x, item.y, item.z] for item in hand.landmark],
                dtype=np.float32,
            )
            digit = self._number_recognizer.predict(hand_points).value
        feature = from_holistic(np.asarray(xyz), np.asarray(conf), width, height)
        return HolisticTrackingResult(frame, feature, digit, timestamp, True, self.status)

    def close(self):
        if self._holistic is not None:
            self._holistic.close()

