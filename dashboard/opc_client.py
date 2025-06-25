"""OPC UA client utilities reused by the dashboard."""

from EnpresorOPCDataViewBeforeRestructure import (
    connect_to_server,
    disconnect_from_server,
    discover_tags,
    debug_discovered_tags,
    discover_all_tags,
    run_async,
    pause_update_thread,
    resume_update_thread,
)

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
