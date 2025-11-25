from valutatrade_hub.cli.interface import run_cli
from valutatrade_hub.logging_config import configure_logging


def main() -> None:
    configure_logging()
    run_cli()


if __name__ == "__main__":
    main()
