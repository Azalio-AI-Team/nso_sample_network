# Implementation Plan: NSO Multi-Platform Topology Configuration & Network Orchestration

**Branch**: `002-nso-topology-config` | **Date**: 2026-11-03 | **Spec**: [specs/002-nso-topology-config/spec.md](./spec.md)

---

## 1. Summary

This plan details the technical architecture, touched files, generated network test payloads, and test strategy for implementing multi-platform network configuration across the Cisco DevNet NSO Sandbox topology. The plan introduces a new standalone package `nso_topology_manager/`, extends the root framework (`nso_client.py`, `nso_scenarios.py`), updates standalone sample scripts to support HTTP/port 8080 and device targeting, and adds comprehensive offline mock tests.

---

## 2. Technical Context

- **Language / Runtime**: Python 3.9+ (Python 3.12 / 3.14 compatible, managed with `uv`)
- **Primary Dependencies**: `requests`, `urllib3`, `unittest.mock` (standard library)
- **Target Network Protocols**: RFC 8040 RESTCONF over HTTP/HTTPS, Cisco NSO Data & Operations Models (`tailf-ncs:devices`, `tailf-ned-cisco-ios`, `tailf-ned-cisco-ios-xr`, `tailf-ned-cisco-nx`, `tailf-ned-cisco-asa`)
- **Target Network Elements**:
  - Cisco IOS-XE: `dist-rtr01` (`10.10.20.175`), `dev-dist-rtr01` (`10.10.20.176`), `internet-rtr01` (`10.10.20.181`)
  - Cisco IOS-XR: `core-rtr01` (`10.10.20.173`), `dev-core-rtr01` (`10.10.20.174`)
  - Cisco NX-OS: `dist-sw01` (`10.10.20.177`), `dev-dist-sw01` (`10.10.20.178`)
  - Cisco ASA: `edge-firewall01` (`10.10.20.171`)
  - Cisco IOS: `edge-sw01` (`10.10.20.172`)
- **Testing Approach**: 100% offline mock tests in `tests/test_topology_manager.py` + live smoke tests when VPN connected.
- **Security & Hygiene**: Zero hardcoded secrets; parameters sourced from environment variables or secure prompts.

---

## 3. Constitution Check

- [x] **Standalone sample principle preserved**: `nso_topology_manager/` has its own `README.md`, `requirements.txt`, and entry point `topology_manager.py`.
- [x] **No hardcoded credentials**: All credentials read via `NSO_USER`, `NSO_PASSWORD`, `RESTCONF_HOST` or `getpass()`.
- [x] **Explicit request timeouts & structured error handling**: `timeout=30` on all requests, graceful exception handling, clean output without unhandled tracebacks.
- [x] **Offline mock/unit test strategy**: `tests/test_topology_manager.py` mocks all RESTCONF requests and verifies 100% offline.
- [x] **Code quality checks**: Passes `ruff check .` with zero errors.

---

## 4. Affected Components & Blast Radius

| Component / Package | Nature of Change | Target Network Devices / Sandboxes | Blast Radius & Rollback Mechanism |
|---|---|---|---|
| `nso_topology_manager/` | **NEW** | NSO Controller (`10.10.20.47-49:8080`), 9 Topology Nodes | Standalone package for multi-tier audit, baseline provisioning, loopback config, and drift checking. Changes can be rolled back via DELETE requests on provisioned loopbacks or restoring initial config. |
| `nso_client.py` | **MODIFIED** | NSO Controller, multi-NED devices | Extends `set_loopback_interface` and interface methods to detect and handle `cisco-ios-cli`, `cisco-iosxr-cli`, and `cisco-nx-cli` YANG models. Backward compatible. |
| `nso_scenarios.py` | **MODIFIED** | NSO Controller, multi-NED devices | Adds multi-platform topology test scenarios (`scenario_12_multi_platform_loopbacks()`, `scenario_13_topology_audit()`). |
| `main.py` | **MODIFIED** | NSO Scenario Runner | Integrates multi-platform scenarios into main execution menu/pipeline. |
| `tests/test_topology_manager.py` | **NEW** | Unit test suite | 100% offline mock tests covering topology audit, multi-platform loopback provisioning, interface description update, and sync validation. |
| `PACKAGES.md` | **MODIFIED** | Documentation | Catalogs Package 23 (`nso_topology_manager/`). |
| `README.md` | **MODIFIED** | Documentation | Updates repository overview and architecture catalog. |

