import importlib.util
import sys
from types import ModuleType
from pathlib import Path
import inspect
from types import SimpleNamespace
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.test_dashboard_utils import load_modules


def load_callbacks(monkeypatch):
    # stub generate_report before importing dashboard package
    report_mod = ModuleType("generate_report")
    report_mod.fetch_last_24h_metrics = lambda: {}

    def _build_report(data, path):
        with open(path, "wb") as fh:
            fh.write(b"PDF")

    report_mod.build_report = _build_report
    monkeypatch.setitem(sys.modules, "generate_report", report_mod)

    # load core modules and prepare stubs
    legacy, settings, opc_client, layout, startup = load_modules(monkeypatch)

    # load dashboard.app and patch callback decorator
    root = Path(__file__).resolve().parents[1] / "dashboard"

    def load(name):
        path = root / f"{name.split('.')[-1]}.py"
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    app_mod = load("dashboard.app")
    sys.modules["dashboard.app"] = app_mod
    registered = {}

    def fake_callback(*args, **kwargs):
        def wrapper(func):
            registered[func.__name__] = func
            return func
        return wrapper

    setattr(app_mod.app, "callback", fake_callback)

    callbacks_spec = importlib.util.spec_from_file_location(
        "dashboard.callbacks", root / "callbacks.py"
    )
    callbacks = importlib.util.module_from_spec(callbacks_spec)
    callbacks_spec.loader.exec_module(callbacks)

    return callbacks, registered


def test_section_callbacks_exist(monkeypatch):
    callbacks, registered = load_callbacks(monkeypatch)

    expected = {
        "update_section_2",
        "update_section_3_1",
        "update_section_4",
        "update_section_5_1",
        "update_section_6_1",
        "update_section_7_1",
        "generate_report_callback",
    }

    assert expected.issubset(set(registered))

    for name in expected:
        func = registered[name]
        params = inspect.signature(func).parameters
        args = [None] * len(params)
        if name == "generate_report_callback":
            args = [1]
        result = func(*args)
        comp = result[0] if isinstance(result, tuple) else result
        assert comp is not None


def test_manage_dashboard_toggle(monkeypatch):
    callbacks, registered = load_callbacks(monkeypatch)
    manage = registered["manage_dashboard"]

    assert manage(None, "new") == "new"
    assert manage(1, "new") == "main"
    assert manage(2, "main") == "new"


def test_floor_machine_container_populated(monkeypatch):
    callbacks, registered = load_callbacks(monkeypatch)
    render = registered["render_floor_machine_layout_cb"]

    comp = render({}, {}, {}, {}, "new", {}, None, "en")
    assert hasattr(comp, "children")


def test_delete_confirmation_callback_registered(monkeypatch):
    callbacks, registered = load_callbacks(monkeypatch)
    func = registered.get("toggle_delete_confirmation_modal")
    assert func is not None
    params = inspect.signature(func).parameters
    args = [None] * len(params)
    result = func(*args)
    assert result is not None


def test_toggle_historical_controls(monkeypatch):
    callbacks, registered = load_callbacks(monkeypatch)
    func = registered.get("toggle_historical_controls_visibility")
    assert func is not None
    assert func("historical") == "d-block"
    assert func("live") == "d-none"


def test_machine_cards_after_add(monkeypatch):
    callbacks, registered = load_callbacks(monkeypatch)
    add_machine = registered["add_machine_cb"]
    render_cards = registered["render_machine_cards"]

    monkeypatch.setattr(callbacks, "_save_floor_machine_data", lambda f, m: True)

    floors = {"selected_floor": "all", "floors": [{"id": 1, "name": "F1"}]}
    machines = {"machines": []}

    machines = add_machine(1, machines, floors)
    expected = f"{callbacks.tr('machine_label', callbacks.load_language_preference())} 1"
    assert machines["machines"][0]["name"] == expected
    cards = render_cards(floors, machines, "new")

    assert cards is not None
    assert cards != callbacks.no_update
    children = cards.children if hasattr(cards, "children") else cards[1]
    assert len(children) == 1


