"""Dash application instance used by the dashboard."""

import logging

try:
    from dash import Dash
    import dash_bootstrap_components as dbc  # type: ignore
    from i18n import tr
except Exception:  # pragma: no cover - dash may be missing during testing
    class Dash:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass

    class _Themes:
        BOOTSTRAP = ""

    class _DBC:
        themes = _Themes()

    dbc = _DBC()  # type: ignore

    def tr(key: str) -> str:
        return key

logger = logging.getLogger(__name__)

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    suppress_callback_exceptions=True,
)
app.title = tr("dashboard_title")

__all__ = ["app"]
