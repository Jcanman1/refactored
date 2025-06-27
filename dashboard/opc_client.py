
"""OPC UA client utilities reused by the dashboard."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime
from threading import Thread
from typing import Any, Dict

try:  # pragma: no cover - optional dependency
    from opcua import Client, ua
except Exception:  # pragma: no cover - optional dependency
    Client = ua = None  # type: ignore

from .state import app_state, TagData

# Basic stubs and placeholders
def opc_update_thread() -> None:
    """Background polling loop that keeps tag data up to date."""

    logger.info("OPC update thread started")

    while not app_state.thread_stop_flag:
        try:
            if not app_state.client:
                time.sleep(1)
                continue

            for tag_name, info in list(app_state.tags.items()):
                if FAST_UPDATE_TAGS and tag_name not in FAST_UPDATE_TAGS:
                    continue

                node = info.get("node")
                data = info.get("data")
                if not node or not data:
                    continue

                try:
                    value = node.get_value()
                    data.add_value(value)
                except Exception as exc:  # pragma: no cover - network dependent
                    logger.debug("Error reading tag %s: %s", tag_name, exc)

            app_state.last_update_time = datetime.now()
        except Exception as exc:  # pragma: no cover - unexpected errors
            logger.error("Error in OPC update thread: %s", exc)

        time.sleep(1)

    logger.info("OPC update thread stopped")

# Known tags defined for the dashboard.  These mirror the mappings
# from ``EnpresorOPCDataViewBeforeRestructureLegacy.py`` so the new
# dashboard behaves the same as the legacy implementation.
KNOWN_TAGS: Dict[str, str] = {
    # Status Information
    "Status.Info.Serial": "ns=2;s=Status.Info.Serial",
    "Status.Info.Type": "ns=2;s=Status.Info.Type",
    "Status.Info.PresetNumber": "ns=2;s=Status.Info.PresetNumber",
    "Status.Info.PresetName": "ns=2;s=Status.Info.PresetName",

    # Alive counter
    "Alive": "ns=2;s=Alive",

    # Production data
    "Status.ColorSort.Sort1.Throughput.KgPerHour.Current": "ns=2;s=Status.ColorSort.Sort1.Throughput.KgPerHour.Current",
    "Status.Production.Accepts": "ns=2;s=Status.Production.Accepts",
    "Status.Production.Rejects": "ns=2;s=Status.Production.Rejects",
    "Status.Production.Weight": "ns=2;s=Status.Production.Weight",
    "Status.Production.Count": "ns=2;s=Status.Production.Count",
    "Status.Production.Units": "ns=2;s=Status.Production.Units",

    # Test weight settings tags
    "Settings.ColorSort.TestWeightValue": "ns=2;s=Settings.ColorSort.TestWeightValue",
    "Settings.ColorSort.TestWeightCount": "ns=2;s=Settings.ColorSort.TestWeightCount",

    # Diagnostic
    "Diagnostic.Counter": "ns=2;s=Diagnostic.Counter",

    # Faults and warnings
    "Status.Faults.GlobalFault": "ns=2;s=Status.Faults.GlobalFault",
    "Status.Faults.GlobalWarning": "ns=2;s=Status.Faults.GlobalWarning",

    # Feeders (1-4)
    **{f"Status.Feeders.{i}IsRunning": f"ns=2;s=Status.Feeders.{i}IsRunning" for i in range(1, 5)},
    **{f"Status.Feeders.{i}Rate": f"ns=2;s=Status.Feeders.{i}Rate" for i in range(1, 5)},

    # Counter rates (1-12)
    **{f"Status.ColorSort.Sort1.DefectCount{i}.Rate.Current": f"ns=2;s=Status.ColorSort.Sort1.DefectCount{i}.Rate.Current" for i in range(1, 13)},

    # Primary color sort settings (1-12)
    **{f"Settings.ColorSort.Primary{i}.IsAssigned": f"ns=2;s=Settings.ColorSort.Primary{i}.IsAssigned" for i in range(1, 13)},
    **{f"Settings.ColorSort.Primary{i}.IsActive": f"ns=2;s=Settings.ColorSort.Primary{i}.IsActive" for i in range(1, 13)},
    **{f"Settings.ColorSort.Primary{i}.Name": f"ns=2;s=Settings.ColorSort.Primary{i}.Name" for i in range(1, 13)},

    # Environmental
    "Status.Environmental.AirPressurePsi": "ns=2;s=Status.Environmental.AirPressurePsi",

    # Objects per minute
    "Status.ColorSort.Primary.ObjectPerMin": "ns=2;s=Status.ColorSort.Primary.ObjectPerMin",
}

# Tags that are updated on every cycle in live mode.  These are the tags
# used throughout the dashboard callbacks for real time display.
FAST_UPDATE_TAGS: set[str] = (
    {
        "Status.Info.Serial",
        "Status.Info.Type",
        "Status.Info.PresetNumber",
        "Status.Info.PresetName",
        "Status.Faults.GlobalFault",
        "Status.Faults.GlobalWarning",
        "Status.ColorSort.Sort1.Throughput.KgPerHour.Current",
        "Status.ColorSort.Sort1.Total.Percentage.Current",
        "Status.ColorSort.Sort1.Throughput.ObjectPerMin.Current",
        "Status.ColorSort.Primary.ObjectPerMin",
        "Settings.ColorSort.TestWeightValue",
        "Settings.ColorSort.TestWeightCount",
        "Diagnostic.Counter",
        "Settings.ColorSort.Primary1.SampleImage",
        "Settings.ColorSort.Primary2.SampleImage",
        "Settings.ColorSort.Primary3.SampleImage",
        "Settings.ColorSort.Primary4.SampleImage",
        "Settings.ColorSort.Primary5.SampleImage",
        "Settings.ColorSort.Primary6.SampleImage",
        "Settings.ColorSort.Primary7.SampleImage",
        "Settings.ColorSort.Primary8.SampleImage",
        "Settings.ColorSort.Primary9.SampleImage",
        "Settings.ColorSort.Primary10.SampleImage",
        "Settings.ColorSort.Primary11.SampleImage",
        "Settings.ColorSort.Primary12.SampleImage",
        "Settings.ColorSort.Primary1.Name",
        "Settings.ColorSort.Primary2.Name",
        "Settings.ColorSort.Primary3.Name",
        "Settings.ColorSort.Primary4.Name",
        "Settings.ColorSort.Primary5.Name",
        "Settings.ColorSort.Primary6.Name",
        "Settings.ColorSort.Primary7.Name",
        "Settings.ColorSort.Primary8.Name",
        "Settings.ColorSort.Primary9.Name",
        "Settings.ColorSort.Primary10.Name",
        "Settings.ColorSort.Primary11.Name",
        "Settings.ColorSort.Primary12.Name",
        "Settings.ColorSort.Primary1.IsAssigned",
        "Settings.ColorSort.Primary2.IsAssigned",
        "Settings.ColorSort.Primary3.IsAssigned",
        "Settings.ColorSort.Primary4.IsAssigned",
        "Settings.ColorSort.Primary5.IsAssigned",
        "Settings.ColorSort.Primary6.IsAssigned",
        "Settings.ColorSort.Primary7.IsAssigned",
        "Settings.ColorSort.Primary8.IsAssigned",
        "Settings.ColorSort.Primary9.IsAssigned",
        "Settings.ColorSort.Primary10.IsAssigned",
        "Settings.ColorSort.Primary11.IsAssigned",
        "Settings.ColorSort.Primary12.IsAssigned",
        "Settings.ColorSort.Primary1.IsActive",
        "Settings.ColorSort.Primary2.IsActive",
        "Settings.ColorSort.Primary3.IsActive",
        "Settings.ColorSort.Primary4.IsActive",
        "Settings.ColorSort.Primary5.IsActive",
        "Settings.ColorSort.Primary6.IsActive",
        "Settings.ColorSort.Primary7.IsActive",
        "Settings.ColorSort.Primary8.IsActive",
        "Settings.ColorSort.Primary9.IsActive",
        "Settings.ColorSort.Primary10.IsActive",
        "Settings.ColorSort.Primary11.IsActive",
        "Settings.ColorSort.Primary12.IsActive",
    }
    | {f"Status.Feeders.{i}IsRunning" for i in range(1, 5)}
    | {f"Status.Feeders.{i}Rate" for i in range(1, 5)}
    | {f"Status.ColorSort.Sort1.DefectCount{i}.Rate.Current" for i in range(1, 13)}
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


# Dictionary tracking connections to individual machines when using
# the multi-machine reconnection helpers.  The keys are machine
# identifiers and the values contain the connected client instance,
# discovered tags and basic metadata.
machine_connections: Dict[str, Dict[str, Any]] = {}


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


async def connect_and_monitor_machine_with_timeout(
    ip_address: str,
    machine_id: str,
    server_name: str | None = None,
    timeout: int = 10,
) -> bool:
    """Connect to ``ip_address`` with a shorter session timeout."""

    try:
        server_url = f"opc.tcp://{ip_address}:4840"

        client = Client(server_url)
        client.set_session_timeout(timeout * 1000)

        if server_name:
            client.application_uri = f"urn:{server_name}"

        client.connect()

        machine_tags: Dict[str, Any] = {}
        essential = [t for t in FAST_UPDATE_TAGS if t in KNOWN_TAGS]

        for tag_name in essential:
            node_id = KNOWN_TAGS[tag_name]
            try:
                node = client.get_node(node_id)
                value = node.get_value()
                tag_data = TagData(tag_name)
                tag_data.add_value(value)
                machine_tags[tag_name] = {"node": node, "data": tag_data}
            except Exception:
                continue

        if machine_tags:
            asyncio.create_task(
                complete_tag_discovery(client, machine_id, machine_tags)
            )

            machine_connections[machine_id] = {
                "client": client,
                "tags": machine_tags,
                "ip": ip_address,
                "connected": True,
                "last_update": datetime.now(),
                "failure_count": 0,
            }

            return True

        client.disconnect()
        return False

    except Exception as exc:  # pragma: no cover - network dependent
        logger.debug(
            "Auto-reconnection failed for machine %s at %s: %s",
            machine_id,
            ip_address,
            exc,
        )
        return False


async def complete_tag_discovery(
    client: Client, machine_id: str, existing_tags: Dict[str, Any]
) -> None:
    """Discover any remaining FAST_UPDATE_TAGS for ``client``."""

    try:
        for tag_name, node_id in KNOWN_TAGS.items():
            if tag_name not in existing_tags and tag_name in FAST_UPDATE_TAGS:
                try:
                    node = client.get_node(node_id)
                    value = node.get_value()
                    tag_data = TagData(tag_name)
                    tag_data.add_value(value)
                    existing_tags[tag_name] = {"node": node, "data": tag_data}
                except Exception:
                    continue
        logger.info(
            "Completed tag discovery for auto-reconnected machine %s: %d tags",
            machine_id,
            len(existing_tags),
        )
    except Exception as exc:  # pragma: no cover - network dependent
        logger.debug(
            "Error in background tag discovery for machine %s: %s", machine_id, exc
        )


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
    "connect_and_monitor_machine_with_timeout",
    "complete_tag_discovery",
    "machine_connections",
    "discover_tags",
    "debug_discovered_tags",
    "discover_all_tags",
    "run_async",
    "pause_update_thread",
    "resume_update_thread",
]

