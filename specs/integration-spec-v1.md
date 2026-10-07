# IPA2026 Part 4: Integration, Webex and Docker

## Goal
Connect Parts 1–3 to the student's own Webex bot and deploy with Docker.
Use the existing YAML schema, response contract and capability matrix.

## Webex input
- Add the student's bot to both IPA2026 (manual testing) and IPA2026 Exam Room (official grading).
- Set the bot display name to the student's 8-digit student ID.
- Choose a unique bot username; use its bot email to add it to the room.
- Select a real @mention of the bot and attach one YAML file in the same message.
- Validate mention metadata using mentionedPeople and the bot's personId.
- Do not require a slash command or identify mentions from plain text.
- Resolve the bot's personId using GET /v1/people/me with its Bot Access Token.

## Required Python APIs
- app.dispatcher.dispatch_request(data)
- app.integration.process_request(mentioned_people, attachment_path, bot_person_id)
- app.webex_client.WebexClient(token=None, session=None)
  - headers property
  - get_message(message_id)
  - download_file(file_url)
  - send_message(room_id, text)
- app.webhook_server.WebexEventHandler(client, bot_person_id, processor=None)
  - handle_event(event)
- app.webhook_server.make_http_handler(submit_event)
- app.webhook_server.main()

## Integration and dispatch
process_request must validate the mention/attachment envelope, load YAML once,
validate the parsed request, and dispatch only accepted requests.
Reuse the student's Part 1 validation and Part 3 backends.
Return the backend response without changing its contract.

dispatch_request accepts an already validated request.
For status/delete pass router and interface name to the backend.
For plan/apply pass router and the desired interface dictionary.
Support all 9 valid method/action combinations in the capability matrix.

## Webex client
Use https://webexapis.com/v1 and Bearer authentication.
Read WEBEX_BOT_TOKEN from environment when no token is supplied.
Raise PermissionError when a token is unavailable.
get_message returns decoded JSON.
download_file returns bytes.
send_message posts roomId and text, and returns decoded JSON.
Check HTTP errors and use a 10-second request timeout.

## Event handling
Handle only messages/created events with a message ID.
Ignore unrelated or malformed events.
Ignore messages from the bot itself, before lookup when possible,
and also check the author of the fetched message to prevent reply loops.

Fetch the message using its ID and use its roomId for the response.
- No attachment: call the processor with attachment_path=None.
- One attachment: download it, write a temporary YAML file, process it,
  then remove the temporary file even if processing fails.
- Multiple attachments: return status=error, result=multiple_attachments
  without downloading files or invoking the processor.

Send the response dictionary as JSON text to the same room.
Return that dictionary from handle_event.
Return None for ignored events without sending a reply.

## HTTP endpoints
GET /health:
- HTTP 200
- {"status":"ok","result":"healthy"}

POST /webhook:
- Accept a JSON object and submit it for background processing.
- HTTP 200 with {"status":"ok","result":"accepted"} acknowledges receipt.
- Send the final validation/backend result separately to the Webex room.
- Invalid JSON, a non-object body, or invalid body length:
  HTTP 400 with {"status":"error","result":"invalid_event"}.
- Accept body lengths from 1 to 1,000,000 bytes.

Unknown paths return HTTP 404.
HTTP acknowledgement must not wait for router operations.
Process router requests sequentially to avoid overlapping changes.

## Deployment
Submit a Dockerfile and compose.yaml that start the webhook service.
Bind the server to 0.0.0.0 inside the container.
Use WEBHOOK_HOST and WEBHOOK_PORT; the default port is 8000.
Provide a health check and a restart policy.
Include runtime Ansible files in the image.

The provided Dockerfile starts the webhook with `CMD ["python", "-m", "app.webhook_server"]`. Keep the Compose service named `webhook` and do not override its command or entrypoint. After building, Student CI runs `scripts/check_webhook_image.py` against the built image. It imports the application and backends, then checks `/health` and `/webhook` with a local fake event. This offline smoke does not use Webex credentials or contact a router. The instructor runs its own copy of the same contract; a smoke failure blocks Live testing.

Supply credentials through environment, not image contents or source code:
WEBEX_BOT_TOKEN, ROUTER_USER, ROUTER_PASS.

Expose the webhook through a reachable HTTPS URL, for example Cloudflare Tunnel.
Register a messages/created Webex webhook using the student's Bot Access Token,
both IPA2026 (manual testing) and IPA2026 Exam Room (official verify/grade) roomId filters, each with targetUrl ending in /webhook. Register a webhook for each room or use a subscription that delivers mentions from both rooms. Update existing registrations when the external URL changes. Reply to the roomId of each incoming request; do not hard-code one reply room.
A Cloudflare account or purchased domain is not required for the live test.

The instructor reference runs webhook and tunnel as two Compose services.
Its tunnel automatically updates the Webex registration on startup.
Students may use a different deployment arrangement with the same behavior
required for request processing and a documented way to update registration.

## Validation
The starter has 88 public tests: 64 for Parts 1–3 and 24 for Part 4.
Mock tests do not require bot credentials or live routers.
Live testing uses the student's own bot in IPA2026 Exam Room and router access to 10.0.29.101. Manual testing uses IPA2026 and an assigned router in 10.0.29.102–10.0.29.105.
See live-test-part4.md for the end-to-end procedure.
