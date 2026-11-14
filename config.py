from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "ISHARA | إشارة"
PROJECT_TITLE = "Neural Translation Architecture for Sign Language-Based Cashier Communication"
COURSE_NAME = "Advanced Software Engineering"
COURSE_CODE = "501446-3"
INSTRUCTOR = "Dr. Azhar Al-Sufyani — د. أزهار السفياني"
DEADLINE = "Sunday, November 15, 2026"

def _resource_root() -> Path:
    """Return the source root or PyInstaller's bundled resource root."""
    if not getattr(sys, "frozen", False):
        return Path(__file__).resolve().parent

    candidates = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass))

    executable = Path(sys.executable).resolve()
    candidates.extend(
        [
            executable.parent,
            executable.parent.parent / "Resources",
            executable.parent.parent / "Frameworks",
        ]
    )
    for candidate in candidates:
        if (candidate / "ai" / "models").is_dir():
            return candidate
    return candidates[0] if candidates else Path(__file__).resolve().parent


def _writable_data_dir() -> Path:
    """Keep mutable SQLite data outside a frozen macOS application bundle."""
    if getattr(sys, "frozen", False) and sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "ISHARA"
    override = os.getenv("ISHARA_DATA_DIR", "").strip()
    return Path(override).expanduser() if override else BASE_DIR / "database"


BASE_DIR = _resource_root()
DATA_DIR = _writable_data_dir()
MODEL_DIR = BASE_DIR / "ai" / "models"
ASSET_DIR = BASE_DIR / "assets"
DB_PATH = DATA_DIR / "ishara.db"

DEMO_USERNAME = "cashier"
DEMO_PASSWORD = "Ishara@2026"

TARGET_PHRASES = (
    "كم الحساب؟",
    "كم الباقي؟",
    "شكرًا",
    "أريد الدفع",
)

STUDENTS = (
    ("العنود فاصل السبيعي", "44501823"),
    ("عهود مفرح السبيعي", "44501331"),
    ("سارة ابراهيم محمد الدوسري", "44508026"),
    ("غلا مطلق السبيعي", "44554025"),
    ("رغد بداح السبيعي", "44502746"),
    ("اروى عبدالرحمن عامر الدوسري", "44505324"),
    ("بدراء مسفر السبيعي", "44506241"),
)

COLORS = {
    "background": "#07111F",
    "surface": "#101D2D",
    "surface_alt": "#16263A",
    "accent": "#13D8C3",
    "text": "#F5F7FA",
    "secondary": "#91A3B8",
    "danger": "#FF6B7A",
    "warning": "#F6C85F",
    "success": "#4ADE80",
}
