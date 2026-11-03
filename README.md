# Network Automation with Python Code Samples

A collection of Python Code Samples for Network Management across Cisco technologies (RESTCONF, NETCONF, Cisco IOS-XE, Cisco NSO, Netmiko, SNMP, EEM, APIC-EM, and Cisco ACI). 

Includes samples that leverage on-box libraries (Guest Shell / EEM), external APIs (NETCONF/RESTCONF, SNMP, SSH, REST), and centralized controllers.

> 📖 **Comprehensive Package Catalog**: See [PACKAGES.md](./PACKAGES.md) for detailed architectural documentation, YANG data models, input parameters, and execution instructions for all 23 packages and the Cisco NSO automation framework.

---

## Spec-Driven Development (SDD) Workflow

This repository is configured for **Spec-Driven Development (SDD)** using **GitHub Spec Kit** with multi-agent integrations for **Antigravity (`agy`)** and **Claude Code (`claude`)**.

Whenever code changes, bug fixes, or new automation scenarios are introduced, engineers and coding agents follow this required repository workflow:

```mermaid
flowchart LR
    A["1. Clarify (/speckit-clarify)"] --> B["2. Specify (/speckit-specify)"]
    B --> C["3. Discover (PACKAGES.md)"]
    C --> D["4. Plan & Payloads (/speckit-plan)"]
    D --> E["5. Impact Review"]
    E --> F["6. Human Approval Gate"]
    F --> G["7. Tasks & Implement (/speckit-implement)"]
```

1. **Clarify Requirements**: Understand user intent and ask up to 5 clarification questions (`/speckit-clarify`).
2. **Structure Specification**: Define requirements and strict acceptance criteria (`/speckit-specify` -> `spec.md`).
3. **Codebase Discovery & Analysis**: Consult [PACKAGES.md](./PACKAGES.md) to discover affected modules, YANG models, and device targets (`/speckit-analyze`).
4. **Planning & Test Payload Generation**: Formulate `plan.md` via `/speckit-plan`, detailing code diffs, offline mock testing strategy, and generated network test payloads (RESTCONF JSON, NETCONF XML, or CLI commands).
5. **Impact Review & Checkpoint**: Verify touched files, blast radius, and rollback capabilities.
6. **Human Approval Gate (Mandatory)**: Human engineer reviews and approves the plan, test payloads, and safety guards before code execution.
7. **Task Decomposition & Implementation**: Deconstruct into tasks (`/speckit-tasks`) and execute against tests (`/speckit-implement`, `/speckit-converge`).

- **Core Constitution**: [`.specify/memory/constitution.md`](.specify/memory/constitution.md)
- **Agent Guidelines**: [`AGENTS.md`](./AGENTS.md) / [`agent.md`](./agent.md)
- **Workflow Skill**: `/speckit-network-workflow`

---

## On-Box Examples (Guest Shell & EEM)

Many Cisco switches and routers provide an on-box Python Interpreter within Guest Shell that can be leveraged to execute scripts directly on end devices.

| Code Sample | Description |
| --- | --- |
| [Execute CLI via Python](/Py-sho-ver-onbox) | Executes `show version` on-box using the Cisco Python `cli` library. |
| [TDR Test Every Interface](/tdr-test) | Runs Time Domain Reflectometry cable diagnostics on all active interfaces to detect physical faults. |
| [EEM Config Changes to Spark](/eem_configdiff_to_spark) | EEM monitors for configuration changes (`%SYS-5-CONFIG_I`) and posts the diff to Cisco Webex/Spark. |
| [Python with Eventing Example](/EEM-interface-move-routes) | EEM dynamically updates static routes when an interface state degrades. |
| [EEM + Python + Spark ChatOps](/spark_checkin) | Sends operational alerts and change check-ins to Webex Teams. |
| [EEM + Python + Email Alert](/PortFlap_email_alert) | Monitors for interface flapping (>5 in 5m), disables the port (`shutdown`), and sends an SMTP alert. |

---

## Off-Box Examples (Model-Driven & Controller APIs)

Python scripts interacting with network elements and controllers via standard interfaces (NETCONF, RESTCONF, SNMP, SSH).

