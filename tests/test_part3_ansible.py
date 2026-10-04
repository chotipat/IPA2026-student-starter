from pathlib import Path

import pytest
import yaml

from app.backends.ansible import apply_interface


PART3_DIR = (
    Path(__file__).resolve().parents[1]
    / "sample-tests"
    / "part3"
    / "ansible"
)

FIXTURE_DIR = PART3_DIR / "fixtures"
CASE_DIR = PART3_DIR / "cases"

CASE_FILES = sorted(CASE_DIR.glob("*.yaml"))


def load_yaml(path):
    with path.open() as f:
        return yaml.safe_load(f)


def make_fake_runner(fixture, calls):
    ansible = fixture["ansible"]

    def fake_run_playbook(variables):
        calls.append(variables)

        exception = ansible.get("exception")

        if exception == "authentication_error":
            raise PermissionError()

        if exception == "connection_error":
            raise ConnectionError()

        if exception == "backend_error":
            raise RuntimeError()

    return fake_run_playbook


@pytest.mark.parametrize(
    "case_file",
    CASE_FILES,
    ids=lambda path: path.stem,
)
def test_ansible_case(case_file):
    case = load_yaml(case_file)
    fixture = load_yaml(
        FIXTURE_DIR / case["fixture"]
    )

    calls = []

    result = apply_interface(
        fixture["router"],
        fixture["desired"],
        make_fake_runner(
            fixture,
            calls,
        ),
    )

    assert len(calls) == 1

    variables = calls[0]
    desired = fixture["desired"]

    assert variables["router"] == fixture["router"]
    assert variables["interface_name"] == desired["name"]
    assert variables["description"] == desired["description"]

    expected_ip, prefix = desired["ipv4"].split("/")

    assert variables["ipv4_address"] == expected_ip

    if prefix == "32":
        assert variables["netmask"] == "255.255.255.255"

    assert variables["shutdown"] == (
        desired["admin_state"] == "down"
    )

    assert result == case["expected"]
