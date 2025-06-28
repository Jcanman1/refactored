"""Simplified Dash layout utilities used by the dashboard."""

from typing import Any

from .machine_layout import load_layout

from .settings import (
    load_language_preference,
    load_weight_preference,
    load_ip_addresses,
    load_threshold_settings,
    load_theme_preference,
    load_email_settings,
)
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

# Flag indicating the shell layout has been generated at least once.
_SHELL_INITIALIZED = False


def _ensure_shell_initialized(func_name: str) -> None:
    """Raise ``RuntimeError`` if the dashboard shell was not built."""

    if not _SHELL_INITIALIZED:
        raise RuntimeError(
            f"{func_name} must be used inside render_dashboard_shell()"
        )


def render_dashboard_shell() -> Any:
    """Return the root layout with a dashboard switcher."""

    global _SHELL_INITIALIZED
    _SHELL_INITIALIZED = True

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
            dcc.Store(id="app-mode", data={"mode": "live"}),
            dcc.Store(id="app-mode-tracker"),
            dcc.Store(id="ip-addresses-store", data=load_ip_addresses()),
            dcc.Store(id="weight-preference-store", data=load_weight_preference()),
            dcc.Store(id="language-preference-store", data=load_language_preference()),
            dcc.Store(id="additional-image-store", data=load_saved_image()),
            dcc.Store(id="delete-pending-store", data={}),
            header,
            connection_controls,
            html.Div(id="dashboard-content"),
            threshold_modal,
            settings_modal,
            upload_modal,
            delete_confirmation_modal,
        ]
    )


def render_new_dashboard() -> Any:
    """Return the floor/machine management view.

    This layout omits the top-level ``dcc.Store`` components required by the
    callbacks.  It must be used inside :func:`render_dashboard_shell` or a
    layout that provides those stores.
    """

    _ensure_shell_initialized("render_new_dashboard")

    floors_data, machines_data = load_layout()
    if not floors_data:
        floors_data = {"floors": [{"id": 1, "name": "1st Floor"}], "selected_floor": "all"}
    if not machines_data:
        machines_data = {"machines": [], "next_machine_id": 1}

    return html.Div(
        [
            html.Div(id="floor-machine-container", className="px-4 pt-2 pb-4"),
            html.Div(
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
            ),
        ]
    )


def render_main_dashboard() -> Any:
    """Return the visible grid of dashboard sections.

    Like :func:`render_new_dashboard`, this produces a partial layout missing
    the ``dcc.Store`` components used by callbacks.  Only use it within
    :func:`render_dashboard_shell` or an equivalent wrapper.
    """

    _ensure_shell_initialized("render_main_dashboard")

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

    floors_data, machines_data = load_layout()
    if not floors_data:
        floors_data = {"floors": [{"id": 1, "name": "1st Floor"}], "selected_floor": "all"}
    if not machines_data:
        machines_data = {"machines": [], "next_machine_id": 1}

    return html.Div(
        [
            dcc.Store(id="current-dashboard", data="new"),
            dcc.Store(id="floors-data", data=floors_data),
            dcc.Store(id="machines-data", data=machines_data),
            dbc.Button("Toggle Dashboard", id="new-dashboard-btn"),
            html.Div(id="dashboard-content", children=render_new_dashboard()),
        ]
    )


