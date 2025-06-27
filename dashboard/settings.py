
"""User settings and preference helpers.

Includes helpers for threshold and email configuration used when
triggering alarm notifications.
"""

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[1]
DISPLAY_SETTINGS_PATH = ROOT_DIR / "display_settings.json"
IP_ADDRESSES_PATH = ROOT_DIR / "ip_addresses.json"
EMAIL_SETTINGS_PATH = ROOT_DIR / "email_settings.json"
# Contains per-sensitivity limits along with email threshold preferences
THRESHOLD_SETTINGS_PATH = ROOT_DIR / "threshold_settings.json"

DEFAULT_EMAIL_SETTINGS = {
    "smtp_server": "smtp.postmarkapp.com",
    "smtp_port": 587,
    "smtp_username": "",
    "smtp_password": "",
    "from_address": "jcantu@satake-usa.com",
}

DEFAULT_WEIGHT_PREF = {"unit": "lb", "label": "lbs", "value": 1.0}
DEFAULT_LANGUAGE = "en"


def load_display_settings(path: Path = DISPLAY_SETTINGS_PATH):
    """Load display settings from ``path``."""
    try:
        if path.exists():
            with open(path, "r") as f:
                loaded_settings = json.load(f)
            settings = {}
            for key, value in loaded_settings.items():
                if str(key).isdigit():
                    settings[int(key)] = value
                else:
                    settings[key] = value
            return settings
        return None
    except Exception as e:  # pragma: no cover - just log
        logger.error(f"Error loading display settings: {e}")
        return None


def save_display_settings(settings: dict, path: Path = DISPLAY_SETTINGS_PATH) -> bool:
    """Save display settings to ``path``."""
    try:
        json_settings = {str(k): v for k, v in settings.items()}
        with open(path, "w") as f:
            json.dump(json_settings, f, indent=4)
        return True
    except Exception as e:  # pragma: no cover - just log
        logger.error(f"Error saving display settings: {e}")
        return False


def save_ip_addresses(addresses: dict, path: Path = IP_ADDRESSES_PATH) -> bool:
    """Save IP addresses to ``path``."""
    try:
        with open(path, "w") as f:
            json.dump(addresses, f, indent=4)
        return True
    except Exception as e:  # pragma: no cover - just log
        logger.error(f"Error saving IP addresses: {e}")
        return False


def load_ip_addresses(path: Path = IP_ADDRESSES_PATH) -> dict:
    """Load IP addresses from ``path``. Returns defaults if file is missing or invalid."""
    try:
        default_data = {"addresses": [{"ip": "192.168.0.125", "label": "Default"}]}
        if path.exists():
            with open(path, "r") as f:
                addresses = json.load(f)
            if not isinstance(addresses, dict) or "addresses" not in addresses:
                logger.warning("Invalid format in ip_addresses.json, using default")
                return default_data
            if not isinstance(addresses["addresses"], list):
                logger.warning("'addresses' is not a list in ip_addresses.json, using default")
                return default_data
            valid = []
            for item in addresses["addresses"]:
                if isinstance(item, dict) and "ip" in item and "label" in item:
                    valid.append(item)
                else:
                    logger.warning(f"Invalid address entry: {item}")
            if valid:
                addresses["addresses"] = valid
                return addresses
            return default_data
        return default_data
    except Exception as e:  # pragma: no cover - just log
        logger.error(f"Error loading IP addresses: {e}")
        return {"addresses": [{"ip": "192.168.0.125", "label": "Default"}]}


def load_theme_preference(path: Path = DISPLAY_SETTINGS_PATH) -> str:
    """Load the UI theme preference."""
    try:
        if path.exists():
            with open(path, "r") as f:
                settings = json.load(f)
                return settings.get("app_theme", "light")
        return "light"
    except Exception as e:  # pragma: no cover - just log
        logger.error(f"Error loading theme preference: {e}")
        return "light"


def save_theme_preference(theme: str, path: Path = DISPLAY_SETTINGS_PATH) -> bool:
    """Save theme preference."""
    try:
        settings = {}
        if path.exists():
            with open(path, "r") as f:
                try:
                    settings = json.load(f)
                except json.JSONDecodeError:
                    settings = {}
        settings["app_theme"] = theme
        with open(path, "w") as f:
            json.dump(settings, f, indent=4)
        return True
    except Exception as e:  # pragma: no cover - just log
        logger.error(f"Error saving theme preference: {e}")
        return False


def load_weight_preference(path: Path = DISPLAY_SETTINGS_PATH) -> dict:
    """Load capacity unit preference."""
    try:
        if path.exists():
            with open(path, "r") as f:
                settings = json.load(f)
                return {
                    "unit": settings.get("capacity_unit", "lb"),
                    "label": settings.get("capacity_custom_label", ""),
                    "value": settings.get("capacity_custom_value", 1.0),
                }
    except Exception as e:  # pragma: no cover - just log
        logger.error(f"Error loading capacity unit preference: {e}")
    return DEFAULT_WEIGHT_PREF.copy()


def save_weight_preference(unit: str, label: str = "", value: float = 1.0, path: Path = DISPLAY_SETTINGS_PATH) -> bool:
    """Save capacity unit preference."""
    try:
        settings = {}
        if path.exists():
            with open(path, "r") as f:
                try:
                    settings = json.load(f)
                except json.JSONDecodeError:
                    settings = {}
        settings["capacity_unit"] = unit
        settings["capacity_custom_label"] = label
        settings["capacity_custom_value"] = value
        with open(path, "w") as f:
            json.dump(settings, f, indent=4)
        return True
    except Exception as e:  # pragma: no cover - just log
        logger.error(f"Error saving capacity unit preference: {e}")
        return False


