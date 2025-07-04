"""Dash callback implementations."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
import base64
import tempfile
import copy
import generate_report
from .email_utils import send_threshold_email

# ``dash`` is optional during testing so fall back to light stubs when missing.
try:  # pragma: no cover - optional dependency
    from dash import (
        ALL,
        Input,
        Output,
        State,
        callback_context,
        html,
        dcc,
        no_update,
    )  # type: ignore
    import dash_bootstrap_components as dbc  # type: ignore

    HAS_DASH = True
except Exception:  # pragma: no cover - provide minimal stubs
    from types import SimpleNamespace

    class _Dummy:
        def __init__(self, *args, **kwargs) -> None:  # pragma: no cover - stub
            pass

    class _ALL:  # pragma: no cover - stand in for ``dash.ALL``
        pass

    ALL = _ALL()
    Input = _Dummy  # type: ignore
    Output = _Dummy  # type: ignore
    State = _Dummy  # type: ignore
    callback_context = SimpleNamespace(triggered=[])  # type: ignore

    class _Module:  # pragma: no cover - simple component factory
        def __getattr__(self, name: str):
            def creator(*children: object, **props: object) -> tuple:
                return (name, children, props)

            return creator

    html = _Module()  # type: ignore
    dcc = _Module()  # type: ignore
    no_update = None  # type: ignore
    HAS_DASH = False

    class _BootstrapModule:  # pragma: no cover - container returning ``html.Div``
        def __getattr__(self, name: str):
            def creator(*children: object, **props: object):
                return html.Div(*children, **props)

            return creator

    dbc = _BootstrapModule()  # type: ignore

from .app import app

try:  # pragma: no cover - handle missing ``callback`` attribute
    _dash_callback = app.callback  # type: ignore[attr-defined]
except Exception:  # pragma: no cover - when Dash is not installed

    def _dash_callback(*args, **kwargs):
        def wrapper(func):
            return func

        return wrapper


from .state import app_state
from .opc_client import (
    pause_update_thread,
    resume_update_thread,
    discover_all_tags,
    run_async,
)
from .settings import (
    save_ip_addresses,
    save_weight_preference,
    save_email_settings,
    DEFAULT_EMAIL_SETTINGS,
    convert_capacity_from_kg,
    capacity_unit_label,
    load_threshold_settings,
    load_language_preference,
    load_weight_preference,
    load_theme_preference,
    save_theme_preference,
)
from .layout import (
    render_new_dashboard,
    render_floor_machine_layout_with_customizable_names,
    build_machine_card,
)
from .images import save_uploaded_image


from i18n import tr
from .layout import render_main_dashboard

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
LAYOUT_PATH = DATA_DIR / "floor_machine_layout.json"

NUMERIC_FONT = "Monaco, Consolas, 'Courier New', monospace"

previous_counter_values = [0] * 12
active_alarms: list[str] = []
machine_control_log: list[dict] = []
threshold_settings = load_threshold_settings() or {}
production_history: list[float] = []
counter_history = {i: [] for i in range(1, 13)}
last_email_times = {i: None for i in range(1, 13)}
threshold_violation_state = {
    i: {
        "is_violating": False,
        "violation_start_time": None,
        "email_sent": False,
    }
    for i in range(1, 13)
}


def _save_floor_machine_data(floors_data: dict, machines_data: dict) -> bool:
    """Persist floor/machine layout to ``data/floor_machine_layout.json``."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(LAYOUT_PATH, "w") as fh:
            json.dump({"floors": floors_data, "machines": machines_data}, fh, indent=4)
        return True
    except Exception as exc:  # pragma: no cover - filesystem errors
        logger.error("Error saving floor/machine data: %s", exc)
        return False


def _generate_csv_string(tags: dict) -> str:
    """Return CSV representation of tag values."""
    import csv
    import io

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Tag Name", "Value", "Timestamp"])
    for name, info in tags.items():
        data = info.get("data")
        value = getattr(data, "latest_value", None)
        ts = getattr(data, "timestamps", [datetime.now()])[-1]
        writer.writerow([name, value, ts])
    return buf.getvalue()


def _ordinal_suffix(n: int) -> str:
    """Return ``n`` with its ordinal suffix."""
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"

# ``send_threshold_email`` is provided by ``email_utils`` to avoid duplication.





@_dash_callback(
    Output("theme-selector", "value", allow_duplicate=True),
    Input("auto-connect-trigger", "data"),
    prevent_initial_call="initial_duplicate",
)
def load_initial_theme(trigger):
    """Load the saved theme preference."""
    theme = load_theme_preference()
    logger.info("Loading initial theme: %s", theme)
    return theme


