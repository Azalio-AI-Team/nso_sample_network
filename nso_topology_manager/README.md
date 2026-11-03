# Cisco NSO Topology Manager Package (`nso_topology_manager`)

A dedicated, standalone network topology orchestration and configuration package for Cisco Network Services Orchestrator (NSO / NCS). Built to model, inspect, configure, and synchronize multi-tier network topologies spanning **Cisco IOS-XE**, **Cisco IOS-XR**, **Cisco Nexus NX-OS**, and **Cisco ASA** firewalls via RFC 8040 RESTCONF.

Target Environment: [Cisco DevNet Reservable NSO Sandbox](https://developer.cisco.com/sandbox/detail/nso-sandbox).

---

## 1. Network Topology Architecture

The package models the complete 9-node Cisco DevNet Sandbox topology across 6 operational network tiers:

| Tier | Device Name | Platform OS | IP Address | NED Package ID | Primary Role |
|:---|:---|:---|:---|:---|:---|
| **Core** | `core-rtr01` | Cisco IOS-XR | `10.10.20.173` | `cisco-iosxr-cli-7.65` | Primary Core Backbone Router |
| **Core** | `dev-core-rtr01` | Cisco IOS-XR | `10.10.20.174` | `cisco-iosxr-cli-7.65` | Secondary Core Router |
| **Distribution** | `dist-rtr01` | Cisco IOS-XE | `10.10.20.175` | `cisco-ios-cli-6.109` | Primary Campus Distribution Router |
| **Distribution** | `dev-dist-rtr01` | Cisco IOS-XE | `10.10.20.176` | `cisco-ios-cli-6.109` | Secondary Campus Distribution Router |
| **DC Switching** | `dist-sw01` | Cisco NX-OS | `10.10.20.177` | `cisco-nx-cli-5.27` | Primary Data Center Nexus Switch |
| **DC Switching** | `dev-dist-sw01` | Cisco NX-OS | `10.10.20.178` | `cisco-nx-cli-5.27` | Secondary Data Center Nexus Switch |
| **Security** | `edge-firewall01` | Cisco ASA | `10.10.20.171` | `cisco-asa-cli-6.18` | Perimeter Firewall & NAT Gateway |
| **Access** | `edge-sw01` | Cisco IOS | `10.10.20.172` | `cisco-ios-cli-6.109` | Edge Campus Access Switch |
| **WAN / Gateway**| `internet-rtr01` | Cisco IOS-XE | `10.10.20.181` | `cisco-ios-cli-6.109` | Internet Gateway / Border Router |

---

## 2. Key Capabilities

1. **Multi-Platform Topology Audit**: Automatically queries NSO CDB, determines active device roles, platforms, and out-of-band sync states (`check-sync`).
2. **Multi-NED Loopback Orchestration**: Generates the exact platform-specific YANG data payloads:
   - IOS-XE: `tailf-ned-cisco-ios:Loopback` with primary address & mask
   - IOS-XR: `tailf-ned-cisco-ios-xr:Loopback` with IPv4 address & mask
   - NX-OS: `tailf-ned-cisco-nx:Loopback` with IP address & mask
3. **Atomic Interface Modification**: Updates interface descriptions and administrative status using RESTCONF `PATCH`.
4. **Baseline Deployment & Rollback**: Deploys baseline management loopbacks across all routers and switches in the topology with a single command, and provides atomic teardown rollback (`teardown-baseline`).
5. **Zero-Hardcoded-Secrets**: All credentials read dynamically from environment variables (`NSO_HOST`, `NSO_PORT`, `NSO_USER`, `NSO_PASSWORD`, `RESTCONF_HOST`) with fallback to interactive prompt.

---

## 3. Installation & CLI Usage

### Prerequisites
```bash
pip install -r requirements.txt
```

### CLI Command Reference

#### 1. Audit the Topology Fleet
```bash
python -m nso_topology_manager.topology_manager --action audit
```

#### 2. Configure a Loopback on Cisco IOS-XR (Core)
```bash
python -m nso_topology_manager.topology_manager \
  --action configure-loopback \
  --device core-rtr01 \
  --loopback-id 101 \
  --ip 172.16.0.1 \
  --description "Core Loopback 101"
```

#### 3. Configure a Loopback on Cisco NX-OS (Switch)
```bash
python -m nso_topology_manager.topology_manager \
  --action configure-loopback \
  --device dist-sw01 \
  --loopback-id 101 \
  --ip 172.16.2.1 \
  --description "Nexus Switch Loopback 101"
```

#### 4. Update Interface Description
```bash
python -m nso_topology_manager.topology_manager \
  --action update-interface \
  --device dist-rtr01 \
  --interface-type GigabitEthernet \
  --interface-name "0/1" \
  --description "Uplink to core-rtr01"
```

#### 5. Deploy Topology Baseline
```bash
python -m nso_topology_manager.topology_manager --action deploy-baseline --loopback-id 100
```

#### 6. Rollback / Teardown Topology Baseline
```bash
python -m nso_topology_manager.topology_manager --action teardown-baseline --loopback-id 100
```

#### 7. Verify Sync State
```bash
python -m nso_topology_manager.topology_manager --action verify-sync
```

---

## 4. Verification & Testing

Unit tests for `nso_topology_manager` are 100% offline using Python's `unittest.mock`:
```bash
uv run python -m unittest tests/test_topology_manager.py
```
