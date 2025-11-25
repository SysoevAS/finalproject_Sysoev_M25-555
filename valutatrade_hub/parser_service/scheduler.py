from __future__ import annotations

import logging
import time
from typing import List

from .api_clients import BaseApiClient
from .updater import RatesUpdater

logger = logging.getLogger(__name__)


def run_scheduler(clients: List[BaseApiClient], interval_seconds: int) -> None:
    updater = RatesUpdater(clients)
    while True:
        try:
            updater.run_update()
        except Exception as exc:
            logger.error("Scheduler iteration failed: %s", exc)
        time.sleep(interval_seconds)
