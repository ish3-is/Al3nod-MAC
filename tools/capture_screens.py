from __future__ import annotations

import sys
import time
import tkinter as tk
from pathlib import Path

from PIL import ImageGrab

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import DEMO_PASSWORD, DEMO_USERNAME
from ui.tk_fallback import IsharaTkApp


def capture(root: tk.Tk, destination: Path) -> None:
    root.update_idletasks()
    root.update()
    time.sleep(.25)
    x = root.winfo_rootx()
    y = root.winfo_rooty()
    width = root.winfo_width()
    height = root.winfo_height()
    ImageGrab.grab((x, y, x + width, y + height)).save(destination)


def main() -> int:
    output = ROOT / "assets" / "screenshots"
    output.mkdir(parents=True, exist_ok=True)
    root = tk.Tk()
    root.geometry("1280x780+30+30")
    app = IsharaTkApp(root)
    root.attributes("-topmost", True)
    capture(root, output / "01_login.png")
    app.username_var.set(DEMO_USERNAME)
    app.password_var.set(DEMO_PASSWORD)
    app.login()
    capture(root, output / "02_translation.png")
    app.run_demo()
    capture(root, output / "03_result.png")
    app.show_page("about")
    capture(root, output / "04_about.png")
    app.close()
    print(f"Captured 4 actual application screens in {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
