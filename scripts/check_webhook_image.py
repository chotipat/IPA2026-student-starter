"""Check the built webhook image without Webex or router credentials."""

import json
import subprocess


CONTAINER_SMOKE = r'''
import importlib
import json
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from threading import Thread

for name in (
    "app.webhook_server",
    "app.integration",
    "app.dispatcher",
    "app.backends.restconf",
    "app.backends.netconf",
    "app.backends.ansible",
    "app.backends.netmiko_textfsm",
):
    importlib.import_module(name)

from app.webhook_server import make_http_handler

received = []
server = ThreadingHTTPServer(("127.0.0.1", 0), make_http_handler(received.append))
thread = Thread(target=server.serve_forever, daemon=True)
thread.start()

def request(method, path, body=None):
    connection = HTTPConnection("127.0.0.1", server.server_port, timeout=3)
    try:
        headers = {"Content-Type": "application/json"} if body is not None else {}
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        return response.status, json.loads(response.read())
    finally:
        connection.close()

try:
    status, result = request("GET", "/health")
    if (status, result) != (200, {"status": "ok", "result": "healthy"}):
        raise RuntimeError(f"/health returned {status}: {result}")

    event = {"resource": "messages", "event": "created", "data": {"id": "smoke"}}
    status, result = request("POST", "/webhook", json.dumps(event).encode())
    if (status, result) != (200, {"status": "ok", "result": "accepted"}):
        raise RuntimeError(f"/webhook returned {status}: {result}")
    if received != [event]:
        raise RuntimeError("/webhook did not submit the event")

    status, result = request("POST", "/webhook", b"{")
    if (status, result) != (400, {"status": "error", "result": "invalid_event"}):
        raise RuntimeError(f"invalid /webhook input returned {status}: {result}")
    if received != [event]:
        raise RuntimeError("invalid /webhook input was submitted")
finally:
    server.shutdown()
    server.server_close()
    thread.join(timeout=3)

print("PASS: image imports and HTTP /health + /webhook")
'''


def output(*args):
    return subprocess.check_output(args, text=True).strip()


def main():
    config = json.loads(output("docker", "compose", "config", "--format", "json"))
    service = config.get("services", {}).get("webhook")
    if not isinstance(service, dict) or not service.get("build"):
        raise RuntimeError("compose.yaml must build a webhook service")
    if service.get("command") is not None or service.get("entrypoint") is not None:
        raise RuntimeError("webhook must use the image's Python module command")

    image = service.get("image") or f"{config['name']}-webhook"
    inspection = json.loads(output("docker", "image", "inspect", image))[0]
    image_config = inspection["Config"]
    if image_config.get("Entrypoint") not in (None, []):
        raise RuntimeError("webhook image must not replace its entrypoint")
    if image_config.get("Cmd") != ["python", "-m", "app.webhook_server"]:
        raise RuntimeError("webhook image must start python -m app.webhook_server")

    subprocess.run(
        ["docker", "compose", "run", "--rm", "-T", "--no-deps",
         "--entrypoint", "python", "webhook", "-"],
        input=CONTAINER_SMOKE,
        text=True,
        check=True,
        timeout=25,
    )


if __name__ == "__main__":
    main()
