# Cisco NSO Port Blocker (`nso_port_blocking`)

This standalone package provides dual-mode network port blocking and traffic isolation across Cisco IOS / IOS-XE devices managed by Cisco Network Services Orchestrator (NSO) via RFC 8040 RESTCONF.

---

## 1. Capabilities

1. **Layer 4 ACL Port Filtering**:
   - Provisions extended Access Control Lists (ACLs) denying specific TCP or UDP destination ports (e.g., Telnet 23, HTTP 80, SMB 445, RDP 3389).
   - Generates explicit deny rules followed by permit rules to avoid breaking legitimate traffic.
   - Binds the ACL to target interfaces (`GigabitEthernet`, `FastEthernet`) in the specified direction (`in` or `out`).
   - Cleanly rolls back / deletes ACLs upon unblock requests.

2. **Interface Administrative Control**:
   - Administratively disables (`shutdown`) physical or routed interfaces.
   - Restores interface links (`no shutdown`) safely.
   - Queries real-time interface configuration status from NSO CDB.

---

## 2. Prerequisites & Installation

```bash
cd nso_port_blocking
pip install -r requirements.txt
```

---

## 3. Environment Configuration

- `NSO_HOST`: IP or hostname of NSO (default: `10.10.20.49`).
- `NSO_PORT`: RESTCONF port (default: `8080` for private lab IP, `443` for public sandbox).
- `NSO_USER`: NSO username (default: `developer`).
- `NSO_PASSWORD`: NSO password (prompted or read from environment).
- `RESTCONF_DEVICE`: Default target device (default: `dist-rtr01`).

---

## 4. CLI Usage Examples

### Block Inbound Telnet (Port 23) via ACL on GigabitEthernet0/1
```bash
python port_blocker.py \
  --action block-port \
  --device dist-rtr01 \
  --interface-type GigabitEthernet \
  --interface 0/1 \
  --port-number 23 \
  --protocol tcp \
  --direction in
```

### Unblock Port 23 and Clean Up ACL
```bash
python port_blocker.py \
  --action unblock-port \
  --device dist-rtr01 \
  --interface-type GigabitEthernet \
  --interface 0/1 \
  --port-number 23 \
  --protocol tcp
```

### Administratively Disable an Interface (`shutdown`)
```bash
python port_blocker.py \
  --action shut-interface \
  --device dist-rtr01 \
  --interface-type GigabitEthernet \
  --interface 0/2
```

### Re-Enable an Interface (`no shutdown`)
```bash
python port_blocker.py \
  --action enable-interface \
  --device dist-rtr01 \
  --interface-type GigabitEthernet \
  --interface 0/2
```

### Inspect Interface Status
```bash
python port_blocker.py \
  --action status \
  --device dist-rtr01 \
  --interface-type GigabitEthernet \
  --interface 0/1
```

### List All Configured Extended ACLs
```bash
python port_blocker.py --action list-acls --device dist-rtr01
```

---

## 5. Python API Usage

```python
from nso_port_blocking.port_blocker import NSOPortBlocker

blocker = NSOPortBlocker(host="10.10.20.49", port=8080)

# Block TCP 80
ok, msg = blocker.block_port_flow(
    device_name="dist-rtr01",
    port_number=80,
    protocol="tcp",
    interface_type="GigabitEthernet",
    interface_name="0/1",
)
print(msg)
```
