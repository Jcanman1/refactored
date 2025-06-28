import sys
from tests.test_dashboard_utils import load_modules


def test_settings_controls_present(monkeypatch):
    _, _, _, layout, _ = load_modules(monkeypatch)
    comp = layout.render_dashboard_shell()

    def find(node, target):
        ident = getattr(node, "props", {}).get("id")
        if ident == target:
            return True
        children = getattr(node, "children", []) or []
        if len(children) == 1 and isinstance(children[0], list):
            children = children[0]
        for child in children:
            if find(child, target):
                return True
        return False

    assert find(comp, "auto-connect-switch")
    assert find(comp, "smtp-server-input")
