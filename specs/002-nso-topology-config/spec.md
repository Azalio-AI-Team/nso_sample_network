# Feature Specification: NSO Multi-Platform Topology Configuration & Network Orchestration

**Feature Branch**: `002-nso-topology-config`  
**Created**: 2026-11-03  
**Status**: In Review / Pending Approval  
**Reference Network Layout**: [Cisco DevNet Reservable NSO Sandbox](https://developer.cisco.com/sandbox/detail/nso-sandbox)  
**Input**: User request: "modify add update and create the python files that are present in this folder. these files should be used to configure and update the connected devices and make necessary edits as requested. it should properly address the network structure and layout. https://developer.cisco.com/sandbox/detail/nso-sandbox has the layout of the network."

---

## 1. Executive Summary & Problem Scope

The Cisco DevNet Reservable NSO Sandbox provides an isolated 9-node multi-tier network topology managed by Cisco Network Services Orchestrator (NSO 6.4.4) on `10.10.20.47-49:8080`. 

Prior codebase samples primarily targeted single IOS-XE devices (`dist-rtr00`/`dist-rtr01`) with IOS-specific NED models (`tailf-ned-cisco-ios`). In real-world enterprise architectures and in the NSO Sandbox, the topology spans four distinct network operating systems and Cisco NED families:
1. **Core Tier (Cisco IOS-XR)**: `core-rtr01` (10.10.20.173), `dev-core-rtr01` (10.10.20.174) with NED `cisco-iosxr-cli-7.65`.
2. **Distribution Tier (Cisco IOS-XE)**: `dist-rtr01` (10.10.20.175), `dev-dist-rtr01` (10.10.20.176) with NED `cisco-ios-cli-6.109`.
3. **Data Center Distribution Tier (Cisco NX-OS)**: `dist-sw01` (10.10.20.177), `dev-dist-sw01` (10.10.20.178) with NED `cisco-nx-cli-5.27`.
4. **Access Tier (Cisco IOS)**: `edge-sw01` (10.10.20.172) with NED `cisco-ios-cli-6.109`.
5. **Perimeter Firewall (Cisco ASA)**: `edge-firewall01` (10.10.20.171) with NED `cisco-asa-cli-6.18`.
6. **WAN/Internet Gateway (Cisco IOS-XE)**: `internet-rtr01` (10.10.20.181) with NED `cisco-ios-cli-6.109`.

This specification defines the additions and enhancements required to:
1. Provide a standalone **NSO Topology Manager Package** (`nso_topology_manager/`) capable of discovering, inspecting, configuring, and updating all 9 network nodes across their respective NED models via Cisco NSO RESTCONF.
2. Extend the centralized `nso_client.py` and `nso_scenarios.py` to support multi-platform Loopback and interface configurations across IOS-XE, IOS-XR, and NX-OS.
3. Provide automated topology layout mapping, baseline hostname/description management, and inter-tier interface provisioning matching the sandbox topology.
4. Support full sync validation (`check-sync`), drift comparison (`compare-config`), and atomic rollback.
5. Provide 100% offline mock unit test coverage (`tests/test_topology_manager.py`).
6. Update `PACKAGES.md` and `README.md` to catalog the new package.

---

## 2. User Scenarios & Prioritized User Stories

### User Story 1 - Standalone NSO Topology Manager Package (`nso_topology_manager/`) (Priority: P1)

As a network automation engineer,  
I want a standalone, CLI-executable and importable Python package to inspect, configure, and update connected devices according to their role in the sandbox topology,  
So that multi-tier network configuration changes (IOS-XE, IOS-XR, NX-OS, ASA) can be deployed consistently via Cisco NSO RESTCONF.

**Why this priority**: Directly satisfies the user requirement to configure and update connected devices addressing the complete network structure and layout.

**Independent Test**: Can be run independently via `python nso_topology_manager/topology_manager.py --action deploy-baseline ...` and verified via offline mock tests in `tests/test_topology_manager.py`.

**Acceptance Scenarios**:
1. **Given** NSO controller endpoint, **When** user runs `--action audit`, **Then** the package queries all 9 topology nodes, identifies their OS/NED type, admin state, and sync status, outputting a structured status report.
2. **Given** topology tier (e.g. Core, Distribution, Edge), **When** user runs `--action configure-loopback --device <name> --loopback-id <id> --ip <ip> --netmask <mask>`, **Then** the package translates the configuration into the platform-specific YANG payload (`tailf-ned-cisco-ios`, `tailf-ned-cisco-ios-xr`, or `tailf-ned-cisco-nx`) and commits it via NSO.
3. **Given** an existing configured interface, **When** user runs `--action update-interface --device <name> --interface <iface> --description <desc>`, **Then** the description is updated atomically via RESTCONF `PATCH`.
4. **Given** configured network devices, **When** user runs `--action verify-sync`, **Then** NSO executes `check-sync` operational RPC across targeted devices, reporting `in-sync` or identifying drift.

---

### User Story 2 - Multi-Platform Support in Central Framework (`nso_client.py` & `nso_scenarios.py`) (Priority: P1)

As a developer using the repository root tools (`nso_client.py`, `nso_scenarios.py`, `main.py`),  
I want `nso_client.py` to provide multi-platform interface abstraction supporting IOS-XR and NX-OS in addition to IOS-XE,  
So that scenarios can interact with Core routers (`core-rtr01`), Distribution switches (`dist-sw01`), and edge routers seamlessly.

**Why this priority**: Existing methods in `nso_client.py` only targeted `tailf-ned-cisco-ios:interface`, which fails when executed against IOS-XR (`core-rtr01`) or NX-OS (`dist-sw01`).

**Acceptance Scenarios**:
1. **Given** device `core-rtr01` (IOS-XR), **When** calling `set_loopback_interface`, **Then** `nso_client.py` formats the payload using `tailf-ned-cisco-ios-xr:interface/Loopback`.
2. **Given** device `dist-sw01` (NX-OS), **When** calling `set_loopback_interface`, **Then** `nso_client.py` formats the payload using `tailf-ned-cisco-nx:interface/Loopback`.
3. **Given** any managed device, **When** calling `compare_config`, **Then** diff output between NSO CDB and running hardware is returned.

---

### User Story 3 - Standalone Sample Directory Alignment (`RESTCONF/`, `RC-get-config/`) (Priority: P2)

As a student or developer running standalone examples in `RESTCONF/` and `RC-get-config/`,  
I want these scripts to support the HTTP scheme on port 8080 and accept target devices matching the 9-node topology (`dist-rtr01`, `core-rtr01`),  
So that individual sample folders function smoothly against the DevNet sandbox.

**Why this priority**: Ensures repository-wide consistency and fulfills Principle I (Standalone Sample Architecture).

---

### User Story 4 - 100% Offline Mock Unit Testing & Quality Verification (Priority: P1)

As a CI/CD pipeline and maintainer,  
I want comprehensive offline mock tests for all new topology configuration methods,  
So that verification is deterministic, runs without live network connectivity, and passes static analysis (`ruff check .`).

**Acceptance Scenarios**:
1. `uv run python -m unittest discover tests` passes 100% of tests.
2. `ruff check .` executes with 0 errors.

---

## 3. Zero-Hardcoded-Secrets Compliance

In strict compliance with Constitution Principle II:
- No real passwords, tokens, private endpoints, or keys will be stored in python source code.
- Credentials must be sourced via environment variables (`NSO_USER`, `NSO_PASSWORD`, `RESTCONF_HOST`) with fallback to `getpass()`.
- `.env` remains gitignored.
