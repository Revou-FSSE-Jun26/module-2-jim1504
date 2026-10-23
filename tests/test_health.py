"""The public health check."""

from sqlalchemy.exc import OperationalError

from models import db


def test_health_reports_connected_database(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json() == {"status": "ok", "database": "connected"}


def test_health_hides_the_driver_error(client, monkeypatch):
    # A real failure message names the database host and user; none of it may reach the caller.
    def fail(*args, **kwargs):
        raise OperationalError("select 1", {}, Exception("connection to server at 10.0.0.1 failed for user postgres.secret"))

    monkeypatch.setattr(db.session, "execute", fail)
    res = client.get("/health")
    assert res.status_code == 503
    assert res.get_json() == {"status": "error", "database": "unreachable"}
    assert b"10.0.0.1" not in res.data and b"postgres.secret" not in res.data
