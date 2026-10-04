from pathlib import Path

import pytest
import yaml

from app.core import process_request_file
from app.request_handler import handle_webex_request


PART1_DIR = Path(__file__).resolve().parents[1] / "sample-tests" / "part1"
FIXTURE_DIR = PART1_DIR / "fixtures"
CASE_DIR = PART1_DIR / "cases"

CASE_FILES = sorted(CASE_DIR.glob("*.yaml"))


def load_case(path):
    with path.open() as f:
        return yaml.safe_load(f)


@pytest.mark.parametrize(
    "case_file",
    CASE_FILES,
    ids=lambda path: path.stem,
)
def test_part1_case(case_file):
    case = load_case(case_file)

    target = case["target"]
    expected = case["expected"]

    if target == "core":
        request_file = FIXTURE_DIR / case["request"]
        result = process_request_file(request_file)

    elif target == "handler":
        attachment = case.get("attachment")

        if attachment is None:
            attachment_path = None
        else:
            attachment_path = FIXTURE_DIR / attachment

        result = handle_webex_request(
            case["mentioned_people"],
            attachment_path,
            case["bot_person_id"],
        )

    else:
        pytest.fail(f"Unknown target: {target}")

    assert result == expected
