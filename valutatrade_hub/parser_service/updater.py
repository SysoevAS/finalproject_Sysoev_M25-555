from __future__ import annotations

import logging
from typing import Dict, List

from ..core.exceptions import ApiRequestError
from .api_clients import BaseApiClient
from .storage import append_history, write_snapshot

logger = logging.getLogger(__name__)


class RatesUpdater:
    def __init__(self, clients: List[BaseApiClient]) -> None:
        self.clients = clients

    def run_update(self) -> dict:
        logger.info("Starting rates update...")
        all_pairs: Dict[str, float] = {}
        errors: List[str] = []

        for client in self.clients:
            name = client.__class__.__name__
            logger.info("Fetching from %s...", name)
            try:
                pairs = client.fetch_rates()
            except ApiRequestError as exc:
                msg = f"Failed to fetch from {name}: {exc}"
                logger.error(msg)
                errors.append(msg)
                continue
            logger.info("%s OK (%d rates)", name, len(pairs))
            all_pairs.update(pairs)
            source = name
            append_history(pairs, source=source)
            write_snapshot(pairs, source=source)

        result = {
            "total_rates": len(all_pairs),
            "errors": errors,
        }
        if errors:
            logger.info(
                "Update completed with errors. Total rates: %d",
                len(all_pairs),
            )
        else:
            logger.info(
                "Update successful. Total rates: %d",
                len(all_pairs),
            )
        return result
