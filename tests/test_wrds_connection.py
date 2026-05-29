import pytest

from wrds_research_mcp import wrds_connection


class _FakeConnection:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


def test_run_wrds_operation_retries_transient_disconnect(monkeypatch) -> None:
    connections = []

    def fake_connect():
        connection = _FakeConnection()
        connections.append(connection)
        return connection

    monkeypatch.setattr(wrds_connection, "connect_wrds_quietly", fake_connect)
    calls = {"count": 0}

    def operation(_connection):
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("server closed the connection unexpectedly")
        return "ok"

    assert wrds_connection.run_wrds_operation(operation, max_attempts=2) == "ok"
    assert calls["count"] == 2
    assert len(connections) == 2
    assert all(connection.closed for connection in connections)


def test_run_wrds_operation_does_not_retry_non_transient_error(monkeypatch) -> None:
    connections = []

    def fake_connect():
        connection = _FakeConnection()
        connections.append(connection)
        return connection

    monkeypatch.setattr(wrds_connection, "connect_wrds_quietly", fake_connect)
    calls = {"count": 0}

    def operation(_connection):
        calls["count"] += 1
        raise ValueError("undefined column")

    with pytest.raises(ValueError, match="undefined column"):
        wrds_connection.run_wrds_operation(operation, max_attempts=2)

    assert calls["count"] == 1
    assert len(connections) == 1
    assert connections[0].closed


def test_is_transient_wrds_error_recognizes_interface_error_name() -> None:
    InterfaceError = type("InterfaceError", (Exception,), {})

    assert wrds_connection.is_transient_wrds_error(InterfaceError("connection already closed"))
