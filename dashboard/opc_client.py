"""OPC UA client utilities reused by the dashboard (stubs)."""

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


async def connect_to_server(server_url: str, server_name: str | None = None) -> None:
    logger.warning("connect_to_server is not implemented")


async def disconnect_from_server() -> None:
    logger.warning("disconnect_from_server is not implemented")


async def discover_tags(*_args: Any, **_kwargs: Any) -> dict:
    logger.warning("discover_tags is not implemented")
    return {}


def debug_discovered_tags(tags: dict) -> None:
    logger.debug("Discovered tags: %s", list(tags))


async def discover_all_tags(*_args: Any, **_kwargs: Any) -> dict:
    logger.warning("discover_all_tags is not implemented")
    return {}


def run_async(coro):
    """Run the given coroutine in the event loop."""
    return asyncio.get_event_loop().run_until_complete(coro)


def pause_update_thread():
    logger.warning("pause_update_thread is not implemented")


def resume_update_thread():
    logger.warning("resume_update_thread is not implemented")


__all__ = [
    "connect_to_server",
    "disconnect_from_server",
    "discover_tags",
    "debug_discovered_tags",
    "discover_all_tags",
    "run_async",
    "pause_update_thread",
    "resume_update_thread",
]
