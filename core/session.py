from __future__ import annotations

from dataclasses import dataclass

from core.auth import User


@dataclass
class Session:
    user: User | None = None

    @property
    def authenticated(self) -> bool:
        return self.user is not None

    def login(self, user: User) -> None:
        self.user = user

    def logout(self) -> None:
        self.user = None
