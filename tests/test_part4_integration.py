import yaml

from app import integration


def write_yaml(tmp_path, data):
    path = tmp_path / "request.yaml"
    path.write_text(
        yaml.safe_dump(data)
    )
    return path


def valid_request():
    return {
        "version": 1,
        "router": "10.0.29.101",
        "method": "ansible",
        "action": "apply",
        "desired": {
            "interface": {
                "name": "Loopback123",
                "ipv4": "172.23.123.1/32",
                "description": "IPA2026-66070123",
                "admin_state": "up",
            }
        },
    }


def test_missing_bot_mention_stops_before_dispatch(
    monkeypatch,
    tmp_path,
):
    path = write_yaml(
        tmp_path,
        valid_request(),
    )

    called = False

    def fake_dispatch(data):
        nonlocal called
        called = True

    monkeypatch.setattr(
        integration,
        "dispatch_request",
        fake_dispatch,
    )

    result = integration.process_request(
        [],
        path,
        "TEST-BOT",
    )

    assert result == {
        "status": "error",
        "result": "missing_bot_mention",
    }

    assert called is False


def test_invalid_yaml_request_stops_before_dispatch(
    monkeypatch,
    tmp_path,
):
    data = valid_request()
    del data["router"]

    path = write_yaml(
        tmp_path,
        data,
    )

    called = False

    def fake_dispatch(data):
        nonlocal called
        called = True

    monkeypatch.setattr(
        integration,
        "dispatch_request",
        fake_dispatch,
    )

    result = integration.process_request(
        ["TEST-BOT"],
        path,
        "TEST-BOT",
    )

    assert result == {
        "status": "error",
        "result": "missing_router",
    }

    assert called is False


def test_valid_request_dispatches_parsed_data(
    monkeypatch,
    tmp_path,
):
    data = valid_request()

    path = write_yaml(
        tmp_path,
        data,
    )

    calls = []

    def fake_dispatch(request_data):
        calls.append(request_data)

        return {
            "status": "ok",
            "result": "applied",
        }

    monkeypatch.setattr(
        integration,
        "dispatch_request",
        fake_dispatch,
    )

    result = integration.process_request(
        ["TEST-BOT"],
        path,
        "TEST-BOT",
    )

    assert result == {
        "status": "ok",
        "result": "applied",
    }

    assert calls == [data]
