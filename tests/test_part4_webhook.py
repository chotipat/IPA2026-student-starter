import json
from contextlib import contextmanager
from http.server import ThreadingHTTPServer
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from app.webhook_server import WebexEventHandler, make_http_handler


class FakeClient:
    def __init__(self, files=None, person_id="STUDENT"):
        self.message = {
            "roomId": "ROOM1",
            "personId": person_id,
            "text": "66070123",
            "mentionedPeople": ["BOT"],
            "files": files or [],
        }
        self.downloads = []
        self.replies = []
        self.lookups = []

    def get_message(self, message_id):
        self.lookups.append(message_id)
        return self.message

    def download_file(self, url):
        self.downloads.append(url)
        return b"version: 1\n"

    def send_message(self, room_id, text):
        self.replies.append((room_id, json.loads(text)))


def event(person_id="STUDENT"):
    return {
        "resource": "messages",
        "event": "created",
        "data": {"id": "MSG1", "personId": person_id},
    }


def test_attachment_processed_replied_and_cleaned():
    client = FakeClient(["https://files.example/request.yaml"])
    paths = []

    def processor(mentioned_people, path, bot_person_id):
        assert mentioned_people == ["BOT"]
        assert bot_person_id == "BOT"
        assert path.read_bytes() == b"version: 1\n"
        paths.append(path)
        return {"status": "ok", "result": "applied"}

    handler = WebexEventHandler(client, "BOT", processor)
    assert handler.handle_event(event()) == {
        "status": "ok", "result": "applied"
    }
    assert client.replies == [
        ("ROOM1", {"status": "ok", "result": "applied"})
    ]
    assert not paths[0].exists()


def test_own_event_skipped_before_api_call():
    client = FakeClient()
    handler = WebexEventHandler(client, "BOT")
    assert handler.handle_event(event("BOT")) is None
    assert client.lookups == []
    assert client.replies == []


def test_own_fetched_message_skipped():
    client = FakeClient(person_id="BOT")
    handler = WebexEventHandler(client, "BOT")
    assert handler.handle_event(event()) is None
    assert client.replies == []


def test_unrelated_event_skipped():
    client = FakeClient()
    handler = WebexEventHandler(client, "BOT")
    assert handler.handle_event({"resource": "rooms", "event": "created"}) is None
    assert client.lookups == []


def test_missing_attachment_uses_existing_validation():
    client = FakeClient()
    handler = WebexEventHandler(client, "BOT")
    result = handler.handle_event(event())
    assert result["status"] == "error"
    assert client.replies == [("ROOM1", result)]


def test_multiple_attachments_stop_before_download():
    client = FakeClient(["url1", "url2"])
    handler = WebexEventHandler(client, "BOT")
    result = handler.handle_event(event())
    assert result == {"status": "error", "result": "multiple_attachments"}
    assert client.downloads == []


@contextmanager
def http_server():
    submitted = []
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), make_http_handler(submitted.append)
    )
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", submitted
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_health_endpoint():
    with http_server() as (base, submitted):
        with urlopen(base + "/health", timeout=3) as response:
            assert response.status == 200
            assert json.load(response) == {
                "status": "ok", "result": "healthy"
            }
        assert submitted == []


def test_webhook_accepts_and_submits_event():
    with http_server() as (base, submitted):
        payload = event()
        request = Request(
            base + "/webhook",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=3) as response:
            assert response.status == 200
            assert json.load(response)["result"] == "accepted"
        assert submitted == [payload]


def test_webhook_rejects_invalid_json():
    with http_server() as (base, submitted):
        request = Request(base + "/webhook", data=b"not-json")
        with pytest.raises(HTTPError) as error:
            urlopen(request, timeout=3)
        assert error.value.code == 400
        assert submitted == []
