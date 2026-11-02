# Implementation Plan: NSO Device Lifecycle Management and Port Blocking Packages

**Branch**: `001-nso-mgmt-portblock` | **Date**: 2026-11-02 | **Spec**: [specs/001-nso-mgmt-portblock/spec.md](./spec.md)

**Input**: Feature specification from `specs/001-nso-mgmt-portblock/spec.md`

---

## 1. Summary

This plan details the design, architecture, and verification strategy for adding two new standalone network automation packages (`nso_device_manager/` and `nso_port_blocking/`), modernizing the centralized `nso_client.py` and `nso_scenarios.py` with zero-secrets hygiene and HTTP/8080 scheme adaptation, authoring offline mock unit tests, updating documentation catalogs, and configuring the GitLab remote (`10.10.20.54:8080`) to commit and push changes.

---

## 2. Technical Context

- **Language/Version**: Python 3.9+ (Python 3.12 / 3.14 compatible, managed via `uv`)
- **Primary Dependencies**: `requests`, `urllib3`, `unittest.mock` (standard library), with per-package `requirements.txt`
- **Network Protocols/Target APIs**: RFC 8040 RESTCONF over HTTP/HTTPS, Cisco NSO Data & Operations Models (`tailf-ncs:devices`, `tailf-ned-cisco-ios:interface`, `tailf-ned-cisco-ios:ip/access-list`)
- **Testing**: 100% offline unit tests (`tests/test_device_manager.py`, `tests/test_port_blocking.py`, `tests/test_nso.py`) using `unittest.mock`
- **Target Platform/Devices**: Cisco NSO 6.4.4 (`10.10.20.49:8080`), Cisco IOS-XE (`dist-rtr01`, `10.10.20.175`), Cisco ASA (`edge-firewall01`), Cisco NX-OS (`dist-sw01`), and Cisco IOS-XR (`core-rtr01`)
- **Project Type**: Standalone Network Automation Packages + Central SDK Framework
- **Security & Secrets**: Strict zero-hardcoded-secrets policy; all credentials read from environment variables or `getpass()`

---

## 3. Constitution Check

- [x] **Standalone sample principle preserved**: `nso_device_manager/` and `nso_port_blocking/` each have their own `README.md`, entry-point CLI scripts, and `requirements.txt`.
- [x] **No hardcoded passwords or tokens**: Stripped from `nso_client.py` and all new files.
- [x] **Explicit request timeouts & structured error handling**: Explicit `timeout=30` on all HTTP calls; errors output to `stderr` with appropriate non-zero exits.
- [x] **Offline mock/unit test strategy included**: Dedicated unit tests mocking `requests.Session.request` for all scenarios.
- [x] **Code quality checks**: Adheres to `ruff check .` formatting and typing standards.

---

## 4. Affected Components & Blast Radius

| Component / Package | Nature of Change | Target Network Devices / Sandboxes | Blast Radius & Rollback Mechanism |
|---|---|---|---|
| `nso_device_manager/` | **NEW** | NSO Controller (`10.10.20.49:8080`), CDB `/tailf-ncs:devices/device` | Manages device entries in NSO CDB. Devices created for testing (e.g. `lab-rtr99`) can be purged via `DELETE /tailf-ncs:devices/device=lab-rtr99`. |
| `nso_port_blocking/` | **NEW** | NSO Controller (`10.10.20.49:8080`), managed IOS-XE (`dist-rtr01`) | ACL and interface shutdown modifications. Rollback removes ACL and issues `no shutdown`. |
| `nso_client.py` | **MODIFIED** | NSO Controller (`10.10.20.49:8080` / `sandbox-nso-1.cisco.com`) | Backward compatible helper class. Auto-detects `http` vs `https`. Removes hardcoded password. Adds device management & port blocking methods. |
| `nso_scenarios.py` | **MODIFIED** | NSO Controller (`10.10.20.49:8080`), target device `dist-rtr01` | Adds scenarios for device lifecycle and port blocking. Parameterizes default device to `dist-rtr01`. |
| `tests/test_nso.py` | **MODIFIED** | Unit test suite | Parameterizes device assertions to support both 9-node reservable and 10-node sandboxes. |
| `tests/test_device_manager.py` | **NEW** | Unit test suite | 100% offline mock tests covering add, edit, rename, delete, sync-from. |
| `tests/test_port_blocking.py` | **NEW** | Unit test suite | 100% offline mock tests covering L4 ACL creation, application, interface shutdown, rollback. |
| `PACKAGES.md` | **MODIFIED** | Documentation | Adds sections 21 (`nso_device_manager`) and 22 (`nso_port_blocking`). |
| `README.md` | **MODIFIED** | Documentation | Updates repository overview table and getting started guidelines. |

