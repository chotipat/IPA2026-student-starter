import pytest

from app.backends.planning import plan_interface


DESIRED = {
    "name": "Loopback123",
    "ipv4": "172.23.123.1/32",
    "description": "IPA2026-66070123",
    "admin_state": "up",
}


@pytest.mark.parametrize(
    ("status_result", "expected_operation"),
    [
        (
            {
                "status": "ok",
                "result": "not_found",
                "interface": None,
            },
            "create",
        ),
        (
            {
                "status": "ok",
                "result": "found",
                "interface": {
                    "name": "Loopback123",
                    "ipv4": "172.23.123.9/32",
                    "description": "OLD",
                    "admin_state": "down",
                },
            },
            "update",
        ),
        (
            {
                "status": "ok",
                "result": "found",
                "interface": DESIRED.copy(),
            },
            "no_change",
        ),
    ],
)
def test_plan_operations(
    status_result,
    expected_operation,
):
    def fake_get_interface_state(
        router,
        interface_name,
    ):
        assert router == "10.0.29.101"
        assert interface_name == "Loopback123"
        return status_result

    result = plan_interface(
        "10.0.29.101",
        DESIRED,
        fake_get_interface_state,
    )

    assert result["status"] == "ok"
    assert result["result"] == "planned"
    assert result["operation"] == expected_operation


def test_plan_propagates_backend_error():
    def fake_get_interface_state(
        router,
        interface_name,
    ):
        return {
            "status": "error",
            "result": "connection_failed",
        }

    result = plan_interface(
        "10.0.29.101",
        DESIRED,
        fake_get_interface_state,
    )

    assert result == {
        "status": "error",
        "result": "connection_failed",
    }
