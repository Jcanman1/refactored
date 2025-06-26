"""Application state classes used by the dashboard."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


class AppState:
    """Minimal application state container."""

    def __init__(self) -> None:
        self.client = None
        self.connected = False
        self.last_update_time: Optional[datetime] = None
        self.thread_stop_flag = False
        self.update_thread = None
        self.tags: Dict[str, "TagData"] = {}


app_state = AppState()


@dataclass
class TagData:
    """Simple structure for maintaining tag history."""

    name: str
    max_points: int = 1000
    timestamps: List[datetime] = field(default_factory=list)
    values: List[Any] = field(default_factory=list)
    latest_value: Any = None

    def add_value(self, value: Any, timestamp: Optional[datetime] = None) -> None:
        if timestamp is None:
            timestamp = datetime.now()
        self.timestamps.append(timestamp)
        self.values.append(value)
        self.latest_value = value
        if len(self.timestamps) > self.max_points:
            self.timestamps = self.timestamps[-self.max_points :]
            self.values = self.values[-self.max_points :]

    def get_dataframe(self):  # pragma: no cover - pandas optional
        try:
            import pandas as pd
        except Exception:  # pragma: no cover - pandas may not be installed
            return None
        if not self.timestamps:
            return pd.DataFrame({"timestamp": [], "value": []})
        return pd.DataFrame({"timestamp": self.timestamps, "value": self.values})


__all__ = ["AppState", "TagData", "app_state"]
