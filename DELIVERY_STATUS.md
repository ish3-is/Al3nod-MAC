# Delivery Status — Offline AI Upgrade

## Completed

- Preserved the existing authentication, four screens, database, student data, and explicit Demo Simulation.
- Added the real DF-Team phone-v1 ONNX model and upstream SF1 assets under `ai/models/`.
- Added MediaPipe Holistic → SF1 conversion for pose, face, and both hands.
- Added 15 FPS resampling, CPU ONNX inference, greedy CTC decoding, and exact Arabic lookup.
- Added safe cashier vocabulary filtering with no invented phrase substitutions.
- Added asynchronous inference to the PySide6 and Tkinter interfaces.
- Added recorded-video inference, Windows setup/run scripts, model documentation, and actual test evidence.
- Added a separate Saudi Arabic number mode for documented static digits 0-9, with a live result and stability filter.
- Refined the dark navy/teal PySide6 interface with gradients, stronger cards, and a large number result panel.
- Passed 27/27 automated tests and the Tkinter application smoke test.
- Added a macOS 15 ARM64 GitHub Actions pipeline that builds and verifies
  `ISHARA.app`; the final Mac ZIP is produced only after that workflow succeeds.
- Stop Translation now always opens a result or a clear tracking diagnostic; unmapped CTC tokens remain visible as unconfirmed model output.

## Environment limitations

- The physical camera probe was attempted but no device was exposed by this host. The Windows build now tries camera indexes 0, 1, and 2 using DirectShow, Media Foundation, and the default OpenCV backend.
- MediaPipe installation was attempted, but PyPI DNS was blocked.
- No real labeled sign video was supplied; therefore semantic recognition on video was not executed.
- The ONNX file itself loaded and ran successfully with the expected input/output contract.
- Number mode is intentionally limited to static 0-9 poses. Larger values in
  the reference chart require additional movement/two-hand modeling and are not claimed.

See `ACTUAL_TEST_RESULTS.md` and `artifacts/verification_results.json`.

