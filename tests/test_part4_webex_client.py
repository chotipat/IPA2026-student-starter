from app.webex_client import (
    WEBEX_API_BASE,
    WebexClient,
)


class FakeResponse:
    def __init__(
        self,
        json_data=None,
        content=b"",
    ):
        self._json_data = json_data
        self.content = content

    def raise_for_status(self):
        pass

    def json(self):
        return self._json_data


class FakeSession:
    def __init__(self):
        self.calls = []

    def get(
        self,
        url,
        headers,
        timeout,
    ):
        self.calls.append(
            ("GET", url, headers, timeout)
        )

        if "/messages/" in url:
            return FakeResponse(
                {
                    "id": "MSG1",
                    "roomId": "ROOM1",
                    "text": "/66070123",
                    "files": [
                        "https://files.example/request.yaml"
                    ],
                }
            )

        return FakeResponse(
            content=b"version: 1\n"
        )

    def post(
        self,
        url,
        headers,
        json,
        timeout,
    ):
        self.calls.append(
            (
                "POST",
                url,
                headers,
                json,
                timeout,
            )
        )

        return FakeResponse(
            {"id": "REPLY1"}
        )


def test_get_message():
    session = FakeSession()
    client = WebexClient(
        token="TEST-TOKEN",
        session=session,
    )

    message = client.get_message("MSG1")

    assert message["text"] == "/66070123"
    assert message["roomId"] == "ROOM1"

    assert session.calls[0][1] == (
        f"{WEBEX_API_BASE}/messages/MSG1"
    )


def test_download_file():
    session = FakeSession()
    client = WebexClient(
        token="TEST-TOKEN",
        session=session,
    )

    content = client.download_file(
        "https://files.example/request.yaml"
    )

    assert content == b"version: 1\n"


def test_send_message():
    session = FakeSession()
    client = WebexClient(
        token="TEST-TOKEN",
        session=session,
    )

    result = client.send_message(
        "ROOM1",
        '{"status":"ok","result":"applied"}',
    )

    assert result == {
        "id": "REPLY1"
    }

    method, url, _, payload, _ = (
        session.calls[0]
    )

    assert method == "POST"
    assert url == f"{WEBEX_API_BASE}/messages"

    assert payload == {
        "roomId": "ROOM1",
        "text": '{"status":"ok","result":"applied"}',
    }
