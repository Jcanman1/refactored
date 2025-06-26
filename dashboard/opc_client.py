"""OPC UA client utilities reused by the dashboard."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime
from threading import Thread
from typing import Any, Dict

from opcua import Client, ua

from EnpresorOPCDataViewBeforeRestructure import (
    app_state,
    opc_update_thread,
    TagData,
    KNOWN_TAGS,
    FAST_UPDATE_TAGS,
)

logger = logging.getLogger(__name__)


def get_event_loop() -> asyncio.AbstractEventLoop:
    """Return the running event loop or create a new one."""
    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


def run_async(coro: Any) -> Any:
    """Run an async coroutine in the event loop and return the result."""
    loop = get_event_loop()
    return loop.run_until_complete(coro)


def pause_update_thread() -> None:
    """Stop the background update thread if running."""
    if app_state.update_thread and app_state.update_thread.is_alive():
        app_state.thread_stop_flag = True
        app_state.update_thread.join(timeout=5)


def resume_update_thread() -> None:
    """Restart the background update thread if it is not running."""
    if app_state.update_thread is None or not app_state.update_thread.is_alive():
        app_state.thread_stop_flag = False
        app_state.update_thread = Thread(target=opc_update_thread)
        app_state.update_thread.daemon = True
        app_state.update_thread.start()


async def connect_to_server(server_url: str, server_name: str | None = None) -> bool:
    """Connect to the OPC UA server."""
    try:
        logger.info("Connecting to OPC UA server at %s...", server_url)

        app_state.client = Client(server_url)

        if server_name:
            app_state.client.application_uri = f"urn:{server_name}"
            logger.info("Setting application URI to: %s", app_state.client.application_uri)

        app_state.client.connect()
        logger.info("Connected to server")

        await discover_tags()
        debug_discovered_tags()

        if app_state.update_thread is None or not app_state.update_thread.is_alive():
            app_state.thread_stop_flag = False
            app_state.update_thread = Thread(target=opc_update_thread)
            app_state.update_thread.daemon = True
            app_state.update_thread.start()
            logger.info("Started background update thread")

        app_state.connected = True
        app_state.last_update_time = datetime.now()
        return True

    except Exception as exc:  # pragma: no cover - rely on opcua behaviour
        logger.error("Connection error: %s", exc)
        app_state.connected = False
        return False


async def disconnect_from_server() -> bool:
    """Disconnect from the OPC UA server and stop the update thread."""
    try:
        logger.info("Disconnecting from server...")

        if app_state.update_thread and app_state.update_thread.is_alive():
            app_state.thread_stop_flag = True
            app_state.update_thread.join(timeout=5)

        if app_state.client:
            app_state.client.disconnect()

        app_state.connected = False
        logger.info("Disconnected from server")
        return True

    except Exception as exc:  # pragma: no cover - rely on opcua behaviour
        logger.error("Disconnection error: %s", exc)
        return False


async def discover_tags() -> bool:
    """Discover available tags on the server."""
    if not app_state.client:
        return False

    try:
        logger.info("Discovering tags...")

        app_state.tags = {}

        logger.info("Attempting to connect to known tags...")
        for tag_name, node_id in KNOWN_TAGS.items():
            if tag_name not in FAST_UPDATE_TAGS:
                continue
            try:
                node = app_state.client.get_node(node_id)
                value = node.get_value()

                logger.info("Successfully connected to known tag: %s = %s", tag_name, value)

                tag_data = TagData(tag_name)
                tag_data.add_value(value)
                app_state.tags[tag_name] = {"node": node, "data": tag_data}
            except Exception as exc:  # pragma: no cover - rely on opcua behaviour
                logger.warning("Could not connect to known tag %s (%s): %s", tag_name, node_id, exc)

        logger.info("Performing additional tag discovery...")

        async def browse_nodes(node: Any, level: int = 0, max_level: int = 3) -> None:
            if level > max_level:
                return

            try:
                children = node.get_children()
                for child in children:
                    try:
                        name = child.get_browse_name().Name
                        node_class = child.get_node_class()

                        if node_class == ua.NodeClass.Variable:
                            try:
                                if name in app_state.tags or name not in FAST_UPDATE_TAGS:
                                    continue

                                value = child.get_value()
                                logger.debug("Found additional tag: %s = %s", name, value)

                                tag_data = TagData(name)
                                tag_data.add_value(value)
                                app_state.tags[name] = {"node": child, "data": tag_data}
                            except Exception:
                                pass

                        await browse_nodes(child, level + 1, max_level)
                    except Exception:
                        pass
            except Exception:
                pass

        objects = app_state.client.get_objects_node()
        await browse_nodes(objects, 0, 2)

        logger.info("Total tags discovered: %d", len(app_state.tags))

        if "Settings.ColorSort.TestWeightValue" in app_state.tags:
            weight_value = app_state.tags["Settings.ColorSort.TestWeightValue"]["data"].latest_value
            logger.info("\u2713 TestWeightValue tag found with value: %s", weight_value)
        else:
            logger.warning("\u2717 TestWeightValue tag NOT found")

        if "Settings.ColorSort.TestWeightCount" in app_state.tags:
            count_value = app_state.tags["Settings.ColorSort.TestWeightCount"]["data"].latest_value
            logger.info("\u2713 TestWeightCount tag found with value: %s", count_value)
        else:
            logger.warning("\u2717 TestWeightCount tag NOT found")

        return True

    except Exception as exc:  # pragma: no cover - rely on opcua behaviour
        logger.error("Error discovering tags: %s", exc)
        return False


def debug_discovered_tags() -> None:
    """Write discovered tags to ``discovered_tags.txt`` for debugging."""
    import os

    file_path = os.path.abspath("discovered_tags.txt")
    logger.info("Writing %d discovered tags to: %s", len(app_state.tags), file_path)

    try:
        with open(file_path, "w") as f:
            f.write(f"Total tags discovered: {len(app_state.tags)}\n\n")

            categories: Dict[str, list[Dict[str, Any]]] = {}
            for tag_name, tag_info in app_state.tags.items():
                try:
                    value = tag_info["data"].latest_value
                    node_id = str(tag_info["node"].nodeid)

                    category = tag_name.split(".")[0] if "." in tag_name else "Other"
                    categories.setdefault(category, []).append({
                        "name": tag_name,
                        "node_id": node_id,
                        "value": value,
                    })
                except Exception as exc:
                    category = "Errors"
                    categories.setdefault(category, []).append({
                        "name": tag_name,
                        "node_id": "unknown",
                        "value": f"Error: {exc}",
                    })

            for category, tags in sorted(categories.items()):
                f.write(f"\n=== {category.upper()} TAGS ===\n")
                for tag in tags[:50]:
                    f.write(f"Name: {tag['name']}\n")
                    f.write(f"NodeID: {tag['node_id']}\n")
                    f.write(f"Value: {tag['value']}\n\n")
                if len(tags) > 50:
                    f.write(f"... and {len(tags) - 50} more tags in this category\n\n")

        logger.info("SUCCESS: Tag discovery results written to: %s", file_path)

    except Exception as exc:  # pragma: no cover - rely on filesystem
        logger.error("ERROR writing file: %s", exc)


async def discover_all_tags(client: Client) -> Dict[str, Any]:
    """Return a dict of all tags available from the OPC server."""
    tags: Dict[str, Any] = {}

    try:
        objects = client.get_objects_node()

        async def browse_nodes(node: Any, level: int = 0, max_level: int = 3) -> None:
            if level > max_level:
                return
            try:
                children = node.get_children()
                for child in children:
                    try:
                        name = child.get_browse_name().Name
                        node_class = child.get_node_class()
                        if node_class == ua.NodeClass.Variable:
                            if name not in tags:
                                try:
                                    value = child.get_value()
                                    tag_data = TagData(name)
                                    tag_data.add_value(value)
                                    tags[name] = {"node": child, "data": tag_data}
                                except Exception:
                                    pass
                        await browse_nodes(child, level + 1, max_level)
                    except Exception:
                        pass
            except Exception:
                pass

        await browse_nodes(objects, 0, 2)
        logger.info("Full tag discovery found %d tags", len(tags))
    except Exception as exc:  # pragma: no cover - rely on opcua behaviour
        logger.error("Error during full tag discovery: %s", exc)

    return tags


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

