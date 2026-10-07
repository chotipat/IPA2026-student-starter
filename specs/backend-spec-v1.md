# IPA2026 Backend Specification v1

## Purpose

Part 3 implements backend adapters for reading, applying, and deleting
interface state using the required network automation technologies.

Part 3 does not implement Webex integration.

## Capability Matrix

| Method | status | plan | apply | delete |
|---|---|---|---|---|
| restconf | yes | yes | yes | no |
| netconf | yes | yes | yes | no |
| ansible | no | no | yes | no |
| netmiko-textfsm | yes | no | no | yes |

## Normalized Interface State

Backends that support status must normalize backend-specific data into
the common interface structure:

    {
      "name": "Loopback123",
      "ipv4": "172.23.123.1/32",
      "description": "IPA2026-66070123",
      "admin_state": "up"
    }

The normalized interface is carried inside the common backend response:

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

If the requested interface does not exist, the backend returns:

    {
      "status": "ok",
      "result": "not_found",
      "interface": null
    }

Part 2 does not receive the complete backend response.

The application extracts:

    response["interface"]

for `found`, or uses:

    None

for `not_found`, before calling `build_plan()`.

## Backend Function Contract

Each backend exposes only the operations appropriate for that technology.

The two required arguments below are used by the dispatcher and Live
requests. The starter stubs also expose an optional injected callable for each
operation. Those optional parameters **are part of the public test contract**:
public tests pass fake transport/runner functions so no router is contacted.

| Backend operation | Optional parameter | Callable receives |
|---|---|---|
| RESTCONF status/plan | `http_get` | `http_get(url)`; returns a response with `status_code` and `json()` |
| RESTCONF apply | `http_put` | `http_put(url, json=payload)`; returns a response with `status_code` |
| NETCONF status/plan | `netconf_get_config` | `netconf_get_config(router, filter_xml)`; returns XML text |
| NETCONF apply | `netconf_edit_config` | `netconf_edit_config(router, config_xml)` |
| Ansible apply | `run_playbook` | `run_playbook(variables)` |
| Netmiko/TextFSM status | `netmiko_get` | `netmiko_get(router, interface_name)`; returns `(ip_info, descriptions)` |
| Netmiko/TextFSM delete | `netmiko_delete` | `netmiko_delete(router, interface_name)`; returns `"deleted"` or `"not_found"` |

When an optional callable is omitted, use a real transport/runner. Keep the
same result and error contract for both paths. The injected fakes in the
public tests raise Python `PermissionError`, `ConnectionError`, and
`RuntimeError`; map them to `authentication_failed`,
`connection_failed`, and `backend_failed`, respectively.

Real libraries have their own exception classes, so catching only Python's
built-in `ConnectionError` is insufficient. Normalize failures from the real
transport before returning a backend response. For example, Requests
`requests.exceptions.Timeout` and `requests.exceptions.ConnectionError`
mean `connection_failed` (the latter is **not** a subclass of the built-in
`ConnectionError`); HTTP 401/403 means `authentication_failed`.
For ncclient, authentication failures map to `authentication_failed`,
SSH/session connection failures to `connection_failed`, and RPC errors
to `backend_failed`. For Netmiko, authentication and timeout exceptions map
to those first two codes, while TextFSM parsing failures map to
`backend_failed`. For Ansible, rejected credentials, unreachable hosts, and
other playbook failures map to the same three categories. Equivalent exceptions
from another implementation should follow the error meanings below.

### RESTCONF

File:

    app/backends/restconf.py

Functions:

    get_interface_state(router, interface_name)
    plan_interface(router, desired_interface)
    apply_interface(router, desired_interface)

### NETCONF

File:

    app/backends/netconf.py

Functions:

    get_interface_state(router, interface_name)
    plan_interface(router, desired_interface)
    apply_interface(router, desired_interface)

### Ansible

File:

    app/backends/ansible.py

Function:

    apply_interface(router, desired_interface)

### Netmiko + TextFSM

File:

    app/backends/netmiko_textfsm.py

Functions:

    get_interface_state(router, interface_name)
    delete_interface(router, interface_name)

`delete_interface()` uses Netmiko for the IOS configuration command and may
use the existing TextFSM-based status path to verify the result.

## Planning

RESTCONF and NETCONF expose `plan_interface()`, but backends must not
implement their own desired/current comparison logic.

The plan flow is:

    plan_interface(router, desired_interface)
        -> get_interface_state(router, desired_interface["name"])
        -> normalized current interface state
        -> build_plan(desired_interface, current_interface)
        -> create / update / no_change

If status returns `not_found`, planning passes `None` as the current
interface to `build_plan()`.

If status returns a backend error, that error is returned unchanged.

The actual comparison logic remains in Part 2:

    app/planner.py
    build_plan(desired_interface, current_interface)

