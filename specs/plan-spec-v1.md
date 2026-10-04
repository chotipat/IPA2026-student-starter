# IPA2026 Plan Specification v1

## Purpose

Part 2 compares a desired interface state with a normalized current
interface state and produces a deterministic plan.

Part 2 must not connect to a real router.


## Delete Scope

Delete is not a Part 2 planning operation.

`build_plan()` continues to produce only:

- create
- update
- no_change

The `delete` action is handled separately in Part 3 by the
`netmiko-textfsm` backend. A delete request is not passed to
`build_plan()` and does not add a `delete` planning operation.

## Function Contract

Implement:

    build_plan(desired_interface, current_interface)

`desired_interface` is a validated complete interface dictionary from Part 1.
Delete requests are not passed to `build_plan()`.

`current_interface` is either:

- a normalized interface dictionary; or
- `None` if the interface does not currently exist.

## Resource Identifier

The `name` field identifies the interface.

Example:

    name: Loopback123

`name` is not a managed field and must not appear in `changes`.

## Managed Fields

The planner manages exactly these fields:

- ipv4
- description
- admin_state

Example desired interface:

    {
      "name": "Loopback123",
      "ipv4": "172.23.123.1/32",
      "description": "IPA2026-66070123",
      "admin_state": "up"
    }

## Operations

The planner must return exactly one of:

- create
- update
- no_change

## create

Use `create` when:

    current_interface is None

Return all managed fields in `changes`, using only the desired `to` value.

Example:

    {
      "status": "ok",
      "result": "planned",
      "operation": "create",
      "changes": {
        "ipv4": {
          "to": "172.23.123.1/32"
        },
        "description": {
          "to": "IPA2026-66070123"
        },
        "admin_state": {
          "to": "up"
        }
      }
    }

## update

Use `update` when the interface exists and at least one managed field
differs from the desired state.

Return only fields whose values differ.

Example current interface:

    {
      "name": "Loopback123",
      "ipv4": "172.23.123.1/32",
      "description": "OLD-DESCRIPTION",
      "admin_state": "up"
    }

Expected result:

    {
      "status": "ok",
      "result": "planned",
      "operation": "update",
      "changes": {
        "description": {
          "from": "OLD-DESCRIPTION",
          "to": "IPA2026-66070123"
        }
      }
    }

## no_change

Use `no_change` when all managed fields already match the desired state.

Expected result:

    {
      "status": "ok",
      "result": "planned",
      "operation": "no_change",
      "changes": {}
    }

## Current-State Assumption

Part 2 receives normalized current state.

Part 2 is not responsible for:

- RESTCONF parsing
- NETCONF parsing
- Ansible output parsing
- Netmiko/TextFSM parsing
- interface deletion
- router authentication
- router connectivity

Those responsibilities belong to later Parts.

## Determinism

For the same desired state and current state, the planner must always
produce the same result.

## Idempotency

If current state already matches desired state, the planner must return:

    operation: no_change
    changes: {}

This behavior is required for idempotent automation.

## Student-created Tests

Students must add at least 3 meaningful Part 2 test cases.

Add new YAML files under:

    sample-tests/part2/fixtures/
    sample-tests/part2/cases/

Do not modify `tests/test_part2.py` only to add test cases.

Student-created cases should use values different from the published
samples and may include, for example:

- update only `ipv4`
- update only `admin_state`
- update multiple managed fields

## Checkpoint

Part 2 is complete when:

- all published Part 2 sample tests pass;
- `build_plan()` works with values different from the samples;
- `create` contains only `to` values in `changes`;
- `update` contains only changed fields with `from` and `to`;
- `no_change` returns an empty `changes` dictionary;
- Part 2 does not connect to a router;
- Part 2 does not parse raw backend output;
- Part 2 does not delete interfaces.

Instructor CI may use interface names, IP addresses, descriptions,
and admin states different from the published samples while remaining
within this specification.
