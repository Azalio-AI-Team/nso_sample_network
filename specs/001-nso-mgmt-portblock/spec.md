# Feature Specification: NSO Device Lifecycle Management and Port Blocking Packages

**Feature Branch**: `001-nso-mgmt-portblock`  
**Created**: 2026-11-02  
**Status**: Ready for Review / Approved  
**Input**: User request: "refer to the SANDBOX_ASSESSMENT.md we have the git repo configured in this folder already. we need to edit commit and push this repo to the connected gitlab env. also we need to update this repo to add more packages relevant to the provided NSO netowkr and make necessary updaes changes device configuration modification. add new devices, remove, rename, edit devices, add port blocking functionality etc."

---

## 1. Executive Summary & Problem Scope

Based on the environment assessment documented in `SANDBOX_ASSESSMENT.md`, the live Cisco DevNet Reservable NSO Sandbox provides an NSO 6.4.4 instance running at `10.10.20.49:8080` (HTTP) managing 9 network elements (IOS-XE, NX-OS, IOS-XR, ASA) and connected to NetDevOps GitLab at `http://10.10.20.54:8080`.

This specification defines the additions and enhancements required to:
1. Provide a standalone **NSO Device Manager Package** (`nso_device_manager/`) implementing full device lifecycle management (add, edit, rename, remove, fetch-keys, sync-from).
2. Provide a standalone **NSO Port Blocking Package** (`nso_port_blocking/`) supporting dual blocking mechanisms: Layer 4 ACL port filtering (TCP/UDP destination port drops) and physical/logical interface administrative shutdown.
3. Generalize the centralized `nso_client.py` and `nso_scenarios.py` with HTTP/HTTPS scheme autodetection, zero-hardcoded secrets, device parameterization (`dist-rtr01` fallback), and device/port-blocking helper APIs.
4. Provide comprehensive offline mock test coverage (`tests/test_nso.py`, `tests/test_device_manager.py`, `tests/test_port_blocking.py`).
5. Update `PACKAGES.md` and `README.md` to catalog all new packages.
6. Configure the connected GitLab remote (`http://10.10.20.54:8080`) and commit/push the codebase.

---

## 2. User Scenarios & Prioritized User Stories

### User Story 1 - NSO Device Lifecycle Management (`nso_device_manager/`) (Priority: P1)

As a network automation engineer,  
I want a standalone, CLI-executable and importable Python package to onboard, edit, rename, and decommission network devices in Cisco NSO via RESTCONF,  
So that device inventory and NED configurations can be managed programmatically without manual NSO CLI sessions.

**Why this priority**: Core user requirement to add, remove, rename, and edit devices in NSO CDB.

**Independent Test**: Can be run independently via `python nso_device_manager/device_manager.py --action add ...` and tested with offline mock tests in `tests/test_device_manager.py`.

**Acceptance Scenarios**:
1. **Given** NSO endpoint `10.10.20.49:8080`, **When** user invokes `add_device` with name `lab-rtr99`, IP `10.10.20.199`, port `23`, authgroup `default`, and NED `cisco-ios-cli-6.109`, **Then** NSO creates the device entry under `/tailf-ncs:devices/device=lab-rtr99` returning HTTP 201 or 204.
2. **Given** existing device `lab-rtr99`, **When** user invokes `edit_device` to change IP or description, **Then** NSO updates the device attributes returning HTTP 200 or 204.
3. **Given** existing device `lab-rtr99`, **When** user invokes `rename_device` to `lab-rtr100`, **Then** the device configuration is safely transitioned to the new key without orphan records.
4. **Given** existing device `lab-rtr100`, **When** user invokes `delete_device`, **Then** NSO issues a `DELETE` request removing the device and returning HTTP 204.
5. **Given** any managed device, **When** user runs `sync_from` or `fetch_ssh_host_keys`, **Then** NSO executes the respective RPC operational action.

---

### User Story 2 - NSO Port Blocking Functionality (`nso_port_blocking/`) (Priority: P1)

As a network security operator,  
I want a standalone package to block specific TCP/UDP network ports or administratively disable switchports/interfaces via Cisco NSO,  
So that malicious traffic, unapproved services (e.g. Telnet 23, HTTP 80, SMB 445), or compromised interfaces can be rapidly isolated.

**Why this priority**: Explicit user requirement for port blocking functionality with dual L4 ACL filtering and interface shutdown support.

**Independent Test**: Can be tested independently via `python nso_port_blocking/port_blocker.py --device dist-rtr01 --action block-port ...` and with offline mock tests in `tests/test_port_blocking.py`.

**Acceptance Scenarios**:
1. **Given** Cisco IOS-XE device `dist-rtr01`, **When** user invokes `block_port` for TCP port `23` on interface `GigabitEthernet0/1` (or `FastEthernet0/0`), **Then** an extended ACL `BLOCK_PORT_23` is provisioned denying `tcp any any eq 23` (with permit any any fallback) and applied `in` to the interface.
2. **Given** an applied port block ACL, **When** user invokes `unblock_port`, **Then** the ACL association is removed from the interface and deleted from NSO CDB.
3. **Given** a network interface (e.g. `GigabitEthernet0/2`), **When** user invokes `shutdown_interface`, **Then** NSO sets `shutdown` to `True` (or present) on the interface config.
4. **Given** a shut interface, **When** user invokes `enable_interface`, **Then** NSO removes the shutdown attribute, restoring link carrier.