This keeps RESTCONF and NETCONF planning behavior identical and avoids
duplicating comparison logic inside individual backends.

## Status Contract

Every `get_interface_state()` function returns a dictionary using the
common response contract.

### Interface Found

If the router is reachable and the requested interface exists:

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

### Interface Not Found

If the router is reachable but the requested interface does not exist:

    {
      "status": "ok",
      "result": "not_found",
      "interface": null
    }

`not_found` is not an error.

It means the backend operation succeeded, but the requested resource
does not currently exist.

For planning, the application converts:

    result: found
        -> current_interface = response["interface"]

    result: not_found
        -> current_interface = None

and then calls:

    build_plan(desired_interface, current_interface)

Part 2 therefore continues to receive only a normalized interface
dictionary or `None`.

## Backend Error Contract

When a backend operation fails, return:

    {
      "status": "error",
      "result": "<error_code>"
    }

Allowed backend error results are:

- authentication_failed
- connection_failed
- backend_failed

### authentication_failed

Authentication or authorization was rejected.

Examples include invalid credentials or an authorization failure.

### connection_failed

A usable connection to the router or backend could not be established.

Examples include connection timeout, connection refused, or an
unreachable router.

### backend_failed

Communication was established, but the requested backend operation
failed.

Examples include protocol errors, unsuccessful commands, malformed
backend responses, or other backend-specific operation failures.

## Apply Contract

`apply_interface(router, desired_interface)` must attempt to make the
target interface match the complete desired interface state.

The desired interface contains:

    {
      "name": "Loopback123",
      "ipv4": "172.23.123.1/32",
      "description": "IPA2026-66070123",
      "admin_state": "up"
    }

On successful execution, return:

    {
      "status": "ok",
      "result": "applied"
    }

On failure, return the common backend error response:

    {
      "status": "error",
      "result": "authentication_failed"
    }

or:

    {
      "status": "error",
      "result": "connection_failed"
    }

or:

    {
      "status": "error",
      "result": "backend_failed"
    }

The backend does not need to return a `changed` field.

Whether the router actually reached the desired state may be verified
separately by reading the router state.

## Delete Contract

Only `netmiko-textfsm` supports the `delete` action.

The public backend function is:

    delete_interface(router, interface_name)

The backend must remove the requested Loopback interface using Cisco IOS CLI:

    no interface <interface_name>

The intended flow is:

    delete_interface(router, interface_name)
        -> get_interface_state(router, interface_name)
        -> if not_found: return not_found
        -> if found: send "no interface <interface_name>" with Netmiko
        -> verify interface state
        -> if absent: return deleted

If the interface is successfully removed, return:

    {
      "status": "ok",
      "result": "deleted"
    }

If the interface is already absent, return:

    {
      "status": "ok",
      "result": "not_found",
      "interface": null
    }

If the delete command fails or the interface is still present after
verification, return the common backend error response.

RESTCONF, NETCONF, and Ansible do not expose `delete_interface()` in this
exam. Unsupported method/action combinations are rejected earlier as
`invalid_action`.

## Idempotent Delete

Deleting an already-absent interface is a successful no-op represented by:

    {
      "status": "ok",
      "result": "not_found",
      "interface": null
    }

Therefore repeated delete requests do not recreate resources and do not
produce duplicate state.

## Idempotent Apply

Applying the same desired state repeatedly must not produce an invalid
configuration or duplicate resources.

For example, applying the same Loopback interface twice must still leave
one interface in the requested desired state.

RESTCONF and NETCONF use resource replacement semantics for the managed
Loopback resource.

Ansible uses `cisco.ios.ios_config` with `defaults: true` so comparison can
include IOS default commands such as the effective `no shutdown` state.
For an already-correct interface, applying the same desired state again
should therefore be idempotent and may complete with Ansible reporting
`changed=0`.

The common backend response does not expose Ansible's internal `changed`
flag; successful execution still returns `result: applied`.

## Separation of Responsibilities

Part 2 compares desired and current state:

    desired + current
        -> build_plan()
        -> create / update / no_change

Part 3 communicates with the backend and exposes only the operations
supported by each technology:

    get_interface_state()
    plan_interface()
    apply_interface()
    delete_interface()

`plan_interface()` is an orchestration wrapper for RESTCONF and NETCONF.
It obtains normalized current state and delegates all comparison logic to
Part 2 `build_plan()`.

`delete_interface()` is separate from Part 2 planning and is exposed only by
the Netmiko + TextFSM backend.

Backends must not duplicate the Part 2 planning rules merely to produce
create/update/no_change output.

## Apply Verification

Instructor tests may verify backend behavior using test doubles or an
authorized live router.

Implementations must use the requested backend technology and must not
return hard-coded success responses without performing the backend
operation.

