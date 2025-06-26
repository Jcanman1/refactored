"""Dash application instance used by the dashboard."""

import logging

try:
    from dash import Dash
except Exception:  # pragma: no cover - dash may be missing during testing
    class Dash:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass

logger = logging.getLogger(__name__)

app = Dash(__name__)

__all__ = ["app"]