def render_floor_machine_layout_with_customizable_names(
    floors_data: dict | None = None,
    machines_data: dict | None = None,
) -> Any:
    """Return a layout for managing floors and machines with editing controls.

    Parameters ``floors_data`` and ``machines_data`` default to ``None`` so the
    layout can load saved values from disk when not explicitly provided.  This
    allows callbacks to pass the in-memory store data directly for immediate
    updates without persisting to disk first.
    """

    if floors_data is None or machines_data is None:
        loaded_floors, loaded_machines = load_layout()
        if floors_data is None:
            floors_data = loaded_floors
        if machines_data is None:
            machines_data = loaded_machines

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
        is_editing = floor.get("editing", False)

        floor_style = {
            "backgroundColor": "#007bff" if is_selected else "#696969",
            "color": "white" if is_selected else "black",
            "border": "2px solid #007bff" if is_selected else "1px solid #dee2e6",
            "cursor": "pointer",
            "borderRadius": "0.375rem",
        }

        if is_editing:
            content = dbc.InputGroup(
                [
                    dbc.Button(
                        "×",
                        id={"type": "delete-floor-btn", "index": fid},
                        color="danger",
                        size="sm",
                        className="delete-floor-btn delete-floor-btn-inline",
                        style={"fontSize": "0.8rem"},
                        title=f"Delete {fname}",
                    ),
                    dbc.Input(
                        id={"type": "floor-name-input", "index": fid},
                        value=fname,
                        size="sm",
                        style={"fontSize": "0.9rem"},
                    ),
                    dbc.Button(
                        "✓",
                        id={"type": "save-floor-name-btn", "index": fid},
                        color="success",
                        size="sm",
                        style={"padding": "0.25rem 0.5rem"},
                    ),
                    dbc.Button(
                        "✗",
                        id={"type": "cancel-floor-name-btn", "index": fid},
                        color="secondary",
                        size="sm",
                        style={"padding": "0.25rem 0.5rem"},
                    ),
                ]
            )
        else:
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
    ]

    if selected_floor != "all":
        right_content.append(
            dbc.Button(
                "Add Machine",
                id="add-machine-btn",
                color="success",
                size="sm",
                className="mt-2",
            )
        )

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


def render_floor_machine_layout_enhanced_with_selection(
    floors_data: dict | None = None,
    machines_data: dict | None = None,
) -> Any:
    """Return floor layout including machine selection capability."""

    # In this simplified refactor the enhanced layout reuses the base layout.
    return render_floor_machine_layout_with_customizable_names(
        floors_data=floors_data, machines_data=machines_data
    )


