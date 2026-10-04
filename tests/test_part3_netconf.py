from pathlib import Path
import xml.etree.ElementTree as ET

import pytest
import yaml

from app.backends.netconf import (
    apply_interface,
    get_interface_state,
)


PART3_DIR = (
    Path(__file__).resolve().parents[1]
    / "sample-tests"
    / "part3"
    / "netconf"
)

FIXTURE_DIR = PART3_DIR / "fixtures"
CASE_DIR = PART3_DIR / "cases"

CASE_FILES = sorted(CASE_DIR.glob("*.yaml"))

NETCONF_NS = "urn:ietf:params:xml:ns:netconf:base:1.0"
NATIVE_NS = "http://cisco.com/ns/yang/Cisco-IOS-XE-native"


def load_yaml(path):
    with path.open() as f:
        return yaml.safe_load(f)


def make_fake_get_config(fixture, calls):
    netconf = fixture["netconf"]

    def fake_get_config(router, filter_xml):
        calls.append({
            "router": router,
            "filter_xml": filter_xml,
        })

        if netconf.get("exception") == "connection_error":
            raise ConnectionError()

        return netconf["xml"]

    return fake_get_config


def make_fake_edit_config(fixture, calls):
    netconf = fixture["netconf"]

    def fake_edit_config(router, config_xml):
        calls.append({
            "router": router,
            "config_xml": config_xml,
        })

        exception = netconf.get("exception")

        if exception == "authentication_error":
            raise PermissionError()

        if exception == "connection_error":
            raise ConnectionError()

        if exception == "backend_error":
            raise RuntimeError()

    return fake_edit_config


def assert_native_apply_xml(config_xml, desired):
    root = ET.fromstring(config_xml)

    ns = {
        "native": NATIVE_NS,
    }

    loopback = root.find(
        ".//native:Loopback",
        ns,
    )

    assert loopback is not None

    operation = loopback.get(
        f"{{{NETCONF_NS}}}operation"
    )
    assert operation == "replace"

    number = desired["name"][len("Loopback"):]

    name = loopback.find(
        f"{{{NATIVE_NS}}}name"
    )
    description = loopback.find(
        f"{{{NATIVE_NS}}}description"
    )

    assert name is not None
    assert name.text == number

    assert description is not None
    assert description.text == desired["description"]

    primary = loopback.find(
        f"{{{NATIVE_NS}}}ip/"
        f"{{{NATIVE_NS}}}address/"
        f"{{{NATIVE_NS}}}primary"
    )

    assert primary is not None

    address = primary.find(
        f"{{{NATIVE_NS}}}address"
    )
    mask = primary.find(
        f"{{{NATIVE_NS}}}mask"
    )

    expected_ip, prefix = desired["ipv4"].split("/")

    assert address is not None
    assert address.text == expected_ip

    assert mask is not None

    if prefix == "32":
        assert mask.text == "255.255.255.255"

    shutdown = loopback.find(
        f"{{{NATIVE_NS}}}shutdown"
    )

    if desired["admin_state"] == "down":
        assert shutdown is not None
    else:
        assert shutdown is None


@pytest.mark.parametrize(
    "case_file",
    CASE_FILES,
    ids=lambda path: path.stem,
)
def test_netconf_case(case_file):
    case = load_yaml(case_file)
    fixture = load_yaml(
        FIXTURE_DIR / case["fixture"]
    )

    if case["target"] == "status":
        calls = []

        result = get_interface_state(
            fixture["router"],
            fixture["interface_name"],
            make_fake_get_config(
                fixture,
                calls,
            ),
        )

        assert len(calls) == 1
        assert calls[0]["router"] == fixture["router"]

        assert (
            fixture["interface_name"]
            in calls[0]["filter_xml"]
        )

    elif case["target"] == "apply":
        calls = []

        result = apply_interface(
            fixture["router"],
            fixture["desired"],
            make_fake_edit_config(
                fixture,
                calls,
            ),
        )

        assert len(calls) == 1
        assert calls[0]["router"] == fixture["router"]

        assert_native_apply_xml(
            calls[0]["config_xml"],
            fixture["desired"],
        )

    else:
        pytest.fail(
            f'Unknown target: {case["target"]}'
        )

    assert result == case["expected"]
