import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import importlib.util

settings_path = Path(__file__).resolve().parents[1] / "dashboard" / "settings.py"
spec = importlib.util.spec_from_file_location("dashboard.settings", settings_path)
settings = importlib.util.module_from_spec(spec)
spec.loader.exec_module(settings)


def test_display_settings_roundtrip(tmp_path):
    path = tmp_path / "display.json"
    data = {1: True, "extra": False}
    assert settings.save_display_settings(data, path=path)
    loaded = settings.load_display_settings(path=path)
    assert loaded[1] is True
    assert loaded["extra"] is False


def test_ip_addresses_roundtrip(tmp_path):
    path = tmp_path / "ips.json"
    addresses = {"addresses": [{"ip": "1.2.3.4", "label": "A"}]}
    assert settings.save_ip_addresses(addresses, path=path)
    loaded = settings.load_ip_addresses(path=path)
    assert loaded == addresses