def build_machine_card(machine: dict, ip_options: list, *, active: bool = False, lang: str | None = None) -> Any:
    """Return a Dash component displaying a machine summary."""

    lang = lang or "en"
    mid = machine.get("id")
    connected = bool(machine.get("connected"))

    if active:
        card_class = (
            "mb-2 machine-card-active-connected"
            if connected
            else "mb-2 machine-card-active-disconnected"
        )
    else:
        card_class = (
            "mb-2 machine-card-connected" if connected else "mb-2 machine-card-disconnected"
        )

    overlay = html.Div(
        "",
        id={"type": "machine-card-click", "index": mid},
        style={
            "position": "absolute",
            "top": "0",
            "left": "0",
            "right": "0",
            "bottom": "0",
            "zIndex": "1",
            "cursor": "pointer",
            "backgroundColor": "transparent",
        },
        title=f"Click to select Machine {mid}",
    )

    preset = machine.get("preset", "N/A")
    status = machine.get("status", "Unknown")
    feeder = machine.get("feeder", "Unknown")
    capacity = machine.get("capacity", "0")
    accepts = machine.get("accepts", "0")
    rejects = machine.get("rejects", "0")

    dropdown = dcc.Dropdown(
        id={"type": "machine-ip-dropdown", "index": mid},
        options=ip_options,
        value=machine.get("selected_ip", ip_options[0]["value"] if ip_options else None),
        placeholder="Select Machine",
        clearable=False,
        className="machine-card-dropdown",
        style={"color": "black", "position": "relative", "zIndex": "2", "width": "100%"},
    )

    left = html.Div(
        [
            html.Small(tr("select_machine_label", lang), className="mb-1 d-block"),
            dropdown,
            html.Small(
                f"({'Connected' if connected else 'Not Connected'})",
                className="d-block mb-1",
                style={
                    "color": "#007bff" if connected else "#dc3545",
                    "fontSize": "1.2rem",
                    "fontWeight": "bold",
                },
            ),
            html.Div(
                [
                    html.Small(tr("model_label", lang), className="fw-bold", style={"fontSize": "1.2rem"}),
                    html.Small(machine.get("model", "N/A"), style={"fontSize": "1.2rem"}),
                ],
                className="mb-1",
            ),
            html.Div(
                [
                    html.Small(tr("serial_number_label", lang), className="fw-bold", style={"fontSize": "1.2rem"}),
                    html.Small(machine.get("serial", "N/A"), style={"fontSize": "1.2rem"}),
                ],
                className="mb-0",
            ),
        ],
        className="mb-0",
    )

    right = html.Div(
        [
            html.Div(
                [
                    html.Small(tr("preset_label", lang).upper(), className="fw-bold d-block", style={"fontSize": "1.2rem"}),
                    html.Small(preset, style={"fontSize": "1.5rem", "color": "#1100FF"}),
                ],
                className="mb-0",
            ),
            html.Div(
                [
                    html.Small(tr("machine_status_label", lang), className="fw-bold d-block", style={"fontSize": "1.2rem"}),
                    html.Small(status, style={"fontSize": "1.5rem", "fontWeight": "bold"}),
                ],
                className="mb-0",
            ),
            html.Div(
                [
                    html.Small(tr("feeder_label", lang), className="fw-bold d-block", style={"fontSize": "1.2rem"}),
                    html.Small(feeder, style={"fontSize": "1.5rem", "fontWeight": "bold"}),
                ],
                className="mb-0",
            ),
        ],
        className="mb-0",
    )

    bottom = dbc.Row(
        [
            dbc.Col([
                html.Div(tr("accepts_label", lang), className="fw-bold text-center", style={"fontSize": "1.2rem"}),
                html.Div(accepts, className="text-center", style={"fontSize": "1.9rem", "fontWeight": "bold"}),
            ], md=6, sm=12),
            dbc.Col([
                html.Div(tr("rejects_label", lang), className="fw-bold text-center", style={"fontSize": "1.2rem"}),
                html.Div(rejects, className="text-center", style={"fontSize": "1.9rem", "fontWeight": "bold"}),
            ], md=6, sm=12),
        ],
        className="mb-0",
    )

    return dbc.Card(
        [
            overlay,
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(html.H6(f"{tr('machine_label', lang)} {mid}", className="text-center mb-2"), width=10),
                            dbc.Col(
                                dbc.Button(
                                    "×",
                                    id={"type": "delete-machine-btn", "index": mid},
                                    color="danger",
                                    size="sm",
                                    className="p-1",
                                    style={"fontSize": "0.8rem", "width": "25px", "height": "25px", "borderRadius": "50%", "lineHeight": "1", "position": "relative", "zIndex": "2"},
                                    title=f"Delete Machine {mid}",
                                ),
                                width=2,
                                className="text-end",
                            ),
                        ],
                        className="mb-0",
                    ),
                    dbc.Row([dbc.Col(left, md=6, sm=12), dbc.Col(right, md=6, sm=12)], className="mb-0"),
                    html.Div(
                        html.Div(f"{capacity}", className="text-center production-data"),
                        className="mb-0",
                    ),
                    bottom,
                ],
                style={"position": "relative"},
            ),
        ],
        className=card_class,
        style={"position": "relative", "cursor": "pointer", "flexWrap": "wrap"},
    )


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


