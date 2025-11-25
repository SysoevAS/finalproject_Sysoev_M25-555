from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict

from .exceptions import CurrencyNotFoundError


class Currency(ABC):
    """Базовый класс валюты."""

    name: str
    code: str

    def __init__(self, name: str, code: str) -> None:
        code_upper = code.upper()
        if not (2 <= len(code_upper) <= 5) or " " in code_upper:
            raise ValueError("Некорректный код валюты")
        if not name:
            raise ValueError("Имя валюты не может быть пустым")
        self.name = name
        self.code = code_upper

    @abstractmethod
    def get_display_info(self) -> str:
        """Строка для UI/логов."""
        raise NotImplementedError


@dataclass
class FiatCurrency(Currency):
    issuing_country: str = "Unknown"

    def __init__(self, name: str, code: str, issuing_country: str) -> None:
        super().__init__(name=name, code=code)
        self.issuing_country = issuing_country

    def get_display_info(self) -> str:
        return (
            f"[FIAT] {self.code} — {self.name} "
            f"(Issuing: {self.issuing_country})"
        )


@dataclass
class CryptoCurrency(Currency):
    algorithm: str = "Unknown"
    market_cap: float = 0.0

    def __init__(
        self,
        name: str,
        code: str,
        algorithm: str,
        market_cap: float,
    ) -> None:
        super().__init__(name=name, code=code)
        self.algorithm = algorithm
        self.market_cap = market_cap

    def get_display_info(self) -> str:
        return (
            f"[CRYPTO] {self.code} — {self.name} "
            f"(Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})"
        )

_CURRENCY_REGISTRY: Dict[str, Currency] = {
    "USD": FiatCurrency("US Dollar", "USD", "United States"),
    "EUR": FiatCurrency("Euro", "EUR", "Eurozone"),
    "RUB": FiatCurrency("Russian Ruble", "RUB", "Russia"),
    "BTC": CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12),
    "ETH": CryptoCurrency("Ethereum", "ETH", "Ethash", 4.5e11),
    "SOL": CryptoCurrency("Solana", "SOL", "Proof-of-History", 8.0e10),
}


def get_currency(code: str) -> Currency:
    """Получить объект валюты по коду или кинуть CurrencyNotFoundError."""
    normalized = code.upper()
    currency = _CURRENCY_REGISTRY.get(normalized)
    if not currency:
        raise CurrencyNotFoundError(code=normalized)
    return currency
