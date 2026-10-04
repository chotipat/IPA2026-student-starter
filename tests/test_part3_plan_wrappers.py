from app.backends import restconf, netconf


DESIRED = {
    "name": "Loopback123",
    "ipv4": "172.23.123.1/32",
    "description": "IPA2026-66070123",
    "admin_state": "up",
}


class FakeHTTPResponse:
    status_code = 404


def test_restconf_plan_wrapper():
    calls = []

    def fake_http_get(url):
        calls.append(url)
        return FakeHTTPResponse()

    result = restconf.plan_interface(
        "10.0.29.101",
        DESIRED,
        fake_http_get,
    )

    assert result["status"] == "ok"
    assert result["result"] == "planned"
    assert result["operation"] == "create"
    assert len(calls) == 1


def test_netconf_plan_wrapper():
    calls = []

    def fake_netconf_get_config(
        router,
        filter_xml,
    ):
        calls.append(
            (router, filter_xml)
        )

        return """<data
          xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
        </data>"""

    result = netconf.plan_interface(
        "10.0.29.101",
        DESIRED,
        fake_netconf_get_config,
    )

    assert result["status"] == "ok"
    assert result["result"] == "planned"
    assert result["operation"] == "create"
    assert len(calls) == 1