# Form for editing threshold settings
def create_threshold_settings_form() -> list[Any]:
    """Return rows of inputs for threshold alarm configuration."""
    settings = load_threshold_settings() or {}
    rows = []
    for i in range(1, 13):
        data = settings.get(i, {})
        rows.append(
            dbc.Row(
                [
                    dbc.Col(html.Div(f"Sensitivity {i}:", className="fw-bold"), width=2),
                    dbc.Col(
                        dbc.Input(
                            id={"type": "threshold-min-value", "index": i},
                            type="number",
                            value=data.get("min_value", 0),
                            min=0,
                            max=180,
                            step=1,
                            size="sm",
                        ),
                        width=1,
                    ),
                    dbc.Col(
                        dbc.Switch(
                            id={"type": "threshold-min-enabled", "index": i},
                            label="Min",
                            value=data.get("min_enabled", False),
                            className="medium",
                        ),
                        width=2,
                    ),
                    dbc.Col(
                        dbc.Input(
                            id={"type": "threshold-max-value", "index": i},
                            type="number",
                            value=data.get("max_value", 0),
                            min=0,
                            max=200,
                            step=1,
                            size="sm",
                        ),
                        width=1,
                    ),
                    dbc.Col(
                        dbc.Switch(
                            id={"type": "threshold-max-enabled", "index": i},
                            label="Max",
                            value=data.get("max_enabled", False),
                            className="medium",
                        ),
                        width=2,
                    ),
                ],
                className="mb-2",
            )
        )

    rows.append(
        dbc.Row(
            [
                dbc.Col(html.Div("Email Notifications:", className="fw-bold"), width=2),
                dbc.Col(
                    dbc.Input(
                        id="threshold-email-address",
                        type="email",
                        placeholder="Email address",
                        value=settings.get("email_address", ""),
                        size="sm",
                    ),
                    width=3,
                ),
                dbc.Col(
                    dbc.InputGroup(
                        [
                            dbc.Input(
                                id="threshold-email-minutes",
                                type="number",
                                min=1,
                                max=60,
                                step=1,
                                value=settings.get("email_minutes", 2),
                                size="sm",
                            ),
                            dbc.InputGroupText("min", className="p-1 small"),
                        ],
                        size="sm",
                    ),
                    width=1,
                ),
                dbc.Col(
                    dbc.Switch(
                        id="threshold-email-enabled",
                        value=settings.get("email_enabled", False),
                        className="medium",
                    ),
                    width=2,
                ),
            ],
            className="mt-3 mb-2",
        )
    )

    return rows


# Modal containing the threshold settings form
threshold_modal = dbc.Modal(
    [
        dbc.ModalHeader(html.Span(tr("threshold_settings_title"), id="threshold-modal-header")),
        dbc.ModalBody(html.Div(id="threshold-form-container", children=create_threshold_settings_form())),
        dbc.ModalFooter(
            [
                dbc.Button(tr("close"), id="close-threshold-settings", color="secondary", className="me-2"),
                dbc.Button(tr("save_changes"), id="save-threshold-settings", color="primary"),
            ]
        ),
    ],
    id="threshold-modal",
    size="xl",
    is_open=False,
)


