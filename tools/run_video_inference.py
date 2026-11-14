from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

from ai.holistic_tracker import HolisticTracker
from ai.models.feats import resample
from ai.pretrained_sign_recognizer import PretrainedSignRecognizer
from config import MODEL_DIR


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the ISHARA model on a recorded sign video.")
    parser.add_argument("video", type=Path)
    args = parser.parse_args()
    if not args.video.is_file():
        parser.error(f"Video not found: {args.video}")

    recognizer = PretrainedSignRecognizer(MODEL_DIR)
    if not recognizer.available:
        print(recognizer.status)
        return 2
    tracker = HolisticTracker()
    if not tracker.available:
        print(tracker.status)
        return 3

    capture = cv2.VideoCapture(str(args.video))
    fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    features, timestamps = [], []
    frame_index = 0
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        tracked = tracker.process(frame)
        if tracked.feature is not None:
            features.append(tracked.feature)
            timestamps.append(frame_index * 1000.0 / fps)
        frame_index += 1
    capture.release()
    tracker.close()
    if len(features) < 2:
        print("No usable holistic frames were extracted.")
        return 4

    sf1 = resample(np.asarray(features, np.float32), timestamps, fps=15)
    result = recognizer.recognize(sf1, cashier_mode=True)
    print(json.dumps({
        "video": str(args.video),
        "source_frames": len(features),
        "sf1_frames_15fps": len(sf1),
        "arabic": result.arabic,
        "glosses": result.glosses,
        "gloss_key": result.gloss_key,
        "ctc_score": result.ctc_score,
        "inference_ms": result.inference_ms,
        "supported_for_cashier": result.supported_for_cashier,
        "status": result.status,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

