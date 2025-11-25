from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from prettytable import PrettyTable

from ..decorators import log_action
from ..infra.database import get_db
from ..infra.settings import get_settings
from .exceptions import (
    ApiRequestError,
    CurrencyNotFoundError,
    InsufficientFundsError,
)
from .models import User, Portfolio
from .utils import validate_currency_code

_current_username: Optional[str] = None


def get_current_username() -> Optional[str]:
    return _current_username


def set_current_username(username: Optional[str]) -> None:
    global _current_username
    _current_username = username


def _find_user_by_name(users: list[User], username: str) -> Optional[User]:
    for u in users:
        if u.username == username:
            return u
    return None


def _find_portfolio_by_user_id(
    portfolios: list[Portfolio],
    user_id: int,
) -> Optional[Portfolio]:
    for p in portfolios:
        if p.user_id == user_id:
            return p
    return None


@log_action("REGISTER")
def register_user(username: str, password: str) -> str:
    db = get_db()
    users = db.load_users()

    if _find_user_by_name(users, username):
        return f"Имя пользователя '{username}' уже занято"

    try:
        new_id = max((u.user_id for u in users), default=0) + 1
    except ValueError:
        new_id = 1

    try:
        user = User.create(user_id=new_id, username=username, password=password)
    except ValueError as exc:
        return str(exc)

    users.append(user)
    db.save_users(users)

    portfolios = db.load_portfolios()
    portfolios.append(Portfolio(_user_id=user.user_id, _wallets={}))
    db.save_portfolios(portfolios)

    return (
        f"Пользователь '{username}' зарегистрирован (id={user.user_id}). "
        "Войдите: login --username <name> --password ****"
    )


@log_action("LOGIN")
def login_user(username: str, password: str) -> str:
    db = get_db()
    users = db.load_users()
    user = _find_user_by_name(users, username)
    if not user:
        return f"Пользователь '{username}' не найден"

    if not user.verify_password(password):
        return "Неверный пароль"

    set_current_username(username)
    return f"Вы вошли как '{username}'"


def _require_login() -> User:
    username = get_current_username()
    if not username:
        raise PermissionError("Сначала выполните login")

    db = get_db()
    users = db.load_users()
    user = _find_user_by_name(users, username)
    if not user:
        raise PermissionError("Сначала выполните login")
    return user


def show_portfolio(base_currency: str = "USD") -> str:
    user = _require_login()
    db = get_db()
    portfolios = db.load_portfolios()
    portfolio = _find_portfolio_by_user_id(portfolios, user.user_id)
    if not portfolio:
        return "Портфель не найден"

    snapshot = db.load_rates_snapshot()
    base = base_currency.upper()

    pairs = snapshot.get("pairs", {})
    if base == "USD":
        rates_data = pairs
    else:
        rates_data = pairs

    if not portfolio.wallets:
        return "У вас пока нет ни одного кошелька"

    table = PrettyTable()
    table.field_names = ["Валюта", "Баланс", f"Стоимость в {base}"]

    total = 0.0
    for code, wallet in portfolio.wallets.items():
        if code == base:
            value_in_base = wallet.balance
        else:
            pair = f"{code}_{base}"
            info = rates_data.get(pair)
            if not info:
                value_in_base = 0.0
            else:
                value_in_base = wallet.balance * float(info["rate"])
        total += value_in_base
        table.add_row(
            [code, f"{wallet.balance:.4f}", f"{value_in_base:.2f} {base}"]
        )

    header = (
        f"Портфель пользователя '{user.username}' "
        f"(база: {base}):\n"
    )
    footer = f"ИТОГО: {total:,.2f} {base}"
    return header + str(table) + "\n" + footer


@log_action("BUY", verbose=True)
def buy_currency(currency_code: str, amount: float) -> str:
    if amount <= 0:
        return "'amount' должен быть положительным числом"
    try:
        code = validate_currency_code(currency_code)
    except CurrencyNotFoundError as exc:
        return str(exc)

    user = _require_login()
    db = get_db()
    portfolios = db.load_portfolios()
    portfolio = _find_portfolio_by_user_id(portfolios, user.user_id)
    if not portfolio:
        portfolio = Portfolio(_user_id=user.user_id, _wallets={})
        portfolios.append(portfolio)

    wallet = portfolio.get_wallet(code)
    if not wallet:
        wallet = portfolio.add_currency(code)

    before = wallet.balance
    wallet.deposit(amount)
    after = wallet.balance

    snapshot = db.load_rates_snapshot()
    pairs = snapshot.get("pairs", {})
    pair = f"{code}_USD"
    info = pairs.get(pair)
    if info:
        rate = float(info["rate"])
        estimated = amount * rate
        est_msg = f"Оценочная стоимость покупки: {estimated:,.2f} USD"
        rate_msg = (
            f"по курсу {rate:.2f} USD/{code}"
            if rate > 0
            else "по неизвестному курсу"
        )
    else:
        rate_msg = "по неизвестному курсу"
        est_msg = "Оценочную стоимость рассчитать не удалось"

    db.save_portfolios(portfolios)

    return (
        f"Покупка выполнена: {amount:.4f} {code} {rate_msg}\n"
        f"Изменения в портфеле:\n"
        f"- {code}: было {before:.4f} → стало {after:.4f}\n"
        f"{est_msg}"
    )