| Code Sample | Description |
| --- | --- |
| [RESTCONF](/RESTCONF) | Complete RESTCONF CRUD operations (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`) supporting IOS-XE and Cisco NSO. |
| [Basic RESTCONF Get](/RC-get-config) | Minimalist RESTCONF script to fetch device running config in JSON format. |
| [Hardware Serial Numbers via RESTCONF](/RC-get-serial-numbers) | Retrieves device chassis and module serial numbers from operational YANG models. |
| [Configure Interface IP with RESTCONF](/restconf_update_ipaddress) | Interactive CLI script to update interface IP address using `ietf-interfaces`. |
| [Basic NETCONF Get](/NC-get-config) | Basic `ncclient` example to `<get-config>` running configuration in XML. |
| [Basic NETCONF Edit](/NC-edit-config) | Transactional `<edit-config>` RPC to update device hostname. |
| [NETCONF XPATH Example](/NC-get-config-xpath) | Server-side XPATH filtering (`/native/interface/Loopback`) for bandwidth-efficient retrieval. |
| [NETCONF Physical Entity](/netconf_entity) | Retrieves RFC 6933 / ENTITY-MIB physical hardware inventory over NETCONF. |
| [Model-Based AAA & NACM](/model-based-aaa) | Role-Based Access Control using `ietf-netconf-acm` (RFC 8341) on Cisco IOS-XE. |
| [Netmiko Interface Management](/netmiko-interface-example) | Multi-vendor CLI automation over SSH for retrieving, creating, and deleting Loopbacks. |
| [SNMP Entity MIB Walk](/snmp_entity) | MIB walk against physical entities using `netsnmp` Python bindings. |
| [Get Host List from APIC-EM](/apic-em_get_hosts) | Queries Cisco APIC-EM REST API (`/api/v1/host`) for connected client IP and MAC mappings. |
| [Get Inventory Stats from APIC-EM](/apic-em_get_inventory_stats) | Fetches complete network device inventory and hardware lifecycle statistics. |
| [Retrieve Tenants from ACI APIC](/acitoolkit_show_tenants) | Queries Cisco ACI fabric for active Tenants, Application Profiles, and EPGs via `acitoolkit`. |
| [NSO Device Lifecycle Manager](/nso_device_manager) | Standalone package to onboard, edit, rename, delete, and synchronize devices in Cisco NSO CDB. |
| [NSO Network Port Blocker](/nso_port_blocking) | Standalone package for Layer 4 ACL port filtering and administrative interface shutdown on NSO devices. |
| [NSO Topology Manager](/nso_topology_manager) | Standalone package for DevNet 9-node multi-platform topology orchestration, multi-NED Loopbacks, descriptions, and audit. |

---

## Centralized Cisco NSO Automation Engine

The root directory contains an enterprise-grade automation framework targeting **Cisco Network Services Orchestrator (NSO / NCS)** via RESTCONF:

- [`nso_client.py`](./nso_client.py): Reusable RESTCONF client with auto-scheme detection (HTTP:8080/HTTPS:443), device lifecycle, port blocking, check-sync, and sync-from.
- [`nso_scenarios.py`](./nso_scenarios.py): 13 automated scenarios covering fleet discovery, interface provisioning, drift analysis, device lifecycle, port blocking, multi-platform loopbacks, and full fleet topology health audit.
- [`main.py`](./main.py): Interactive terminal runner for network engineers.
- [`tests/`](./tests/): Comprehensive unit test suite with 100% offline mock verification (`test_nso.py`, `test_device_manager.py`, `test_port_blocking.py`, `test_topology_manager.py`).
- [`VODAFONE_PRESENTATION_WORKFLOW_AND_SCRIPT.md`](./VODAFONE_PRESENTATION_WORKFLOW_AND_SCRIPT.md): Complete demonstration and presentation runbook.

---

## Cisco DevNet NSO Sandbox Topology & Multi-Platform Architecture

The repository's NSO packages and orchestration scenarios are modeled around the official [Cisco DevNet Reservable NSO Sandbox](https://developer.cisco.com/sandbox/detail/nso-sandbox) multi-tier network topology:

```mermaid
graph TD
    subgraph WAN_Internet ["Internet / External"]
        INET["internet-rtr01<br/>10.10.20.181 (SSH:22)<br/>Cisco IOS-XE"]
    end

    subgraph Security_Perimeter ["Perimeter Security"]
        FW["edge-firewall01<br/>10.10.20.171 (Telnet:23)<br/>Cisco ASA"]
        EDGE_SW["edge-sw01<br/>10.10.20.172 (Telnet:23)<br/>Cisco IOS"]
    end

    subgraph Core_Tier ["Core Routing Tier"]
        CORE1["core-rtr01<br/>10.10.20.173 (Telnet:23)<br/>Cisco IOS-XR"]
        CORE2["dev-core-rtr01<br/>10.10.20.174 (Telnet:23)<br/>Cisco IOS-XR"]
    end

    subgraph Distribution_Tier ["Distribution & Switching Tier"]
        DIST_R1["dist-rtr01<br/>10.10.20.175 (SSH:22)<br/>Cisco IOS-XE"]
        DIST_R2["dev-dist-rtr01<br/>10.10.20.176 (SSH:22)<br/>Cisco IOS-XE"]
        DIST_SW1["dist-sw01<br/>10.10.20.177 (SSH:22)<br/>Cisco NX-OS"]
        DIST_SW2["dev-dist-sw01<br/>10.10.20.178 (SSH:22)<br/>Cisco NX-OS"]
    end

    INET --- FW
    FW --- EDGE_SW
    EDGE_SW --- CORE1
    EDGE_SW --- CORE2
    CORE1 --- DIST_R1
    CORE1 --- DIST_SW1
    CORE2 --- DIST_R2
    CORE2 --- DIST_SW2
```

### 1. Topology Inventory & Management Protocol Partitioning

> ⚠️ **CRITICAL PROTOCOL CONSTRAINT**: The physical/virtual devices in this sandbox strictly partition management access by transport protocol. Connecting with the wrong protocol or port will cause connection refusal:
> - **Telnet Devices (Port 23)**: `edge-firewall01` (`.171`), `edge-sw01` (`.172`), `core-rtr01` (`.173`), `dev-core-rtr01` (`.174`).
> - **SSH Devices (Port 22)**: `dist-rtr01` (`.175`), `dev-dist-rtr01` (`.176`), `dist-sw01` (`.177`), `dev-dist-sw01` (`.178`), `internet-rtr01` (`.181`).

| Network Tier | Device Name | Management IP | Protocol | Port | Network Element Driver (NED) | Role / Function |
|---|---|---|---|---|---|---|
| **Firewall** | `edge-firewall01` | `10.10.20.171` | **Telnet** | 23 | `cisco-asa-cli-6.18` | Perimeter firewall & ACL enforcement |
| **Edge Access** | `edge-sw01` | `10.10.20.172` | **Telnet** | 23 | `cisco-ios-cli-6.109` | Campus edge switch |
| **Core** | `core-rtr01` | `10.10.20.173` | **Telnet** | 23 | `cisco-iosxr-cli-7.65` | Backbone core router (IOS-XR) |
| **Core Dev** | `dev-core-rtr01` | `10.10.20.174` | **Telnet** | 23 | `cisco-iosxr-cli-7.65` | Staging core router (IOS-XR) |
| **Distribution** | `dist-rtr01` | `10.10.20.175` | **SSH** | 22 | `cisco-ios-cli-6.109` | Production aggregation router (IOS-XE) |
| **Dist Dev** | `dev-dist-rtr01` | `10.10.20.176` | **SSH** | 22 | `cisco-ios-cli-6.109` | Staging aggregation router (IOS-XE) |
| **Dist Switch** | `dist-sw01` | `10.10.20.177` | **SSH** | 22 | `cisco-nx-cli-5.27` | Data center aggregation switch (NX-OS) |
| **Dist Sw Dev** | `dev-dist-sw01` | `10.10.20.178` | **SSH** | 22 | `cisco-nx-cli-5.27` | Staging data center switch (NX-OS) |
| **Internet / WAN** | `internet-rtr01` | `10.10.20.181` | **SSH** | 22 | `cisco-ios-cli-6.109` | Gateway internet uplink router |

### 2. Standalone Packages & Multi-Platform Capabilities

1. **[`nso_topology_manager/`](./nso_topology_manager/)**:
   - High-level topology orchestration package aligning device configurations to sandbox roles.
   - `topology_models.py`: Strongly-typed dataclasses (`NetworkNode`, `NetworkTier`), 9-node metadata, and NED definitions.
   - `topology_manager.py`: Supports CLI actions:
     - `--action audit`: Displays live sync status, reachability, and tier classification across all 9 devices.
     - `--action deploy-baseline`: Deploys tier-based Loopbacks (`172.16.x.x/32`) and interface descriptions.
     - `--action configure-loopback`: Provisions platform-aware Loopbacks (translating IOS, XR, and NX-OS formats).
     - `--action delete-loopback`: Removes loopback interfaces cleanly.
     - `--action set-description`: Updates interface descriptions.
     - `--action verify-sync`: Verifies CDB out-of-band state across all nodes.
     - `--action rollback`: Restores interface configurations.

2. **Core NSO Client Engine ([`nso_client.py`](./nso_client.py) & [`nso_scenarios.py`](./nso_scenarios.py))**:
   - **Multi-NED Loopback Management**: Automatically adapts payloads:
     - **IOS-XE**: `tailf-ned-cisco-ios:interface/Loopback={id}` with `primary.address` and `mask`.
     - **IOS-XR**: `tailf-ned-cisco-ios-xr:interface/Loopback={id}` with `ipv4.address.ip` and `mask`.
     - **NX-OS**: `tailf-ned-cisco-nx:interface/loopback={id}` (lowercase) with `ipaddr` in CIDR notation (e.g. `172.16.2.1/32`).
   - **Layer 4 Security & Extended ACLs**: Corrected extended named ACL model (`tailf-ned-cisco-ios:ext-named-acl` with `ext-access-list-rule`) and interface `access-group` binding.
   - **Management Interface Protection**: Safety guardrails preventing ACL attachment or shutdown on out-of-band management interfaces (e.g., `GigabitEthernet1` on `10.10.20.175`).
   - **Complete Scenario Suite**: 13 automated scenarios covering fleet discovery, interface inspection, declarative provisioning, intent drift check, out-of-band sync check, policy guardrails, teardown, e2e orchestration, CDB lifecycle management, Layer 4 ACL port filtering, interface isolation, multi-platform loopbacks, and full fleet topology health audit.
