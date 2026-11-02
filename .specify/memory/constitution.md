# Python Code Samples Network Constitution

## Core Principles

### I. Standalone Sample Architecture
Every network automation example must be self-contained within its own directory, including:
- A descriptive `README.md` explaining the workflow, architecture, and prerequisites.
- A minimal `requirements.txt` listing direct dependencies.
- Clear, well-documented entry point scripts with minimal coupling to sibling samples.
- Shared logic (e.g., NSO client utilities, mock helpers) must remain well-factored and documented.

### II. Secrets & Security Hygiene (NON-NEGOTIABLE)
Hardcoded credentials, API keys, private tokens, or device passwords MUST NEVER be committed to version control:
- Scripts MUST accept credentials from environment variables (`RESTCONF_HOST`, `RESTCONF_USER`, `RESTCONF_PASSWORD`, `NSO_HOST`, `DEVNET_RESTCONF_PASSWORD`, etc.) or prompt securely via `getpass()`.
- Default values must only point to public Cisco DevNet sandboxes with dummy credentials if required for local development.
- All secrets and credential files (`.env`, private keys) must be ignored via `.gitignore`.

### III. Spec-Driven Development (SDD) Lifecycle
Any new feature, scenario, or major script enhancement MUST strictly follow the Spec Kit development lifecycle:
1. **Constitution**: Establish and verify non-negotiable architectural principles (`constitution.md`).
2. **Specification**: Document user stories, requirements, and acceptance criteria (`/speckit-specify` -> `spec.md`).
3. **Planning**: Formulate technical architecture, API contracts, and file impact (`/speckit-plan` -> `plan.md`).
4. **Task Decomposition**: Break implementation into sequenced, testable work units (`/speckit-tasks` -> `tasks.md`).
5. **Implementation & Convergence**: Execute tasks iteratively against tests, converging on the approved spec (`/speckit-implement`, `/speckit-converge`).

### IV. Deterministic Network I/O & Resilient Error Handling
Network automation interacts with real devices, controllers (Cisco NSO, APIC-EM), and sandboxes that can experience latency, transient connectivity loss, or session aborts:
- Every network request (RESTCONF HTTP, NETCONF RPC, SSH Netmiko) MUST define explicit timeouts.
- Scripts must handle HTTP error codes (`raise_for_status()`) and network exceptions gracefully, reporting meaningful messages to `stderr` and returning standard non-zero exit codes.
- Responses should default to structured output (JSON/YANG data) or clean console output; avoid unparsed tracebacks and noisy logs.

### V. Test-First & Smoke Verification Gates
Reliability across varied network environments requires multi-tiered verification:
- **Unit & Mock Tests**: New automation logic, scenario handlers, and API wrappers must include automated mock/offline unit tests (using `pytest` or `unittest` with mock responses) runnable without active network access.
- **Integration & Smoke Tests**: Where DevNet sandboxes are available, live smoke verification should validate device reachability and payload compatibility before release.
- **Static Quality**: Scripts must pass code quality checks (`ruff check .`, `mypy --ignore-missing-imports`).

## Technology Standards & Tooling

### Python Runtime & Environment
- Target Python version: Python 3.9+ (supporting modern typing, async, and modern packaging).
- Package management: `pyproject.toml` and `uv.lock` for modern workspace workflows, with per-folder `requirements.txt` for standalone portability.
- Primary network libraries: `requests` for RESTCONF, `ncclient` for NETCONF, `netmiko` for CLI automation, `pysnmp` for SNMP operations.

### API & Protocol Conventions
- **RESTCONF**: RFC 8040 standard endpoints with `application/yang-data+json` media types. Support both direct Cisco IOS-XE native models and Cisco NSO device hierarchy (`/restconf/data/tailf-ncs:devices/device={device}/config`).
- **NETCONF**: RFC 6241 operations (`get-config`, `edit-config`, `copy-config`) with valid XML/YANG filter specifications.
- **CLI / SSH**: Netmiko handlers with robust prompt detection and config session rollback where supported.

## Development Workflow & Contribution Governance

### Contribution Conventions
- **PR Title Format**: `[sample-folder] <Short description>` (e.g., `[RESTCONF] support NSO device targeting`).
- **Scope**: Keep changes localized to the relevant sample directory or core module.
- **Review Gates**:
  1. Offline unit/mock tests pass.
  2. Static lint checks pass (`ruff check .`).
  3. No hardcoded credentials or sensitive tokens introduced.
  4. Updated documentation in the sample's `README.md`.

### Constitution Governance
- This constitution supersedes all informal development practices.
- Proposed modifications require:
  1. Documentation of the rationale and architectural impact.
  2. Semantic version bump:
     - **MAJOR**: Incompatible governance overhaul or principle removal.
     - **MINOR**: New principle, technological constraint, or expanded workflow gate.
     - **PATCH**: Clarifications, formatting, and non-semantic refinements.
  3. Amendment logging in the project history.

**Version**: 1.0.0 | **Ratified**: 2026-11-02 | **Last Amended**: 2026-11-02
