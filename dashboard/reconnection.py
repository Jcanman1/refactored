"""OPC UA reconnection utilities reused by the dashboard."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from threading import Thread
from typing import Optional

from .state import app_state
from .opc_client import connect_to_server, run_async, resume_update_thread


logger = logging.getLogger(__name__)


RECONNECT_INTERVAL = 10


def _reconnection_loop() -> None:
    """Background thread attempting to reconnect when disconnected."""

    logger.info("Auto-reconnection thread started")
    delay = RECONNECT_INTERVAL

    while not app_state.thread_stop_flag:
        try:
            server_url: Optional[str] = getattr(app_state, "server_url", None)
            server_name: Optional[str] = getattr(app_state, "server_name", None)

            if not app_state.connected and server_url:
                logger.info("Attempting reconnect to %s", server_url)
                success = False
                try:
                    success = run_async(connect_to_server(server_url, server_name))
                except Exception as exc:  # pragma: no cover - network dependent
                    logger.error("Auto-reconnection attempt failed: %s", exc)

                if success:
                    logger.info("Reconnected successfully")
                    resume_update_thread()
                    delay = RECONNECT_INTERVAL
                else:
                    delay = min(60, delay * 2)
                    logger.debug(
                        "Reconnection failed, retrying in %s seconds", delay
                    )
            else:
                delay = RECONNECT_INTERVAL
        except Exception as exc:  # pragma: no cover - unexpected errors
            logger.error("Error in auto-reconnection loop: %s", exc)
            delay = min(60, delay * 2)

        time.sleep(delay)

    logger.info("Auto-reconnection thread stopped")


def start_auto_reconnection() -> None:
    """Begin the automatic reconnection loop in a daemon thread."""

    if getattr(app_state, "reconnection_thread", None) and getattr(
        app_state.reconnection_thread, "is_alive", lambda: False
    )():
        logger.debug("Auto-reconnection thread already running")
        return

    app_state.thread_stop_flag = False
    thread = Thread(target=_reconnection_loop)
    thread.daemon = True
    thread.start()

    app_state.reconnection_thread = thread
    logger.info("Started auto-reconnection thread")


def delayed_startup_connect(delay: int = 3) -> None:
    """Connect to the OPC server after a short delay."""

    time.sleep(delay)

    server_url: Optional[str] = getattr(app_state, "server_url", None)
    server_name: Optional[str] = getattr(app_state, "server_name", None)

    if not server_url:
        logger.info("No server URL configured for startup connection")
        return

    try:
        logger.info("Performing startup connection to %s", server_url)
        connected = run_async(connect_to_server(server_url, server_name))
        if connected:
            resume_update_thread()
            logger.info("Startup connection successful")
        else:
            logger.warning("Startup connection failed")
    except Exception as exc:  # pragma: no cover - network dependent
        logger.error("Startup connection error: %s", exc)


def load_saved_image():
    """Return previously saved custom image data if available."""
    path = Path(__file__).resolve().parents[1] / "data" / "custom_image.txt"
    try:
        if path.exists():
            with open(path, "r") as f:
                data = f.read()
            logger.info("Custom image loaded successfully")
            return {"image": data}
        logger.info("No saved custom image found")
        return {}
    except Exception as exc:  # pragma: no cover - rely on filesystem
        logger.error("Error loading custom image: %s", exc)
        return {}


def save_uploaded_image(image_data: str) -> bool:
    """Persist ``image_data`` to :mod:`data/custom_image.txt`."""

    path = Path(__file__).resolve().parents[1] / "data" / "custom_image.txt"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as fh:
            fh.write(image_data)
        logger.info("Custom image saved successfully")
        return True
    except Exception as exc:  # pragma: no cover - rely on filesystem
        logger.error("Error saving custom image: %s", exc)
        return False

__all__ = [
    "start_auto_reconnection",
    "delayed_startup_connect",
    "load_saved_image",
    "save_uploaded_image",
]
