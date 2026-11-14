# macOS Apple Silicon Build Status

## Repository preparation

- Status: **READY FOR GITHUB ACTIONS**
- Target runner: `macos-15` (`arm64`)
- Target Python: `3.11`
- Packaging: PyInstaller `--windowed --onedir`
- Expected output: `ISHARA-macOS-M2.zip`

## Local validation performed on Windows

- Python source compilation and unit tests are executed before delivery.
- The ONNX model is present and can be validated from the source tree.
- macOS bundle creation is intentionally not claimed on Windows.

## GitHub-generated evidence

After the workflow succeeds, the downloaded Artifact contains:

- `ISHARA-macOS-M2.zip`
- `macos_build_verification.json`
- `MACOS_BUILD_REPORT.md`

Those generated reports are the authoritative evidence for the macOS ARM64
build, bundled ONNX load, synthetic SF1 inference, and resource checks. A real
camera test must be performed on the recipient's Mac.
