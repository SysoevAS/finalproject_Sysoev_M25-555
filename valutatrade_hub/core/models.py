from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict

from .exceptions import InsufficientFundsError


def _hash_password(password: str, salt: str) -> str:
    data = (password + salt).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


@dataclass
class User:
    _user_id: int
    _username: str
    _hashed_password: str
    _salt: str
    _registration_date: datetime

    @classmethod
    def create(cls, user_id: int, username: str, password: str) -> "User":
        if not username:
            raise ValueError("Имя пользователя не может быть пустым")
        if len(password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")

        salt = secrets.token_hex(8)
        hashed = _hash_password(password, salt)
        return cls(
            _user_id=user_id,
            _username=username,
            _hashed_password=hashed,
            _salt=salt,
            _registration_date=datetime.utcnow(),
        )

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, value: str) -> None:
        if not value:
            raise ValueError("Имя пользователя не может быть пустым")
        self._username = value

    @property
    def registration_date(self) -> datetime:
        return self._registration_date

    @property
    def salt(self) -> str:
        return self._salt

    @property
    def hashed_password(self) -> str:
        return self._hashed_password

    def get_user_info(self) -> dict:
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat(),
        }

    def change_password(self, new_password: str) -> None:
        if len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")
        self._salt = secrets.token_hex(8)
        self._hashed_password = _hash_password(new_password, self._salt)

    def verify_password(self, password: str) -> bool:
        expected = _hash_password(password, self._salt)
        return expected == self._hashed_password

    def to_json(self) -> dict:
        return {
            "user_id": self._user_id,
            "username": self._username,
            "hashed_password": self._hashed_password,
            "salt": self._salt,
            "registration_date": self._registration_date.isoformat(),
        }

    @classmethod
    def from_json(cls, data: dict) -> "User":
        return cls(
            _user_id=int(data["user_id"]),
            _username=str(data["username"]),
            _hashed_password=str(data["hashed_password"]),
            _salt=str(data["salt"]),
            _registration_date=datetime.fromisoformat(
                str(data["registration_date"])
            ),
        )


@dataclass
class Wallet:
    currency_code: str
    _balance: float = field(default=0.0)

    def deposit(self, amount: float) -> None:
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом")
        if amount <= 0:
            raise ValueError("'amount' должен быть положительным числом")
        self._balance += float(amount)

    def withdraw(self, amount: float) -> None:
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом")
        if amount <= 0:
            raise ValueError("'amount' должен быть положительным числом")
        if amount > self._balance:
            raise InsufficientFundsError(
                available=self._balance,
                required=float(amount),
                code=self.currency_code,
            )
        self._balance -= float(amount)

    def get_balance_info(self) -> str:
        return f"{self.currency_code}: {self._balance:.4f}"

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, value: float) -> None:
        if not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self._balance = float(value)

    def to_json(self) -> dict:
        return {
            "currency_code": self.currency_code,
            "balance": self._balance,
        }

    @classmethod
    def from_json(cls, code: str, data: dict) -> "Wallet":
        return cls(currency_code=code, _balance=float(data["balance"]))


@dataclass
class Portfolio:
    _user_id: int
    _wallets: Dict[str, Wallet]

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def wallets(self) -> Dict[str, Wallet]:
        return dict(self._wallets)

    def add_currency(self, currency_code: str) -> Wallet:
        code = currency_code.upper()
        if code in self._wallets:
            return self._wallets[code]
        wallet = Wallet(currency_code=code, _balance=0.0)
        self._wallets[code] = wallet
        return wallet

    def get_wallet(self, currency_code: str) -> Wallet | None:
        return self._wallets.get(currency_code.upper())

    def get_total_value(
        self,
        exchange_rates: dict,
        base_currency: str = "USD",
    ) -> float:
        total = 0.0
        base = base_currency.upper()
        for code, wallet in self._wallets.items():
            if code == base:
                total += wallet.balance
                continue
            pair = f"{code}_{base}"
            rate_info = exchange_rates.get(pair)
            if not rate_info:
                continue
            rate = float(rate_info["rate"])
            total += wallet.balance * rate
        return total

    def to_json(self) -> dict:
        wallets_data = {
            code: {"balance": wallet.balance}
            for code, wallet in self._wallets.items()
        }
        return {
            "user_id": self._user_id,
            "wallets": wallets_data,
        }

    @classmethod
    def from_json(cls, data: dict) -> "Portfolio":
        wallets_raw = data.get("wallets", {})
        wallets: Dict[str, Wallet] = {}
        for code, wallet_data in wallets_raw.items():
            wallets[code.upper()] = Wallet.from_json(code, wallet_data)
        return cls(_user_id=int(data["user_id"]), _wallets=wallets)
