from __future__ import annotations

import json
import os
import plistlib
import subprocess
import sys
from pathlib import Path


def run(command: list[str]) -> str:
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    return completed.stdout.strip()


def main() -> int:
    if sys.platform != "darwin":
        raise SystemExit("This verifier must run on the macOS GitHub Actions runner.")

    app = Path(sys.argv[1] if len(sys.argv) > 1 else "dist/ISHARA.app").resolve()
    executable = app / "Contents" / "MacOS" / "ISHARA"
    plist_path = app / "Contents" / "Info.plist"
    if not executable.is_file() or not plist_path.is_file():
        raise SystemExit(f"Invalid application bundle: {app}")

    machine = run(["uname", "-m"])
    architectures = run(["lipo", "-archs", str(executable)]).split()
    if machine != "arm64" or "arm64" not in architectures:
        raise SystemExit(
            f"Expected an arm64 runner and executable; runner={machine}, binary={architectures}"
        )

    with plist_path.open("rb") as handle:
        plist = plistlib.load(handle)
    camera_reason = str(plist.get("NSCameraUsageDescription", "")).strip()
    if not camera_reason:
        raise SystemExit("NSCameraUsageDescription is missing from Info.plist")

    runtime_report = Path("artifacts/bundled_runtime_verification.json").resolve()
    runtime_report.parent.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ)
    environment["ISHARA_VERIFY_OUTPUT"] = str(runtime_report)
    subprocess.run(
        [str(executable), "--verify-runtime"],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
        timeout=60,
    )
    runtime = json.loads(runtime_report.read_text(encoding="utf-8"))
    if not runtime.get("frozen"):
        raise SystemExit("The runtime verifier did not execute from a frozen bundle")
    if runtime.get("resources_missing"):
        raise SystemExit(f"Missing bundled resources: {runtime['resources_missing']}")
    if not runtime.get("model_loaded") or runtime.get("inference_ms") is None:
        raise SystemExit(f"Bundled ONNX verification failed: {runtime}")

    report = {
        "runner_architecture": machine,
        "executable_architectures": architectures,
        "application": str(app),
        "camera_usage_description": camera_reason,
        "runtime": runtime,
        "camera_hardware_tested": False,
        "note": "No physical Mac camera is available on the GitHub-hosted runner.",
    }
    output = Path("artifacts/macos_build_verification.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
