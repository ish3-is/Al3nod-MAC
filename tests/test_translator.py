from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np

from ai.models.feats import FEAT_DIM, from_holistic, resample
from ai.pretrained_sign_recognizer import PretrainedSignRecognizer
from ai.translator import TranslationEngine
from config import MODEL_DIR, TARGET_PHRASES


class TranslatorTests(unittest.TestCase):
    def test_missing_model_is_unavailable_not_fake_demo(self):
        with tempfile.TemporaryDirectory() as temp:
            engine = TranslationEngine(Path(temp))
            self.assertEqual(engine.mode, "unavailable")
            result = engine.classify(None)
            self.assertFalse(result.confirmed)
            self.assertIsNone(result.phrase)

    def test_demo_result_is_labeled_and_has_no_fake_confidence(self):
        engine = TranslationEngine(MODEL_DIR)
        result = engine.simulate(TARGET_PHRASES[0])
        self.assertTrue(result.confirmed)
        self.assertEqual(result.source, "demo")
        self.assertIsNone(result.confidence)
        self.assertIn("Demo Simulation", result.status)

    def test_real_onnx_loads_and_accepts_sf1(self):
        recognizer = PretrainedSignRecognizer(MODEL_DIR)
        self.assertTrue(recognizer.available, recognizer.status)
        result = recognizer.recognize(np.zeros((15, FEAT_DIM), np.float32))
        self.assertGreater(result.inference_ms, 0)
        self.assertIsInstance(result.status, str)

    def test_ctc_collapse_and_vocab_lookup(self):
        recognizer = PretrainedSignRecognizer(MODEL_DIR)
        token = recognizer.vocab["glosses"].index("شكر") + 1
        logits = np.full((5, 673), -20.0, np.float32)
        logits[0, 0] = 0.0
        logits[1, token] = 0.0
        logits[2, token] = 0.0
        logits[3, 0] = 0.0
        logits[4, token] = 0.0
        glosses, key, arabic, score = recognizer.decode_ctc(logits)
        self.assertEqual(glosses, ("شكر", "شكر"))
        self.assertEqual(key, "شكر شكر")
        self.assertIsNone(arabic)
        self.assertAlmostEqual(score, 1.0, places=5)

    def test_documented_thanks_mapping_is_cashier_supported(self):
        recognizer = PretrainedSignRecognizer(MODEL_DIR)
        token = recognizer.vocab["glosses"].index("شكر") + 1
        logits = np.full((3, 673), -20.0, np.float32)
        logits[0, 0] = logits[2, 0] = 0.0
        logits[1, token] = 0.0
        glosses, key, arabic, _ = recognizer.decode_ctc(logits)
        self.assertEqual(glosses, ("شكر",))
        self.assertEqual(key, "شكر")
        self.assertEqual(arabic, "شكرا")
        self.assertTrue(recognizer.cashier_support["شكرًا"])

    def test_official_sf1_shape_and_resampling(self):
        xyz = np.zeros((543, 3), dtype=np.float32)
        conf = np.zeros(543, dtype=np.float32)
        xyz[11] = [100, 100, 0]
        xyz[12] = [200, 100, 0]
        conf[11] = conf[12] = 1
        feature = from_holistic(xyz, conf, 640, 480)
        self.assertEqual(feature.shape, (356,))
        self.assertEqual(feature.dtype, np.float32)
        sampled = resample(np.stack([feature, feature]), [0.0, 100.0], fps=15)
        self.assertEqual(sampled.shape[1], 356)

    def test_unknown_sign_is_not_translated(self):
        result = TranslationEngine(MODEL_DIR).unknown()
        self.assertFalse(result.confirmed)
        self.assertIsNone(result.phrase)

    def test_missing_tracking_sequence_returns_visible_diagnostic(self):
        result = TranslationEngine(MODEL_DIR).classify(None)
        self.assertFalse(result.confirmed)
        self.assertIsNone(result.phrase)
        self.assertIn("MediaPipe", result.status)

    def test_unmapped_ctc_tokens_are_visible_but_unconfirmed(self):
        recognizer = PretrainedSignRecognizer(MODEL_DIR)
        lookup = recognizer.vocab["lookup"]
        gloss = next(item for item in recognizer.vocab["glosses"] if item not in lookup)
        token = recognizer.vocab["glosses"].index(gloss) + 1
        logits = np.full((3, 673), -20.0, np.float32)
        logits[0, 0] = logits[2, 0] = 0.0
        logits[1, token] = 0.0

        class FakeSession:
            def run(self, *_):
                return [logits[None, ...]]

        recognizer.session = FakeSession()
        output = recognizer.recognize(np.zeros((15, FEAT_DIM), np.float32))
        self.assertEqual(output.arabic, gloss.replace("_", " "))
        self.assertFalse(output.supported_for_cashier)
        self.assertIn("\u0645\u062e\u0631\u062c\u0627\u062a \u0623\u0648\u0644\u064a\u0629", output.status)

    def test_invalid_demo_phrase_is_rejected(self):
        result = TranslationEngine(MODEL_DIR).simulate("غير موجود")
        self.assertFalse(result.confirmed)
        self.assertIsNone(result.phrase)


if __name__ == "__main__":
    unittest.main()

