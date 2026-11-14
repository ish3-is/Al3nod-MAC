# ISHARA AI Model Integration

## Integrated model

- Repository: https://huggingface.co/DF-Team/sli-sentences
- Reference implementation: https://github.com/Digital-Fingers-Team/sli-ai
- File: `sli-sentences-phone-v1.onnx`
- Runtime: ONNX Runtime CPU
- Bundled size: 17,935,987 bytes
- SHA-256: `59F47F5DC7FFC02F00DF6B0563BEAD2ECA0DE15B4BD96851B0C690AB8F58E805`
- Weights license: CC BY-NC-SA 4.0
- Reference code license: MIT

## Verified runtime contract

The local file was opened by ONNX Runtime with `CPUExecutionProvider`.

| Contract item | Observed value |
|---|---|
| Input name | `feats` |
| Input type | `tensor(float)` |
| Input shape | `[1, T, 356]` |
| Output name | `logprobs` |
| Output shape | `[1, T2, 673]` |
| Vocabulary | 672 glosses + CTC blank class 0 |
| Arabic lookup entries | 1,161 |
| Test input | `float32 [1, 15, 356]` |
| Test output | `float32 [1, 8, 673]` |

The synthetic test verifies loading, dimensions, execution, finite outputs, and decoding plumbing. It is not a recognition-accuracy test.

## SF1 preprocessing

ISHARA bundles the upstream files without redesigning the feature layout:

- `feats.py`
- `face_idx.json`
- `conventions.json`
- `vocab.json`

Each frame contains 176 normalized 2D points and four presence flags:

- Pose: 6 points
- Face: 128 points
- Signer's left hand: 21 points
- Signer's right hand: 21 points
- Presence: pose, face, left hand, right hand

MediaPipe Holistic produces 33 pose + 468 face + 21 left-hand + 21 right-hand points. `from_holistic()` normalizes each component using the upstream anchors/scales. `resample()` linearly resamples captured frames to 15 FPS. Missing components remain zero with a zero presence flag.

## Inference and CTC decoding

1. Validate `[T,356]` float32 and the supported 8–450 frame range.
2. Add batch dimension.
3. Run CPU ONNX inference.
4. Take argmax per output timestep.
5. Collapse adjacent repeated classes.
6. Remove blank class 0.
7. Map class `k` to `vocab["glosses"][k-1]`.
8. Join glosses and look up the exact key in `vocab["lookup"]`.
9. If the key is absent, show an unknown/unmapped status instead of inventing Arabic.

The displayed CTC score is an average posterior for selected token frames. It is a model score, not accuracy or a clinically calibrated probability.

## Cashier vocabulary audit

Exact target checks were performed against the supplied `vocab.json`.

- `شكرًا`: supported through lookup output `شكرا`.
- `كم الحساب؟`: no exact sentence.
- `كم الباقي؟`: no exact sentence.
- `أريد الدفع`: no exact sentence.

Related entries are not silently renamed. For example, `لم تعطيني باقي النقود` remains that exact sentence and is not presented as `كم الباقي؟`.

## Threading and UI behavior

Camera processing runs outside the UI event loop. Start clears the prior segment and begins camera/SF1 capture. Stop ends capture, displays Processing, resamples the collected sequence, and starts a separate inference thread. Result navigation occurs only after completion. Each Start/Stop cycle produces at most one inference, preventing repeated predictions.

## Separate Arabic digit recognizer

The sentence ONNX model is not used to guess isolated finger counts. ISHARA
adds a separate MediaPipe landmark classifier for the ten static Saudi Arabic
digit poses 0-9 documented in the supplied reference chart. It evaluates thumb,
index, middle, ring, and little-finger extension from joint angles and normalized
distances, then requires a consistent result across multiple camera frames.
This deterministic component is not described as a newly trained neural model,
and it does not support the chart's moving or two-hand numbers above 9.

## Actual execution limits

- ONNX Runtime, NumPy, and OpenCV were available.
- The actual ONNX model loaded and executed.
- Package installation for MediaPipe was attempted but the verification host could not resolve PyPI DNS.
- Therefore no end-to-end live MediaPipe camera recognition is claimed in that host.
- `setup_windows.bat` installs MediaPipe and PySide6 on a normal Windows machine with internet access.
- No labeled real sign video was included, so no semantic video result or new accuracy metric is claimed.

