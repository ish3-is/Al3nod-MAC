# ISHARA — Actual Offline Integration Test Results

Generated: 14 November 2026 (Saudi Arabia)

## Outcome

The bundled `sli-sentences-phone-v1.onnx` file was loaded and executed with ONNX Runtime CPU. The complete automated test suite and the application fallback smoke test passed. The host did not expose a camera and could not install MediaPipe because PyPI DNS resolution was blocked, so no live-camera semantic recognition claim is made.

## Actual results

| Test | Actual result | Evidence |
|---|---|---|
| ONNX file present and readable | PASS | 17,935,987 bytes; SHA-256 recorded in `AI_MODEL_INTEGRATION.md` |
| ONNX Runtime CPU load | PASS | `CPUExecutionProvider` |
| Input contract | PASS | `feats: float32 [1,T,356]` |
| Output contract | PASS | `logprobs: float32 [1,T2,673]` |
| Real inference execution | PASS | Input `[1,15,356]`; measured 3.018 ms model inference in the final run |
| Finite model output | PASS | Output returned normally |
| SF1 feature construction | PASS | Official `from_holistic()` produced 356 float32 values |
| 15 FPS resampling | PASS | Official `resample()` unit test |
| CTC repeat collapse / blank removal | PASS | Crafted deterministic logits |
| CTC gloss-to-Arabic lookup | PASS | Supplied `vocab.json`; `شكر` → `شكرا` |
| Unsupported cashier phrases | PASS | No false mapping created |
| Valid login / invalid login | PASS | Automated tests |
| Session and protected navigation | PASS | Automated tests |
| Camera adapter start/stop/failure | PASS | Injected capture tests plus Windows USB/backend fallback |
| Physical camera probe | NOT AVAILABLE | No device was exposed; the app now tries indexes 0-2 and Windows backends |
| MediaPipe Holistic on this host | NOT AVAILABLE | Installation attempt failed due DNS |
| Real labeled sign video | NOT PROVIDED | No semantic video result claimed |
| Tkinter application launch/close | PASS | Timed smoke test |
| Arabic digits 0-9 pattern table | PASS | All ten reference patterns mapped exactly once |
| Number stability / changing-hand rejection | PASS | Automated deterministic tests |
| Full automated suite | PASS | 27/27 passed after number mode, guide assets, and macOS data-path integration |

## Model timing interpretation

The measured 3.018 ms is one CPU inference on a synthetic zero SF1 tensor. It proves that the local ONNX graph loads and executes with the expected dimensions. It is not an accuracy result and does not prove recognition of a real sign.

## Vocabulary audit

- `شكرًا`: exact supported output after Arabic normalization.
- `كم الحساب؟`: not present exactly.
- `كم الباقي؟`: not present exactly.
- `أريد الدفع`: not present exactly.
- Related phrases remain unchanged and are shown as unconfirmed in cashier mode.

Machine-readable evidence is in `artifacts/verification_results.json`.

## macOS ARM64 build verification

The repository now contains an Apple Silicon GitHub Actions build. Windows
cannot create or validate `ISHARA.app`; therefore no macOS bundle success is
claimed in this local report. A successful `macos-15` workflow generates the
authoritative `macos_build_verification.json` and `MACOS_BUILD_REPORT.md`, which
verify the ARM64 executable, bundled resources, Info.plist camera description,
and ONNX inference from inside the frozen application. The hosted runner has no
physical camera, so camera hardware remains a recipient-device test.

