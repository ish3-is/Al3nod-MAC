from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

import config
from config import ASSET_DIR, STUDENTS
from core.auth import User
from core.session import Session


class SessionAndContentTests(unittest.TestCase):
    def test_login_logout_guards_session(self):
        session = Session()
        self.assertFalse(session.authenticated)
        session.login(User("cashier", "الكاشير", "cashier"))
        self.assertTrue(session.authenticated)
        session.logout()
        self.assertFalse(session.authenticated)

    def test_student_data_exact_and_complete(self):
        expected = (
            ("العنود فاصل السبيعي", "44501823"),
            ("عهود مفرح السبيعي", "44501331"),
            ("سارة ابراهيم محمد الدوسري", "44508026"),
            ("غلا مطلق السبيعي", "44554025"),
            ("رغد بداح السبيعي", "44502746"),
            ("اروى عبدالرحمن عامر الدوسري", "44505324"),
            ("بدراء مسفر السبيعي", "44506241"),
        )
        self.assertEqual(STUDENTS, expected)

    def test_sign_guide_assets_are_packaged(self):
        guide_dir = ASSET_DIR / "sign_guides"
        expected_sizes = {
            "social_signs.png": 179877,
            "cashier_signs.png": 206987,
        }
        for name, minimum_size in expected_sizes.items():
            asset = guide_dir / name
            self.assertTrue(asset.is_file(), f"Missing sign guide asset: {name}")
            self.assertGreaterEqual(asset.stat().st_size, minimum_size)

    def test_frozen_macos_database_uses_application_support(self):
        with (
            patch.object(config.sys, "frozen", True, create=True),
            patch.object(config.sys, "platform", "darwin"),
            patch.object(Path, "home", return_value=Path("/Users/tester")),
        ):
            self.assertEqual(
                config._writable_data_dir(),
                Path("/Users/tester/Library/Application Support/ISHARA"),
            )


if __name__ == "__main__":
    unittest.main()
