"""Simplified Dash layout utilities used by the dashboard."""

from typing import Any

from .machine_layout import load_layout

from .settings import load_language_preference, load_weight_preference

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

# ``dash-bootstrap-components`` is also optional for the tests. When missing,
# bootstrap components fall back to simple ``html.Div`` containers so the
# layout functions can still be imported.
try:  # pragma: no cover - optional dependency
    import dash_bootstrap_components as dbc  # type: ignore
except Exception:  # pragma: no cover - provide minimal stubs
    class _BootstrapModule:  # pragma: no cover - container returning ``html.Div``
        def __getattr__(self, name: str):
            def creator(*children: Any, **props: Any):
                return html.Div(*children, **props)

            return creator

    dbc = _BootstrapModule()  # type: ignore


# Height constants used by the dashboard grid layout
SECTION_HEIGHT = "220px"
SECTION_HEIGHT2 = "250px"
HEADER_CARD_HEIGHT = "65px"


def render_dashboard_shell() -> Any:
    """Return the root layout with a dashboard switcher."""

    floors_data, machines_data = load_layout()
    if not floors_data:
        floors_data = {"floors": [{"id": 1, "name": "1st Floor"}], "selected_floor": "all"}
    if not machines_data:
        machines_data = {"machines": [], "next_machine_id": 1}

    return html.Div(
        [
            dcc.Store(id="current-dashboard", data="main"),
            dcc.Store(id="floors-data", data=floors_data),
            dcc.Store(id="machines-data", data=machines_data),
            dcc.Store(id="active-machine-store", data={"machine_id": None}),
            dbc.Row(
                [
                    dbc.Col(
                        html.H4("Dashboard", className="m-2"),
                        width="auto",
                    ),
                    dbc.Col(
                        dcc.Dropdown(
                            id="dashboard-selector",
                            options=[
                                {"label": "Main", "value": "main"},
                                {"label": "Layout", "value": "layout"},
                            ],
                            value="main",
                            clearable=False,
                            className="w-100",
                        ),
                        width=2,
                    ),
                ],
                className="g-2 align-items-center mb-2",
            ),
            html.Div(id="dashboard-content"),
        ]
    )


def render_new_dashboard() -> Any:
    """Return the main dashboard layout filled with visible sections."""
    grid = render_main_dashboard()

    return html.Div(
        [
            dcc.Interval(
                id="status-update-interval",
                interval=1000,
                n_intervals=0,
            ),
            dcc.Store(id="production-data-store"),
            dcc.Store(
                id="weight-preference-store",
                data=load_weight_preference(),
            ),
            dcc.Store(
                id="language-preference-store",
                data=load_language_preference(),
            ),
            grid,
        ]
    )


