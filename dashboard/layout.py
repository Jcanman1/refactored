"""Simplified Dash layout utilities used by the dashboard."""

from typing import Any

# ``dash`` is an optional dependency during testing.  These helpers fall
# back to lightweight stubs when the package is unavailable so that the unit
# tests can import the module without needing the real library installed.
try:  # pragma: no cover - optional dependency
    from dash import html, dcc  # type: ignore
except Exception:  # pragma: no cover - provide minimal stubs

    class _Component:  # pragma: no cover - simple stand in for Dash components
        def __init__(self, *children: Any, **props: Any) -> None:
            self.children = list(children)
            self.props = props

        # Dash components normally have a ``_traverse`` method for JSON
        # serialisation.  The tests only access ``children`` so it can be
        # omitted here.

    class _Module:  # pragma: no cover - container returning ``_Component``
        def __getattr__(self, name: str):
            def creator(*children: Any, **props: Any) -> _Component:
                return _Component(*children, **props)

            return creator

    html = _Module()  # type: ignore
    dcc = _Module()  # type: ignore


def render_new_dashboard() -> Any:
    """Return the main dashboard layout filled with visible sections."""

    sections = html.Div(
        [
            html.Div(id="section-1-1", children=[dcc.Graph(id="graph-1-1")]),
            html.Div(id="section-1-2", children=[dcc.Graph(id="graph-1-2")]),
            html.Div(id="section-2", children=[html.Div("Status Controls")]),
            html.Div(id="section-3-1", children=[dcc.Graph(id="graph-3-1")]),
            html.Div(id="section-3-2", children=[dcc.Graph(id="graph-3-2")]),
            html.Div(id="section-4", children=[dcc.Graph(id="graph-4")]),
            html.Div(id="section-5-1", children=[dcc.Graph(id="graph-5-1")]),
            html.Div(id="section-5-2", children=[dcc.Graph(id="graph-5-2")]),
            html.Div(id="section-6-1", children=[dcc.Graph(id="graph-6-1")]),
            html.Div(id="section-6-2", children=[dcc.Graph(id="graph-6-2")]),
            html.Div(id="section-7-1", children=[dcc.Graph(id="graph-7-1")]),
            html.Div(id="section-7-2", children=[dcc.Graph(id="graph-7-2")]),
        ]
    )

    return html.Div([
        html.Div(id="floor-machine-container", className="px-4 pt-2 pb-4"),
        sections,
    ])


def render_floor_machine_layout_with_customizable_names() -> Any:
    """Return a layout for managing floors and machines."""

    sidebar = html.Div(
        [
            html.Img(src="/assets/EnpresorMachine.png", className="mb-2"),
            dcc.Store(id="floors-data"),
            dcc.Store(id="machines-data"),
            html.Button("Show All Machines", id={"type": "floor-tile", "index": "all"}),
            html.Div(id="floor-buttons"),
            html.Button("Add Floor", id="add-floor-btn"),
            html.Div(id="machines-online"),
            html.Div(id="save-status"),
        ],
        id="sidebar",
    )

    main = html.Div(
        [
            html.Div("Selected Floor", id="floor-header"),
            html.Div(id="machines-container"),
            html.Button("Add Machine", id="add-machine-btn"),
        ],
        id="main-content",
    )

    return html.Div([sidebar, main], id="floor-machine-layout")


def render_floor_machine_layout_enhanced_with_selection() -> Any:
    """Return floor layout including machine selection capability."""

    # In this simplified refactor the enhanced layout reuses the base layout.
    return render_floor_machine_layout_with_customizable_names()


__all__ = [
    "render_new_dashboard",
    "render_floor_machine_layout_with_customizable_names",
    "render_floor_machine_layout_enhanced_with_selection",
]
