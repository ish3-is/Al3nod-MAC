from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.auth import AuthService, hash_password, verify_password


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.service = AuthService(Path(self.temp.name) / "auth.db")
        self.service.initialize("cashier", "Ishara@2026")

    def tearDown(self):
        self.temp.cleanup()

    def test_correct_login(self):
        user = self.service.authenticate("cashier", "Ishara@2026")
        self.assertIsNotNone(user)
        self.assertEqual(user.role, "cashier")

    def test_wrong_login(self):
        self.assertIsNone(self.service.authenticate("cashier", "wrong"))
        self.assertIsNone(self.service.authenticate("", ""))

    def test_password_is_hashed(self):
        stored = self.service.stored_password_value("cashier")
        self.assertIsNotNone(stored)
        self.assertNotEqual(stored, "Ishara@2026")
        self.assertTrue(stored.startswith("pbkdf2_sha256$"))

    def test_hash_verification(self):
        encoded = hash_password("secret")
        self.assertTrue(verify_password("secret", encoded))
        self.assertFalse(verify_password("other", encoded))


if __name__ == "__main__":
    unittest.main()
