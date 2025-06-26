import os
import sys
import types
import importlib

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

class StubModule(types.ModuleType):
    def __getattr__(self, name):
        return lambda *a, **k: {"tag": name, "children": a, **k}


def load_modules(monkeypatch, src_patches=None):
    """Import modules with Dash stubs so import succeeds without real Dash.

    ``src_patches`` is an optional dict of attribute names to callables that
    will be applied to ``EnpresorOPCDataViewBeforeRestructure`` before the
    dashboard modules are imported.
    """
    dash = types.ModuleType("dash")

    class Dash:
        def __init__(self, *a, **k):
            pass

        def callback(self, *a, **k):
            def decorator(func):
                return func
            return decorator

        def clientside_callback(self, *a, **k):
            return None
    dash.Dash = Dash
    dash.no_update = object()
    dash.callback_context = type("Ctx", (), {"triggered": []})()

    dash.html = StubModule("dash.html")
    dash.dcc = StubModule("dash.dcc")

    deps = types.ModuleType("dash.dependencies")
    deps.Input = deps.Output = deps.State = lambda *a, **k: None
    deps.ALL = "ALL"
    dash.dependencies = deps

    dbc = StubModule("dash_bootstrap_components")
    dbc.themes = types.SimpleNamespace(BOOTSTRAP="BOOTSTRAP")

    monkeypatch.setitem(sys.modules, "dash", dash)
    monkeypatch.setitem(sys.modules, "dash.dcc", dash.dcc)
    monkeypatch.setitem(sys.modules, "dash.html", dash.html)
    monkeypatch.setitem(sys.modules, "dash.dependencies", deps)
    monkeypatch.setitem(sys.modules, "dash_bootstrap_components", dbc)

    src = importlib.import_module("EnpresorOPCDataViewBeforeRestructure")
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


def test_settings_wrapper_load_and_save(monkeypatch):
    loaded = {"a": 1}
    saved = {}

    def fake_load():
        return loaded

    def fake_save(arg):
        saved["arg"] = arg
        return True

    src_patches = {
        "load_display_settings": fake_load,
        "save_display_settings": fake_save,
    }

    src, settings, _, _ = load_modules(monkeypatch, src_patches)

    assert settings.load_display_settings() == loaded
    assert settings.save_display_settings({"b": 2}) is True
    assert saved["arg"] == {"b": 2}


def test_capacity_conversions(monkeypatch):
    _, settings, _, _ = load_modules(monkeypatch)
    pref_lb = {"unit": "lb"}
    pref_custom = {"unit": "custom", "value": 2}

    assert settings.convert_capacity_from_kg(1, pref_lb) == 2.205
    assert settings.convert_capacity_to_lbs(5, pref_custom) == 10
    assert settings.convert_capacity_from_lbs(10, pref_custom) == 5
    assert settings.capacity_unit_label({"unit": "kg"}) == "kg/hr"


def test_opc_client_helpers_call_through(monkeypatch):
    names = [
        "connect_to_server",
        "disconnect_from_server",
        "discover_tags",
        "debug_discovered_tags",
        "discover_all_tags",
        "run_async",
        "pause_update_thread",
        "resume_update_thread",
    ]
    src_patches = {}
    call_records = {}
    for n in names:
        def _make(name):
            def _func(*a, **k):
                call_records[name] = (a, k)
                return name
            return _func
        src_patches[n] = _make(n)

    src, _, opc_client, _ = load_modules(monkeypatch, src_patches)

    for n in names:
        result = getattr(opc_client, n)(1, two=2)
        assert result == n
        args, kwargs = call_records[n]
        assert args[0] == 1
        assert kwargs["two"] == 2


class DummyHtml:
    def Div(self, children=None, **kwargs):
        return {"tag": "Div", "children": children, **kwargs}


def test_layout_functions_return_components(monkeypatch):
    src, _, _, layout = load_modules(monkeypatch)
    monkeypatch.setattr(src, "html", DummyHtml())
    monkeypatch.setattr(src, "callback_context", type("Ctx", (), {"triggered": []})())

    comp1 = layout.render_new_dashboard()
    assert isinstance(comp1, dict) and comp1.get("tag") == "Div"

    comp2 = layout.render_floor_machine_layout_with_customizable_names(None, None, None, None, "new")
    assert isinstance(comp2, dict) and comp2.get("tag") == "Div"

    comp3 = layout.render_floor_machine_layout_enhanced_with_selection(None, None, None, None, "new", None, None, "en")
    assert isinstance(comp3, dict) and comp3.get("tag") == "Div"