# Settings modal mirroring the legacy dashboard configuration options
email_settings = load_email_settings()
theme_pref = load_theme_preference()
weight_pref = load_weight_preference()
language_pref = load_language_preference()
settings_modal = dbc.Modal(
    [
        dbc.ModalHeader(html.Span(tr("system_settings_title"), id="settings-modal-header")),
        dbc.ModalBody(
            dbc.Tabs(
                [
                    # Display tab
                    dbc.Tab(
                        html.Div(
                            [
                                html.P(tr("display_settings_title"), className="lead mt-2", id="display-settings-subtitle"),
                                html.Hr(),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Label(tr("color_theme_label"), className="fw-bold", id="color-theme-label"),
                                            width=4,
                                        ),
                                        dbc.Col(
                                            dbc.RadioItems(
                                                id="theme-selector",
                                                options=[
                                                    {"label": tr("light_mode_option"), "value": "light"},
                                                    {"label": tr("dark_mode_option"), "value": "dark"},
                                                ],
                                                value=theme_pref,
                                                inline=True,
                                            ),
                                            width=8,
                                        ),
                                    ],
                                    className="mb-3",
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Label(tr("capacity_units_label"), className="fw-bold", id="capacity-units-label"),
                                            width=4,
                                        ),
                                        dbc.Col(
                                            [
                                                dbc.RadioItems(
                                                    id="capacity-units-selector",
                                                    options=[
                                                        {"label": "Kg", "value": "kg"},
                                                        {"label": "Lbs", "value": "lb"},
                                                        {"label": "Custom", "value": "custom"},
                                                    ],
                                                    value=weight_pref.get("unit", "lb"),
                                                    inline=True,
                                                ),
                                                dbc.Input(
                                                    id="custom-unit-name",
                                                    type="text",
                                                    placeholder="Unit Name",
                                                    className="mt-2",
                                                    style={"display": "none"},
                                                    value=weight_pref.get("label", ""),
                                                ),
                                                dbc.Input(
                                                    id="custom-unit-weight",
                                                    type="number",
                                                    placeholder="Weight in lbs",
                                                    className="mt-2",
                                                    style={"display": "none"},
                                                    value=weight_pref.get("value", 1.0),
                                                ),
                                            ],
                                            width=8,
                                        ),
                                    ],
                                    className="mb-3",
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Label(tr("language_label"), className="fw-bold", id="language-label"),
                                            width=4,
                                        ),
                                        dbc.Col(
                                            dbc.RadioItems(
                                                id="language-selector",
                                                options=[
                                                    {"label": tr("english_option"), "value": "en"},
                                                    {"label": tr("spanish_option"), "value": "es"},
                                                    {"label": tr("japanese_option"), "value": "ja"},
                                                ],
                                                value=language_pref,
                                                inline=True,
                                            ),
                                            width=8,
                                        ),
                                    ],
                                    className="mb-3",
                                ),
                            ]
                        ),
                        label=tr("display_tab_label"),
                    ),
                    # System tab
                    dbc.Tab(
                        html.Div(
                            [
                                html.P(tr("system_configuration_title"), className="lead mt-2", id="system-configuration-title"),
                                html.Hr(),
                                dbc.Row(
                                    [
                                        dbc.Col(dbc.Label(tr("auto_connect_label"), id="auto-connect-label"), width=8),
                                        dbc.Col(
                                            dbc.Switch(id="auto-connect-switch", value=True, className="float-end"),
                                            width=4,
                                        ),
                                    ],
                                    className="mb-3",
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(dbc.Label(tr("add_machine_ip_label"), id="add-machine-ip-label"), width=3),
                                        dbc.Col(
                                            dbc.InputGroup(
                                                [
                                                    dbc.Input(
                                                        id="new-ip-label",
                                                        value="",
                                                        type="text",
                                                        placeholder=tr("machine_name_placeholder"),
                                                        size="sm",
                                                    ),
                                                    dbc.Input(
                                                        id="new-ip-input",
                                                        value="",
                                                        type="text",
                                                        placeholder=tr("ip_address_placeholder"),
                                                        size="sm",
                                                    ),
                                                    dbc.Button(tr("add_button"), id="add-ip-button", color="primary", size="sm"),
                                                ]
                                            ),
                                            width=9,
                                        ),
                                    ],
                                    className="mb-3",
                                ),
                                html.Div(
                                    [
                                        html.P(tr("saved_machine_ips"), className="mt-3 mb-2"),
                                        html.Div(id="delete-result", className="mb-2 text-success"),
                                        html.Div(id="saved-ip-list", className="border p-2 mb-3", style={"minHeight": "100px"}),
                                    ]
                                ),
                                dbc.Button(
                                    tr("save_system_settings"),
                                    id="save-system-settings",
                                    color="success",
                                    className="mt-3 w-100",
                                ),
                                html.Div(id="system-settings-save-status", className="text-success mt-2"),
                            ]
                        ),
                        label=tr("system_tab_label"),
                    ),
                    # Email setup tab
                    dbc.Tab(
                        html.Div(
                            [
                                html.P(tr("smtp_email_configuration_title"), className="lead mt-2", id="smtp-email-configuration-title"),
                                html.Hr(),
                                dbc.Row([
                                    dbc.Col(dbc.Label(tr("smtp_server_label"), id="smtp-server-label"), width=4),
                                    dbc.Col(dbc.Input(id="smtp-server-input", type="text", value=email_settings.get("smtp_server", "")), width=8),
                                ], className="mb-3"),
                                dbc.Row([
                                    dbc.Col(dbc.Label(tr("port_label"), id="smtp-port-label"), width=4),
                                    dbc.Col(dbc.Input(id="smtp-port-input", type="number", value=email_settings.get("smtp_port", 587)), width=8),
                                ], className="mb-3"),
                                dbc.Row([
                                    dbc.Col(dbc.Label(tr("username_label"), id="smtp-username-label"), width=4),
                                    dbc.Col(dbc.Input(id="smtp-username-input", type="text", value=email_settings.get("smtp_username", "")), width=8),
                                ], className="mb-3"),
                                dbc.Row([
                                    dbc.Col(dbc.Label(tr("password_label"), id="smtp-password-label"), width=4),
                                    dbc.Col(dbc.Input(id="smtp-password-input", type="password", value=email_settings.get("smtp_password", "")), width=8),
                                ], className="mb-3"),
                                dbc.Row([
                                    dbc.Col(dbc.Label(tr("from_address_label"), id="smtp-from-label"), width=4),
                                    dbc.Col(dbc.Input(id="smtp-sender-input", type="email", value=email_settings.get("from_address", "")), width=8),
                                ], className="mb-3"),
                                dbc.Button(
                                    tr("save_email_settings"),
                                    id="save-email-settings",
                                    color="success",
                                    className="mt-3 w-100",
                                ),
                                html.Div(id="email-settings-save-status", className="text-success mt-2"),
                            ]
                        ),
                        label=tr("email_tab_label"),
                    ),
                    # About tab
                    dbc.Tab(
                        html.Div(
                            [
                                html.P(tr("about_this_dashboard_title"), className="lead mt-2"),
                                html.Hr(),
                                html.P([
                                    "Satake Enpresor Monitor Dashboard ",
                                    html.Span("v1.0.3", className="badge bg-secondary"),
                                ]),
                                html.P("OPC UA Monitoring System for Satake Enpresor RGB Sorters"),
                                html.P(
                                    "© 2023 Satake USA, Inc. All rights reserved.",
                                    className="text-muted small",
                                ),
                                html.Hr(),
                                html.P("Support Contact:", className="mb-1 fw-bold"),
                                html.P([
                                    html.I(className="fas fa-envelope me-2"),
                                    "techsupport@satake-usa.com",
                                ], className="mb-1"),
                                html.P([
                                    html.I(className="fas fa-phone me-2"),
                                    "(281) 276-3700",
                                ], className="mb-1"),
                            ]
                        ),
                        label=tr("about_tab_label"),
                    ),
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


