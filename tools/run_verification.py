from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def run_tests() -> dict:
    loader = unittest.TestLoader()
    suite = loader.discover(str(ROOT / "tests"), pattern="test_*.py")
    result = unittest.TestResult()
    started = time.time()
    suite.run(result)
    return {
        "tests_run": result.testsRun,
        "passed": result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped),
        "failures": [f"{test}: {trace}" for test, trace in result.failures],
        "errors": [f"{test}: {trace}" for test, trace in result.errors],
        "skipped": [f"{test}: {reason}" for test, reason in result.skipped],
        "duration_seconds": round(time.time() - started, 3),
    }


def smoke_test() -> dict:
    env = dict(os.environ)
    command = [sys.executable, str(ROOT / "main.py"), "--fallback", "--smoke-test", "1.2"]
    started = time.time()
    try:
        completed = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=8)
        return {
            "passed": completed.returncode == 0,
            "returncode": completed.returncode,
            "duration_seconds": round(time.time() - started, 3),
            "stderr": completed.stderr.strip(),
        }
    except subprocess.TimeoutExpired:
        return {"passed": False, "returncode": None, "duration_seconds": round(time.time() - started, 3), "stderr": "Smoke test timed out"}


def environment() -> dict:
    import cv2
    import importlib.util

    return {
        "python": sys.version.split()[0],
        "opencv": cv2.__version__,
        "pyside6_available": importlib.util.find_spec("PySide6") is not None,
        "mediapipe_available": importlib.util.find_spec("mediapipe") is not None,
        "onnxruntime_available": importlib.util.find_spec("onnxruntime") is not None,
        "tensorflow_available": importlib.util.find_spec("tensorflow") is not None,
    }


def verify_model() -> dict:
    import numpy as np
    from ai.pretrained_sign_recognizer import PretrainedSignRecognizer
    from config import MODEL_DIR

    recognizer = PretrainedSignRecognizer(MODEL_DIR)
    result = {"loaded": recognizer.available, "status": recognizer.status}
    if not recognizer.available:
        return result
    started = time.perf_counter()
    output = recognizer.recognize(np.zeros((15, 356), dtype=np.float32))
    result.update({
        "input_shape": [1, 15, 356],
        "output_classes": 673,
        "inference_ms_reported": round(output.inference_ms, 3),
        "end_to_end_ms": round((time.perf_counter() - started) * 1000, 3),
        "decoded_status": output.status,
        "semantic_video_claimed": False,
        "note": "Synthetic zero SF1 verifies the runtime contract only; it is not an accuracy test.",
    })
    return result


def camera_probe() -> dict:
    import cv2

    capture = cv2.VideoCapture(0)
    opened = bool(capture.isOpened())
    read_ok = False
    shape = None
    if opened:
        read_ok, frame = capture.read()
        if read_ok and frame is not None:
            shape = list(frame.shape)
    capture.release()
    return {
        "attempted": True,
        "opened": opened,
        "frame_read": bool(read_ok),
        "frame_shape": shape,
        "note": "A live camera frame was read." if read_ok else "No camera frame was exposed to this execution environment.",
    }


def main() -> int:
    artifacts = ROOT / "artifacts"
    artifacts.mkdir(exist_ok=True)
    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "environment": environment(),
        "real_onnx_model": verify_model(),
        "physical_camera": camera_probe(),
        "automated_tests": run_tests(),
        "application_smoke_test": smoke_test(),
    }
    report["overall_passed"] = not report["automated_tests"]["failures"] and not report["automated_tests"]["errors"] and report["application_smoke_test"]["passed"]
    (artifacts / "verification_results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["overall_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
