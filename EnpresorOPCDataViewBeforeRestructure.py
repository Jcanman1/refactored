"""Deprecated compatibility layer for the dashboard package."""

from __future__ import annotations

import warnings

warnings.warn(
    "EnpresorOPCDataViewBeforeRestructure is deprecated; use the 'dashboard' package instead",
    DeprecationWarning,
    stacklevel=2,
)

from dashboard.app import app
from dashboard.state import AppState, TagData, app_state
from dashboard.opc_client import (
    connect_to_server,
    disconnect_from_server,
    discover_tags,
    debug_discovered_tags,
    discover_all_tags,
    run_async,
    pause_update_thread,
    resume_update_thread,
)
from dashboard.settings import (
    load_display_settings,
    save_display_settings,
    load_ip_addresses,
    save_ip_addresses,
    load_weight_preference,
    save_weight_preference,
    load_theme_preference,
    save_theme_preference,
    load_language_preference,
    save_language_preference,
    load_email_settings,
    save_email_settings,
    load_threshold_settings,
    save_threshold_settings,
    convert_capacity_from_kg,
    convert_capacity_to_lbs,
    convert_capacity_from_lbs,
    capacity_unit_label,
)
from dashboard.layout import (
    render_new_dashboard,
    render_floor_machine_layout_with_customizable_names,
    render_floor_machine_layout_enhanced_with_selection,
)
from dashboard.reconnection import (
    start_auto_reconnection,
    delayed_startup_connect,
    load_saved_image,
)

__all__ = [
    "app",
    "AppState",
    "TagData",
    "app_state",
    "connect_to_server",
    "disconnect_from_server",
    "discover_tags",
    "debug_discovered_tags",
    "discover_all_tags",
    "run_async",
    "pause_update_thread",
    "resume_update_thread",
    "load_display_settings",
    "save_display_settings",
    "load_ip_addresses",
    "save_ip_addresses",
    "load_weight_preference",
    "save_weight_preference",
    "load_theme_preference",
    "save_theme_preference",
    "load_language_preference",
    "save_language_preference",
    "load_email_settings",
    "save_email_settings",
    "load_threshold_settings",
    "save_threshold_settings",
    "convert_capacity_from_kg",
    "convert_capacity_to_lbs",
    "convert_capacity_from_lbs",
    "capacity_unit_label",
    "render_new_dashboard",
    "render_floor_machine_layout_with_customizable_names",
    "render_floor_machine_layout_enhanced_with_selection",
    "start_auto_reconnection",
    "delayed_startup_connect",
    "load_saved_image",
]