@log_action("SELL", verbose=True)
def sell_currency(currency_code: str, amount: float) -> str:
    if amount <= 0:
        return "'amount' должен быть положительным числом"
    try:
        code = validate_currency_code(currency_code)
    except CurrencyNotFoundError as exc:
        return str(exc)

    user = _require_login()
    db = get_db()
    portfolios = db.load_portfolios()
    portfolio = _find_portfolio_by_user_id(portfolios, user.user_id)
    if not portfolio:
        return (
            f"У вас нет кошелька '{code}'. Добавьте валюту: "
            "она создаётся автоматически при первой покупке."
        )

    wallet = portfolio.get_wallet(code)
    if not wallet:
        return (
            f"У вас нет кошелька '{code}'. Добавьте валюту: "
            "она создаётся автоматически при первой покупке."
        )

    before = wallet.balance
    try:
        wallet.withdraw(amount)
    except InsufficientFundsError as exc:
        return str(exc)
    after = wallet.balance

    snapshot = db.load_rates_snapshot()
    pairs = snapshot.get("pairs", {})
    pair = f"{code}_USD"
    info = pairs.get(pair)
    if info:
        rate = float(info["rate"])
        revenue = amount * rate
        msg = (
            f"Продажа выполнена: {amount:.4f} {code} "
            f"по курсу {rate:.2f} USD/{code}\n"
            f"Изменения в портфеле:\n"
            f"- {code}: было {before:.4f} → стало {after:.4f}\n"
            f"Оценочная выручка: {revenue:,.2f} USD"
        )
    else:
        msg = (
            f"Продажа выполнена: {amount:.4f} {code}\n"
            f"Изменения в портфеле:\n"
            f"- {code}: было {before:.4f} → стало {after:.4f}\n"
            "Курс не найден, оценочную выручку рассчитать не удалось"
        )

    db.save_portfolios(portfolios)
    return msg


def get_rate(from_code: str, to_code: str) -> str:
    settings = get_settings()
    ttl_seconds = int(settings.get("RATES_TTL_SECONDS", 300))
    base = validate_currency_code(from_code)
    quote = validate_currency_code(to_code)

    db = get_db()
    snapshot = db.load_rates_snapshot()
    pairs = snapshot.get("pairs", {})
    last_refresh_raw = snapshot.get("last_refresh")

    if last_refresh_raw:
        last_refresh = datetime.fromisoformat(last_refresh_raw)
        if datetime.utcnow() - last_refresh > timedelta(
            seconds=ttl_seconds
        ):
            raise ApiRequestError(
                "Локальный кеш курсов устарел. "
                "Выполните 'update-rates' и попробуйте снова.",
            )
    else:
        raise ApiRequestError(
            "Кеш курсов пуст. Выполните 'update-rates' и попробуйте снова."
        )

    pair = f"{base}_{quote}"
    rev_pair = f"{quote}_{base}"
    info = pairs.get(pair)
    rev_info = pairs.get(rev_pair)

    if not info and not rev_info:
        raise CurrencyNotFoundError(code=pair)

    if info:
        rate = float(info["rate"])
        ts = info["updated_at"]
        msg = (
            f"Курс {base}→{quote}: {rate:.8f} "
            f"(обновлено: {ts})"
        )
        if rev_info:
            rev_rate = float(rev_info["rate"])
        else:
            rev_rate = 1.0 / rate if rate != 0 else 0.0
        msg += (
            f"\nОбратный курс {quote}→{base}: "
            f"{rev_rate:.5f}"
        )
        return msg

    if rev_info:
        rev_rate = float(rev_info["rate"])
        ts = rev_info["updated_at"]
        rate = 1.0 / rev_rate if rev_rate != 0 else 0.0
        return (
            f"Курс {base}→{quote}: {rate:.8f} "
            f"(обновлено: {ts})\n"
            f"Обратный курс {quote}→{base}: {rev_rate:.5f}"
        )

    raise CurrencyNotFoundError(code=pair)


def show_rates(
    currency: str | None = None,
    top: int | None = None,
) -> str:
    db = get_db()
    snapshot = db.load_rates_snapshot()
    pairs = snapshot.get("pairs", {})
    last_refresh = snapshot.get("last_refresh")

    if not pairs:
        return (
            "Локальный кеш курсов пуст. "
            "Выполните 'update-rates', чтобы загрузить данные."
        )

    filtered = []
    if currency:
        code = currency.upper()
        for pair, info in pairs.items():
            if pair.startswith(f"{code}_"):
                filtered.append((pair, info))
        if not filtered:
            return f"Курс для '{code}' не найден в кеше."
    else:
        filtered = list(pairs.items())

    filtered.sort(key=lambda x: float(x[1]["rate"]), reverse=True)
    if top is not None and top > 0:
        filtered = filtered[:top]

    table = PrettyTable()
    table.field_names = ["Пара", "Курс", "Обновлено", "Источник"]
    for pair, info in filtered:
        table.add_row(
            [
                pair,
                f"{float(info['rate']):.6f}",
                info.get("updated_at", "-"),
                info.get("source", "-"),
            ]
        )

    header = f"Rates from cache (updated at {last_refresh}):\n"
    return header + str(table)
