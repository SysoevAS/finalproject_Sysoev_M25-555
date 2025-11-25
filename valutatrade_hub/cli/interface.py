from __future__ import annotations

import shlex
from typing import Dict, List, Optional

from ..core.exceptions import (
    ApiRequestError,
    CurrencyNotFoundError,
    InsufficientFundsError,
)
from ..core.usecases import (
    buy_currency,
    get_current_username,
    get_rate,
    login_user,
    register_user,
    sell_currency,
    set_current_username,
    show_portfolio,
    show_rates,
)
from ..parser_service.api_clients import CoinGeckoClient, ExchangeRateApiClient
from ..parser_service.config import ParserConfig
from ..parser_service.updater import RatesUpdater


def _parse_options(tokens: List[str]) -> Dict[str, str]:
    """Минимальный разбор типа --key value."""
    opts: Dict[str, str] = {}
    key: Optional[str] = None
    for token in tokens:
        if token.startswith("--"):
            key = token[2:]
            opts[key] = ""
        else:
            if key is None:
                continue
            if opts[key]:
                opts[key] += " " + token
            else:
                opts[key] = token
    return opts


def _print_help() -> None:
    print("Доступные команды:")
    print("  register --username NAME --password PASS")
    print("  login --username NAME --password PASS")
    print("  show-portfolio [--base USD]")
    print("  buy --currency CODE --amount N")
    print("  sell --currency CODE --amount N")
    print("  get-rate --from CODE --to CODE")
    print("  update-rates [--source coingecko|exchangerate]")
    print("  show-rates [--currency CODE] [--top N]")
    print("  whoami")
    print("  logout")
    print("  help")
    print("  exit / quit")


def _cmd_register(args: List[str]) -> None:
    opts = _parse_options(args)
    username = opts.get("username", "").strip()
    password = opts.get("password", "").strip()
    if not username:
        print("Укажите --username")
        return
    if not password:
        print("Укажите --password")
        return
    msg = register_user(username=username, password=password)
    print(msg)


def _cmd_login(args: List[str]) -> None:
    opts = _parse_options(args)
    username = opts.get("username", "").strip()
    password = opts.get("password", "").strip()
    if not username or not password:
        print("Укажите --username и --password")
        return
    msg = login_user(username=username, password=password)
    print(msg)


def _cmd_show_portfolio(args: List[str]) -> None:
    opts = _parse_options(args)
    base = opts.get("base", "USD").strip() or "USD"
    try:
        msg = show_portfolio(base_currency=base)
        print(msg)
    except PermissionError as exc:
        print(str(exc))


def _cmd_buy(args: List[str]) -> None:
    opts = _parse_options(args)
    currency = opts.get("currency", "").strip()
    amount_raw = opts.get("amount", "").strip()
    if not currency or not amount_raw:
        print("Укажите --currency и --amount")
        return
    try:
        amount = float(amount_raw)
    except ValueError:
        print("'amount' должен быть числом")
        return

    try:
        msg = buy_currency(currency_code=currency, amount=amount)
        print(msg)
    except PermissionError as exc:
        print(str(exc))


def _cmd_sell(args: List[str]) -> None:
    opts = _parse_options(args)
    currency = opts.get("currency", "").strip()
    amount_raw = opts.get("amount", "").strip()
    if not currency or not amount_raw:
        print("Укажите --currency и --amount")
        return
    try:
        amount = float(amount_raw)
    except ValueError:
        print("'amount' должен быть числом")
        return

    try:
        msg = sell_currency(currency_code=currency, amount=amount)
        print(msg)
    except PermissionError as exc:
        print(str(exc))


def _cmd_get_rate(args: List[str]) -> None:
    opts = _parse_options(args)
    from_code = opts.get("from", "").strip()
    to_code = opts.get("to", "").strip()
    if not from_code or not to_code:
        print("Укажите --from и --to")
        return
    try:
        msg = get_rate(from_code=from_code, to_code=to_code)
        print(msg)
    except CurrencyNotFoundError as exc:
        print(str(exc))
        print(
            "Проверьте коды валют или выполните 'show-rates', "
            "чтобы посмотреть доступные пары.",
        )
    except ApiRequestError as exc:
        print(str(exc))


def _cmd_update_rates(args: List[str]) -> None:
    opts = _parse_options(args)
    source = opts.get("source", "").strip().lower() or "all"

    config = ParserConfig()
    clients = []
    if source in ("all", "coingecko"):
        clients.append(CoinGeckoClient(config))
    if source in ("all", "exchangerate"):
        clients.append(ExchangeRateApiClient(config))

    if not clients:
        print("Неизвестный source. Используйте coingecko или exchangerate.")
        return

    updater = RatesUpdater(clients)
    try:
        result = updater.run_update()
    except ApiRequestError as exc:
        print(str(exc))
        return

    total = result["total_rates"]
    errors = result["errors"]
    if errors:
        print("Update completed with errors. См. логи.")
    else:
        print("Update successful.")
    print(f"Total rates updated: {total}")


def _cmd_show_rates(args: List[str]) -> None:
    opts = _parse_options(args)
    currency = opts.get("currency")
    top_raw = opts.get("top")
    top = None
    if top_raw:
        try:
            top = int(top_raw)
        except ValueError:
            print("'--top' должно быть целым числом")
            return
    msg = show_rates(currency=currency, top=top)
    print(msg)


def _cmd_whoami() -> None:
    username = get_current_username()
    if username:
        print(f"Текущий пользователь: {username}")
    else:
        print("Вы не залогинены")


def _cmd_logout() -> None:
    set_current_username(None)
    print("Вы вышли из системы")


def run_cli() -> None:
    print("ValutaTrade Hub CLI. Напишите 'help' для списка команд.")
    while True:
        try:
            line = input("> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        stripped = line.strip()
        if not stripped:
            continue
        try:
            tokens = shlex.split(stripped)
        except ValueError as exc:
            print(f"Ошибка парсинга команды: {exc}")
            continue

        cmd = tokens[0]
        args = tokens[1:]

        if cmd in ("exit", "quit"):
            break
        if cmd == "help":
            _print_help()
        elif cmd == "register":
            _cmd_register(args)
        elif cmd == "login":
            _cmd_login(args)
        elif cmd == "show-portfolio":
            _cmd_show_portfolio(args)
        elif cmd == "buy":
            _cmd_buy(args)
        elif cmd == "sell":
            _cmd_sell(args)
        elif cmd == "get-rate":
            _cmd_get_rate(args)
        elif cmd == "update-rates":
            _cmd_update_rates(args)
        elif cmd == "show-rates":
            _cmd_show_rates(args)
        elif cmd == "whoami":
            _cmd_whoami()
        elif cmd == "logout":
            _cmd_logout()
        else:
            print("Неизвестная команда. Напишите 'help' для списка.")
