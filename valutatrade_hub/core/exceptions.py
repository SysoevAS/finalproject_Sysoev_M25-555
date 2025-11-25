class InsufficientFundsError(Exception):
    def __init__(self, available: float, required: float, code: str) -> None:
        msg = (
            f"Недостаточно средств: доступно {available:.4f} {code}, "
            f"требуется {required:.4f} {code}"
        )
        super().__init__(msg)
        self.available = available
        self.required = required
        self.code = code


class CurrencyNotFoundError(Exception):
    def __init__(self, code: str) -> None:
        msg = f"Неизвестная валюта '{code}'"
        super().__init__(msg)
        self.code = code


class ApiRequestError(Exception):
    def __init__(self, reason: str) -> None:
        msg = f"Ошибка при обращении к внешнему API: {reason}"
        super().__init__(msg)
        self.reason = reason
