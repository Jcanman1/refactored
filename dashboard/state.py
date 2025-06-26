"""Application state classes used by the dashboard."""


from datetime import datetime

try:  # pragma: no cover - optional dependency
    import pandas as pd
except Exception:  # pragma: no cover - optional dependency
    pd = None


class AppState:
    """Simple container for OPC UA connection state."""


    def __init__(self) -> None:
        self.client = None
        self.connected = False

        self.last_update_time = None
        self.thread_stop_flag = False
        self.update_thread = None
        self.tags = {}


class TagData:
    """Helper for storing a tag history."""

    def __init__(self, name: str, max_points: int = 1000) -> None:
        self.name = name
        self.max_points = max_points
        self.timestamps = []
        self.values = []
        self.latest_value = None

    def add_value(self, value, timestamp=None) -> None:
        if timestamp is None:
            timestamp = datetime.now()

        self.timestamps.append(timestamp)
        self.values.append(value)
        self.latest_value = value

        if len(self.timestamps) > self.max_points:
            self.timestamps = self.timestamps[-self.max_points :]
            self.values = self.values[-self.max_points :]


    def get_dataframe(self):
        if not self.timestamps:
            return pd.DataFrame({"timestamp": [], "value": []}) if pd else None

        if pd is None:  # pragma: no cover - optional dependency
            return None

        return pd.DataFrame({"timestamp": self.timestamps, "value": self.values})


app_state = AppState()


__all__ = ["AppState", "TagData", "app_state"]