def load_language_preference(path: Path = DISPLAY_SETTINGS_PATH) -> str:
    """Load UI language preference."""
    try:
        if path.exists():
            with open(path, "r") as f:
                settings = json.load(f)
                return settings.get("language", DEFAULT_LANGUAGE)
    except Exception as e:  # pragma: no cover - just log
        logger.error(f"Error loading language preference: {e}")
    return DEFAULT_LANGUAGE


def save_language_preference(language: str, path: Path = DISPLAY_SETTINGS_PATH) -> bool:
    """Save UI language preference."""
    try:
        settings = {}
        if path.exists():
            with open(path, "r") as f:
                try:
                    settings = json.load(f)
                except json.JSONDecodeError:
                    settings = {}
        settings["language"] = language
        with open(path, "w") as f:
            json.dump(settings, f, indent=4)
        return True
    except Exception as e:  # pragma: no cover - just log
        logger.error(f"Error saving language preference: {e}")
        return False


def convert_capacity_from_kg(value_kg: float, pref: dict) -> float:
    """Convert capacity from kilograms based on unit preference."""
    if value_kg is None:
        return 0
    unit = pref.get("unit", "lb")
    if unit == "kg":
        return value_kg
    lbs = value_kg * 2.205
    if unit == "lb":
        return lbs
    if unit == "custom":

        per_unit = pref.get("value", 1.0)
        return lbs / per_unit if per_unit else 0
    return lbs



def convert_capacity_to_lbs(value: float, pref: dict) -> float:
    """Convert capacity value to pounds."""
    if value is None:
        return 0
    unit = pref.get("unit", "lb")
    if unit == "kg":
        return value * 2.205
    if unit == "lb":
        return value
    if unit == "custom":
        per_unit = pref.get("value", 1.0)
        return value * per_unit
    return value


def convert_capacity_from_lbs(value_lbs: float, pref: dict) -> float:
    """Convert capacity from pounds to preferred unit."""
    if value_lbs is None:
        return 0
    unit = pref.get("unit", "lb")
    if unit == "kg":
        return value_lbs / 2.205
    if unit == "lb":
        return value_lbs
    if unit == "custom":

        per_unit = pref.get("value", 1.0)
        return value_lbs / per_unit if per_unit else 0
    return value_lbs



def capacity_unit_label(pref: dict, per_hour: bool = True) -> str:
    unit = pref.get("unit", "lb")
    if unit == "kg":
        label = "kg"
    elif unit == "lb":
        label = "lbs"
    else:
        label = pref.get("label", "unit")
    return f"{label}/hr" if per_hour else label


def load_email_settings(path: Path = EMAIL_SETTINGS_PATH) -> dict:
    """Load SMTP email settings."""
    try:
        if path.exists():
            with open(path, "r") as f:
                data = json.load(f)
                return {
                    "smtp_server": data.get("smtp_server", DEFAULT_EMAIL_SETTINGS["smtp_server"]),
                    "smtp_port": data.get("smtp_port", DEFAULT_EMAIL_SETTINGS["smtp_port"]),
                    "smtp_username": data.get("smtp_username", ""),
                    "smtp_password": data.get("smtp_password", ""),
                    "from_address": data.get("from_address", DEFAULT_EMAIL_SETTINGS["from_address"]),
                }
    except Exception as e:  # pragma: no cover - just log
        logger.error(f"Error loading email settings: {e}")
    return DEFAULT_EMAIL_SETTINGS.copy()


def save_email_settings(settings: dict, path: Path = EMAIL_SETTINGS_PATH) -> bool:
    """Save SMTP email settings."""
    try:
        with open(path, "w") as f:
            json.dump(settings, f, indent=4)
        return True
    except Exception as e:  # pragma: no cover - just log
        logger.error(f"Error saving email settings: {e}")
        return False


def load_threshold_settings(path: Path = THRESHOLD_SETTINGS_PATH):
    """Load threshold settings from ``path``.

    The returned dictionary includes per-sensitivity limits as well as
    email alert fields ``email_enabled``,
    ``email_address`` and ``email_minutes`` controlling when threshold
    notifications are sent.
    """
    try:
        if path.exists():
            with open(path, "r") as f:
                loaded_settings = json.load(f)
            settings = {}
            for key, value in loaded_settings.items():
                if key in ["email_enabled", "email_address", "email_minutes"]:
                    settings[key] = value
                else:
                    settings[int(key)] = value
            return settings
        else:
            return None
    except Exception as e:  # pragma: no cover - just log
        logger.error(f"Error loading threshold settings: {e}")
        return None


def save_threshold_settings(settings: dict, path: Path = THRESHOLD_SETTINGS_PATH) -> bool:
    """Save threshold settings to ``path``."""
    try:
        json_settings = {str(k): v for k, v in settings.items()}
        with open(path, "w") as f:
            json.dump(json_settings, f, indent=4)
        return True
    except Exception as e:  # pragma: no cover - just log
        logger.error(f"Error saving threshold settings: {e}")
        return False



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
    "DEFAULT_LANGUAGE",
]
