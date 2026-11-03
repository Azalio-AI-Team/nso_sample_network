# Tasks: NSO Multi-Platform Topology Configuration & Network Orchestration

**Branch**: `002-nso-topology-config` | **Spec**: [specs/002-nso-topology-config/spec.md](./spec.md) | **Plan**: [specs/002-nso-topology-config/plan.md](./plan.md)

---

## Phase 1: Foundational Core Modernization (User Story 2)

- [x] **T001**: [US2] Update `nso_client.py`:
  - Enhance `set_loopback_interface` to detect device NED / OS type (`cisco-ios-cli`, `cisco-iosxr-cli`, `cisco-nx-cli`).
  - Implement platform-specific YANG payload formatting:
    - IOS-XE: `tailf-ned-cisco-ios:Loopback` with `primary.address` and `mask`.
    - IOS-XR: `tailf-ned-cisco-ios-xr:Loopback` with `ipv4.address.ip` and `mask`.
    - NX-OS: `tailf-ned-cisco-nx:loopback` with `ipaddr` (CIDR notation).
  - Enhance `delete_loopback_interface` to support IOS-XR and NX-OS paths.
  - Add `update_interface_description()` supporting multi-NED interface paths.
- [x] **T002**: [US2] Update `nso_scenarios.py`:
  - Add `scenario_12_multi_platform_loopbacks()` configuring loopbacks across `core-rtr01` (IOS-XR), `dist-rtr01` (IOS-XE), and `dist-sw01` (NX-OS).
  - Add `scenario_13_topology_audit()` displaying topology inventory and operational sync states.
- [x] **T003**: [US2] Update `main.py` to include new topology scenarios in the execution suite.

---

## Phase 2: Standalone NSO Topology Manager Package (User Story 1)

- [x] **T004**: [P] [US1] Create `nso_topology_manager/requirements.txt` (`requests`, `urllib3`).
- [x] **T005**: [US1] Author `nso_topology_manager/topology_models.py`:
  - Define data structures for DevNet Sandbox 9-node topology (`TOPOLOGY_NODES`), roles (Core, Dist, Access, Firewall, WAN), NED IDs, and interconnect maps.
- [x] **T006**: [US1] Author `nso_topology_manager/topology_manager.py`:
  - CLI argument parser supporting `--action {audit,configure-loopback,update-interface,deploy-baseline,verify-sync,teardown}`, `--device`, `--loopback-id`, `--ip`, `--netmask`, `--description`, `--json`.
  - Implement `NSOTopologyManager` class with multi-platform payload dispatch, error handling, and rollbacks.
- [x] **T007**: [P] [US1] Author `nso_topology_manager/README.md` with complete architecture diagram, topology table, CLI usage, and rollback procedures.

---

## Phase 3: Offline Mock Unit Testing (User Story 4)

- [x] **T008**: [US4] Author `tests/test_topology_manager.py`:
  - 100% offline mock tests covering:
    - Topology audit and role mapping.
    - Multi-platform loopback creation (IOS-XE, IOS-XR, NX-OS).
    - Multi-platform interface description update.
    - Sync check verification and rollback.
- [x] **T009**: [US4] Update `tests/test_nso.py` to cover multi-platform client methods.

---

## Phase 4: Documentation & Quality Convergence

- [x] **T010**: [US4] Run `uv run python -m unittest discover tests` and ensure 100% test pass rate.
- [x] **T011**: [US4] Run `ruff check .` to enforce clean code quality.
- [x] **T012**: Update `PACKAGES.md` to catalog Package 23 (`nso_topology_manager/`).
- [x] **T013**: Update `README.md` with the new topology orchestration capabilities.
