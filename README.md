Структура проекта

    finalproject_<фамилия>_<группа>/
      data/
        users.json
        portfolios.json
        rates.json
        exchange_rates.json
      valutatrade_hub/
        core/
        infra/
        parser_service/
        cli/
        logging_config.py
        decorators.py
      main.py
      Makefile
      pyproject.toml
      README.txt

Установка

1.  Установить зависимости:

    make install

2.  Указать API‑ключ для ExchangeRate‑API:

    export EXCHANGERATE_API_KEY="ваш_ключ"

Запуск

Запуск консольного приложения:

    make project

Основные команды

Регистрация

    register --username alice --password 1234

Вход

    login --username alice --password 1234

Показать портфель

    show-portfolio

Покупка

    buy --currency BTC --amount 0.05

Продажа

    sell --currency BTC --amount 0.01

Получить курс

    get-rate --from USD --to BTC

Обновить курсы (Parser Service)

    update-rates

Показать список курсов

    show-rates

Линтер и сборка

Проверка стиля:

    make lint

Сборка пакета:

    make build

Демо
запись выполнения asciinema:

      https://asciinema.org/a/1nMhlzo0T6ljyaJ9WJHXF5Qxx