## Frozen YANG Models

IPA2026 uses different YANG models for reading interface state and applying
configuration.

    status / read
        -> ietf-interfaces
        -> ietf-ip

    apply / write
        -> Cisco-IOS-XE-native

This model selection is the same for RESTCONF and NETCONF.

The live Cisco IOS XE router has been verified with:

    ietf-interfaces
    revision: 2014-05-08

    ietf-ip
    revision: 2014-06-16

    Cisco-IOS-XE-native
    revision: 2018-07-27


## Status Model

RESTCONF and NETCONF read interface state using the vendor-neutral IETF
interface models. Netmiko + TextFSM reads IOS CLI output and normalizes it
to the same interface structure.

The normalized interface state is:

    {
      "name": "Loopback123",
      "ipv4": "172.23.123.1/32",
      "description": "IPA2026-66070123",
      "admin_state": "up"
    }


### RESTCONF Status

RESTCONF reads:

    /restconf/data/ietf-interfaces:interfaces/interface=<interface_name>

Example:

    /restconf/data/ietf-interfaces:interfaces/interface=Loopback123

Raw data has this form:

    {
      "ietf-interfaces:interface": {
        "name": "Loopback123",
        "description": "IPA2026-66070123",
        "type": "iana-if-type:softwareLoopback",
        "enabled": true,
        "ietf-ip:ipv4": {
          "address": [
            {
              "ip": "172.23.123.1",
              "netmask": "255.255.255.255"
            }
          ]
        },
        "ietf-ip:ipv6": {}
      }
    }

RESTCONF production transport uses HTTPS. The reference implementation uses
Python `requests` and the common router credentials supplied at runtime.


### NETCONF Status

NETCONF uses a subtree filter:

    <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
      <interface>
        <name>Loopback123</name>
      </interface>
    </interfaces>

The returned interface data has this form:

    <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
      <interface>
        <name>Loopback123</name>
        <description>IPA2026-66070123</description>
        <type xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">
          ianaift:softwareLoopback
        </type>
        <enabled>true</enabled>

        <ipv4 xmlns="urn:ietf:params:xml:ns:yang:ietf-ip">
          <address>
            <ip>172.23.123.1</ip>
            <netmask>255.255.255.255</netmask>
          </address>
        </ipv4>

        <ipv6 xmlns="urn:ietf:params:xml:ns:yang:ietf-ip"/>
      </interface>
    </interfaces>

NETCONF production transport uses `ncclient` over SSH port 830.


### Netmiko + TextFSM Status

Netmiko + TextFSM supports status and delete. This section describes the
status path.

The reference implementation runs two read-only IOS commands:

    show ip interface <interface_name>
    show interfaces description

`show ip interface` is parsed with the NTC TextFSM template for Cisco IOS
and supplies:

    interface
    IP address
    prefix length
    administrative link state

`show interfaces description` supplies the interface description.

Cisco IOS may abbreviate Loopback names in this command, for example:

    Loopback123 -> Lo123

The backend must normalize the abbreviated name before matching the
records.

Administrative state is normalized from `show ip interface`:

    administratively down
        -> admin_state: down

    otherwise
        -> admin_state: up

The first parsed IPv4 address and its corresponding prefix length form the
normalized `ipv4` field.


### Status Normalization

RESTCONF and NETCONF normalize the IETF model using these rules:

    name
        -> name

    description
        -> description

    enabled: true
        -> admin_state: up

    enabled: false
        -> admin_state: down

    ip + netmask
        -> ipv4 in CIDR notation

Example:

    172.23.123.1 + 255.255.255.255
        -> 172.23.123.1/32

For Netmiko + TextFSM, parsed CLI fields are normalized to the same output
shape.

The following IETF fields are ignored:

    type
    ipv6

If description is absent:

    description: null

## Apply Model

RESTCONF and NETCONF apply Loopback configuration using the Cisco native
YANG model:

    Cisco-IOS-XE-native

Ansible applies the same normalized desired state through Cisco IOS CLI
using `cisco.ios.ios_config`.

For a normalized name such as:

    Loopback123

the Cisco native Loopback key is:

    123

The desired state:

    {
      "name": "Loopback123",
      "ipv4": "172.23.123.1/32",
      "description": "IPA2026-66070123",
      "admin_state": "up"
    }

maps to the Cisco native model as follows:

    name
        -> Loopback name 123

    description
        -> description

    ipv4
        -> ip/address/primary/address
        -> ip/address/primary/mask

    admin_state: down
        -> shutdown present

    admin_state: up
        -> shutdown absent


### RESTCONF Apply

RESTCONF writes the native Loopback resource using HTTP PUT:

    /restconf/data/Cisco-IOS-XE-native:native/interface/Loopback=123

