from __future__ import annotations

import unittest
from unittest.mock import patch

import cv2
import numpy as np

from core.camera import CameraDevice


class FakeCapture:
    def __init__(self, index, opened=True, frame_ok=True):
        self.opened = opened
        self.frame_ok = frame_ok
        self.released = False

    def isOpened(self):
        return self.opened and not self.released

    def set(self, *_):
        return True

    def read(self):
        return self.frame_ok, np.zeros((20, 30, 3), dtype=np.uint8) if self.frame_ok else None

    def release(self):
        self.released = True


class CameraTests(unittest.TestCase):
    def test_camera_start_read_stop(self):
        camera = CameraDevice(capture_factory=lambda index: FakeCapture(index))
        ok, _ = camera.open()
        self.assertTrue(ok)
        self.assertTrue(camera.is_open)
        self.assertTrue(camera.read().ok)
        camera.release()
        self.assertFalse(camera.is_open)

    def test_camera_unavailable(self):
        camera = CameraDevice(capture_factory=lambda index: FakeCapture(index, opened=False))
        ok, message = camera.open()
        self.assertFalse(ok)
        self.assertIn("unavailable", message.lower())
        self.assertFalse(camera.read().ok)

    def test_frame_failure_does_not_raise(self):
        camera = CameraDevice(capture_factory=lambda index: FakeCapture(index, frame_ok=False))
        self.assertTrue(camera.open()[0])
        result = camera.read()
        self.assertFalse(result.ok)
        self.assertIsNone(result.frame)

    @patch("core.camera.platform.system", return_value="Windows")
    def test_windows_falls_back_to_usb_camera(self, _):
        calls = []

        def factory(index, backend=None):
            calls.append((index, backend))
            return FakeCapture(index, opened=index == 1)

        # Mark this as the real OpenCV factory only for the duration of the
        # test so the Windows backend/index search is exercised.
        with patch("core.camera.cv2.VideoCapture", side_effect=factory) as mocked:
            camera = CameraDevice(capture_factory=mocked)
            # Mock is not object-identical to cv2.VideoCapture after injection,
            # so construct with the patched default through a small subclass.
            camera.capture_factory = cv2.VideoCapture
            ok, message = camera.open()
        self.assertTrue(ok)
        self.assertEqual(camera.active_index, 1)
        self.assertIn("Camera 1", message)


if __name__ == "__main__":
    unittest.main()