def render_main_dashboard() -> Any:
    """Return the visible grid of dashboard sections."""

    row1 = dbc.Row(
        [
            dbc.Col(
                [
                    dbc.Card(
                        dbc.CardBody(id="section-1-1", className="p-2"),
                        className="mb-2",
                        style={"height": SECTION_HEIGHT},
                    ),
                    dbc.Card(
                        dbc.CardBody(id="section-1-2", className="p-2"),
                        className="mb-0",
                        style={"height": SECTION_HEIGHT},
                    ),
                ],
                width=5,
            ),
            dbc.Col(
                [
                    dbc.Card(
                        dbc.CardBody(id="section-2", className="p-2"),
                        style={"height": "449px"},
                    )
                ],
                width=3,
            ),
            dbc.Col(
                [
                    dbc.Card(
                        dbc.CardBody(id="section-3-1", className="p-2"),
                        className="mb-2",
                        style={"height": SECTION_HEIGHT},
                    ),
                    dbc.Card(
                        dbc.CardBody(id="section-3-2", className="p-2"),
                        className="mb-0",
                        style={"height": SECTION_HEIGHT},
                    ),
                ],
                width=4,
            ),
        ],
        className="mb-0 g-0",
    )

    row2 = dbc.Row(
        [
            dbc.Col(
                [
                    dbc.Card(
                        dbc.CardBody(id="section-4", className="p-2"),
                        className="mb-2",
                        style={"height": "508px"},
                    ),
                ],
                width=2,
                className="pe-2",
            ),
            dbc.Col(
                [
                    dbc.Card(
                        dbc.CardBody(id="section-5-1", className="p-2"),
                        className="mb-2",
                        style={"height": SECTION_HEIGHT2},
                    ),
                    dbc.Card(
                        dbc.CardBody(id="section-5-2", className="p-2"),
                        className="mb-2",
                        style={"height": SECTION_HEIGHT2},
                    ),
                ],
                width=4,
                className="pe-2",
            ),
            dbc.Col(
                [
                    dbc.Card(
                        dbc.CardBody(id="section-6-1", className="p-2"),
                        className="mb-2",
                        style={"height": SECTION_HEIGHT2},
                    ),
                    dbc.Card(
                        dbc.CardBody(id="section-6-2", className="p-2"),
                        className="mb-2",
                        style={"height": SECTION_HEIGHT2},
                    ),
                ],
                width=4,
                className="pe-2",
            ),
            dbc.Col(
                [
                    dbc.Card(
                        dbc.CardBody(id="section-7-1", className="p-2"),
                        className="mb-2",
                        style={"height": SECTION_HEIGHT2},
                    ),
                    dbc.Card(
                        dbc.CardBody(
                            id="section-7-2",
                            className="p-2 overflow-auto h-100",
                        ),
                        className="mb-2",
                        style={"height": SECTION_HEIGHT2},
                    ),
                ],
                width=2,
            ),
        ],
        className="g-2",
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


def render_dashboard_wrapper() -> Any:
    """Return a wrapper containing dashboard switch controls."""

    return html.Div(
        [
            dcc.Store(id="current-dashboard", data="new"),
            dbc.Button("Toggle Dashboard", id="new-dashboard-btn"),
            html.Div(id="dashboard-content", children=render_new_dashboard()),
        ]
    )


def render_floor_machine_layout_with_customizable_names() -> Any:
    """Return a layout for managing floors and machines with editing controls."""

    floors_data, machines_data = load_layout()
    if not floors_data:
        floors_data = {"floors": [{"id": 1, "name": "1st Floor"}], "selected_floor": "all"}
    if not machines_data:
        machines_data = {"machines": []}

    floors = floors_data.get("floors", [])
    selected_floor = floors_data.get("selected_floor", "all")
    machines = machines_data.get("machines", [])

    # sidebar buttons
    is_all_selected = selected_floor == "all"
    all_button_style = {
        "backgroundColor": "#007bff" if is_all_selected else "#696969",
        "color": "white" if is_all_selected else "black",
        "border": "2px solid #28a745" if is_all_selected else "1px solid #dee2e6",
        "cursor": "pointer",
        "borderRadius": "0.375rem",
    }

    left_sidebar_buttons = []
    left_sidebar_buttons.append(dcc.Store(id="floors-data", data=floors_data))
    left_sidebar_buttons.append(dcc.Store(id="machines-data", data=machines_data))
    left_sidebar_buttons.append(
        html.Div(
            html.Img(src="/assets/EnpresorMachine.png", style={"maxWidth": "100%", "maxHeight": "120px", "objectFit": "contain", "margin": "0 auto", "display": "block"}),
            className="text-center mb-3",
        )
    )

    left_sidebar_buttons.append(
        dbc.Button(
            "Show All Machines",
            id={"type": "floor-tile", "index": "all"},
            n_clicks=0,
            style=all_button_style,
            className="mb-3 w-100 floor-tile-btn",
            size="lg",
        )
    )

    for floor in floors:
        fid = floor.get("id")
        fname = floor.get("name", f"Floor {fid}")
        is_selected = fid == selected_floor and selected_floor != "all"
        floor_style = {
            "backgroundColor": "#007bff" if is_selected else "#696969",
            "color": "white" if is_selected else "black",
            "border": "2px solid #007bff" if is_selected else "1px solid #dee2e6",
            "cursor": "pointer",
            "borderRadius": "0.375rem",
        }

        content = dbc.Row(
            [
                dbc.Col(
                    dbc.Button(
                        "×",
                        id={"type": "delete-floor-btn", "index": fid},
                        color="danger",
                        size="md",
                        className="delete-floor-btn",
                        style={"fontSize": "1rem"},
                        title=f"Delete {fname}",
                    ),
                    width=1,
                    className="pe-1",
                ),
                dbc.Col(
                    dbc.Button(
                        fname,
                        id={"type": "floor-tile", "index": fid},
                        n_clicks=0,
                        style=floor_style,
                        className="w-100 floor-tile-btn",
                        size="lg",
                    ),
                    width=9,
                    className="px-1",
                ),
                dbc.Col(
                    dbc.Button(
                        "✏️",
                        id={"type": "edit-floor-name-btn", "index": fid},
                        color="light",
                        size="lg",
                        className="w-100 edit-floor-name-btn",
                    ),
                    width=2,
                    className="ps-1",
                ),
            ],
            className="g-0 align-items-center",
        )
        left_sidebar_buttons.append(html.Div(content, className="mb-2"))

    left_sidebar_buttons.append(
        dbc.Button("Add Floor", id="add-floor-btn", color="secondary", className="mb-2 w-100", size="lg")
    )

    connected_count = 0
    total_count = len(machines)
    left_sidebar_buttons.append(
        dbc.Card(
            dbc.CardBody(
                [
                    html.Div("Total Machines Online", className="text-muted mb-1", style={"fontSize": "1.2rem", "textAlign": "center"}),
                    html.Div(f"{connected_count} / {total_count}", style={"fontSize": "4.8rem", "fontWeight": "bold", "lineHeight": "1.2", "textAlign": "center"}),
                ],
                className="p-2",
            ),
            className="mb-2 machine-card-disconnected",
        )
    )

    left_sidebar_buttons.append(html.Div(id="save-status", className="text-success small text-center mt-3"))

    sidebar = dbc.Col(html.Div(left_sidebar_buttons), width=3, style={"alignSelf": "flex-start"})

    header_text = "All Machines" if selected_floor == "all" else next((f["name"] for f in floors if f["id"] == selected_floor), f"Floor {selected_floor}")

    right_content = [
        dbc.Card(
            dbc.CardBody(
                html.Div(
                    header_text,
                    className="text-center mb-0 floor-header-text",
                ),
                className="p-2 d-flex align-items-center justify-content-center",
                style={"height": HEADER_CARD_HEIGHT},
            ),
            className="mb-1 machine-card-disconnected",
        ),
        html.Div(id="machines-container"),
        dbc.Button("Add Machine", id="add-machine-btn", color="success", size="sm", className="mt-2"),
    ]

    main = dbc.Col(html.Div(right_content), width=9)

    return dbc.Row([sidebar, main])


def render_floor_machine_layout_enhanced_with_selection() -> Any:
    """Return floor layout including machine selection capability."""

    # In this simplified refactor the enhanced layout reuses the base layout.
    return render_floor_machine_layout_with_customizable_names()


__all__ = [
    "render_dashboard_wrapper",
    "render_new_dashboard",
    "render_main_dashboard",
    "render_floor_machine_layout_with_customizable_names",
    "render_floor_machine_layout_enhanced_with_selection",
]
