"""Logging setup with rich output."""

from __future__ import annotations

import logging
from typing import Final

from rich.logging import RichHandler

VERBOSE_FORMAT: Final[str] = "[%(levelname)s] - %(message)s - [%(filename)s:%(lineno)d]"
PLAIN_FORMAT: Final[str] = "%(message)s"


def configure_logging(verbose: bool) -> None:
    """Configure root logging according to verbosity mode.

    Args:
        verbose: Whether debug logging with metadata is enabled.

    Returns:
        None
    """

    level = logging.DEBUG if verbose else logging.WARNING
    format_string = VERBOSE_FORMAT if verbose else PLAIN_FORMAT
    logging.basicConfig(
        level=level,
        format=format_string,
        handlers=[RichHandler(rich_tracebacks=True, show_path=False)],
        force=True,
    )
