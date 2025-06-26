"""Floor and machine layout helpers."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger(__name__)

# Data directory lives in repository root next to ``run_dashboard.py``
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
LAYOUT_PATH = DATA_DIR / "floor_machine_layout.json"


def save_layout(
    floors_data: Dict[str, Any],
    machines_data: Dict[str, Any],
    path: Path = LAYOUT_PATH,
) -> bool:
    """Persist ``floors_data`` and ``machines_data`` to ``path``."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(
                {
                    "floors": floors_data,
                    "machines": machines_data,
                    "saved_timestamp": datetime.now().isoformat(),
                },
                f,
                indent=4,
            )
        return True
    except Exception as exc:  # pragma: no cover - filesystem dependent
        logger.error("Error saving floor/machine layout: %s", exc)
        return False


def load_layout(
    path: Path = LAYOUT_PATH,
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Return saved ``floors_data`` and ``machines_data`` from ``path``."""
    try:
        if path.exists():
            with open(path, "r") as f:
                data = json.load(f)
            floors = data.get(
                "floors",
                {"floors": [{"id": 1, "name": "1st Floor"}], "selected_floor": "all"},
            )
            machines = data.get("machines", {"machines": [], "next_machine_id": 1})
            return floors, machines
        return None, None
    except Exception as exc:  # pragma: no cover - filesystem dependent
        logger.error("Error loading floor/machine layout: %s", exc)
        return None, None

__all__ = ["save_layout", "load_layout"]
