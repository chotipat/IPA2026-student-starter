# Part 4 Live Test

## Preparation
Start Docker services, check /health through the external HTTPS URL,
and confirm the Webex webhook is active for the correct room and bot.
Use a permitted router and a dedicated test interface. Do not use
`192.0.2.128/27` for your own manual Loopback addresses; this range is
reserved for official Live requests. Before official Live, the grader
deletes `Loopback<student-id>` on `10.0.29.101` if it exists, regardless
of its description, then cleans up the same interface after testing.
Starting `grade` authorizes this reset. Other interfaces are not deleted.
Each YAML request must be attached in the same message as a real bot mention.

## Test sequence
1. Mention without an attachment: expect error/no_yaml.
2. Send malformed YAML: expect error/invalid_yaml.
3. Send the name-only status fixture: expect found or not_found.
4. If the interface is absent, send plan: expect planned/create.
5. Send apply: expect ok/applied.
6. Send status again: expect found with ipv4, description and admin_state
   read from the router and matching the applied values. Extra values in a
   status request are ignored, even when they disagree with the router.
7. Send plan again: expect planned/no_change and changes={}.
8. Send a Netmiko delete request: expect deleted.
9. Send status again: expect not_found and interface=null.
10. Send delete again: expect not_found.

Do not delete an existing interface belonging to another user.
The delete fixture intentionally contains only desired.interface.name.
Validate additional backends against the Part 3 capability matrix as needed.

## Deployment recovery
For the reference Quick Tunnel setup, restart the tunnel service.
Confirm its log reports the new target URL and an active Webex webhook.
Mention the bot without an attachment: expect error/no_yaml again.

## Self-check and official grading
The sequence above is a self-check before official grading. Students do not
submit screenshots, `docker compose ps`, JSON reply logs, or other manual live
evidence. Use a real mention of the IPA2026-Reference bot in IPA2026:
`register https://github.com/owner/repository`, then the free `verify` command,
then `grade` when ready. `score` is free. Keep the student bot running; official
Live requests and replies are visible in the room. The instructor runner sends
20 sequential cases to the registered bot, reads router state independently,
and cleans up only its student-owned Loopback. Never include credentials in the
repository or Webex attachments.