---

## 5. Network Test Strategy & Generated Test Payloads

### 1. Test Strategy
- **Offline Mock Tests**: Uses `unittest.mock` to patch `requests.Session.request`, validating request methods, URLs, YANG model paths, and JSON payloads.
- **Live DevNet Sandbox Verification**: Live run against `10.10.20.47-49:8080` to verify live commits, NED transactions, and out-of-band sync verification (`check-sync`).

### 2. Generated Network Test Payloads

#### Payload 1: Cisco IOS-XE Loopback Configuration (e.g. `dist-rtr01`)
- **Endpoint**: `PUT /restconf/data/tailf-ncs:devices/device=dist-rtr01/config/tailf-ned-cisco-ios:interface/Loopback=101`
- **Payload**:
```json
{
  "tailf-ned-cisco-ios:Loopback": {
    "name": "101",
    "description": "Configured via NSO Topology Manager (Distribution Tier)",
    "ip": {
      "address": {
        "primary": {
          "address": "172.16.1.1",
          "mask": "255.255.255.255"
        }
      }
    }
  }
}
```
- **Expected Status**: `HTTP 201 Created` or `HTTP 204 No Content`

#### Payload 2: Cisco IOS-XR Loopback Configuration (e.g. `core-rtr01`)
- **Endpoint**: `PUT /restconf/data/tailf-ncs:devices/device=core-rtr01/config/tailf-ned-cisco-ios-xr:interface/Loopback=101`
- **Payload**:
```json
{
  "tailf-ned-cisco-ios-xr:Loopback": {
    "id": "101",
    "description": "Configured via NSO Topology Manager (Core Tier)",
    "ipv4": {
      "address": {
        "ip": "172.16.0.1",
        "mask": "255.255.255.255"
      }
    }
  }
}
```
- **Expected Status**: `HTTP 201 Created` or `HTTP 204 No Content`

#### Payload 3: Cisco NX-OS Loopback Configuration (e.g. `dist-sw01`)
- **Endpoint**: `PUT /restconf/data/tailf-ncs:devices/device=dist-sw01/config/tailf-ned-cisco-nx:interface/Loopback=101`
- **Payload**:
```json
{
  "tailf-ned-cisco-nx:Loopback": {
    "id": "101",
    "description": "Configured via NSO Topology Manager (NX-OS Dist Switch)",
    "ip": {
      "address": {
        "ip-address": "172.16.2.1",
        "mask": "255.255.255.255"
      }
    }
  }
}
```
- **Expected Status**: `HTTP 201 Created` or `HTTP 204 No Content`

#### Payload 4: Interface Description Update via Atomic PATCH (e.g. `dist-rtr01`)
- **Endpoint**: `PATCH /restconf/data/tailf-ncs:devices/device=dist-rtr01/config/tailf-ned-cisco-ios:interface/GigabitEthernet=0%2F1`
- **Payload**:
```json
{
  "tailf-ned-cisco-ios:GigabitEthernet": {
    "name": "0/1",
    "description": "Uplink to core-rtr01 (Topology Interconnect)"
  }
}
```
- **Expected Status**: `HTTP 200 OK` or `HTTP 204 No Content`

#### Payload 5: Operational Action - Check-Sync
- **Endpoint**: `POST /restconf/operations/tailf-ncs:devices/device=dist-rtr01/check-sync`
- **Payload**: `{}`
- **Expected Status**: `HTTP 200 OK`, response `{"tailf-ncs:output": {"result": "in-sync"}}`

---

## 6. Rollback & Safety Plan

1. **Loopback Rollbacks**: Delete provisioned Loopback interfaces via `DELETE /restconf/data/tailf-ncs:devices/device={device}/config/tailf-ned-cisco-{ned}:interface/Loopback={id}`.
2. **Interface Descriptions**: Revert descriptions to original strings via atomic `PATCH`.
3. **Out-of-band Sync**: After any rollback, execute `check-sync` to verify the NSO CDB and network hardware match.
