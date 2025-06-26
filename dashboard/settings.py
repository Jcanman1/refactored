"""User settings and preference helpers (simplified)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

DISPLAY_SETTINGS_PATH = Path(__file__).resolve().parent.parent / "display_settings.json"
EMAIL_SETTINGS_PATH = Path(__file__).resolve().parent.parent / "email_settings.json"


# ---------------------------------------------------------------------------
# Display settings helpers
# ---------------------------------------------------------------------------

def load_display_settings() -> Dict[str, Any] | None:
    if DISPLAY_SETTINGS_PATH.exists():
        try:
            with open(DISPLAY_SETTINGS_PATH, "r") as f:
                return json.load(f)
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to load display settings: %s", exc)
    return None


def save_display_settings(settings: Dict[str, Any]) -> bool:
    try:
        with open(DISPLAY_SETTINGS_PATH, "w") as f:
            json.dump(settings, f, indent=4)
        return True
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to save display settings: %s", exc)
        return False


def load_ip_addresses() -> Dict[str, Any]:
    path = Path("ip_addresses.json")
    if path.exists():
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:  # pragma: no cover
            logger.warning("ip_addresses.json is corrupted; using default")
    return {"addresses": [{"ip": "192.168.0.125", "label": "Default"}]}


def save_ip_addresses(addresses: Dict[str, Any]) -> bool:
    try:
        with open("ip_addresses.json", "w") as f:
            json.dump(addresses, f, indent=4)
        return True
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to save IP addresses: %s", exc)
        return False


DEFAULT_WEIGHT_PREF = {"unit": "lb", "label": "lbs", "value": 1.0}

def load_weight_preference() -> Dict[str, Any]:
    return DEFAULT_WEIGHT_PREF.copy()


def save_weight_preference(unit: str, label: str = "", value: float = 1.0) -> bool:
    pref = {"unit": unit, "label": label, "value": value}
    settings = load_display_settings() or {}
    settings.update({
        "capacity_unit": unit,
        "capacity_custom_label": label,
        "capacity_custom_value": value,
    })
    return save_display_settings(settings) and True


def load_theme_preference() -> str:
    settings = load_display_settings()
    if settings:
        return settings.get("app_theme", "light")
    return "light"


def save_theme_preference(theme: str) -> bool:
    settings = load_display_settings() or {}
    settings["app_theme"] = theme
    return save_display_settings(settings)


def load_language_preference() -> str:
    settings = load_display_settings()
    return settings.get("language", "en") if settings else "en"


def save_language_preference(language: str) -> bool:
    settings = load_display_settings() or {}
    settings["language"] = language
    return save_display_settings(settings)


DEFAULT_EMAIL_SETTINGS = {
    "smtp_server": "smtp.postmarkapp.com",
    "smtp_port": 587,
    "smtp_username": "",
    "smtp_password": "",
    "from_address": "jcantu@satake-usa.com",
}


def load_email_settings() -> Dict[str, Any]:
    if EMAIL_SETTINGS_PATH.exists():
        try:
            with open(EMAIL_SETTINGS_PATH, "r") as f:
                data = json.load(f)
                return {
                    "smtp_server": data.get("smtp_server", DEFAULT_EMAIL_SETTINGS["smtp_server"]),
                    "smtp_port": data.get("smtp_port", DEFAULT_EMAIL_SETTINGS["smtp_port"]),
                    "smtp_username": data.get("smtp_username", ""),
                    "smtp_password": data.get("smtp_password", ""),
                    "from_address": data.get("from_address", DEFAULT_EMAIL_SETTINGS["from_address"]),
                }
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to load email settings: %s", exc)
    return DEFAULT_EMAIL_SETTINGS.copy()


def save_email_settings(settings: Dict[str, Any]) -> bool:
    try:
        with open(EMAIL_SETTINGS_PATH, "w") as f:
            json.dump(settings, f, indent=4)
        return True
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to save email settings: %s", exc)
        return False


# Threshold settings ---------------------------------------------------------

def load_threshold_settings() -> Dict[str, Any] | None:
    path = Path("threshold_settings.json")
    if path.exists():
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to load threshold settings: %s", exc)
    return None


def save_threshold_settings(settings: Dict[str, Any]) -> bool:
    try:
        with open("threshold_settings.json", "w") as f:
            json.dump(settings, f, indent=4)
        return True
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to save threshold settings: %s", exc)
        return False


def convert_capacity_from_kg(value_kg: float, pref: Dict[str, Any]) -> float:
    if pref.get("unit") == "kg":
        return value_kg
    lbs = value_kg * 2.205
    if pref.get("unit") == "custom":
        per_unit = pref.get("value", 1.0)
        return lbs / per_unit if per_unit else 0
    return lbs


def convert_capacity_to_lbs(value: float, pref: Dict[str, Any]) -> float:
    if pref.get("unit") == "kg":
        return value * 2.205
    if pref.get("unit") == "custom":
        return value * pref.get("value", 1.0)
    return value


def convert_capacity_from_lbs(value_lbs: float, pref: Dict[str, Any]) -> float:
    if pref.get("unit") == "kg":
        return value_lbs / 2.205
    if pref.get("unit") == "custom":
        per_unit = pref.get("value", 1.0)
        return value_lbs / per_unit if per_unit else 0
    return value_lbs


def capacity_unit_label(pref: Dict[str, Any], per_hour: bool = True) -> str:
    label = pref.get("label", "unit")
    if pref.get("unit") == "kg":
        label = "kg"
    elif pref.get("unit") == "lb":
        label = "lbs"
    return f"{label}/hr" if per_hour else label


__all__ = [
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
]
