from __future__ import annotations

import os
import platform
from dataclasses import dataclass
from typing import Callable

import cv2


@dataclass(frozen=True)
class CameraRead:
    ok: bool
    frame: object | None
    message: str


class CameraDevice:
    """Injectable OpenCV camera wrapper with Windows backend fallback."""

    def __init__(self, index: int = 0, capture_factory: Callable = cv2.VideoCapture):
        configured = os.getenv("ISHARA_CAMERA_INDEX", "").strip()
        self.index = int(configured) if configured.isdigit() else index
        self.capture_factory = capture_factory
        self._capture = None
        self.active_index: int | None = None
        self.active_backend = ""

    @property
    def is_open(self) -> bool:
        return bool(self._capture is not None and self._capture.isOpened())

    def open(self) -> tuple[bool, str]:
        if self.is_open:
            return True, "Camera already active"

        # Keep dependency-injected test captures deterministic. Real Windows
        # devices are tried through DirectShow, Media Foundation and OpenCV's
        # default backend; USB cameras commonly appear at index 1 or 2.
        if self.capture_factory is not cv2.VideoCapture:
            candidates = [(self.index, None, "injected")]
        elif platform.system() == "Windows":
            indexes = list(dict.fromkeys((self.index, 0, 1, 2)))
            candidates = [
                (camera_index, backend, backend_name)
                for camera_index in indexes
                for backend, backend_name in (
                    (cv2.CAP_DSHOW, "DirectShow"),
                    (cv2.CAP_MSMF, "Media Foundation"),
                    (None, "OpenCV default"),
                )
            ]
        else:
            indexes = list(dict.fromkeys((self.index, 0, 1, 2)))
            candidates = [(camera_index, None, "OpenCV default") for camera_index in indexes]

        for camera_index, backend, backend_name in candidates:
            capture = (
                self.capture_factory(camera_index)
                if backend is None
                else self.capture_factory(camera_index, backend)
            )
            if capture and capture.isOpened():
                self._capture = capture
                self.active_index = camera_index
                self.active_backend = backend_name
                break
            if capture:
                capture.release()

        if not self.is_open:
            self.release()
            settings_hint = (
                "Allow camera access in System Settings > Privacy & Security > Camera"
                if platform.system() == "Darwin"
                else "Allow desktop camera access in Windows Settings"
            )
            return False, (
                f"Camera unavailable or permission denied. {settings_hint}, "
                "then close other camera apps."
            )
        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 540)
        return True, f"Camera {self.active_index} active ({self.active_backend})"

    def read(self) -> CameraRead:
        if not self.is_open:
            return CameraRead(False, None, "Camera is not active")
        ok, frame = self._capture.read()
        if not ok or frame is None:
            return CameraRead(False, None, "Unable to read a camera frame")
        return CameraRead(True, frame, "Frame captured")

    def release(self) -> None:
        if self._capture is not None:
            self._capture.release()
        self._capture = None
        self.active_index = None
        self.active_backend = ""

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *_):
        self.release()
