from pathlib import Path

import pytest
import yaml

from app.planner import build_plan


PART2_DIR = Path(__file__).resolve().parents[1] / "sample-tests" / "part2"
FIXTURE_DIR = PART2_DIR / "fixtures"
CASE_DIR = PART2_DIR / "cases"

CASE_FILES = sorted(CASE_DIR.glob("*.yaml"))


def load_yaml(path):
    with path.open() as f:
        return yaml.safe_load(f)


@pytest.mark.parametrize(
    "case_file",
    CASE_FILES,
    ids=lambda path: path.stem,
)
def test_part2_case(case_file):
    case = load_yaml(case_file)
    fixture = load_yaml(FIXTURE_DIR / case["fixture"])

    result = build_plan(
        fixture["desired"],
        fixture["current"],
    )

    assert result == case["expected"]
