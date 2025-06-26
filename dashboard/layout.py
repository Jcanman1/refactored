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


# Height constants used by the dashboard grid layout
SECTION_HEIGHT = "220px"
SECTION_HEIGHT2 = "250px"


def render_new_dashboard() -> Any:
    """Return the main dashboard layout filled with visible sections."""

    return render_main_dashboard()


def render_main_dashboard() -> Any:
    """Return the visible grid of dashboard sections."""

    row1 = html.Div(
        [
            html.Div(
                [
                    html.Div(id="section-1-1", className="p-2 mb-2", style={"height": SECTION_HEIGHT}),
                    html.Div(id="section-1-2", className="p-2", style={"height": SECTION_HEIGHT}),
                ],
                className="col-5",
            ),
            html.Div(
                [html.Div(id="section-2", className="p-2", style={"height": "449px"})],
                className="col-3",
            ),
            html.Div(
                [
                    html.Div(id="section-3-1", className="p-2 mb-2", style={"height": SECTION_HEIGHT}),
                    html.Div(id="section-3-2", className="p-2", style={"height": SECTION_HEIGHT}),
                ],
                className="col-4",
            ),
        ],
        className="row mb-0 g-0",
    )

    row2 = html.Div(
        [
            html.Div(
                [html.Div(id="section-4", className="p-2 mb-2", style={"height": "508px"})],
                className="col-2 pe-2",
            ),
            html.Div(
                [
                    html.Div(id="section-5-1", className="p-2 mb-2", style={"height": SECTION_HEIGHT2}),
                    html.Div(id="section-5-2", className="p-2 mb-2", style={"height": SECTION_HEIGHT2}),
                ],
                className="col-4 pe-2",
            ),
            html.Div(
                [
                    html.Div(id="section-6-1", className="p-2 mb-2", style={"height": SECTION_HEIGHT2}),
                    html.Div(id="section-6-2", className="p-2 mb-2", style={"height": SECTION_HEIGHT2}),
                ],
                className="col-4 pe-2",
            ),
            html.Div(
                [
                    html.Div(id="section-7-1", className="p-2 mb-2", style={"height": SECTION_HEIGHT2}),
                    html.Div(id="section-7-2", className="p-2 mb-2 overflow-auto h-100", style={"height": SECTION_HEIGHT2}),
                ],
                className="col-2",
            ),
        ],
        className="row g-2",
    )

    grid = html.Div([row1, row2], className="container-fluid px-2")

    return html.Div(
        [grid],
        style={
            "backgroundColor": "#f0f0f0",
            "minHeight": "100vh",
            "display": "flex",
            "flexDirection": "column",
        },
    )


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
    "render_main_dashboard",
    "render_floor_machine_layout_with_customizable_names",
    "render_floor_machine_layout_enhanced_with_selection",
]
