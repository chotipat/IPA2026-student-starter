import pytest

from app import dispatcher
from app.backends import (
    ansible,
    netconf,
    netmiko_textfsm,
    restconf,
)


BASE = {
    "version": 1,
    "router": "10.0.29.101",
    "desired": {
        "interface": {
            "name": "Loopback123",
            "ipv4": "172.23.123.1/32",
            "description": "IPA2026-66070123",
            "admin_state": "up",
        }
    },
}


@pytest.mark.parametrize(
    ("method", "action", "module", "function_name"),
    [
        ("restconf", "status", restconf, "get_interface_state"),
        ("restconf", "plan", restconf, "plan_interface"),
        ("restconf", "apply", restconf, "apply_interface"),
        ("netconf", "status", netconf, "get_interface_state"),
        ("netconf", "plan", netconf, "plan_interface"),
        ("netconf", "apply", netconf, "apply_interface"),
        ("ansible", "apply", ansible, "apply_interface"),
        (
            "netmiko-textfsm",
            "status",
            netmiko_textfsm,
            "get_interface_state",
        ),
        (
            "netmiko-textfsm",
            "delete",
            netmiko_textfsm,
            "delete_interface",
        ),
    ],
)
def test_dispatch_routes_to_correct_backend(
    monkeypatch,
    method,
    action,
    module,
    function_name,
):
    calls = []

    def fake_backend(*args):
        calls.append(args)
        return {
            "status": "ok",
            "result": "FAKE",
        }

    monkeypatch.setattr(
        module,
        function_name,
        fake_backend,
    )

    request = {
        **BASE,
        "method": method,
        "action": action,
    }

    result = dispatcher.dispatch_request(request)

    assert result == {
        "status": "ok",
        "result": "FAKE",
    }

    assert len(calls) == 1

    router = BASE["router"]
    interface = BASE["desired"]["interface"]

    if action in ("status", "delete"):
        assert calls[0] == (
            router,
            interface["name"],
        )
    else:
        assert calls[0] == (
            router,
            interface,
        )