---

### User Story 3 - Centralized NSO Client & Scenario Modernization (Priority: P1)

As a developer using the repository root tools (`nso_client.py`, `nso_scenarios.py`, `main.py`),  
I want `nso_client.py` to auto-detect the HTTP/HTTPS scheme based on port, support device parameters with `dist-rtr01` as the active sandbox default, eliminate hardcoded secrets, and provide device lifecycle and port blocking helper methods,  
So that existing automation runs reliably against the reservable DevNet NSO sandbox.

**Why this priority**: Required to fix sandbox incompatibilities identified in `SANDBOX_ASSESSMENT.md` and satisfy Constitution Principle II.

**Independent Test**: `python main.py` and `nso_scenarios.py` execute cleanly against both live sandbox and offline mocks.

**Acceptance Scenarios**:
1. **Given** port `8080`, **When** `NSOClient` initializes without explicit scheme, **Then** scheme defaults to `http://`. When port is `443`, scheme defaults to `https://`.
2. **Given** no environment variable `NSO_PASSWORD`, **When** script runs, **Then** it prompts via `getpass()` or falls back to standard DevNet sandbox credentials without hardcoded sensitive strings in source code.
3. **Given** `dist-rtr01` as target, **When** running scenarios, **Then** interface retrieval, provisioning, sync checks, and teardown work seamlessly against the 9-node sandbox topology.

---

### User Story 4 - Test-Driven Quality & Offline Mock Verification (Priority: P2)

As a CI/CD pipeline or offline developer,  
I want full unit test coverage using offline mocks (`unittest.mock`),  
So that all device management, port blocking, and RESTCONF operations can be tested without active VPN access.

**Why this priority**: Constitution Principle V mandates automated offline tests runnable without physical hardware.

**Independent Test**: `uv run python -m unittest discover tests` runs in under 5 seconds with 100% pass rate.

**Acceptance Scenarios**:
1. All unit tests in `tests/test_nso.py`, `tests/test_device_manager.py`, and `tests/test_port_blocking.py` pass without network connectivity.
2. `ruff check .` passes with zero lint errors.

---

### User Story 5 - NetDevOps GitLab Git Remote Configuration & Push (Priority: P2)

As an engineer collaborating on the sandbox NetDevOps stack,  
I want the repository configured with the sandbox GitLab remote (`http://10.10.20.54:8080`) and all modifications committed and pushed,  
So that CI/CD pipelines and web IDEs within the sandbox can access the updated codebase.

**Acceptance Scenarios**:
1. Remote `gitlab` configured with target URL.
2. Git working tree clean, with all new packages, tests, and documentation staged and committed.
3. Changes pushed to the GitLab repository.

---

## 3. Functional Requirements

- **FR-001**: Package `nso_device_manager/` MUST contain `device_manager.py`, `README.md`, and `requirements.txt`.
- **FR-002**: `device_manager.py` MUST support `--action {add,edit,delete,rename,sync-from,fetch-keys,list}`.
- **FR-003**: Package `nso_port_blocking/` MUST contain `port_blocker.py`, `README.md`, and `requirements.txt`.
- **FR-004**: `port_blocker.py` MUST support `--action {block-port,unblock-port,shut-interface,enable-interface,status}`.
- **FR-005**: All scripts MUST accept credentials via environment variables (`NSO_HOST`, `NSO_PORT`, `NSO_USER`, `NSO_PASSWORD`, `NSO_SCHEME`, `RESTCONF_DEVICE`) or CLI flags.
- **FR-006**: NO plaintext passwords or API keys shall be hardcoded into any Python script.
- **FR-007**: Default target device MUST be parameterized and default to `dist-rtr01`.
- **FR-008**: `PACKAGES.md` MUST be updated to document packages 21 (`nso_device_manager/`) and 22 (`nso_port_blocking/`).
- **FR-009**: All network requests MUST specify explicit HTTP timeouts (minimum 15s, maximum 60s).

---

## 4. Edge Cases & Safety Constraints

- **Duplicate Device Addition**: Adding a device that already exists in NSO CDB must return a clear message or allow update/override with `--force`.
- **Non-Existent Device Deletion**: Deleting a device that does not exist must handle HTTP 404 gracefully without crashing.
- **Port Blocking on Inactive Interface**: Applying an ACL to an interface that does not exist in CDB must report a descriptive error before committing.
- **Rollback Safety**: Any failed port blocking or ACL push must offer automated rollback to prevent inadvertent network isolation.
- **Offline / Sandbox Proxy Isolation**: Code must operate reliably in both sandboxed mock mode and live VPN connected mode.