def test_floor_selection_updates_selected(monkeypatch):
    callbacks, registered = load_callbacks(monkeypatch)
    select = registered["handle_floor_selection"]

    for fid in [1, 2, 3]:
        ctx = SimpleNamespace(triggered_id={"type": "floor-tile", "index": fid})
        monkeypatch.setattr(callbacks, "callback_context", ctx)
        data = {"selected_floor": "all"}
        result = select([], [], data)
        assert result["selected_floor"] == fid


def test_floor_selection_fallback_to_triggered(monkeypatch):
    callbacks, registered = load_callbacks(monkeypatch)
    select = registered["handle_floor_selection"]

    for fid in [1, 2, 3]:
        prop = json.dumps({"type": "floor-tile", "index": fid}) + ".n_clicks"
        ctx = SimpleNamespace(triggered=[{"prop_id": prop}], triggered_id=None)
        monkeypatch.setattr(callbacks, "callback_context", ctx)
        data = {"selected_floor": "all"}
        result = select([], [], data)
        assert result["selected_floor"] == fid


def test_new_floor_is_selected(monkeypatch):
    callbacks, registered = load_callbacks(monkeypatch)
    add_floor = registered["add_floor_cb"]

    monkeypatch.setattr(callbacks, "_save_floor_machine_data", lambda f, m: True)

    floors = {"floors": [{"id": 1, "name": "F1"}], "selected_floor": 1}
    machines = {"machines": []}

    result = add_floor(1, floors, machines)
    assert result["selected_floor"] == 2
    assert any(f.get("id") == 2 for f in result["floors"])


def test_machine_filter_by_floor(monkeypatch):
    callbacks, registered = load_callbacks(monkeypatch)
    add_machine = registered["add_machine_cb"]
    render_cards = registered["render_machine_cards"]

    monkeypatch.setattr(callbacks, "_save_floor_machine_data", lambda f, m: True)

    floors = {
        "floors": [{"id": 1, "name": "F1"}, {"id": 2, "name": "F2"}],
        "selected_floor": 2,
    }
    machines = {"machines": []}

    machines = add_machine(1, machines, floors)
    machines["machines"].append({"id": 99, "floor_id": 1, "name": "M99"})

    cards = render_cards(floors, machines, "new")
    children = cards.children if hasattr(cards, "children") else cards[1]
    assert len(children) == 1


def test_add_floor_then_machine_filters(monkeypatch):
    callbacks, registered = load_callbacks(monkeypatch)
    add_floor = registered["add_floor_cb"]
    add_machine = registered["add_machine_cb"]
    render_cards = registered["render_machine_cards"]

    monkeypatch.setattr(callbacks, "_save_floor_machine_data", lambda f, m: True)

    floors = {"floors": [{"id": 1, "name": "F1"}], "selected_floor": 1}
    machines = {"machines": []}

    new_floors = add_floor(1, floors, machines)
    machines = add_machine(1, machines, new_floors)

    cards = render_cards(new_floors, machines, "new")
    children = cards.children if hasattr(cards, "children") else cards[1]
    assert len(children) == 1
    assert machines["machines"][0]["floor_id"] == new_floors["selected_floor"]


def test_add_floor_cb_does_not_mutate_input(monkeypatch):
    callbacks, registered = load_callbacks(monkeypatch)
    add_floor = registered["add_floor_cb"]

    monkeypatch.setattr(callbacks, "_save_floor_machine_data", lambda f, m: True)

    floors = {"floors": [{"id": 1, "name": "F1"}], "selected_floor": 1}
    machines = {"machines": []}
    original = json.loads(json.dumps(floors))

    add_floor(1, floors, machines)

    assert floors == original


def test_add_machine_cb_does_not_mutate_input(monkeypatch):
    callbacks, registered = load_callbacks(monkeypatch)
    add_machine = registered["add_machine_cb"]

    monkeypatch.setattr(callbacks, "_save_floor_machine_data", lambda f, m: True)

    floors = {"floors": [{"id": 1, "name": "F1"}], "selected_floor": 1}
    machines = {"machines": []}
    original = json.loads(json.dumps(machines))

    add_machine(1, machines, floors)

    assert machines == original
