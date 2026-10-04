from ipaddress import IPv4Interface
from pathlib import Path

import pytest
import yaml

from app.backends.restconf import (
    apply_interface,
    get_interface_state,
)


PART3_DIR = (
    Path(__file__).resolve().parents[1]
    / "sample-tests"
    / "part3"
    / "restconf"
)

FIXTURE_DIR = PART3_DIR / "fixtures"
CASE_DIR = PART3_DIR / "cases"

CASE_FILES = sorted(CASE_DIR.glob("*.yaml"))


class FakeResponse:
    def __init__(self, status_code, json_data=None):
        self.status_code = status_code
        self._json_data = json_data

    def json(self):
        return self._json_data


def load_yaml(path):
    with path.open() as f:
        return yaml.safe_load(f)


def make_fake_get(fixture):
    http = fixture["http"]

    def fake_get(url):
        if http.get("exception") == "connection_error":
            raise ConnectionError()

        return FakeResponse(
            status_code=http["status_code"],
            json_data=http.get("json"),
        )

    return fake_get


def make_fake_put(fixture, calls):
    http = fixture["http"]

    def fake_put(url, json):
        calls.append({
            "url": url,
            "json": json,
        })

        if http.get("exception") == "connection_error":
            raise ConnectionError()

        return FakeResponse(
            status_code=http["status_code"],
        )

    return fake_put


@pytest.mark.parametrize(
    "case_file",
    CASE_FILES,
    ids=lambda path: path.stem,
)
def test_restconf_case(case_file):
    case = load_yaml(case_file)
    fixture = load_yaml(FIXTURE_DIR / case["fixture"])

    if case["target"] == "status":
        result = get_interface_state(
            fixture["router"],
            fixture["interface_name"],
            make_fake_get(fixture),
        )

    elif case["target"] == "apply":
        calls = []

        result = apply_interface(
            fixture["router"],
            fixture["desired"],
            make_fake_put(fixture, calls),
        )

        assert len(calls) == 1

        call = calls[0]
        desired = fixture["desired"]

        number = int(
            desired["name"][len("Loopback"):]
        )

        expected_url = (
            f"https://{fixture['router']}/restconf/data/"
            f"Cisco-IOS-XE-native:native/interface/Loopback={number}"
        )

        assert call["url"] == expected_url

        payload = call["json"]["Cisco-IOS-XE-native:Loopback"]

        assert payload["name"] == number
        assert payload["description"] == desired["description"]

        ipv4 = IPv4Interface(desired["ipv4"])

        primary = payload["ip"]["address"]["primary"]

        assert primary["address"] == str(ipv4.ip)
        assert primary["mask"] == str(ipv4.network.netmask)

        if desired["admin_state"] == "down":
            assert payload["shutdown"] == [None]
        else:
            assert "shutdown" not in payload

    else:
        pytest.fail(
            f'Unknown target: {case["target"]}'
        )

    assert result == case["expected"]