# Modal for uploading a custom image
upload_modal = dbc.Modal(
    [
        dbc.ModalHeader(html.Span(tr("upload_image_title"), id="upload-modal-header")),
        dbc.ModalBody(
            [
                dcc.Upload(
                    id="upload-image",
                    children=html.Div([
                        tr("drag_and_drop"),
                        html.A(tr("select_image")),
                    ]),
                    style={
                        "width": "100%",
                        "height": "60px",
                        "lineHeight": "60px",
                        "borderWidth": "1px",
                        "borderStyle": "dashed",
                        "borderRadius": "5px",
                        "textAlign": "center",
                        "margin": "10px",
                    },
                    multiple=False,
                ),
                html.Div(id="upload-status"),
            ]
        ),
        dbc.ModalFooter(
            [dbc.Button(tr("close"), id="close-upload-modal", color="secondary")]
        ),
    ],
    id="upload-modal",
    is_open=False,
)


# Confirmation modal displayed before deleting a floor or machine
delete_confirmation_modal = dbc.Modal(
    [
        dbc.ModalHeader(
            dbc.ModalTitle(tr("confirm_deletion_title"), id="delete-confirmation-header")
        ),
        dbc.ModalBody(
            [
                html.Div(tr("delete_warning"), id="delete-warning", className="mb-2"),
                html.Div(id="delete-item-details"),
            ]
        ),
        dbc.ModalFooter(
            [
                dbc.Button(tr("cancel"), id="cancel-delete-btn", color="secondary", className="me-2"),
                dbc.Button(tr("yes_delete"), id="confirm-delete-btn", color="danger"),
            ]
        ),
    ],
    id="delete-confirmation-modal",
    is_open=False,
    centered=True,
)


__all__ = [
    "render_dashboard_shell",
    "render_dashboard_wrapper",
    "render_new_dashboard",
    "render_main_dashboard",
    "render_floor_machine_layout_with_customizable_names",
    "render_floor_machine_layout_enhanced_with_selection",
    "build_machine_card",
    "connection_controls",
    "threshold_modal",
    "settings_modal",
    "upload_modal",
    "delete_confirmation_modal",
]
