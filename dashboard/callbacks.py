"""Dash callback implementations."""

from __future__ import annotations

import json
import logging
import random
from datetime import datetime
from pathlib import Path

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
)
from i18n import tr

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
LAYOUT_PATH = DATA_DIR / "floor_machine_layout.json"


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


def register_callbacks() -> None:
    """Register core callbacks with the Dash app."""

    @_dash_callback(
        Output("section-1-1", "children"),
        Output("production-data-store", "data"),
        Input("status-update-interval", "n_intervals"),
        State("production-data-store", "data"),
        State("weight-preference-store", "data"),
        State("language-preference-store", "data"),
    )
    def update_production_section(n, production_data, weight_pref, lang):
        """Update capacity display using latest OPC tag values."""
        pref = weight_pref or {"unit": "lb", "label": "lbs", "value": 1.0}
        lang = lang or "en"
        capacity_tag = "Status.ColorSort.Sort1.Throughput.KgPerHour.Current"
        capacity_val = None
        if app_state.connected and capacity_tag in app_state.tags:
            capacity_val = app_state.tags[capacity_tag]["data"].latest_value
        if capacity_val is None:
            capacity_val = 0
        total_capacity = convert_capacity_from_kg(capacity_val, pref)
        data = production_data or {}
        data.update({"capacity": total_capacity})
        content = html.Div(
            [
                html.H6(tr("production_capacity_title", lang)),
                html.Div(
                    f"{total_capacity:,.0f} {capacity_unit_label(pref)}",
                    className="fw-bold",
                ),
            ]
        )
        return content, data

    @_dash_callback(
        Output("floors-data", "data", allow_duplicate=True),
        [
            Input("floor-tile-1", "n_clicks"),
            Input("floor-tile-2", "n_clicks"),
            Input("floor-tile-3", "n_clicks"),
            Input("floor-tile-4", "n_clicks"),
            Input("floor-tile-5", "n_clicks"),
        ],
        State("floors-data", "data"),
        prevent_initial_call=True,
    )
    def handle_floor_selection(n1, n2, n3, n4, n5, floors_data):
        """Switch the selected floor when a tile is clicked."""
        ctx = callback_context
        if not ctx.triggered:
            return no_update
        trigger = ctx.triggered[0]["prop_id"]
        if "floor-tile-" in trigger:
            floor_id = int(trigger.split("floor-tile-")[1].split(".")[0])
            floors_data["selected_floor"] = floor_id
            return floors_data
        return no_update

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
        Output("section-1-2", "children"),
        Input("status-update-interval", "n_intervals"),
        State("production-data-store", "data"),
        State("language-preference-store", "data"),
    )
    def update_section_1_2(n, prod_data, lang):
        lang = lang or "en"
        accepts = (prod_data or {}).get("accepts", 47500)
        rejects = (prod_data or {}).get("rejects", 2500)
        total = accepts + rejects
        acc_pct = accepts / total * 100 if total else 0
        rej_pct = rejects / total * 100 if total else 0
        try:
            import plotly.graph_objects as go

            fig = go.Figure(
                data=[go.Pie(labels=[tr("accepts", lang), tr("rejects", lang)], values=[accepts, rejects], hole=0.4)]
            )
            fig.update_layout(margin=dict(l=20, r=20, t=20, b=20), showlegend=False)
            graph = dcc.Graph(figure=fig, config={"displayModeBar": False})
        except Exception:  # pragma: no cover - plotly missing
            graph = html.Div(f"{acc_pct:.1f}% / {rej_pct:.1f}%")
        return html.Div([graph])

    @_dash_callback(
        Output("section-3-2", "children"),
        Input("status-update-interval", "n_intervals"),
        State("language-preference-store", "data"),
    )
    def update_section_3_2(n, lang):
        lang = lang or "en"
        status_text = tr("good_status", lang) if app_state.connected else tr("fault_status", lang)
        return html.Div([
            html.H6(tr("machine_info_title", lang)),
            html.Div(f"Status: {status_text}"),
        ])

    @_dash_callback(
        Output("section-5-2", "children"),
        Input("status-update-interval", "n_intervals"),
    )
    def update_section_5_2(n):
        try:
            import plotly.graph_objects as go

            counts = [random.randint(10, 100) for _ in range(12)]
            fig = go.Figure(go.Bar(x=list(range(1, 13)), y=counts))
            fig.update_layout(margin=dict(l=20, r=20, t=20, b=20), showlegend=False)
            return dcc.Graph(figure=fig, config={"displayModeBar": False})
        except Exception:  # pragma: no cover - plotly missing
            return html.Div("N/A")

    @_dash_callback(
        Output("section-6-2", "children"),
        Input("status-update-interval", "n_intervals"),
        State("language-preference-store", "data"),
    )
    def update_section_6_2(n, lang):
        lang = lang or "en"
        return html.Div([
            html.H6(tr("sensitivity_threshold_alarms_title", lang)),
            html.Div(tr("no_changes_yet", lang)),
        ])

    @_dash_callback(
        Output("section-7-2", "children"),
        Input("status-update-interval", "n_intervals"),
        State("language-preference-store", "data"),
    )
    def update_section_7_2(n, lang):
        lang = lang or "en"
        return html.Div([
            html.H6(tr("machine_control_log_title", lang)),
            html.Div(tr("no_changes_yet", lang)),
        ])


register_callbacks()

__all__ = ["register_callbacks"]
