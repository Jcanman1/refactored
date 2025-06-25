import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import hourly_data_saving as hds


def test_append_and_load_metrics(tmp_path):
    metrics = {"capacity": 10, "accepts": 3, "rejects": 1, "counter_1": 7}
    hds.append_metrics(metrics, machine_id="m1", export_dir=tmp_path)

    data = hds.load_recent_metrics(export_dir=tmp_path, machine_id="m1")

    assert data["capacity"]["values"] == [10.0]
    assert data["accepts"]["values"] == [3.0]
    assert data["rejects"]["values"] == [1.0]
    assert data[1]["values"] == [7.0]
    for i in range(2, 13):
        assert data[i]["values"] == []


def test_load_recent_metrics_empty(tmp_path):
    data = hds.load_recent_metrics(export_dir=tmp_path, machine_id="nope")
    for key in ["capacity", "accepts", "rejects"]:
        assert data[key]["values"] == []
    for i in range(1, 13):
        assert data[i]["values"] == []


def test_append_and_load_control_log(tmp_path):
    entry = {"time": datetime.now(), "command": "start", "value": "1"}
    hds.append_control_log(entry, machine_id="m1", export_dir=tmp_path)

    log = hds.load_recent_control_log(export_dir=tmp_path, machine_id="m1")
    assert len(log) == 1
    row = log[0]
    assert row["command"] == "start"
    assert row["value"] == "1"
    assert isinstance(row["timestamp"], datetime)


def test_load_recent_control_log_empty(tmp_path):
    log = hds.load_recent_control_log(export_dir=tmp_path, machine_id="missing")
    assert log == []