def register_callbacks() -> None:
    """Register core callbacks with the Dash app."""

    @_dash_callback(
        Output("dashboard-content", "children"),
        Input("current-dashboard", "data"),
    )
    def render_dashboard(which):
        if which == "layout":
            return render_floor_machine_layout_with_customizable_names()
        if which == "new":
            return render_new_dashboard()
        return render_main_dashboard()

    @_dash_callback(
        Output("current-dashboard", "data", allow_duplicate=True),
        Input("new-dashboard-btn", "n_clicks"),
        State("current-dashboard", "data"),
        prevent_initial_call=True,
    )
    def manage_dashboard(n_clicks, current):
        if n_clicks is None:
            return "new"
        return "new" if current == "main" else "main"

    @_dash_callback(
        Output("historical-time-controls", "className"),
        Input("mode-selector", "value"),
        prevent_initial_call=True,
    )
    def toggle_historical_controls_visibility(mode):
        """Show or hide historical controls based on mode."""
        if mode == "historical":
            return "d-block"
        return "d-none"

    @_dash_callback(
        Output("floor-machine-container", "children"),
        Input("machines-data", "data"),
        Input("floors-data", "data"),
        Input("ip-addresses-store", "data"),
        Input("additional-image-store", "data"),
        Input("current-dashboard", "data"),
        Input("active-machine-store", "data"),
        Input("app-mode", "data"),
        Input("language-preference-store", "data"),
    )
    def render_floor_machine_layout_cb(
        machines_data,
        floors_data,
        ip_addrs,
        image_data,
        dashboard,
        active_machine,
        app_mode_data,
        lang,
    ):
        """Render the floor/machine management layout when on the new dashboard."""
        if dashboard != "new":
            if HAS_DASH:
                from dash.exceptions import PreventUpdate

                raise PreventUpdate
            return no_update

        ctx = callback_context
        if ctx.triggered:
            trigger_id = ctx.triggered[0]["prop_id"]
            if "machines-data" in trigger_id:
                floors = (
                    floors_data.get("floors", [])
                    if isinstance(floors_data, dict)
                    else []
                )
                for floor in floors:
                    if floor.get("editing"):
                        return no_update

        return render_floor_machine_layout_with_customizable_names(
            floors_data=floors_data,
            machines_data=machines_data,
        )

    @_dash_callback(
        Output("section-1-1", "children"),
        Output("production-data-store", "data"),
        Input("current-dashboard", "data"),
        Input("status-update-interval", "n_intervals"),
        State("production-data-store", "data"),
        State("weight-preference-store", "data"),
        State("language-preference-store", "data"),
        prevent_initial_call=True,
    )
    def update_production_section(which, n, production_data, weight_pref, lang):
        """Update capacity display using latest OPC tag values."""
        if which not in ("new", "main"):
            return no_update, no_update
        pref = weight_pref or {"unit": "lb", "label": "lbs", "value": 1.0}
        lang = lang or "en"

        cap_tag = "Status.ColorSort.Sort1.Throughput.KgPerHour.Current"
        acc_tag = "Status.Production.Accepts"
        rej_tag = "Status.Production.Rejects"

        cap_val = acc_val = rej_val = 0
        if app_state.connected:
            if cap_tag in app_state.tags:
                val = app_state.tags[cap_tag]["data"].latest_value
                cap_val = val if val is not None else 0
            if acc_tag in app_state.tags:
                val = app_state.tags[acc_tag]["data"].latest_value
                acc_val = val if val is not None else 0
            if rej_tag in app_state.tags:
                val = app_state.tags[rej_tag]["data"].latest_value
                rej_val = val if val is not None else 0

        total_capacity = convert_capacity_from_kg(cap_val, pref)
        accepts = convert_capacity_from_kg(acc_val, pref)
        rejects = convert_capacity_from_kg(rej_val, pref)

        total = accepts + rejects
        acc_pct = accepts / total * 100 if total else 0
        rej_pct = rejects / total * 100 if total else 0

        data = production_data or {}
        data.update(
            {"capacity": total_capacity, "accepts": accepts, "rejects": rejects}
        )

        content = html.Div(
            [
                html.H6(
                    tr("production_capacity_title", lang), className="text-left mb-2"
                ),
                html.Div(
                    f"{total_capacity:,.0f} {capacity_unit_label(pref)}",
                    className="fw-bold",
                ),
                html.Div(
                    f"{tr('accepts', lang)}: {accepts:,.0f} {capacity_unit_label(pref, False)} ({acc_pct:.1f}%)",
                    className="small",
                ),
                html.Div(
                    f"{tr('rejects', lang)}: {rejects:,.0f} {capacity_unit_label(pref, False)} ({rej_pct:.1f}%)",
                    className="small",
                ),
            ]
        )
        return content, data

    @_dash_callback(
        Output("floors-data", "data", allow_duplicate=True),
        Input({"type": "floor-tile", "index": ALL}, "n_clicks"),
        State({"type": "floor-tile", "index": ALL}, "id"),
        State("floors-data", "data"),
        prevent_initial_call=True,
    )
    def handle_floor_selection(clicks, ids, floors_data):
        """Switch the selected floor when a tile is clicked."""
        ctx = callback_context
        trigger = getattr(ctx, "triggered_id", None)

        fid = None
        if isinstance(trigger, dict) and trigger.get("type") == "floor-tile":
            fid = trigger.get("index")
        elif ctx.triggered:
            info = ctx.triggered[0]
            if not info.get("value"):
                return no_update
            prop = info.get("prop_id")
            if prop and "floor-tile" in prop:
                import json
                import re

                match = re.search(r"\{[^}]+\}", prop)
                if match:
                    try:
                        data = json.loads(match.group())
                        fid = data.get("index")
                    except Exception:
                        return no_update
            else:
                return no_update

        if fid is None:
            return no_update

        floors_data["selected_floor"] = fid
        return floors_data

    @_dash_callback(
        Output("floors-data", "data", allow_duplicate=True),
        Input("add-floor-btn", "n_clicks"),
        State("floors-data", "data"),
        State("machines-data", "data"),
        prevent_initial_call=True,
    )
    def add_floor_cb(n_clicks, floors_data, machines_data):
        if not n_clicks:
            return no_update
        floors = list(floors_data.get("floors", []))
        next_id = max([f.get("id", 0) for f in floors] or [0]) + 1
        floors.append(
            {
                "id": next_id,
                "name": f"{_ordinal_suffix(next_id)} Floor",
                "editing": False,
            }
        )
        new_floors = copy.deepcopy(floors_data)
        new_floors["floors"] = floors
        # Select the newly created floor so the machine list starts empty
        new_floors["selected_floor"] = next_id
        _save_floor_machine_data(new_floors, machines_data or {})
        return new_floors

    @_dash_callback(
        Output("floors-data", "data", allow_duplicate=True),
        Input({"type": "edit-floor-name-btn", "index": ALL}, "n_clicks"),
        State({"type": "edit-floor-name-btn", "index": ALL}, "id"),
        State("floors-data", "data"),
        prevent_initial_call=True,
    )
    def edit_floor_cb(clicks, ids, floors_data):
        ctx = callback_context
        if not ctx.triggered:
            return no_update
        for i, c in enumerate(clicks):
            if c and i < len(ids):
                fid = ids[i]["index"]
                for f in floors_data.get("floors", []):
                    if f.get("id") == fid:
                        f["editing"] = True
                        break
                return floors_data
        return no_update

    @_dash_callback(
        Output("floors-data", "data", allow_duplicate=True),
        Input({"type": "save-floor-name-btn", "index": ALL}, "n_clicks"),
        State({"type": "save-floor-name-btn", "index": ALL}, "id"),
        State({"type": "floor-name-input", "index": ALL}, "value"),
        State("floors-data", "data"),
        State("machines-data", "data"),
        prevent_initial_call=True,
    )
    def save_floor_name_cb(clicks, ids, values, floors_data, machines_data):
        ctx = callback_context
        if not ctx.triggered:
            return no_update
        for i, c in enumerate(clicks):
            if c and i < len(ids) and i < len(values):
                fid = ids[i]["index"]
                new_name = values[i]
                for f in floors_data.get("floors", []):
                    if f.get("id") == fid:
                        f["name"] = new_name
                        f["editing"] = False
                        break
                _save_floor_machine_data(floors_data, machines_data or {})
                return floors_data
        return no_update

    @_dash_callback(
        Output("floors-data", "data", allow_duplicate=True),
        Input({"type": "cancel-floor-name-btn", "index": ALL}, "n_clicks"),
        State({"type": "cancel-floor-name-btn", "index": ALL}, "id"),
        State("floors-data", "data"),
        prevent_initial_call=True,
    )
    def cancel_floor_name_cb(clicks, ids, floors_data):
        ctx = callback_context
        if not ctx.triggered:
            return no_update
        for i, c in enumerate(clicks):
            if c and i < len(ids):
                fid = ids[i]["index"]
                for f in floors_data.get("floors", []):
                    if f.get("id") == fid:
                        f["editing"] = False
                        break
                return floors_data
        return no_update

    @_dash_callback(
        Output("delete-confirmation-modal", "is_open"),
        Output("delete-item-details", "children"),
        Output("delete-pending-store", "data"),
        [
            Input({"type": "delete-floor-btn", "index": ALL}, "n_clicks"),
            Input({"type": "delete-machine-btn", "index": ALL}, "n_clicks"),
            Input("cancel-delete-btn", "n_clicks"),
        ],
        [
            State({"type": "delete-floor-btn", "index": ALL}, "id"),
            State({"type": "delete-machine-btn", "index": ALL}, "id"),
            State("floors-data", "data"),
            State("machines-data", "data"),
            State("delete-confirmation-modal", "is_open"),
        ],
        prevent_initial_call=True,
    )
    def toggle_delete_confirmation_modal(
        floor_clicks,
        machine_clicks,
        cancel_clicks,
        floor_ids,
        machine_ids,
        floors_data,
        machines_data,
        is_open,
    ):
        """Open or close the delete confirmation modal."""
        ctx = callback_context
        if not ctx.triggered:
            return no_update, no_update, no_update
        trigger = ctx.triggered[0]["prop_id"].split(".")[0]
        if trigger == "cancel-delete-btn" and cancel_clicks:
            return False, no_update, {}
        if "delete-floor-btn" in trigger:
            for i, c in enumerate(floor_clicks):
                if c and i < len(floor_ids):
                    fid = floor_ids[i]["index"]
                    name = next(
                        (
                            f.get("name", f"Floor {fid}")
                            for f in floors_data.get("floors", [])
                            if f.get("id") == fid
                        ),
                        f"Floor {fid}",
                    )
                    return True, name, {"type": "floor", "id": fid}
        if "delete-machine-btn" in trigger:
            for i, c in enumerate(machine_clicks):
                if c and i < len(machine_ids):
                    mid = machine_ids[i]["index"]
                    name = next(
                        (
                            m.get("name", f"Machine {mid}")
                            for m in machines_data.get("machines", [])
                            if m.get("id") == mid
                        ),
                        f"Machine {mid}",
                    )
                    return True, name, {"type": "machine", "id": mid}
        return no_update, no_update, no_update

    @_dash_callback(
        Output("machines-container", "children"),
        Input("floors-data", "data"),
        Input("machines-data", "data"),
        Input("current-dashboard", "data"),
    )
    def render_machine_cards(floors_data, machines_data, which):
        if which != "new":
            return no_update
        selected = floors_data.get("selected_floor", "all")
        machines = machines_data.get("machines", [])
        if selected != "all":
            # Cast IDs to strings to avoid type mismatch when filtering by floor
            machines = [m for m in machines if str(m.get("floor_id")) == str(selected)]
        from .settings import load_ip_addresses

        data = load_ip_addresses()
        ip_options = [
            {"label": item.get("label"), "value": item.get("ip")}
            for item in data.get("addresses", [])
            if isinstance(item, dict) and "ip" in item and "label" in item
        ]
        if not ip_options:
            ip_options = [
                {"label": "Default (192.168.0.125)", "value": "192.168.0.125"}
            ]

        cols = [
            dbc.Col(build_machine_card(m, ip_options), xs=6, md=4) for m in machines
        ]
        if not cols:
            return html.Div("No machines configured")

        def _to_float(val: object) -> float:
            try:
                return float(str(val).replace(",", ""))
            except Exception:
                return 0.0

        total_capacity = sum(_to_float(m.get("capacity")) for m in machines)
        total_accepts = sum(_to_float(m.get("accepts")) for m in machines)
        total_rejects = sum(_to_float(m.get("rejects")) for m in machines)

        pref = load_weight_preference()
        lang = load_language_preference()

        total_capacity_fmt = f"{total_capacity:,.0f}"
        total_accepts_fmt = f"{total_accepts:,.0f}"
        total_rejects_fmt = f"{total_rejects:,.0f}"

        summary_card = dbc.Card(
            dbc.CardBody(
                html.Div(
                    [
                        html.Span(
                            tr("total_production_label", lang),
                            className="fw-bold",
                            style={"fontSize": "1.2rem"},
                        ),
                        html.Span(
                            f"{total_capacity_fmt} {capacity_unit_label(pref)}",
                            style={"fontFamily": NUMERIC_FONT, "fontSize": "2.5rem"},
                        ),
                        html.Span(
                            tr("accepts_label", lang),
                            className="fw-bold ms-3",
                            style={"fontSize": "1.2rem"},
                        ),
                        html.Span(
                            f"{total_accepts_fmt} {capacity_unit_label(pref, False)}",
                            style={"fontFamily": NUMERIC_FONT, "fontSize": "2.5rem"},
                        ),
                        html.Span(
                            tr("rejects_label", lang),
                            className="fw-bold ms-3",
                            style={"fontSize": "1.2rem"},
                        ),
                        html.Span(
                            f"{total_rejects_fmt} {capacity_unit_label(pref, False)}",
                            style={"fontFamily": NUMERIC_FONT, "fontSize": "2.5rem"},
                        ),
                    ],
                    className="d-flex justify-content-around",
                )
            ),
            className="mt-2 bg-primary text-white",
        )

        return html.Div([dbc.Row(cols), summary_card])

    @_dash_callback(
        Output("machines-data", "data", allow_duplicate=True),
        Input("add-machine-btn", "n_clicks"),
        State("machines-data", "data"),
        State("floors-data", "data"),
        prevent_initial_call=True,
    )
    def add_machine_cb(n_clicks, machines_data, floors_data):
        if not n_clicks:
            return no_update
        machines = list(machines_data.get("machines", []))
        next_id = machines_data.get("next_machine_id") or (
            max([m.get("id", 0) for m in machines] or [0]) + 1
        )
        fid = floors_data.get("selected_floor", "all")
        if fid == "all":
            floors = floors_data.get("floors", [])
            fid = floors[0]["id"] if floors else 1
        name = f"{tr('machine_label', load_language_preference())} {next_id}"
        machines.append({"id": next_id, "floor_id": fid, "name": name})
        new_machines = copy.deepcopy(machines_data)
        new_machines["machines"] = machines
        new_machines["next_machine_id"] = next_id + 1
        _save_floor_machine_data(floors_data, new_machines)
        return new_machines

    @_dash_callback(
        Output("floors-data", "data", allow_duplicate=True),
        Output("machines-data", "data", allow_duplicate=True),
        Output("delete-confirmation-modal", "is_open", allow_duplicate=True),
        Input("confirm-delete-btn", "n_clicks"),
        State("delete-pending-store", "data"),
        State("floors-data", "data"),
        State("machines-data", "data"),
        prevent_initial_call=True,
    )
    def execute_confirmed_delete(n_clicks, pending, floors_data, machines_data):
        """Delete the selected item after user confirmation."""
        if not n_clicks or not pending:
            return no_update, no_update, no_update
        item_type = pending.get("type")
        item_id = pending.get("id")
        if item_type == "floor":
            floors_data["floors"] = [
                f for f in floors_data.get("floors", []) if f.get("id") != item_id
            ]
            machines_data["machines"] = [
                m
                for m in machines_data.get("machines", [])
                if m.get("floor_id") != item_id
            ]
            if floors_data.get("selected_floor") == item_id:
                floors_data["selected_floor"] = "all"
        elif item_type == "machine":
            machines_data["machines"] = [
                m for m in machines_data.get("machines", []) if m.get("id") != item_id
            ]
        else:
            return no_update, no_update, False
        _save_floor_machine_data(floors_data, machines_data)
        return floors_data, machines_data, False

    @_dash_callback(
        Output("current-dashboard", "data", allow_duplicate=True),
        Output("active-machine-store", "data"),
        Input({"type": "machine-card-click", "index": ALL}, "n_clicks"),
        State({"type": "machine-card-click", "index": ALL}, "id"),
        prevent_initial_call=True,
    )
    def manage_machine_selection(clicks, ids):
        """Set the active machine and return to the main dashboard."""
        ctx = callback_context
        if not ctx.triggered:
            return no_update, no_update
        for i, c in enumerate(clicks):
            if c and i < len(ids):
                mid = ids[i]["index"]
                return "main", {"machine_id": mid}
        return no_update, no_update

    @_dash_callback(
        Output("system-settings-save-status", "children", allow_duplicate=True),
        Output("weight-preference-store", "data", allow_duplicate=True),
        Input("save-system-settings", "n_clicks"),
        State("auto-connect-switch", "value"),
        State("ip-addresses-store", "data"),
        State("capacity-units-selector", "value"),
        State("custom-unit-name", "value"),
        State("custom-unit-weight", "value"),
        prevent_initial_call=True,
    )
    def save_system_settings_cb(
        n_clicks,
        auto_connect,
        ip_addresses,
        unit_value,
        custom_name,
        custom_weight,
    ):
        """Persist system configuration to disk."""
        if not n_clicks:
            return no_update, no_update
        settings = {"auto_connect": auto_connect}
        try:
            with open("system_settings.json", "w") as fh:
                json.dump(settings, fh, indent=4)
        except Exception as exc:  # pragma: no cover - filesystem errors
            logger.error("Error saving system settings: %s", exc)
            return "Error saving system settings", no_update
        if not save_ip_addresses(ip_addresses or {}):
            return "Error saving IP addresses", no_update
        if unit_value != "custom":
            save_weight_preference(unit_value, "", 1.0)
            pref = {"unit": unit_value, "label": "", "value": 1.0}
        else:
            weight = float(custom_weight or 1.0)
            save_weight_preference("custom", custom_name or "", weight)
            pref = {"unit": "custom", "label": custom_name or "", "value": weight}
        return "Settings saved successfully", pref

    @_dash_callback(
        Output("email-settings-save-status", "children"),
        Output("email-settings-store", "data", allow_duplicate=True),
        Input("save-email-settings", "n_clicks"),
        State("smtp-server-input", "value"),
        State("smtp-port-input", "value"),
        State("smtp-username-input", "value"),
        State("smtp-password-input", "value"),
        State("smtp-sender-input", "value"),
        prevent_initial_call=True,
    )
    def save_email_settings_cb(n_clicks, server, port, username, password, sender):
        """Persist SMTP credentials."""
        if not n_clicks:
            return no_update, no_update
        settings = {
            "smtp_server": server or DEFAULT_EMAIL_SETTINGS["smtp_server"],
            "smtp_port": int(port) if port else DEFAULT_EMAIL_SETTINGS["smtp_port"],
            "smtp_username": username or "",
            "smtp_password": password or "",
            "from_address": sender or DEFAULT_EMAIL_SETTINGS["from_address"],
        }
        success = save_email_settings(settings)
        if success:
            return "Email settings saved", settings
        return "Error saving email settings", no_update

    def _render_saved_ip_list(ip_data: dict) -> object:
        """Return HTML for the saved IP list."""
        if not ip_data or not ip_data.get("addresses"):
            return html.Div("No IP addresses saved", className="text-muted fst-italic")
        rows = []
        for item in ip_data["addresses"]:
            ip = item.get("ip")
            label = item.get("label")
            rows.append(
                dbc.Row(
                    [
                        dbc.Col(f"{label}: {ip}", width=9),
                        dbc.Col(
                            dbc.Button(
                                "×",
                                id={"type": "delete-ip-button", "index": ip},
                                color="danger",
                                size="sm",
                                className="py-0 px-2",
                            ),
                            width=3,
                            className="text-end",
                        ),
                    ],
                    className="mb-2 border-bottom pb-2",
                )
            )
        return html.Div(rows)

    @_dash_callback(
        Output("saved-ip-list", "children"),
        Input("ip-addresses-store", "data"),
    )
    def update_saved_ip_list(ip_data):
        return _render_saved_ip_list(ip_data)

    globals()["update_saved_ip_list"] = update_saved_ip_list

    @_dash_callback(
        Output("theme-selector", "value", allow_duplicate=True),
        Input("theme-selector", "value"),
        prevent_initial_call="initial_duplicate",
    )
    def load_initial_theme(_value):
        return load_theme_preference()

    @_dash_callback(
        Output("theme-selector", "value", allow_duplicate=True),
        Input("theme-selector", "value"),
        prevent_initial_call=True,
    )
    def save_theme_on_change(theme_value):
        if theme_value:
            save_theme_preference(theme_value)
        return theme_value

    @_dash_callback(
        Output("ip-addresses-store", "data", allow_duplicate=True),
        Output("new-ip-input", "value"),
        Output("new-ip-label", "value"),
        Output("system-settings-save-status", "children", allow_duplicate=True),
        Input("add-ip-button", "n_clicks"),
        State("new-ip-input", "value"),
        State("new-ip-label", "value"),
        State("ip-addresses-store", "data"),
        prevent_initial_call=True,
    )
    def add_ip_address(n_clicks, new_ip, new_label, current_data):
        if not n_clicks or not (new_ip and new_ip.strip()):
            return no_update, no_update, no_update, no_update

        if not new_label or not new_label.strip():
            lang = load_language_preference()
            new_label = f"{tr('machine_label', lang)} {len(current_data.get('addresses', [])) + 1}"

        ip = new_ip.strip().lower()
        localhost = ["localhost", "127.0.0.1", "::1"]
        valid = False
        if ip in localhost:
            valid = True
            if ip == "localhost":
                ip = "127.0.0.1"
        else:
            parts = ip.split(".")
            if len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
                valid = True
            else:
                import re
                if re.match(r"^[a-zA-Z0-9.-]+$", ip):
                    valid = True

        if not valid:
            return no_update, no_update, "", "Invalid IP address, hostname, or localhost format"

        addresses = list(current_data.get("addresses", []))
        if any(item.get("ip") == ip for item in addresses):
            return no_update, no_update, "", "IP address already exists"

        addresses.append({"ip": ip, "label": new_label})
        new_data = {"addresses": addresses}
        save_ip_addresses(new_data)
        return new_data, "", "", "IP address added successfully"

    globals()["add_ip_address"] = add_ip_address

    @_dash_callback(
        Output("delete-ip-trigger", "data"),
        Input({"type": "delete-ip-button", "index": ALL}, "n_clicks"),
        State({"type": "delete-ip-button", "index": ALL}, "id"),
        prevent_initial_call=True,
    )
    def handle_delete_button(n_clicks_list, button_ids):
        ctx = callback_context
        if not ctx.triggered:
            return no_update
        idx = None
        for i, c in enumerate(n_clicks_list):
            if c:
                idx = i
                break
        if idx is None or idx >= len(button_ids):
            return no_update
        ip_to_delete = button_ids[idx]["index"]
        return {"ip": ip_to_delete, "timestamp": datetime.now().timestamp()}

    globals()["handle_delete_button"] = handle_delete_button

    @_dash_callback(
        Output("ip-addresses-store", "data", allow_duplicate=True),
        Output("delete-result", "children"),
        Input("delete-ip-trigger", "data"),
        State("ip-addresses-store", "data"),
        prevent_initial_call=True,
    )
    def delete_ip_address(trigger_data, current_data):
        if not trigger_data or "ip" not in trigger_data:
            return no_update, no_update
        ip_to_delete = trigger_data["ip"]
        addresses = list(current_data.get("addresses", []))
        found = False
        label = ""
        for i, item in enumerate(addresses):
            if item.get("ip") == ip_to_delete:
                label = item.get("label", "")
                addresses.pop(i)
                found = True
                break
        message = f"Deleted {label} ({ip_to_delete})" if found else "IP address not found"
        new_data = {"addresses": addresses}
        save_ip_addresses(new_data)
        return new_data, message

    globals()["delete_ip_address"] = delete_ip_address

    @_dash_callback(
        Output("export-download", "data"),
        Input("export-data-button", "n_clicks"),
        prevent_initial_call=True,
    )
    def export_all_tags_cb(n_clicks):
        """Export all discovered OPC tags as a CSV download."""
        from dash.exceptions import PreventUpdate

        if not n_clicks or not app_state.client or not app_state.connected:
            raise PreventUpdate
        pause_update_thread()
        tags = run_async(discover_all_tags(app_state.client))
        csv_data = _generate_csv_string(tags)
        resume_update_thread()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return {"content": csv_data, "filename": f"satake_data_export_{timestamp}.csv"}

    @_dash_callback(
        Output("report-download", "data"),
        Input("generate-report-btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def generate_report_callback(n_clicks):
        """Generate a PDF report when the button is clicked."""
        try:
            from dash.exceptions import PreventUpdate
        except Exception:  # pragma: no cover - dash missing

            class PreventUpdate(Exception):
                pass

        if not n_clicks:
            raise PreventUpdate
        if generate_report is None:
            raise PreventUpdate

        data = generate_report.fetch_last_24h_metrics()
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            generate_report.build_report(data, tmp.name)
            with open(tmp.name, "rb") as f:
                pdf_bytes = f.read()

        pdf_b64 = base64.b64encode(pdf_bytes).decode()
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        return {
            "content": pdf_b64,
            "filename": f"production_report_{timestamp_str}.pdf",
            "type": "application/pdf",
            "base64": True,
        }

    globals()["generate_report_callback"] = generate_report_callback

    @_dash_callback(
        Output("settings-modal", "is_open"),
        [
            Input("settings-button", "n_clicks"),
            Input("close-settings", "n_clicks"),
        ],
        [State("settings-modal", "is_open")],
        prevent_initial_call=True,
    )
    def toggle_settings_modal(side_clicks, close_clicks, is_open):
        ctx = callback_context
        if not ctx.triggered:
            return no_update
        trigger = ctx.triggered[0]["prop_id"].split(".")[0]
        if trigger == "settings-button" and side_clicks:
            return not is_open
        if trigger == "close-settings" and close_clicks:
            return False
        return is_open

    @_dash_callback(
        Output("threshold-modal", "is_open"),
        [
            Input({"type": "open-threshold", "index": ALL}, "n_clicks"),
            Input("close-threshold-settings", "n_clicks"),
            Input("save-threshold-settings", "n_clicks"),
        ],
        [
            State("threshold-modal", "is_open"),
            State({"type": "threshold-min-enabled", "index": ALL}, "value"),
            State({"type": "threshold-max-enabled", "index": ALL}, "value"),
            State({"type": "threshold-min-value", "index": ALL}, "value"),
            State({"type": "threshold-max-value", "index": ALL}, "value"),
            State("threshold-email-address", "value"),
            State("threshold-email-minutes", "value"),
            State("threshold-email-enabled", "value"),
        ],
        prevent_initial_call=True,
    )
    def toggle_threshold_modal(
        open_clicks,
        close_clicks,
        save_clicks,
        is_open,
        min_enabled,
        max_enabled,
        min_values,
        max_values,
        email_address,
        email_minutes,
        email_enabled,
    ):
        ctx = callback_context
        if not ctx.triggered:
            return no_update
        trigger = ctx.triggered[0]["prop_id"].split(".")[0]
        if "open-threshold" in trigger and any(open_clicks):
            return True
        if trigger == "close-threshold-settings" and close_clicks:
            return False
        if trigger == "save-threshold-settings" and save_clicks:
            for i in range(12):
                threshold_settings[i + 1] = {
                    "min_enabled": bool(min_enabled[i]),
                    "max_enabled": bool(max_enabled[i]),
                    "min_value": float(min_values[i] or 0),
                    "max_value": float(max_values[i] or 0),
                }
            threshold_settings["email_enabled"] = bool(email_enabled)
            threshold_settings["email_address"] = email_address or ""
            threshold_settings["email_minutes"] = int(email_minutes or 2)
            save_threshold_settings(threshold_settings)
            return False
        return is_open

    @_dash_callback(
        Output("section-1-2", "children"),
        Input("status-update-interval", "n_intervals"),
        State("production-data-store", "data"),
        State("language-preference-store", "data"),
        prevent_initial_call=True,
    )
    def update_section_1_2(n, prod_data, lang):
        lang = lang or "en"
        accepts = (prod_data or {}).get("accepts", 0)
        rejects = (prod_data or {}).get("rejects", 0)
        total = accepts + rejects
        acc_pct = accepts / total * 100 if total else 0
        rej_pct = rejects / total * 100 if total else 0

        global previous_counter_values

        try:
            import plotly.graph_objects as go

            fig1 = go.Figure(
                data=[
                    go.Pie(
                        labels=[tr("accepts", lang), tr("rejects", lang)],
                        values=[accepts, rejects],
                        hole=0.4,
                    )
                ]
            )
            fig1.update_layout(margin=dict(l=10, r=10, t=20, b=20), showlegend=False)

            total_counter = sum(previous_counter_values)
            labels = [str(i) for i, v in enumerate(previous_counter_values, 1) if v > 0]
            values = (
                [v / total_counter * 100 for v in previous_counter_values if v > 0]
                if total_counter
                else []
            )
            fig2 = (
                go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.4)])
                if values
                else go.Figure()
            )
            fig2.update_layout(margin=dict(l=10, r=10, t=20, b=20), showlegend=False)

            graph1 = dcc.Graph(
                figure=fig1,
                config={"displayModeBar": False},
                style={"width": "100%", "height": "100%"},
            )
            graph2 = (
                dcc.Graph(
                    figure=fig2,
                    config={"displayModeBar": False},
                    style={"width": "100%", "height": "100%"},
                )
                if values
                else html.Div(tr("no_changes_yet", lang))
            )
        except Exception:  # pragma: no cover - plotly missing
            graph1 = html.Div(f"{acc_pct:.1f}% / {rej_pct:.1f}%")
            graph2 = html.Div("N/A")

        return html.Div(
            [
                html.Div(graph1, className="col-6"),
                html.Div(graph2, className="col-6"),
            ],
            className="row",
        )

    @_dash_callback(
        Output("section-3-2", "children"),
        Input("status-update-interval", "n_intervals"),
        State("language-preference-store", "data"),
        prevent_initial_call=True,
    )
    def update_section_3_2(n, lang):
        lang = lang or "en"
        serial_tag = "Status.Info.Serial"
        model_tag = "Status.Info.Type"

        serial = model = ""
        if app_state.connected:
            if serial_tag in app_state.tags:
                val = app_state.tags[serial_tag]["data"].latest_value
                serial = val if val is not None else ""
            if model_tag in app_state.tags:
                val = app_state.tags[model_tag]["data"].latest_value
                model = val if val is not None else ""

        status_text = (
            tr("good_status", lang) if app_state.connected else tr("fault_status", lang)
        )
        return html.Div(
            [
                html.H6(tr("machine_info_title", lang)),
                html.Div(f"{tr('serial_number_label', lang)} {serial}"),
                html.Div(f"{tr('model_label', lang)} {model}"),
                html.Div(f"Status: {status_text}"),
            ]
        )

    @_dash_callback(
        Output("section-2", "children"),
        Input("status-update-interval", "n_intervals"),
        State("language-preference-store", "data"),
        prevent_initial_call=True,
    )
    def update_section_2(n, lang):
        """Display preset, status and feeder information."""
        lang = lang or "en"
        preset_num_tag = "Status.Info.PresetNumber"
        preset_name_tag = "Status.Info.PresetName"
        fault_tag = "Status.Faults.GlobalFault"
        warn_tag = "Status.Faults.GlobalWarning"

        preset = "N/A"
        if app_state.connected:
            num = app_state.tags.get(preset_num_tag, {}).get("data")
            name = app_state.tags.get(preset_name_tag, {}).get("data")
            num_val = getattr(num, "latest_value", None)
            name_val = getattr(name, "latest_value", None)
            parts = []
            if num_val is not None:
                parts.append(str(num_val))
            if name_val:
                parts.append(str(name_val))
            if parts:
                preset = " ".join(parts)

        fault = False
        warning = False
        if app_state.connected:
            if fault_tag in app_state.tags:
                val = app_state.tags[fault_tag]["data"].latest_value
                fault = bool(val)
            if warn_tag in app_state.tags:
                val = app_state.tags[warn_tag]["data"].latest_value
                warning = bool(val)

        status_text = tr("good_status", lang)
        status_style = {"backgroundColor": "#28a745", "color": "white"}
        if fault:
            status_text = tr("fault_status", lang)
            status_style = {"backgroundColor": "#dc3545", "color": "white"}
        elif warning:
            status_text = tr("warning_status", lang)
            status_style = {"backgroundColor": "#ffc107", "color": "black"}

        running = False
        for i in range(1, 5):
            tag = f"Status.Feeders.{i}IsRunning"
            if app_state.connected and tag in app_state.tags:
                if bool(app_state.tags[tag]["data"].latest_value):
                    running = True
                    break
        feeder_text = (
            tr("running_state", lang) if running else tr("stopped_state", lang)
        )
        feeder_style = {
            "backgroundColor": "#28a745" if running else "#6c757d",
            "color": "white",
        }

        boxes = [
            html.Div(
                preset,
                className="mb-1 p-1",
                style={"backgroundColor": "#28a745", "color": "white"},
            ),
            html.Div(status_text, className="mb-1 p-1", style=status_style),
            html.Div(feeder_text, className="mb-2 p-1", style=feeder_style),
        ]

        rate_boxes = []
        for i in range(1, 5):
            rate = 0
            tag = f"Status.Feeders.{i}Rate"
            if app_state.connected and tag in app_state.tags:
                val = app_state.tags[tag]["data"].latest_value
                rate = val if val is not None else 0
            rate_boxes.append(
                html.Div(
                    f"F{i}: {rate}",
                    className="me-1 p-1",
                    style={
                        "backgroundColor": "#28a745" if running else "#6c757d",
                        "color": "white",
                    },
                )
            )

        return html.Div(
            [
                html.H6(tr("machine_status_title", lang)),
                *boxes,
                html.Div(rate_boxes, className="d-flex"),
            ]
        )

    @_dash_callback(
        Output("section-3-1", "children"),
        Input("status-update-interval", "n_intervals"),
        State("additional-image-store", "data"),
        State("language-preference-store", "data"),
        prevent_initial_call=True,
    )
    def update_section_3_1(n, img_data, lang):
        """Show corporate image with a load button."""
        lang = lang or "en"
        image_src = None
        if isinstance(img_data, dict):
            image_src = img_data.get("image")
        if image_src:
            image = html.Img(
                src=image_src,
                style={
                    "maxWidth": "100%",
                    "maxHeight": "130px",
                    "objectFit": "contain",
                    "display": "block",
                    "margin": "0 auto",
                },
            )
        else:
            image = html.Div(
                "No custom image loaded",
                className="text-muted text-center",
                style={
                    "height": "130px",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                },
            )

        return html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(html.H6(tr("corporate_logo_title", lang)), width=8),
                        dbc.Col(
                            dbc.Button(
                                tr("load_image_button", lang),
                                id="load-additional-image",
                                size="sm",
                                color="primary",
                            ),
                            width=4,
                        ),
                    ],
                    className="mb-2",
                ),
                image,
            ]
        )

    @_dash_callback(
        Output("upload-modal", "is_open"),
        [
            Input("load-additional-image", "n_clicks"),
            Input("close-upload-modal", "n_clicks"),
        ],
        [State("upload-modal", "is_open")],
        prevent_initial_call=True,
    )
    def toggle_upload_modal(load_clicks, close_clicks, is_open):
        """Show or hide the upload modal."""

        ctx = callback_context
        if not ctx.triggered:
            return no_update
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if trigger_id == "load-additional-image" and load_clicks and not is_open:
            return True
        if trigger_id == "close-upload-modal" and close_clicks and is_open:
            return False
        return is_open

    @_dash_callback(
        Output("additional-image-store", "data"),
        Output("upload-status", "children"),
        Input("upload-image", "contents"),
        State("upload-image", "filename"),
        prevent_initial_call=True,
    )
    def process_uploaded_image(contents, filename):
        """Handle an uploaded image and persist it."""

        if contents is None:
            return no_update, no_update
        try:
            logger.info("Processing image upload: %s", filename)
            new_data = {"image": contents}
            save_success = save_uploaded_image(contents)
            logger.info("Image save result: %s", save_success)
            return new_data, html.Div(f"Uploaded: {filename}", className="text-success")
        except Exception as exc:  # pragma: no cover - unexpected errors
            logger.error("Error uploading image: %s", exc)
            return no_update, html.Div(
                f"Error uploading image: {exc}", className="text-danger"
            )

    @_dash_callback(
        Output("section-4", "children"),
        Input("status-update-interval", "n_intervals"),
        State("language-preference-store", "data"),
        prevent_initial_call=True,
    )
    def update_section_4(n, lang):
        """List sensitivity names."""
        lang = lang or "en"
        items = []
        for i in range(1, 13):
            name = f"Primary {i}"
            tag = f"Settings.ColorSort.Primary{i}.Name"
            if app_state.connected and tag in app_state.tags:
                val = app_state.tags[tag]["data"].latest_value
                if val:
                    name = val
            items.append(html.Li(f"{i}. {name}", className="mb-1"))

        return html.Div(
            [
                html.H6(tr("sensitivities_title", lang)),
                html.Ul(items, className="mb-0"),
            ]
        )

    @_dash_callback(
        Output("section-5-1", "children"),
        Input("status-update-interval", "n_intervals"),
        State("language-preference-store", "data"),
        prevent_initial_call=True,
    )
    def update_section_5_1(n, lang):
        """Trend graph for production rate."""
        lang = lang or "en"
        tag = "Status.ColorSort.Sort1.Throughput.ObjectPerMin.Current"
        val = 0
        if app_state.connected and tag in app_state.tags:
            raw = app_state.tags[tag]["data"].latest_value
            val = raw if raw is not None else 0
        production_history.append(val)
        if len(production_history) > 60:
            production_history[:] = production_history[-60:]
        try:
            import plotly.graph_objects as go

            fig = go.Figure(
                go.Scatter(x=list(range(len(production_history))), y=production_history)
            )
            fig.update_layout(margin=dict(l=20, r=20, t=20, b=20), showlegend=False)
            graph = dcc.Graph(
                figure=fig,
                config={"displayModeBar": False},
                style={"width": "100%", "height": "100%"},
            )
        except Exception:  # pragma: no cover - plotly missing
            graph = html.Div(str(val))
        return html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            html.H6(tr("production_rate_objects_title", lang)), width=9
                        ),
                        dbc.Col(
                            dbc.Button(
                                "Units",
                                id={"type": "open-production-rate-units", "index": 0},
                                size="sm",
                                color="primary",
                            ),
                            width=3,
                        ),
                    ],
                    className="mb-2",
                ),
                graph,
            ]
        )

    @_dash_callback(
        Output("section-6-1", "children"),
        Input("status-update-interval", "n_intervals"),
        State("language-preference-store", "data"),
        prevent_initial_call=True,
    )
    def update_section_6_1(n, lang):
        """Trend graph for counter values."""
        global counter_history
        lang = lang or "en"
        for i, val in enumerate(previous_counter_values, 1):
            hist = counter_history[i]
            hist.append(val)
            if len(hist) > 60:
                counter_history[i] = hist[-60:]
        try:
            import plotly.graph_objects as go

            fig = go.Figure()
            for i in range(1, 13):
                fig.add_trace(
                    go.Scatter(
                        x=list(range(len(counter_history[i]))),
                        y=counter_history[i],
                        name=str(i),
                    )
                )
            fig.update_layout(margin=dict(l=20, r=20, t=20, b=20), showlegend=False)
            graph = dcc.Graph(
                figure=fig,
                config={"displayModeBar": False},
                style={"width": "100%", "height": "100%"},
            )
        except Exception:  # pragma: no cover - plotly missing
            graph = html.Div("N/A")
        return html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            html.H6(tr("counter_values_trend_title", lang)), width=9
                        ),
                        dbc.Col(
                            dbc.Button(
                                "Display",
                                id={"type": "open-display", "index": 0},
                                size="sm",
                                color="primary",
                            ),
                            width=3,
                        ),
                    ],
                    className="mb-2",
                ),
                graph,
            ]
        )

    @_dash_callback(
        Output("section-7-1", "children"),
        Input("status-update-interval", "n_intervals"),
        State("language-preference-store", "data"),
        prevent_initial_call=True,
    )
    def update_section_7_1(n, lang):
        """Air pressure gauge display."""
        lang = lang or "en"
        tag = "Status.Environmental.AirPressurePsi"
        value = 0
        if app_state.connected and tag in app_state.tags:
            raw = app_state.tags[tag]["data"].latest_value
            value = raw / 100 if raw is not None else 0
        try:
            import plotly.graph_objects as go

            fig = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=value,
                    gauge={"axis": {"range": [0, 100]}},
                )
            )
            fig.update_layout(margin=dict(l=20, r=20, t=30, b=20))
            graph = dcc.Graph(
                figure=fig,
                config={"displayModeBar": False},
                style={"width": "100%", "height": "100%"},
            )
        except Exception:  # pragma: no cover - plotly missing
            graph = html.Div(str(value))
        return html.Div(
            [
                html.H6(tr("air_pressure_title", lang)),
                graph,
            ]
        )

    @_dash_callback(
        Output("section-5-2", "children"),
        Input("status-update-interval", "n_intervals"),
        prevent_initial_call=True,
    )
    def update_section_5_2(n):
        global previous_counter_values, active_alarms
        try:
            import plotly.graph_objects as go

            TAG_PATTERN = "Status.ColorSort.Sort1.DefectCount{}.Rate.Current"
            values = []
            for i in range(1, 13):
                tag = TAG_PATTERN.format(i)
                val = previous_counter_values[i - 1]
                if app_state.connected and tag in app_state.tags:
                    new_val = app_state.tags[tag]["data"].latest_value
                    if new_val is not None:
                        val = new_val
                values.append(val)

            previous_counter_values = values

            # Threshold check
            active_alarms = []
            now = datetime.now()
            email_enabled = threshold_settings.get("email_enabled")
            email_minutes = threshold_settings.get("email_minutes", 2)
            for i, val in enumerate(values, 1):
                settings = threshold_settings.get(i, {})
                violation = False
                is_high = False
                if settings.get("min_enabled") and val < settings.get("min_value", 0):
                    active_alarms.append(f"Sens. {i} below min")
                    violation = True
                elif settings.get("max_enabled") and val > settings.get("max_value", 0):
                    active_alarms.append(f"Sens. {i} above max")
                    violation = True
                    is_high = True

                state = threshold_violation_state[i]
                if email_enabled:
                    if violation and not state["is_violating"]:
                        state["is_violating"] = True
                        state["violation_start_time"] = now
                        state["email_sent"] = False
                    elif violation and state["is_violating"]:
                        if not state["email_sent"]:
                            elapsed = (
                                now - state["violation_start_time"]
                            ).total_seconds()
                            if elapsed >= email_minutes * 60:
                                if send_threshold_email(i, is_high=is_high):
                                    state["email_sent"] = True
                    elif not violation and state["is_violating"]:
                        state["is_violating"] = False
                        state["violation_start_time"] = None
                        state["email_sent"] = False

            fig = go.Figure(go.Bar(x=list(range(1, 13)), y=values))
            fig.update_layout(margin=dict(l=20, r=20, t=20, b=20), showlegend=False)
            return dcc.Graph(
                figure=fig,
                config={"displayModeBar": False},
                style={"width": "100%", "height": "100%"},
            )
        except Exception:  # pragma: no cover - plotly missing
            return html.Div("N/A")

    @_dash_callback(
        Output("section-6-2", "children"),
        Input("status-update-interval", "n_intervals"),
        State("language-preference-store", "data"),
        prevent_initial_call=True,
    )
    def update_section_6_2(n, lang):
        lang = lang or "en"
        alarms = active_alarms

        if alarms:
            mid = len(alarms) // 2 + len(alarms) % 2
            left = [html.Li(a, className="text-danger mb-1") for a in alarms[:mid]]
            right = [html.Li(a, className="text-danger mb-1") for a in alarms[mid:]]
            alarm_display = html.Div(
                [
                    html.Div(
                        tr("active_alarms_title", lang),
                        className="fw-bold text-danger mb-2",
                    ),
                    html.Div(
                        [
                            html.Ul(left, className="ps-3 mb-0 col-6"),
                            html.Ul(right, className="ps-3 mb-0 col-6"),
                        ],
                        className="row",
                    ),
                ]
            )
        else:
            alarm_display = html.Div(
                tr("no_changes_yet", lang), className="text-success"
            )

        return html.Div(
            [
                html.H6(tr("sensitivity_threshold_alarms_title", lang)),
                alarm_display,
            ]
        )

    @_dash_callback(
        Output("section-7-2", "children"),
        Input("status-update-interval", "n_intervals"),
        State("language-preference-store", "data"),
        prevent_initial_call=True,
    )
    def update_section_7_2(n, lang):
        lang = lang or "en"
        entries = machine_control_log[:20]
        rows = []
        for idx, entry in enumerate(entries, start=1):
            ts = entry.get("timestamp", "")
            desc = f"{entry.get('tag', '')} {entry.get('action', '')}".strip()
            if desc:
                rows.append(html.Div(f"{idx}. {desc} {ts}", className="mb-1 small"))
        if not rows:
            rows.append(html.Div(tr("no_changes_yet", lang), className="text-muted"))

        return html.Div(
            [
                html.H6(tr("machine_control_log_title", lang)),
                *rows,
            ]
        )


register_callbacks()

__all__ = [
    "register_callbacks",
    "generate_report_callback",
    "add_ip_address",
    "update_saved_ip_list",
    "handle_delete_button",
    "delete_ip_address",
    "load_initial_theme",
]
