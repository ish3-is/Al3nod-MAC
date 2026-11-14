from __future__ import annotations

import json
import math
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class RecognitionOutput:
    arabic: str | None
    glosses: tuple[str, ...]
    gloss_key: str
    ctc_score: float | None
    inference_ms: float
    supported_for_cashier: bool
    status: str


def normalise_arabic(text: str) -> str:
    text = "".join(
        ch for ch in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(ch)
    )
    return " ".join(text.replace("?", "").replace("\u061f", "").split()).strip()


class PretrainedSignRecognizer:
    """CPU ONNX runner for DF-Team/sli-sentences (SF1 + CTC)."""

    MODEL_NAME = "sli-sentences-phone-v1.onnx"
    MIN_FRAMES = 8
    MAX_FRAMES = 450
    FEATURE_DIM = 356

    def __init__(self, model_dir: str | Path):
        self.model_dir = Path(model_dir)
        self.model_path = self.model_dir / self.MODEL_NAME
        self.vocab_path = self.model_dir / "vocab.json"
        self.session = None
        self.input_name = "feats"
        self.output_name = "logprobs"
        self.vocab: dict = {}
        self.available = False
        self.status = "Real AI model unavailable"
        self.cashier_targets = {
            normalise_arabic("\u0643\u0645 \u0627\u0644\u062d\u0633\u0627\u0628\u061f"): "\u0643\u0645 \u0627\u0644\u062d\u0633\u0627\u0628\u061f",
            normalise_arabic("\u0643\u0645 \u0627\u0644\u0628\u0627\u0642\u064a\u061f"): "\u0643\u0645 \u0627\u0644\u0628\u0627\u0642\u064a\u061f",
            normalise_arabic("\u0634\u0643\u0631\u064b\u0627"): "\u0634\u0643\u0631\u064b\u0627",
            normalise_arabic("\u0623\u0631\u064a\u062f \u0627\u0644\u062f\u0641\u0639"): "\u0623\u0631\u064a\u062f \u0627\u0644\u062f\u0641\u0639",
        }
        self.cashier_support: dict[str, bool] = {}
        self._load()

    def _load(self) -> None:
        if not self.model_path.is_file() or not self.vocab_path.is_file():
            self.status = "Real AI model files are missing"
            return
        try:
            import onnxruntime as ort

            self.vocab = json.loads(self.vocab_path.read_text(encoding="utf-8"))
            if len(self.vocab.get("glosses", [])) != 672:
                raise ValueError("Expected 672 gloss classes")
            self.session = ort.InferenceSession(
                str(self.model_path), providers=["CPUExecutionProvider"]
            )
            model_input = self.session.get_inputs()[0]
            model_output = self.session.get_outputs()[0]
            self.input_name = model_input.name
            self.output_name = model_output.name
            if model_input.shape[-1] != self.FEATURE_DIM:
                raise ValueError(f"Expected {self.FEATURE_DIM} SF1 features")
            if model_output.shape[-1] != 673:
                raise ValueError("Expected 673 CTC classes")
            lookup_values = {
                normalise_arabic(value)
                for value in self.vocab.get("lookup", {}).values()
            }
            self.cashier_support = {
                label: key in lookup_values
                for key, label in self.cashier_targets.items()
            }
            self.available = True
            self.status = "Real Saudi Sign Language ONNX model loaded (CPU)"
        except Exception as exc:
            self.session = None
            self.status = (
                f"Real AI model failed to load: {exc.__class__.__name__}: {exc}"
            )

    def decode_ctc(
        self, logprobs: np.ndarray
    ) -> tuple[tuple[str, ...], str, str | None, float | None]:
        scores = np.asarray(logprobs, dtype=np.float32)
        if scores.ndim == 3:
            scores = scores[0]
        if scores.ndim != 2 or scores.shape[1] != 673:
            raise ValueError("CTC output must have shape [T, 673] or [1, T, 673]")
        ids = np.argmax(scores, axis=-1).astype(int).tolist()
        collapsed: list[int] = []
        chosen_scores: list[float] = []
        previous = None
        for frame_idx, class_id in enumerate(ids):
            if class_id != previous and class_id != 0:
                collapsed.append(class_id)
                chosen_scores.append(
                    float(math.exp(float(scores[frame_idx, class_id])))
                )
            previous = class_id
        source = self.vocab.get("glosses", [])
        glosses = tuple(
            source[index - 1]
            for index in collapsed
            if 0 < index <= len(source)
        )
        key = " ".join(glosses)
        arabic = self.vocab.get("lookup", {}).get(key)
        score = float(np.mean(chosen_scores)) if chosen_scores else None
        return glosses, key, arabic, score

    def recognize(
        self, features: np.ndarray, cashier_mode: bool = True
    ) -> RecognitionOutput:
        if not self.available or self.session is None:
            return RecognitionOutput(None, (), "", None, 0.0, False, self.status)
        array = np.asarray(features, dtype=np.float32)
        if array.ndim != 2 or array.shape[1] != self.FEATURE_DIM:
            raise ValueError("SF1 features must have shape [T, 356]")
        if not self.MIN_FRAMES <= len(array) <= self.MAX_FRAMES:
            return RecognitionOutput(
                None, (), "", None, 0.0, False,
                f"Recording length must be {self.MIN_FRAMES}-{self.MAX_FRAMES} frames after 15 FPS resampling",
            )
        started = time.perf_counter()
        output = self.session.run(
            [self.output_name], {self.input_name: array[None, ...]}
        )[0]
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        glosses, key, arabic, score = self.decode_ctc(output)
        if not glosses:
            return RecognitionOutput(
                None, (), "", score, elapsed_ms, False,
                "Unknown sign: CTC produced no tokens",
            )
        if arabic is None:
            raw_gloss = " ".join(token.replace("_", " ") for token in glosses)
            return RecognitionOutput(
                raw_gloss, glosses, key, score, elapsed_ms, False,
                "\u0645\u062e\u0631\u062c\u0627\u062a \u0623\u0648\u0644\u064a\u0629 \u0645\u0646 \u0627\u0644\u0646\u0645\u0648\u0630\u062c\u061b \u0644\u0627 \u062a\u0648\u062c\u062f \u062c\u0645\u0644\u0629 \u0639\u0631\u0628\u064a\u0629 \u0645\u0624\u0643\u062f\u0629 \u0645\u0637\u0627\u0628\u0642\u0629 \u0641\u064a \u0627\u0644\u0642\u0627\u0645\u0648\u0633",
            )
        normalized = normalise_arabic(arabic)
        supported = normalized in self.cashier_targets
        display = self.cashier_targets[normalized] if supported else arabic
        if cashier_mode and not supported:
            return RecognitionOutput(
                display, glosses, key, score, elapsed_ms, False,
                "The model recognized Arabic text, but it is not one of the verified cashier target phrases",
            )
        return RecognitionOutput(
            display, glosses, key, score, elapsed_ms, supported,
            "Real ONNX translation completed",
        )
