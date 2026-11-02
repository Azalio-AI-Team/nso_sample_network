# Tasks: NSO Device Lifecycle Management and Port Blocking Packages

**Input**: Design documents from `specs/001-nso-mgmt-portblock/` (`spec.md`, `plan.md`)  
**Prerequisites**: `spec.md`, `plan.md`  
**Organization**: Tasks are grouped by User Story and execution phase.

---

## Phase 1: Foundational Framework Modernization (User Story 3)

- [x] **T001**: [US3] Modernize `nso_client.py`:
  - Implement auto-scheme detection (`http` for port 8080, `https` for port 443, or `NSO_SCHEME`).
  - Eliminate hardcoded plaintext passwords, falling back cleanly to environment variables or `getpass()`.
  - Add RESTCONF helper methods for device lifecycle: `add_device()`, `delete_device()`, `edit_device()`, `rename_device()`, `sync_from()`, `fetch_host_keys()`.
  - Add RESTCONF helper methods for port blocking: `block_port_acl()`, `unblock_port_acl()`, `shutdown_interface()`, `enable_interface()`.
- [x] **T002**: [US3] Update `nso_scenarios.py`:
  - Parameterize target device to `RESTCONF_DEVICE` (default `dist-rtr01`, fallback `dist-rtr00`).
  - Add new scenario methods: `scenario_9_device_lifecycle()`, `scenario_10_port_blocking_acl()`, `scenario_11_interface_shutdown()`.
- [x] **T003**: [US3] Update `tests/test_nso.py`:
  - Make test device parameter dynamic (`RESTCONF_DEVICE`).
  - Relax fleet count check to `>= 9` devices to support both reservable and always-on sandboxes.
  - Implement offline mock test cases for the modernized NSOClient methods.

---

## Phase 2: Standalone NSO Device Manager Package (User Story 1)

- [x] **T004**: [P] [US1] Create `nso_device_manager/requirements.txt` with dependencies (`requests`, `urllib3`).
- [x] **T005**: [US1] Author `nso_device_manager/device_manager.py`:
  - Provide full CLI argument parser (`--action {add,edit,delete,rename,sync-from,fetch-keys,list}`, `--device`, `--ip`, `--port`, `--protocol`, `--authgroup`, `--ned-id`, `--description`).
  - Implement `NSODeviceManager` class with robust RESTCONF operations, explicit timeouts, and status handling.
  - Support dry-run and JSON output.
- [x] **T006**: [P] [US1] Author `nso_device_manager/README.md` with complete documentation, architecture diagrams, CLI examples, and parameter references.
- [x] **T007**: [US1] Author `tests/test_device_manager.py` with 100% offline unit tests using `unittest.mock`.

---

## Phase 3: Standalone NSO Port Blocking Package (User Story 2)

- [x] **T008**: [P] [US2] Create `nso_port_blocking/requirements.txt` with dependencies (`requests`, `urllib3`).
- [x] **T009**: [US2] Author `nso_port_blocking/port_blocker.py`:
  - Provide CLI argument parser (`--action {block-port,unblock-port,shut-interface,enable-interface,status}`, `--device`, `--interface`, `--port-number`, `--protocol {tcp,udp,any}`, `--direction {in,out}`).
  - Implement `NSOPortBlocker` class for ACL-based filtering and interface shutdown/no-shutdown.
  - Provide rollback safety and error diagnostics.
- [x] **T010**: [P] [US2] Author `nso_port_blocking/README.md` with architecture, usage examples, ACL payload structures, and verification steps.
- [x] **T011**: [US2] Author `tests/test_port_blocking.py` with 100% offline unit tests using `unittest.mock`.

---

## Phase 4: Quality Verification & Documentation Convergence (User Story 4 & 5)

- [x] **T012**: [US4] Execute full test suite via `python -m unittest discover tests` and verify 100% pass rate.
- [x] **T013**: [US4] Run code quality checks (`ruff check .`) and resolve any formatting/typing warnings.
- [x] **T014**: [US5] Update `PACKAGES.md` to catalog packages 21 (`nso_device_manager/`) and 22 (`nso_port_blocking/`).
- [x] **T015**: [US5] Update `README.md` with updated package inventory and usage instructions.

---

## Phase 5: Git Remote Configuration, Commit & GitLab Push (User Story 5)

- [ ] **T016**: [US5] Configure GitLab remote (`gitlab`) pointing to `http://10.10.20.54:8080/root/python_code_samples_network.git` (or devadmin credentials as appropriate).
- [ ] **T017**: [US5] Stage all modified and new files (`.gitignore` ensures no secrets or `.env` are added).
- [ ] **T018**: [US5] Commit with descriptive conventional message.
- [ ] **T019**: [US5] Push to connected GitLab environment.
