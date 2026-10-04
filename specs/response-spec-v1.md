# IPA2026 Response Specification v1

All responses must be valid JSON.

Every response must contain:

    status
    result

`status` must be either:

    ok
    error

## Success responses

Successful operations use:

    {
      "status": "ok",
      "result": "<success_result>"
    }

Common success results include:

- accepted
- found
- not_found
- planned
- applied
- deleted

Additional fields are included when required by the operation.

### Part 1 accepted request

    {
      "status": "ok",
      "result": "accepted"
    }

### Interface found

    {
      "status": "ok",
      "result": "found",
      "interface": {
        "name": "Loopback123",
        "ipv4": "172.23.123.1/32",
        "description": "IPA2026-66070123",
        "admin_state": "up"
      }
    }

### Interface not found

    {
      "status": "ok",
      "result": "not_found",
      "interface": null
    }

`not_found` is not an error. It may be returned by a status operation or
when deleting an interface that is already absent.

### Apply success

    {
      "status": "ok",
      "result": "applied"
    }

### Delete success

    {
      "status": "ok",
      "result": "deleted"
    }

## Error response

All errors must use:

    {
      "status": "error",
      "result": "<error_code>"
    }

## Error codes for Part 1

- missing_bot_mention
- no_yaml
- invalid_yaml
- invalid_version
- missing_router
- invalid_router
- missing_method
- invalid_method
- missing_action
- invalid_action
- missing_desired
- missing_interface
- missing_interface_name
- missing_ipv4
- missing_description
- missing_admin_state
- invalid_admin_state

For `action: delete`, `missing_ipv4`, `missing_description`,
`missing_admin_state`, and `invalid_admin_state` do not apply because delete
requires only the interface name inside `desired.interface`.

## Backend error results

Backend failures use:

- authentication_failed
- connection_failed
- backend_failed

Example:

    {
      "status": "error",
      "result": "connection_failed"
    }

## Rules

- Output must be valid JSON.
- `status` is always required.
- `result` is always required.
- `status` must be either `ok` or `error`.
- If `status` is `error`, `result` contains the error code.
- Do not depend on exact whitespace or JSON key order.
- Additional fields are allowed unless otherwise specified.
