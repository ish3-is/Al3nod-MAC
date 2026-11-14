# ISHARA | إشارة

ISHARA is a Python desktop application for communication between Saudi Sign Language users and cashiers. The existing login, camera, result, About, SQLite, and Demo Simulation features are preserved. The default AI path now loads the bundled **DF-Team/sli-sentences phone v1 ONNX model** on CPU.

## Demo cashier account

- Username: `cashier`
- Password: `Ishara@2026`

SQLite stores a PBKDF2-SHA256 salted password hash, not the plain password.

## Fast Windows setup

Python 3.11 or 3.12 (64-bit) is recommended.

For the standalone Apple Silicon build (M1/M2/M3), see `README-Mac.md`. The
recipient does not install Python; GitHub Actions creates `ISHARA.app` using the
`macos-15` ARM64 runner.

1. Extract `ISHARA_Updated_Project.zip`.
2. Double-click `setup_windows.bat` once.
3. Double-click `run_windows.bat`.
4. Log in, press **Start Translation**, perform one sign sentence while your face, shoulders, and both hands are visible, then press **Stop Translation**.
5. The UI changes to **Processing** while ONNX inference runs outside the UI thread.

### Arabic number mode (0-9)

1. Select **الأرقام ٠-٩** from **وضع التعرف**.
2. Press **Start Translation**.
3. Show one documented Saudi Arabic digit pose clearly to the camera and keep it still for about one second.
4. The detected Arabic digit appears live. Press **Stop Translation** to open the final result page.

This mode uses MediaPipe's 21 hand landmarks plus a stability filter. Its ten
finger-extension patterns follow the supplied Saudi sign-number chart. It does
not claim support for 10, 20, 100, or other moving/two-hand number signs.

### Sign guide page

After login, press **دليل الإشارات** to open the two supplied reference charts:

- **عبارات يومية:** common and social signs from the supplied chart.
- **إشارات الكاشير:** the supplied cashier and beverage reference chart.

These charts are visual learning aids only. They are deliberately separate from
the AI result pipeline: a pictured gesture is not reported as recognized unless
the active model genuinely supports and predicts it. This prevents a five-finger
pose from being mislabeled as both the number 5 and a phrase such as “hello”.

Manual equivalent:

```powershell
cd ISHARA
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

If PySide6 is unavailable, run the functional Tkinter UI:

```powershell
python main.py --fallback
```

## Real AI pipeline

```text
Camera → MediaPipe Holistic → official SF1 features → 15 FPS resampling
       → ONNX Runtime CPU → greedy CTC decoding → vocab.json Arabic lookup
```

The bundled model expects `float32 [1, T, 356]` named `feats`, with 8–450 resampled frames. SF1 contains normalized pose, face, left-hand, right-hand coordinates plus presence flags. Raw hand coordinates are never sent directly to ONNX.

The AI model and Demo Simulation are separate:

- **Real AI:** camera/video-derived SF1 data, ONNX inference, CTC output, and vocabulary lookup.
- **Visible outcome:** Stop Translation always opens the result page. Exact
  vocabulary matches show Arabic text; other CTC tokens are shown as
  unconfirmed model output, and missing tracking reports a clear diagnostic.
- **Demo Simulation:** an explicitly labeled manual UI demonstration with no AI confidence claim.
- **Number recognition:** a separate 0-9 landmark classifier; it does not send
  a static finger pose to the sentence model.

## Cashier phrases verified against vocab.json

| Requested phrase | Exact vocabulary support |
|---|---|
| كم الحساب؟ | Not found |
| كم الباقي؟ | Not found |
| شكرًا | Supported as model sentence `شكرا` |
| أريد الدفع | Not found |

The vocabulary also contains related sentences such as `لم تعطيني باقي النقود`, but ISHARA does **not** relabel that sentence as `كم الباقي؟`. In cashier mode, only an exact verified target is marked confirmed; other decoded Arabic remains visibly unconfirmed.

## Recorded-video test

After installing MediaPipe:

```powershell
python tools\run_video_inference.py path\to\real_sign_video.mp4
```

The command prints the decoded Arabic, CTC glosses, score, timing, and cashier-support status. A real Saudi Sign Language video must match a sentence supported by the supplied model vocabulary.

## Verification

```powershell
python -m unittest discover -s tests -p "test_*.py"
python tools\run_verification.py
```

Actual verification is saved to `artifacts/verification_results.json`. The test runner checks authentication, navigation/session behavior, packaged guide images, camera adapters, SF1 shape/resampling, real ONNX loading, a real `[1,15,356]` inference, CTC collapse, and Arabic vocabulary mapping.

## Camera troubleshooting

- Enable **Settings → Privacy & security → Camera → Let desktop apps access your camera**.
- Close Teams, Zoom, OBS, or browser tabs that may own the camera.
- Keep face, shoulders, and both hands inside the frame.
- Use even lighting and a plain background.
- The model accepts about 0.5–30 seconds after 15 FPS resampling.
- If MediaPipe is missing, the app reports it and does not fabricate a result.
- The app automatically tries camera indexes 0, 1, and 2 through DirectShow,
  Media Foundation, and OpenCV's default backend on Windows.
- To force a specific device, set `ISHARA_CAMERA_INDEX` before launch, for
  example: `set ISHARA_CAMERA_INDEX=1` then run `run_windows.bat`.

## Important limitations

- This is a pretrained research model, not a certified accessibility product.
- Its vocabulary is limited; it outputs CTC glosses and only sentences present in `vocab.json` become Arabic.
- The included model was loaded and executed in the delivery environment. MediaPipe installation was blocked there by DNS, so a live end-to-end camera-to-model test was not claimed.
- No new accuracy, precision, recall, or F1 numbers were invented. The project does not retrain the model.
- Model weights are licensed CC BY-NC-SA 4.0; the reference code is MIT. See `AI_MODEL_INTEGRATION.md`.

## Key files

- `ai/pretrained_sign_recognizer.py` — ONNX validation, inference, CTC, Arabic lookup.
- `ai/holistic_tracker.py` — MediaPipe Holistic to official SF1.
- `ai/models/feats.py` — upstream SF1 feature implementation.
- `ui/pyside_app.py`, `ui/tk_fallback.py` — asynchronous camera/inference integration.
- `setup_windows.bat`, `run_windows.bat` — one-click Windows setup/run.

