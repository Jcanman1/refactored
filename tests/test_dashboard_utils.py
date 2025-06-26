import os
import sys
import types
import importlib
from pathlib import Path
import asyncio
from types import SimpleNamespace, ModuleType

# Ensure the repository root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))




def load_modules(monkeypatch, src_patches=None):
    """Import modules with Dash stubs so import succeeds without real Dash.

    ``src_patches`` is an optional dict of attribute names to callables that
    will be applied to ``dashboard.reconnection`` before the
    dashboard modules are imported.
    """
    dash = types.ModuleType("dash")

    class Dash:
        def __init__(self, *a, **k):
            pass

        def disconnect(self):
            pass

    src = importlib.import_module("dashboard.reconnection")
    importlib.reload(src)
    if src_patches:
        for name, value in src_patches.items():
            setattr(src, name, value)
    settings = importlib.import_module("dashboard.settings")
    importlib.reload(settings)
    opc_client = importlib.import_module("dashboard.opc_client")
    importlib.reload(opc_client)
    layout = importlib.import_module("dashboard.layout")
    importlib.reload(layout)
    return src, settings, opc_client, layout

        def get_objects_node(self):
            return DummyNode()

    ua = ModuleType("ua")
    ua.NodeClass = SimpleNamespace(Variable="Variable")
    opcua.Client = DummyClient
    opcua.ua = ua
    monkeypatch.setitem(sys.modules, "opcua", opcua)

    root = Path(__file__).resolve().parents[1] / "dashboard"

    def load(name):
        path = root / f"{name.split('.')[-1]}.py"
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    settings = load("dashboard.settings")
    opc_client = load("dashboard.opc_client")
    layout = load("dashboard.layout")
    startup = load("dashboard.startup")
    return legacy, settings, opc_client, layout, startup


def test_display_settings_roundtrip(monkeypatch, tmp_path):
    _, settings, _, _, _ = load_modules(monkeypatch)
    path = tmp_path / "display.json"
    data = {1: True, "extra": False}
    assert settings.save_display_settings(data, path=path)
    loaded = settings.load_display_settings(path=path)
    assert loaded[1] is True
    assert loaded["extra"] is False


def test_capacity_conversions(monkeypatch):
    _, settings, _, _, _ = load_modules(monkeypatch)
    pref_lb = {"unit": "lb"}
    pref_custom = {"unit": "custom", "value": 2}

    assert settings.convert_capacity_from_kg(1, pref_lb) == 2.205
    assert settings.convert_capacity_to_lbs(5, pref_custom) == 10
    assert settings.convert_capacity_from_lbs(10, pref_custom) == 5
    assert settings.capacity_unit_label({"unit": "kg"}) == "kg/hr"


def test_startup_helpers(monkeypatch):
    _, _, _, _, startup = load_modules(monkeypatch)
    called = {}

    def fake_start():
        called["start"] = True
        return "ok"

    def fake_delayed():
        called["delayed"] = True
        return "later"

    monkeypatch.setattr(startup, "start_auto_reconnection", fake_start)
    monkeypatch.setattr(startup, "delayed_startup_connect", fake_delayed)

    assert startup.start_auto_reconnection() == "ok"
    assert startup.delayed_startup_connect() == "later"
    assert called == {"start": True, "delayed": True}


def test_opc_client_run_async_and_thread_helpers(monkeypatch):
    legacy, _, opc_client, _, _ = load_modules(monkeypatch)

    async def coro():
        return 42

    assert opc_client.run_async(coro()) == 42

    class DummyThread:
        def __init__(self, target):
            self.target = target
            self.started = False

        def start(self):
            self.started = True

        def is_alive(self):
            return self.started

        def join(self, timeout=None):
            self.started = False

    dummy_thread = DummyThread(lambda: None)
    dummy_thread.started = True
    legacy.app_state.update_thread = dummy_thread

    opc_client.pause_update_thread()
    assert legacy.app_state.thread_stop_flag is True
    assert not dummy_thread.started

    legacy.app_state.update_thread = None
    monkeypatch.setattr(opc_client, "Thread", lambda target: dummy_thread)
    opc_client.resume_update_thread()
    assert legacy.app_state.update_thread is dummy_thread
    assert legacy.app_state.thread_stop_flag is False
    assert dummy_thread.started is True


def test_layout_functions_return_none(monkeypatch):
    _, _, _, layout, _ = load_modules(monkeypatch)

    assert layout.render_new_dashboard() is None
    assert layout.render_floor_machine_layout_with_customizable_names() is None
    assert (
        layout.render_floor_machine_layout_enhanced_with_selection() is None
    )
