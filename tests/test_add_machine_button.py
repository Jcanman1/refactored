import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.test_dashboard_utils import load_modules


def _find_by_id(node, target):
    if getattr(node, "props", {}).get("id") == target:
        return True
    children = getattr(node, "children", []) or []
    if len(children) == 1 and isinstance(children[0], list):
        children = children[0]
    for child in children:
        if _find_by_id(child, target):
            return True
    return False


def test_button_present_for_selected_floor(monkeypatch):
    floors = {"floors": [{"id": 1, "name": "F1"}], "selected_floor": 1}
    machines = {"machines": []}
    _, _, _, layout, _ = load_modules(monkeypatch)
    monkeypatch.setattr(layout, "load_layout", lambda: (floors, machines))
    comp = layout.render_floor_machine_layout_with_customizable_names()
    assert _find_by_id(comp, "add-machine-btn")


def test_button_absent_for_all(monkeypatch):
    floors = {"floors": [{"id": 1, "name": "F1"}], "selected_floor": "all"}
    machines = {"machines": []}
    _, _, _, layout, _ = load_modules(monkeypatch)
    monkeypatch.setattr(layout, "load_layout", lambda: (floors, machines))
    comp = layout.render_floor_machine_layout_with_customizable_names()
    assert not _find_by_id(comp, "add-machine-btn")