For admin_state `up`, the payload has this form:

    {
      "Cisco-IOS-XE-native:Loopback": {
        "name": 123,
        "description": "IPA2026-66070123",
        "ip": {
          "address": {
            "primary": {
              "address": "172.23.123.1",
              "mask": "255.255.255.255"
            }
          }
        }
      }
    }

For admin_state `down`, include:

    "shutdown": [null]

HTTP PUT is used so the managed Loopback resource is replaced by the
complete desired state.

Successful HTTP responses include:

    200
    201
    204


### NETCONF Apply

NETCONF writes the same Cisco native Loopback model using:

    edit-config
    target: running

The Loopback list entry is replaced as a complete managed resource.

For admin_state `up`:

    <config
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">

      <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
        <interface>

          <Loopback nc:operation="replace">
            <name>123</name>

            <description>IPA2026-66070123</description>

            <ip>
              <address>
                <primary>
                  <address>172.23.123.1</address>
                  <mask>255.255.255.255</mask>
                </primary>
              </address>
            </ip>

          </Loopback>

        </interface>
      </native>
    </config>

For admin_state `down`, the Loopback element also contains:

    <shutdown/>

For admin_state `up`, the shutdown leaf is omitted.

Replacing the complete native Loopback entry prevents stale secondary IPv4
addresses from remaining after an IPv4 change.


### Ansible Apply

Ansible is apply-only.

The reference implementation uses:

    cisco.ios.ios_config
    ansible.netcommon.network_cli

The normalized desired state is converted to IOS interface configuration:

    interface Loopback123
     description IPA2026-66070123
     ip address 172.23.123.1 255.255.255.255
     no shutdown

For admin_state `down`, the final command is:

    shutdown

The `ios_config` task uses:

    defaults: true

This allows comparison against IOS default configuration and prevents an
already-up interface from being reported as changed on every repeated
apply merely because `no shutdown` is omitted from normal running-config
output.

The reference implementation has been verified to replace the primary IPv4
address without leaving the previous primary address as a secondary
address.

## Delete Model

Delete is intentionally implemented only with Netmiko + TextFSM.

The delete path uses Netmiko to enter IOS configuration mode and issue:

    no interface Loopback123

TextFSM is not needed to parse the delete command itself. The existing
Netmiko + TextFSM status path may be used before and after the command to
determine whether the interface exists and to verify that deletion succeeded.

This separation keeps delete behavior simple and avoids requiring
backend-specific delete semantics from RESTCONF, NETCONF, or Ansible.

## Delete Result

Successful removal returns:

    {
      "status": "ok",
      "result": "deleted"
    }

Deleting an interface that is already absent returns:

    {
      "status": "ok",
      "result": "not_found",
      "interface": null
    }

Delete failures use the common backend error contract:

    authentication_failed
    connection_failed
    backend_failed

## Apply Result

Successful RESTCONF, NETCONF, or Ansible apply returns:

    {
      "status": "ok",
      "result": "applied"
    }

Failures use the common backend error contract:

    authentication_failed
    connection_failed
    backend_failed

The common result does not expose backend-specific details such as
Ansible's `changed` flag.

## Verified Live-Router Behavior

The IPA2026 Cisco IOS XE router was used to verify that:

    RESTCONF native PUT can create a Loopback.

    RESTCONF native PUT can replace the primary IPv4 address without
    leaving the old address as a secondary address.

    RESTCONF native shutdown maps to IETF enabled=false.

    Omitting native shutdown in a RESTCONF PUT maps to IETF enabled=true.

    NETCONF native configuration can create a Loopback and can set or
    remove shutdown.

    NETCONF native Loopback replacement removes stale secondary IPv4
    addresses and leaves only the requested primary address.

    Ansible network_cli can connect to the IOS XE router through Paramiko
    and `cisco.ios.ios_config` can create and update a Loopback.

    Reapplying an unchanged Ansible desired state with `defaults: true`
    completes idempotently with Ansible reporting changed=0.

    Ansible can change the primary IPv4 address without leaving the old
    primary address as a secondary address.

    Netmiko + TextFSM can read Loopback IPv4/prefix, description, and
    administrative state using the two-command status flow described
    above.

    Cisco IOS abbreviates Loopback names such as Loopback994 to Lo994 in
    `show interfaces description`; the backend normalization handles this
    abbreviation.

    Netmiko can remove a Loopback with the IOS command
    `no interface <interface_name>`.

    Netmiko deletion was verified on Loopback test resources that were not
    consistently removable through the RESTCONF native DELETE path. For this
    exam, delete is therefore intentionally scoped to `netmiko-textfsm`.

Status verification after apply may use an independent read path. For
RESTCONF and NETCONF, the IETF status model is intentionally independent of
the Cisco native apply model.
