# Bundled DF-Team sentence model

Required runtime assets:

- `sli-sentences-phone-v1.onnx`
- `vocab.json`
- `feats.py`
- `face_idx.json`
- `conventions.json`

Source: https://huggingface.co/DF-Team/sli-sentences

The ONNX file is loaded by `ai/pretrained_sign_recognizer.py`. The preprocessing files implement the upstream SF1 contract. Do not replace `feats.py` with raw hand coordinates.

Weights license: CC BY-NC-SA 4.0. See the root `AI_MODEL_INTEGRATION.md` for hashes, runtime dimensions, testing, and limitations.

