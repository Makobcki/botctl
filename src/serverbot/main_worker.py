"""Background worker process entrypoint."""

from __future__ import annotations

import asyncio
import logging
import signal

from serverbot.application.config_service import ConfigService
from serverbot.application.worker_alerts import AlertEngine, WorkerAlertLoop
from serverbot.config.logging import configure_logging
from serverbot.config.settings import RuntimeOptions
from serverbot.infrastructure.config.kdl_loader import KdlConfigLoader
from serverbot.infrastructure.db.sqlite_alert_state_repository import (
    SqliteAlertStateBootstrap,
    SqliteAlertStateRepository,
)
from serverbot.infrastructure.db.sqlite_repositories import SqliteConnectionFactory
from serverbot.infrastructure.notifications import LoggingAlertNotifier
from serverbot.workers.checker_factory import CheckerFactory

logger = logging.getLogger(__name__)


async def run_worker() -> None:
    """Run periodic monitoring loop with graceful stop.

    Returns:
        None
    """

    runtime_options = RuntimeOptions()
    app_config = ConfigService(KdlConfigLoader()).load(runtime_options.config_path)
    configure_logging(app_config.verbose)
    connection_factory = SqliteConnectionFactory(app_config.db_path)
    SqliteAlertStateBootstrap(connection_factory).apply()
    alert_loop = WorkerAlertLoop(
        checker=CheckerFactory().create(app_config.alert_checks),
        engine=AlertEngine(
            state_repository=SqliteAlertStateRepository(connection_factory),
            notifier=LoggingAlertNotifier(),
        ),
    )
    stop_event = asyncio.Event()

    def _stop_signal_handler() -> None:
        logger.warning("Shutdown signal received, stopping worker process.")
        stop_event.set()

    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, _stop_signal_handler)
    loop.add_signal_handler(signal.SIGTERM, _stop_signal_handler)

    while not stop_event.is_set():
        logger.debug("worker tick")
        sent_count = await alert_loop.tick()
        logger.debug("worker alerts processed sent_count=%s", sent_count)
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=app_config.worker_interval_seconds)
        except asyncio.TimeoutError:
            continue


def main() -> None:
    """Sync launcher for worker process.

    Returns:
        None
    """

    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        print("Interrupted by user.")


if __name__ == "__main__":
    main()
