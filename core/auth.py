from __future__ import annotations

import hashlib
import hmac
import os
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path


PBKDF2_ITERATIONS = 310_000


def hash_password(password: str, salt: bytes | None = None) -> str:
    if not password:
        raise ValueError("Password cannot be empty")
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
        )
        return hmac.compare_digest(actual.hex(), digest_hex)
    except (TypeError, ValueError):
        return False


@dataclass(frozen=True)
class User:
    username: str
    display_name: str
    role: str


class AuthService:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self, demo_username: str, demo_password: str) -> None:
        with closing(self._connect()) as connection:
            with connection:
                connection.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    password_hash TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
                exists = connection.execute(
                    "SELECT 1 FROM users WHERE username = ?", (demo_username,)
                ).fetchone()
                if not exists:
                    connection.execute(
                        "INSERT INTO users(username, password_hash, display_name, role) VALUES (?, ?, ?, ?)",
                        (demo_username, hash_password(demo_password), "الكاشير التجريبي", "cashier"),
                    )

    def authenticate(self, username: str, password: str) -> User | None:
        username = username.strip()
        if not username or not password:
            return None
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT username, password_hash, display_name, role FROM users "
                "WHERE username = ? AND is_active = 1",
                (username,),
            ).fetchone()
        if row and verify_password(password, row["password_hash"]):
            return User(row["username"], row["display_name"], row["role"])
        return None

    def stored_password_value(self, username: str) -> str | None:
        """Inspection helper used by automated security tests."""
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT password_hash FROM users WHERE username = ?", (username,)
            ).fetchone()
        return row[0] if row else None
