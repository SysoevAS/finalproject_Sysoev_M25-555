from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Dict

import requests

from ..core.exceptions import ApiRequestError
from .config import ParserConfig

logger = logging.getLogger(__name__)


class BaseApiClient(ABC):
    def __init__(self, config: ParserConfig) -> None:
        self.config = config

    @abstractmethod
    def fetch_rates(self) -> Dict[str, float]:
        raise NotImplementedError


class CoinGeckoClient(BaseApiClient):
    def fetch_rates(self) -> Dict[str, float]:
        ids = ",".join(
            self.config.CRYPTO_ID_MAP[code]
            for code in self.config.CRYPTO_CURRENCIES
        )
        params = {
            "ids": ids,
            "vs_currencies": self.config.BASE_CURRENCY.lower(),
        }
        try:
            resp = requests.get(
                self.config.COINGECKO_URL,
                params=params,
                timeout=self.config.REQUEST_TIMEOUT,
            )
        except requests.exceptions.RequestException as exc:
            raise ApiRequestError(f"CoinGecko network error: {exc}") from exc

        if resp.status_code != 200:
            raise ApiRequestError(
                f"CoinGecko HTTP {resp.status_code}: {resp.text[:200]}"
            )

        data = resp.json()
        result: Dict[str, float] = {}
        for code in self.config.CRYPTO_CURRENCIES:
            coin_id = self.config.CRYPTO_ID_MAP[code]
            price_info = data.get(coin_id, {})
            value = price_info.get(self.config.BASE_CURRENCY.lower())
            if value is not None:
                pair = f"{code}_{self.config.BASE_CURRENCY}"
                result[pair] = float(value)
        logger.info("CoinGecko fetched %d rates", len(result))
        return result


class ExchangeRateApiClient(BaseApiClient):
    def fetch_rates(self) -> Dict[str, float]:
        if not self.config.EXCHANGERATE_API_KEY:
            raise ApiRequestError(
                "EXCHANGERATE_API_KEY не задан в переменных окружения"
            )

        url = (
            f"{self.config.EXCHANGERATE_API_URL}/"
            f"{self.config.EXCHANGERATE_API_KEY}/latest/"
            f"{self.config.BASE_CURRENCY}"
        )
        try:
            resp = requests.get(
                url,
                timeout=self.config.REQUEST_TIMEOUT,
            )
        except requests.exceptions.RequestException as exc:
            raise ApiRequestError(
                f"ExchangeRate-API network error: {exc}"
            ) from exc

        if resp.status_code != 200:
            raise ApiRequestError(
                f"ExchangeRate-API HTTP {resp.status_code}: "
                f"{resp.text[:200]}"
            )

        data = resp.json()
        if data.get("result") != "success":
            raise ApiRequestError(
                f"ExchangeRate-API error: {data.get('error-type')}"
            )

        rates = data.get("rates", {})
        result: Dict[str, float] = {}
        for code in self.config.FIAT_CURRENCIES:
            if code == self.config.BASE_CURRENCY:
                continue
            value = rates.get(code)
            if value is not None:
                pair = f"{code}_{self.config.BASE_CURRENCY}"
                result[pair] = float(value)
        logger.info("ExchangeRate-API fetched %d rates", len(result))
        return result
