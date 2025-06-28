import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.test_callbacks import load_callbacks


def test_send_threshold_email(monkeypatch):
    callbacks, _ = load_callbacks(monkeypatch)
    callbacks.threshold_settings = {"email_address": "user@example.com"}
    monkeypatch.setitem(sys.modules, "dashboard.callbacks", callbacks)

    import dashboard.email_utils as email_utils

    monkeypatch.setattr(
        email_utils,
        "email_settings",
        {
            "smtp_server": "smtp.example.com",
            "smtp_port": 25,
            "smtp_username": "",
            "smtp_password": "",
            "from_address": "from@example.com",
        },
        raising=False,
    )

    captured = {}

    class DummySMTP:
        def __init__(self, host, port):
            captured["host"] = host
            captured["port"] = port

        def starttls(self):
            captured["tls"] = True

        def login(self, username, password):
            captured["login"] = (username, password)

        def sendmail(self, from_addr, to_addr, msg):
            captured["mail"] = (from_addr, to_addr, msg)

        def quit(self):
            captured["quit"] = True

    monkeypatch.setattr(email_utils.smtplib, "SMTP", DummySMTP)

    result = email_utils.send_threshold_email(3, is_high=False)
    assert result is True
    assert captured["host"] == "smtp.example.com"
    assert captured["port"] == 25
    assert captured["mail"][0] == "from@example.com"
    assert captured["mail"][1] == "user@example.com"
    assert "lower" in captured["mail"][2]
