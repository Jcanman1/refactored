"""Placeholder reconnection helpers."""

import logging

logger = logging.getLogger(__name__)


def start_auto_reconnection():
    """Begin automatic reconnection loop (stub)."""
    logger.warning("start_auto_reconnection is not implemented")


def delayed_startup_connect():
    """Connect to the OPC server after a delay (stub)."""
    logger.warning("delayed_startup_connect is not implemented")


def load_saved_image():
    """Return previously saved custom image data if available."""
    return {}

__all__ = [
    "start_auto_reconnection",
    "delayed_startup_connect",
    "load_saved_image",
]
