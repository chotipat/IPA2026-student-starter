import pytest
from app.request_handler import validate_webex_envelope


@pytest.mark.parametrize("mentions", [
    [], ["OTHER-BOT"], None, "BOT",
])
def test_missing_or_wrong_bot_mention(mentions):
    assert validate_webex_envelope(mentions, "request.yaml", "BOT") == {
        "status": "error", "result": "missing_bot_mention",
    }


def test_own_bot_mention_accepted():
    assert validate_webex_envelope(
        ["OTHER-BOT", "BOT"], "request.yaml", "BOT"
    ) is None


def test_own_bot_mention_without_attachment():
    assert validate_webex_envelope(["BOT"], None, "BOT") == {
        "status": "error", "result": "no_yaml",
    }
