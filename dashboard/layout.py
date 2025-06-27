"""Simplified Dash layout utilities used by the dashboard."""

from typing import Any

from .machine_layout import load_layout

from .settings import load_language_preference, load_weight_preference
from i18n import tr
from .images import load_saved_image

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

# The taller cards span two standard section heights plus the vertical margin
# between them.  Derive these values from the base constants so any adjustments
# remain consistent with the overall grid layout.
ROW1_TALL_HEIGHT = f"{2 * int(SECTION_HEIGHT[:-2]) + 9}px"
ROW2_TALL_HEIGHT = f"{2 * int(SECTION_HEIGHT2[:-2]) + 8}px"


def render_dashboard_shell() -> Any:
    """Return the root layout with a dashboard switcher."""

    floors_data, machines_data = load_layout()
    if not floors_data:
        floors_data = {"floors": [{"id": 1, "name": "1st Floor"}], "selected_floor": "all"}
    if not machines_data:
        machines_data = {"machines": [], "next_machine_id": 1}

    header = html.Div(
        [
            html.H3(id="dashboard-title", children=tr("dashboard_title"), className="m-0"),
            html.Div(
                [
                    dbc.Button(tr("switch_dashboards"), id="new-dashboard-btn", color="light", size="sm", className="me-2"),
                    dbc.Button(tr("generate_report"), id="generate-report-btn", color="light", size="sm", className="me-2"),
                    # settings button in the header opens the configuration modal
                    dbc.Button(html.I(className="fas fa-cog"), id="header-settings-button", color="secondary", size="sm"),
                    dcc.Download(id="report-download"),
                ],
                className="ms-auto d-flex align-items-center",
            ),
        ],
        className="d-flex justify-content-between align-items-center bg-primary text-white p-2 mb-2",
    )

    return html.Div(
        [
            dcc.Store(id="current-dashboard", data="new"),
            dcc.Store(id="floors-data", data=floors_data),
            dcc.Store(id="machines-data", data=machines_data),
            dcc.Store(id="active-machine-store", data={"machine_id": None}),
            dcc.Interval(id="status-update-interval", interval=1000, n_intervals=0),
            dcc.Store(id="production-data-store"),
            dcc.Store(id="weight-preference-store", data=load_weight_preference()),
            dcc.Store(id="language-preference-store", data=load_language_preference()),
            dcc.Store(id="additional-image-store", data=load_saved_image()),
            header,
            connection_controls,
            html.Div(id="dashboard-content"),
            settings_modal,
        ]
    )


