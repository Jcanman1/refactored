import sys

from tests.test_dashboard_utils import load_modules


def test_connect_and_monitor_success(monkeypatch):
    legacy, _, opc_client, _, _ = load_modules(monkeypatch)
    opc_client.machine_connections.clear()

    called = {}

    def connect(self):
        called['connect'] = True

    monkeypatch.setattr(sys.modules['opcua'].Client, 'connect', connect, raising=False)
    monkeypatch.setattr(sys.modules['opcua'].Client, 'set_session_timeout', lambda self, ms: None, raising=False)

    result = opc_client.run_async(
        opc_client.connect_and_monitor_machine_with_timeout('1.2.3.4', 'm1')
    )
    assert result is True
    assert 'm1' in opc_client.machine_connections
    assert called.get('connect')


def test_connect_and_monitor_failure(monkeypatch):
    legacy, _, opc_client, _, _ = load_modules(monkeypatch)
    opc_client.machine_connections.clear()

    def connect(self):
        raise RuntimeError('boom')

    monkeypatch.setattr(sys.modules['opcua'].Client, 'connect', connect, raising=False)
    monkeypatch.setattr(sys.modules['opcua'].Client, 'set_session_timeout', lambda self, ms: None, raising=False)

    result = opc_client.run_async(
        opc_client.connect_and_monitor_machine_with_timeout('1.2.3.4', 'm2')
    )
    assert result is False
    assert 'm2' not in opc_client.machine_connections
