"""Notification adapters used by worker alert loop."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from serverbot.application.worker_alerts import AlertNotifier
from serverbot.domain.alerts import AlertEvent

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LoggingAlertNotifier(AlertNotifier):
    """Notifier adapter that writes alert events to logs.

    Args:
        logger_name: Logger name for alert notifications.
    """

    logger_name: str = "serverbot.alerts"

    async def notify(self, event: AlertEvent) -> None:
        """Log alert event as placeholder notification transport.

        Args:
            event: Alert event payload.

        Returns:
            None.

        Raises:
            None.
        """

        notifier_logger = logging.getLogger(self.logger_name)
        notifier_logger.warning(
            "alert key=%s firing=%s title=%s details=%s",
            event.key,
            event.is_firing,
            event.title,
            event.details,
        )
        logger.debug("Alert event logged key=%s", event.key)