---

## 5. Network Test Strategy & Generated Payloads

### 1. Test Strategy (Offline Mocks vs Sandbox)
- **Offline Mocking**: `unittest.mock.patch("requests.Session.request")` intercepts all RESTCONF HTTP calls. Mocked responses return realistic NSO JSON bodies (e.g. `{"tailf-ncs:device": [...]}`) and status codes (200, 201, 204, 404).
- **DevNet Sandbox Smoke Test**: When connected via VPN to `10.10.20.49:8080`, scripts perform live verification using `dist-rtr01`.

### 2. Generated Payloads & Contracts

#### Payload 1: Add New Device to NSO CDB (`POST /restconf/data/tailf-ncs:devices`)
```json
{
  "tailf-ncs:device": [
    {
      "name": "lab-rtr99",
      "address": "10.10.20.199",
      "port": 23,
      "authgroup": "default",
      "device-type": {
        "cli": {
          "ned-id": "tailf-ned-cisco-ios-id:cisco-ios-cli-6.109",
          "protocol": "telnet"
        }
      },
      "state": {
        "admin-state": "unlocked"
      }
    }
  ]
}
```
- **Expected Status**: `HTTP 201 Created` or `HTTP 204 No Content`

#### Payload 2: Edit Device Configuration (`PATCH /restconf/data/tailf-ncs:devices/device=lab-rtr99`)
```json
{
  "tailf-ncs:device": {
    "name": "lab-rtr99",
    "description": "Lab distribution router provisioned by NSO Device Manager",
    "address": "10.10.20.200"
  }
}
```
- **Expected Status**: `HTTP 200 OK` or `HTTP 204 No Content`

#### Payload 3: Port Blocking - Extended ACL Creation (`PUT /restconf/data/tailf-ncs:devices/device=dist-rtr01/config/tailf-ned-cisco-ios:ip/access-list/extended=BLOCK_PORT_23`)
```json
{
  "tailf-ned-cisco-ios:extended": {
    "id": "BLOCK_PORT_23",
    "rule": [
      {
        "name": "10",
        "action": "deny",
        "protocol": "tcp",
        "source": {
          "any": [null]
        },
        "destination": {
          "any": [null],
          "port": {
            "eq": 23
          }
        }
      },
      {
        "name": "20",
        "action": "permit",
        "protocol": "ip",
        "source": {
          "any": [null]
        },
        "destination": {
          "any": [null]
        }
      }
    ]
  }
}
```
- **Expected Status**: `HTTP 201 Created` or `HTTP 204 No Content`

#### Payload 4: Port Blocking - Interface Shutdown (`PATCH /restconf/data/tailf-ncs:devices/device=dist-rtr01/config/tailf-ned-cisco-ios:interface/GigabitEthernet=0%2F2`)
```json
{
  "tailf-ned-cisco-ios:GigabitEthernet": {
    "name": "0/2",
    "shutdown": [null]
  }
}
```
- **Expected Status**: `HTTP 200 OK` or `HTTP 204 No Content`

#### Payload 5: Rollback - Interface Re-enable (`PATCH /restconf/data/tailf-ncs:devices/device=dist-rtr01/config/tailf-ned-cisco-ios:interface/GigabitEthernet=0%2F2`)
```json
{
  "tailf-ned-cisco-ios:GigabitEthernet": {
    "name": "0/2"
  }
}
```
(Or `DELETE .../shutdown`)
- **Expected Status**: `HTTP 204 No Content`

---

## 6. Pre-Implementation Human Review Gate Checkpoint

- [x] Planned code modifications reviewed: `nso_device_manager/`, `nso_port_blocking/`, `nso_client.py`, `nso_scenarios.py`, `tests/`.
- [x] Network payloads verified against YANG data models (`tailf-ncs:devices`, `tailf-ned-cisco-ios`).
- [x] Offline unit test suite prepared with comprehensive mocks.
- [x] Rollback safety procedures established for all configuration mutations.
