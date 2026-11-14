from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    verification_path = Path("artifacts/macos_build_verification.json")
    archive = Path("ISHARA-macOS-M2.zip")
    verification = json.loads(verification_path.read_text(encoding="utf-8"))
    runtime = verification["runtime"]
    lines = [
        "# ISHARA macOS M2 Build Report",
        "",
        "## Result",
        "",
        "- Build: **PASS**",
        f"- Git commit: `{os.getenv('GITHUB_SHA', 'local')}`",
        f"- Workflow run: `{os.getenv('GITHUB_RUN_ID', 'local')}`",
        f"- Runner architecture: `{verification['runner_architecture']}`",
        f"- Executable architectures: `{', '.join(verification['executable_architectures'])}`",
        f"- Python: `{runtime['python']}`",
        f"- PySide6: `{runtime['versions']['PySide6']}`",
        f"- MediaPipe: `{runtime['versions']['MediaPipe']}`",
        f"- ONNX Runtime: `{runtime['versions']['ONNXRuntime']}`",
        f"- OpenCV: `{runtime['versions']['OpenCV']}`",
        f"- Bundled model loaded: `{runtime['model_loaded']}`",
        f"- Synthetic SF1 inference: `{runtime['inference_ms']} ms`",
        f"- Missing resources: `{runtime['resources_missing']}`",
        f"- Archive size: `{archive.stat().st_size}` bytes",
        f"- Archive SHA-256: `{sha256(archive)}`",
        "",
        "## Scope and limitations",
        "",
        "- The ONNX test used a correctly shaped synthetic `[15, 356]` SF1 sequence.",
        "- This proves bundle loading and inference plumbing, not sign-recognition accuracy.",
        "- A physical camera was not available on the GitHub-hosted macOS runner.",
        "- The application is ad-hoc signed for bundle integrity, not Developer ID signed or notarized.",
    ]
    output = Path("artifacts/MACOS_BUILD_REPORT.md")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(output.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