def render_new_dashboard() -> Any:
    """Return the main dashboard layout filled with visible sections."""
    grid = render_main_dashboard()

    return html.Div(
        [
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
                        style={"height": ROW1_TALL_HEIGHT},
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
                        style={"height": ROW2_TALL_HEIGHT},
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

    layout_row = dbc.Row([sidebar, main])

    hidden_sections = html.Div(
        [
            html.Div(id="section-1-1", children=[], style={"display": "none"}),
            html.Div(id="section-1-2", children=[], style={"display": "none"}),
            html.Div(id="section-2", children=[], style={"display": "none"}),
            html.Div(id="section-3-1", children=[], style={"display": "none"}),
            html.Div(id="section-3-2", children=[], style={"display": "none"}),
            html.Div(id="section-4", children=[], style={"display": "none"}),
            html.Div(id="section-5-1", children=[], style={"display": "none"}),
            html.Div(id="section-5-2", children=[], style={"display": "none"}),
            html.Div(id="section-6-1", children=[], style={"display": "none"}),
            html.Div(id="section-6-2", children=[], style={"display": "none"}),
            html.Div(id="section-7-1", children=[], style={"display": "none"}),
            html.Div(id="section-7-2", children=[], style={"display": "none"}),
        ]
    )

    return html.Div([layout_row, hidden_sections])


def render_floor_machine_layout_enhanced_with_selection() -> Any:
    """Return floor layout including machine selection capability."""

    # In this simplified refactor the enhanced layout reuses the base layout.
    return render_floor_machine_layout_with_customizable_names()


# Connection controls replicated from the legacy dashboard
connection_controls = dbc.Card(
    dbc.CardBody(
        [
            dbc.Row(
                [
                    # Active Machine display
                    dbc.Col(
                        html.Div(
                            [
                                html.Span(
                                    tr("active_machine_label"),
                                    id="active-machine-label",
                                    className="fw-bold small me-1",
                                ),
                                html.Span(
                                    id="active-machine-display",
                                    className="small",
                                ),
                            ],
                            className="mt-1",
                        ),
                        width={"xs": 3, "md": 3},
                        className="px-1",
                    ),

                    # Connection status text
                    dbc.Col(
                        html.Div(
                            [
                                html.Span(
                                    tr("status_label"),
                                    id="status-label",
                                    className="fw-bold small me-1",
                                ),
                                html.Span(
                                    tr("no_machine_selected"),
                                    id="connection-status",
                                    className="text-warning small",
                                ),
                            ],
                            className="mt-1 ms-2",
                        ),
                        width={"xs": 2, "md": 2},
                        className="px-1",
                    ),

                    # Mode selector dropdown
                    dbc.Col(
                        dcc.Dropdown(
                            id="mode-selector",
                            options=[
                                {"label": tr("live_mode_option"), "value": "live"},
                                {"label": tr("demo_mode_option"), "value": "demo"},
                                {
                                    "label": tr("historical_mode_option"),
                                    "value": "historical",
                                },
                            ],
                            value="live",
                            clearable=False,
                            searchable=False,
                            className="small p-0",
                            style={"min-width": "80px"},
                        ),
                        width={"xs": 1, "md": 1},
                        className="px-1",
                    ),

                    # Historical time slider
                    dbc.Col(
                        html.Div(
                            id="historical-time-controls",
                            className="d-none",
                            children=[
                                dcc.Slider(
                                    id="historical-time-slider",
                                    min=1,
                                    max=24,
                                    step=None,
                                    value=24,
                                    marks={
                                        1: {"label": "1hr", "style": {"fontSize": "8px"}},
                                        4: {"label": "4hr", "style": {"fontSize": "8px"}},
                                        8: {"label": "8hr", "style": {"fontSize": "8px"}},
                                        12: {"label": "12hr", "style": {"fontSize": "8px"}},
                                        24: {"label": "24hr", "style": {"fontSize": "8px"}},
                                    },
                                    included=False,
                                    className="mt-1",
                                ),
                                html.Div(
                                    id="historical-time-display",
                                    className="small text-info text-center",
                                    style={
                                        "whiteSpace": "nowrap",
                                        "fontSize": "0.7rem",
                                        "marginTop": "-2px",
                                    },
                                ),
                            ],
                        ),
                        width={"xs": 2, "md": 2},
                        className="px-1",
                    ),

                    # Settings and export buttons
                    dbc.Col(
                        html.Div(
                            dbc.ButtonGroup(
                                [
                                    dbc.Button(
                                        html.I(className="fas fa-cog"),
                                        id="settings-button",
                                        color="secondary",
                                        size="sm",
                                        className="py-0 me-1",
                                        style={"width": "38px"},
                                    ),
                                    html.Div(
                                        id="export-button-container",
                                        className="d-inline-block",
                                        children=[
                                            dbc.Button(
                                                tr("export_data"),
                                                id="export-data-button",
                                                color="primary",
                                                size="sm",
                                                className="py-0",
                                                disabled=True,
                                            ),
                                            dcc.Download(id="export-download"),
                                        ],
                                    ),
                                ],
                                className="",
                            ),
                            className="text-end",
                        ),
                        width={"xs": 4, "md": 4},
                        className="px-1",
                    ),

                    # Hidden server name input
                    dbc.Col(
                        dbc.Input(
                            id="server-name-input",
                            value="Satake.EvoRGB.1",
                            type="hidden",
                        ),
                        width=0,
                        style={"display": "none"},
                    ),
                ],
                className="g-0 align-items-center",
            ),
        ],
        className="py-1 px-2",
    ),
    className="mb-1 mt-0",
)


# Simplified settings modal used for configuration
settings_modal = dbc.Modal(
    [
        dbc.ModalHeader(html.Span(tr("system_settings_title"), id="settings-modal-header")),
        dbc.ModalBody(
            dbc.Tabs(
                [
                    dbc.Tab(html.Div("Display settings"), label="Display"),
                    dbc.Tab(html.Div("System settings"), label="System"),
                    dbc.Tab(html.Div("Email setup"), label="Email Setup"),
                ]
            )
        ),
        dbc.ModalFooter(
            dbc.Button(tr("close"), id="close-settings", color="secondary")
        ),
    ],
    id="settings-modal",
    size="lg",
    is_open=False,
)


__all__ = [
    "render_dashboard_wrapper",
    "render_new_dashboard",
    "render_main_dashboard",
    "render_floor_machine_layout_with_customizable_names",
    "render_floor_machine_layout_enhanced_with_selection",
    "connection_controls",
    "settings_modal",
]
