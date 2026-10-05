# IPA2026 YAML Specification v1

Each Webex request consists of:

- Message: select an actual mention of the target bot in the Webex group room.
  Example displayed mention: `@66070123`. No slash command is required.
- Set Bot name to the student's 8-digit student ID.
  Bot username must be unique, for example `ipa2026-66070123`.
  Find/add the bot using `ipa2026-66070123@webex.bot`.
- Validate mentions using person IDs, not the displayed name or plain text.

Part 1 receives simulated mention metadata and does not call Webex APIs:

```python
validate_webex_envelope(mentioned_people, attachment_path, bot_person_id)
handle_webex_request(mentioned_people, attachment_path, bot_person_id)
```

`mentioned_people` is the list from Webex's `mentionedPeople` field.
`bot_person_id` is the target bot's person ID, obtained from its own identity.
These IDs are not student IDs or the Bot ID shown in the Developer Portal.

Validation order:

1. `bot_person_id` must be a non-empty string, and `mentioned_people`
   must be a list containing it. Otherwise return
   `{"status": "error", "result": "missing_bot_mention"}`.
2. If the mention is valid but `attachment_path` is `None`, return
   `{"status": "error", "result": "no_yaml"}`.
3. `validate_webex_envelope()` returns `None` when both checks pass.
   `handle_webex_request()` then calls YAML core validation.
   It must not dispatch to a router.

Part 4 supplies the real mention metadata and downloaded attachment to
the same functions.
- One YAML attachment

Each YAML file is a complete, stateless request. The program must not depend
on a previous request.

## Request

Example `apply` request:

    version: 1

    router: 10.0.29.101
    method: restconf
    action: apply

    desired:
      interface:
        name: Loopback123
        ipv4: 172.23.123.1/32
        description: IPA2026-66070123
        admin_state: up

Example `delete` request:

    version: 1

    router: 10.0.29.101
    method: netmiko-textfsm
    action: delete

    desired:
      interface:
        name: Loopback123

## Allowed routers

- 10.0.29.101
- 10.0.29.102
- 10.0.29.103
- 10.0.29.104
- 10.0.29.105

## Methods and actions

| method | status | plan | apply | delete |
|---|---|---|---|---|
| restconf | yes | yes | yes | no |
| netconf | yes | yes | yes | no |
| ansible | no | no | yes | no |
| netmiko-textfsm | yes | no | no | yes |

## Interface fields

For `status`, only the interface identifier is required:

    desired:
      interface:
        name: Loopback123

The request still requires `version`, `router`, `method`, and `action`.
Optional `ipv4`, `description`, and `admin_state` fields are accepted for
`status` but ignored, including their values. Status reads the actual router
state by name and returns `found` with the actual interface values, or
`not_found` when the interface is absent. It does not compare these fields
with the router or use them for validation.

For `plan` and `apply`, `desired.interface` is a complete interface
definition and contains:

    name
    ipv4
    description
    admin_state

For `delete`, only the interface identifier is required:

    desired:
      interface:
        name: Loopback123

`ipv4`, `description`, and `admin_state` are not required for `delete`.

## admin_state

Allowed values:

- up
- down

`admin_state` is required for `plan` and `apply` only. It is ignored
for `status` and is not required for `delete`.

## Method/action compatibility

Valid combinations:

- restconf + status
- restconf + plan
- restconf + apply
- netconf + status
- netconf + plan
- netconf + apply
- ansible + apply
- netmiko-textfsm + status
- netmiko-textfsm + delete

If `method` is valid but the selected `action` is not supported by that
method, return:

    {
      "status": "error",
      "result": "invalid_action"
    }

Method/action compatibility is checked before validating fields that are
specific to the selected action.

## Validation for status and delete

For `action: status` and `action: delete`, the normal request envelope is still required:

    version
    router
    method
    action
    desired
    desired.interface
    desired.interface.name

The following errors therefore still apply when the corresponding value is
missing:

    missing_desired
    missing_interface
    missing_interface_name

The following complete-desired-state errors apply only to `plan` and `apply`,
not to `status` or `delete`:

    missing_ipv4
    missing_description
    missing_admin_state
    invalid_admin_state
