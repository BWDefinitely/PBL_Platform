# backend/logger.py
"""Logger initialization utilities."""

from __future__ import annotations

import logging
from settings import LOG_LEVEL


def init_logger() -> None:
    """Initialize root logger once."""
    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )
