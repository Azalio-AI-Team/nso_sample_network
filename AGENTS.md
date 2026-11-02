# Agent & Developer Guidelines: Python Code Samples Network

This repository contains network programmability and automation code samples across Cisco technologies (RESTCONF, NETCONF, Cisco IOS-XE, Cisco NSO, Netmiko, SNMP, and Python-based network scenarios).

This project is configured for **Spec-Driven Development (SDD)** using **GitHub Spec Kit** with multi-agent integrations for **Antigravity (`agy`)** and **Claude Code (`claude`)**.

---

## 1. Spec-Driven Development (SDD) with Spec Kit

Spec Kit provides a structured, disciplined development pipeline where specifications and core architectural rules act as the source of truth.

### Core Constitution
- **Location**: [`.specify/memory/constitution.md`](.specify/memory/constitution.md)
- **Purpose**: Establishes non-negotiable principles, security rules, network I/O resilience requirements, and governance. All specifications, technical plans, tasks, and generated code MUST comply with the project constitution.

### SDD Workflow & Available Skills
Both Antigravity (`.agents/skills/`) and Claude Code (`.claude/skills/`) integrations are configured with the following command skills:

1. **`/speckit-constitution`**: Establish, audit, or amend the project constitution and core principles.
2. **`/speckit-specify`**: Create a baseline specification (`spec.md`) focusing on user stories, goals, and acceptance criteria.
3. **`/speckit-clarify`** *(Optional)*: Interactively resolve ambiguities and edge cases before technical planning.
4. **`/speckit-plan`**: Formulate an implementation blueprint (`plan.md`) defining architecture, API endpoints, schema models, and file impacts.
5. **`/speckit-checklist`** *(Optional)*: Generate quality and requirements checklists to validate the plan.
6. **`/speckit-tasks`**: Generate an ordered, dependency-aware task list (`tasks.md`) broken into discrete, testable work units.
7. **`/speckit-implement`**: Execute tasks step-by-step against tests and validation criteria.
8. **`/speckit-converge`**: Evaluate the codebase state against the active specification and append remaining work items.

---

## 2. Dev Environment & Setup

- **Python Version**: Python 3.9+ (Python 3.12 / 3.14 compatible).
- **Virtual Environment**:
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  python -m pip install -U pip
  ```
- **Modern uv Workflow**:
  ```bash
  uv sync
  uv run pytest
  ```
- **Standalone Sample Folders**: Each network sample directory is self-contained. Navigate to the folder, read its `README.md`, install dependencies, and run:
  ```bash
  cd <sample-folder>
  [ -f requirements.txt ] && python -m pip install -r requirements.txt
  python <script>.py
  ```
- **Common Packages**: `requests`, `ncclient`, `netmiko`, `pysnmp`, `pytest`.

---

## 3. Secrets & Device Configuration (NON-NEGOTIABLE)

**Never commit real credentials, passwords, tokens, or private endpoints.**

- Scripts must prioritize configuration via environment variables:
  - `RESTCONF_HOST` / `NSO_HOST`
  - `RESTCONF_USER` / `NSO_USER`
  - `RESTCONF_PASSWORD` / `DEVNET_RESTCONF_PASSWORD` / `NSO_PASSWORD`
  - `RESTCONF_DEVICE` (default: `dist-rtr00`)
- If credentials are not present in the environment, scripts must prompt securely via `getpass()`.
- Default values must only point to public Cisco DevNet sandboxes.
- Never commit `.env` or personal credential files.

---

## 4. Testing & Quality Verification

- **Offline Unit & Mock Tests**:
  Network scripts should include unit tests with mocked responses (e.g. `unittest.mock` or `pytest-mock` for HTTP/RESTCONF and NETCONF calls) to allow verification without physical hardware:
  ```bash
  pytest tests/
  ```
- **DevNet Sandbox Smoke Tests**:
  Test against live devices using Cisco DevNet Sandbox:
  - https://devnetsandbox.cisco.com/DevNet
  - Cisco API Docs: https://developer.cisco.com/docs/
- **Static Checks & Linting**:
  ```bash
  ruff check .
  mypy --ignore-missing-imports .
  ```

---

## 5. Contribution & PR Instructions

- **PR Title Format**: `[sample-folder] <Short description>` (e.g. `[RESTCONF] support NSO device targeting`).
- **Scope**: Keep changes limited to one sample folder or one self-contained capability whenever possible.
- **Pre-Commit Checklist**:
  - Run modified scripts and automated unit tests.
  - Update folder `requirements.txt` if dependencies changed.
  - Update `README.md` within the affected folder.
  - Run `ruff check .` to ensure clean code style.
  - Verify no passwords, tokens, or internal IP addresses are committed.
