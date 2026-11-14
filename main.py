from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="ISHARA desktop application")
    parser.add_argument("--smoke-test", type=float, metavar="SECONDS", help="launch and close automatically")
    parser.add_argument("--fallback", action="store_true", help="force the built-in Tkinter interface")
    parser.add_argument(
        "--verify-runtime",
        action="store_true",
        help="verify bundled dependencies, resources, and ONNX inference without opening the UI",
    )
    args = parser.parse_args()
    if args.verify_runtime:
        return verify_runtime()
    if not args.fallback:
        try:
            from ui.pyside_app import run
            return run(args.smoke_test)
        except ImportError as exc:
            if exc.name not in {"PySide6", "shiboken6"}:
                raise
            print("PySide6 is unavailable; starting the tested Tkinter fallback.", file=sys.stderr)
    from ui.tk_fallback import run
    return run(args.smoke_test)


def verify_runtime() -> int:
    """CI-friendly validation that also runs from the frozen macOS executable."""
    import cv2
    import mediapipe
    import numpy as np
    import onnxruntime
    import PySide6

    from ai.pretrained_sign_recognizer import PretrainedSignRecognizer
    from config import ASSET_DIR, MODEL_DIR

    required = [
        MODEL_DIR / "sli-sentences-phone-v1.onnx",
        MODEL_DIR / "vocab.json",
        MODEL_DIR / "face_idx.json",
        MODEL_DIR / "conventions.json",
        MODEL_DIR / "feats.py",
        ASSET_DIR / "ishara_logo.svg",
        ASSET_DIR / "sign_guides" / "social_signs.png",
        ASSET_DIR / "sign_guides" / "cashier_signs.png",
    ]
    missing = [str(path) for path in required if not path.is_file()]
    recognizer = PretrainedSignRecognizer(MODEL_DIR)
    inference = None
    if recognizer.available:
        inference = recognizer.recognize(np.zeros((15, 356), dtype=np.float32))
    report = {
        "python": sys.version.split()[0],
        "platform": sys.platform,
        "frozen": bool(getattr(sys, "frozen", False)),
        "versions": {
            "PySide6": PySide6.__version__,
            "OpenCV": cv2.__version__,
            "MediaPipe": mediapipe.__version__,
            "ONNXRuntime": onnxruntime.__version__,
            "NumPy": np.__version__,
        },
        "model_dir": str(MODEL_DIR),
        "resources_missing": missing,
        "model_loaded": recognizer.available,
        "model_status": recognizer.status,
        "input_shape": [1, 15, 356],
        "inference_ms": round(inference.inference_ms, 3) if inference else None,
        "semantic_accuracy_claimed": False,
    }
    serialized = json.dumps(report, ensure_ascii=False, indent=2)
    output_path = os.getenv("ISHARA_VERIFY_OUTPUT", "").strip()
    if output_path:
        destination = Path(output_path).expanduser().resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(serialized, encoding="utf-8")
    print(serialized)
    return 0 if not missing and recognizer.available and inference is not None else 1


if __name__ == "__main__":
    raise SystemExit(main())
