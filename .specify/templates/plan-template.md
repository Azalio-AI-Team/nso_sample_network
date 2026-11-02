# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]

**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

**Language/Version**: [e.g., Python 3.9+, Python 3.14 via uv]

**Primary Dependencies**: [e.g., requests, ncclient, netmiko, pysnmp, pytest]

**Network Protocols/Target APIs**: [e.g., RESTCONF (RFC 8040), NETCONF (RFC 6241), SNMP (v2c/v3), Cisco IOS-XE CLI, Cisco NSO CDB]

**Testing**: [e.g., pytest tests/ with mocked responses, offline unit verification]

**Target Platform/Devices**: [e.g., Cisco IOS-XE (Cat9300, CSR1000v), Cisco NSO (tailf-ncs), APIC-EM, Cisco ACI]

**Project Type**: [Network automation sample script / CLI scenario / SDK library]

**Security & Secrets**: [Environment variables (RESTCONF_HOST, RESTCONF_USER, DEVNET_RESTCONF_PASSWORD), no hardcoded credentials]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [ ] Standalone sample principle preserved (clear folder, README, requirements).
- [ ] No hardcoded passwords, tokens, or private device endpoints.
- [ ] Explicit request timeouts and structured error handling on stderr.
- [ ] Offline mock/unit test strategy included.
- [ ] Code formatted and typed cleanly (ruff, mypy).

## Affected Components & Blast Radius

| Component / Package | Nature of Change (New/Modified/Deprecated) | Target Network Devices / Sandboxes | Blast Radius & Rollback Mechanism |
|---|---|---|---|
| [e.g., RESTCONF/] | [e.g., Modified endpoint handling] | [e.g., dist-rtr00 on NSO] | [e.g., Isolated to Loopback interface; DELETE undo script] |

## Network Test Strategy & Generated Payloads

### 1. Test Strategy (Offline Mocks vs Sandbox)
- **Offline Mocking**: [Detail how requests/ncclient/netmiko will be mocked in unit tests]
- **Live Device Smoke Test**: [Target DevNet sandbox endpoint and verification procedure]

### 2. Generated Payloads & Contracts

#### A. Request Payload (RESTCONF JSON / NETCONF XML / CLI commands)
```json
// Example RESTCONF payload
{
  "tailf-ned-cisco-ios:Loopback": {
    "name": "100",
    "ip": {
      "address": {
        "primary": {
          "address": "10.100.100.1",
          "mask": "255.255.255.255"
        }
      }
    }
  }
}
```

#### B. Expected Response & Status Codes
- **Success Criteria**: HTTP 200/201/204 or `<ok/>` RPC reply
- **Failure Cases Handled**: HTTP 400 (Malformed payload), 401/403 (Auth failure), 404 (Missing container), 409 (Resource conflict), 500 (Controller error)

## Pre-Implementation Human Review Gate

> **CRITICAL**: Before proceeding to code generation (`/speckit-tasks` and `/speckit-implement`), the engineer MUST review and sign off on:
> 1. Planned file modifications and impacted packages.
> 2. Network test payloads and expected device states.
> 3. Rollback / idempotency safety guards.

- [ ] Planned code modifications reviewed and approved by Human Engineer.
- [ ] Network payloads verified against YANG data models / device capabilities.
- [ ] Offline unit test suite prepared with appropriate mocks.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| [e.g., None] | [N/A] | [N/A] |
