from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from ai.models.feats import resample
from ai.pretrained_sign_recognizer import PretrainedSignRecognizer
from config import TARGET_PHRASES


@dataclass(frozen=True)
class TranslationResult:
    phrase: str | None
    confidence: float | None
    status: str
    source: str
    confirmed: bool


class TranslationEngine:
    """Real ONNX recognition and a clearly separate manual UI demo."""

    def __init__(
        self, model_dir: str | Path, confidence_threshold: float = 0.75
    ):
        self.model_dir = Path(model_dir)
        self.confidence_threshold = confidence_threshold
        self.recognizer = PretrainedSignRecognizer(self.model_dir)
        self.mode = "model" if self.recognizer.available else "unavailable"
        self.status = self.recognizer.status

    def classify(
        self, sequence: np.ndarray | None, timestamps_ms=None
    ) -> TranslationResult:
        if not self.recognizer.available:
            return TranslationResult(None, None, self.status, "model", False)
        if sequence is None or len(sequence) < 2:
            return TranslationResult(
                None,
                None,
                "\u0644\u0645 \u064a\u0644\u062a\u0642\u0637 MediaPipe \u0645\u0639\u0627\u0644\u0645 \u0643\u0627\u0641\u064a\u0629. \u062a\u0623\u0643\u062f \u0645\u0646 \u0638\u0647\u0648\u0631 \u0627\u0644\u0648\u062c\u0647 \u0648\u0627\u0644\u0643\u062a\u0641\u064a\u0646 \u0648\u0627\u0644\u064a\u062f\u064a\u0646 \u0628\u0627\u0644\u0643\u0627\u0645\u0644.",
                "model",
                False,
            )
        frames = np.asarray(sequence, dtype=np.float32)
        if timestamps_ms is not None:
            frames = resample(frames, timestamps_ms, fps=15)
        output = self.recognizer.recognize(frames, cashier_mode=True)
        status = f"{output.status} | inference {output.inference_ms:.1f} ms"
        confirmed = bool(
            output.supported_for_cashier
            and output.ctc_score is not None
            and output.ctc_score >= self.confidence_threshold
        )
        if not confirmed:
            status = (
                "\u0625\u0634\u0627\u0631\u0629 \u063a\u064a\u0631 \u0645\u0624\u0643\u062f\u0629 \u0623\u0648 \u063a\u064a\u0631 \u0645\u062f\u0639\u0648\u0645\u0629 \u0641\u064a \u0648\u0636\u0639 \u0627\u0644\u0643\u0627\u0634\u064a\u0631. "
                + status
            )
        return TranslationResult(
            output.arabic if confirmed else None,
            output.ctc_score,
            status,
            "model",
            confirmed,
        )

    def simulate(self, phrase: str) -> TranslationResult:
        if phrase not in TARGET_PHRASES:
            return TranslationResult(
                None, None, "Invalid demo phrase", "demo", False
            )
        return TranslationResult(
            phrase,
            None,
            "Demo Simulation only - not Saudi Sign Language recognition",
            "demo",
            True,
        )

    def unknown(self) -> TranslationResult:
        return TranslationResult(
            None,
            None,
            "Unknown sign - no translation asserted",
            self.mode,
            False,
        )
