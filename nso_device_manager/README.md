# Cisco NSO Device Lifecycle Manager (`nso_device_manager`)

This standalone package provides programmatic and CLI-driven management of managed network devices within Cisco Network Services Orchestrator (NSO) via the RFC 8040 RESTCONF API.

---

## 1. Capabilities

- **Add Devices**: Onboard new devices with custom authgroups, ports, protocols (SSH/Telnet), and Network Element Drivers (NEDs).
- **Edit Devices**: Update IP addresses, ports, authgroups, or descriptions on live NSO CDB device instances.
- **Rename Devices**: Atomically migrate configuration and state from one device identifier to another.
- **Delete Devices**: Safely decommission and purge devices from NSO CDB.
- **Device Operations**: Trigger `sync-from`, `fetch-ssh-host-keys`, and `check-sync` operational actions.

---

## 2. Supported Platforms & NEDs

| Platform | Shorthand | Full NED ID |
|---|---|---|
| **Cisco IOS / IOS-XE** | `ios` | `tailf-ned-cisco-ios-id:cisco-ios-cli-6.109` |
| **Cisco IOS-XR** | `iosxr` | `tailf-ned-cisco-iosxr-id:cisco-iosxr-cli-7.65` |
| **Cisco NX-OS** | `nx` | `tailf-ned-cisco-nx-id:cisco-nx-cli-5.27` |
| **Cisco ASA** | `asa` | `tailf-ned-cisco-asa-id:cisco-asa-cli-6.18` |

---

## 3. Installation & Prerequisites

```bash
cd nso_device_manager
pip install -r requirements.txt
```

---

## 4. Environment Variables

- `NSO_HOST`: IP address or FQDN of the Cisco NSO controller (default: `10.10.20.49`).
- `NSO_PORT`: RESTCONF port (default: `8080` for private lab IP, `443` for public sandbox).
- `NSO_USER`: NSO username (default: `developer`).
- `NSO_PASSWORD`: NSO password (prompted or read from environment).
- `NSO_SCHEME`: Transport scheme (`http` or `https`).

---

## 5. CLI Usage Examples

### List All Managed Devices
```bash
python device_manager.py --action list
```

### Onboard / Add a New IOS Device
```bash
python device_manager.py \
  --action add \
  --device lab-rtr99 \
  --ip 10.10.20.199 \
  --port 23 \
  --authgroup default \
  --ned-id ios \
  --protocol telnet
```

### Update Device Attributes
```bash
python device_manager.py \
  --action edit \
  --device lab-rtr99 \
  --description "Lab distribution router provisioned via SDD"
```

### Rename a Device
```bash
python device_manager.py \
  --action rename \
  --device lab-rtr99 \
  --new-name lab-rtr100
```

### Fetch SSH Host Keys and Synchronize
```bash
python device_manager.py --action fetch-keys --device lab-rtr100
python device_manager.py --action sync-from --device lab-rtr100
```

### Decommission / Delete a Device
```bash
python device_manager.py --action delete --device lab-rtr100
```

---

## 6. Python API Import Example

```python
from nso_device_manager.device_manager import NSODeviceManager

manager = NSODeviceManager(host="10.10.20.49", port=8080, username="developer")
status, resp = manager.add_device(
    name="lab-rtr01",
    address="10.10.20.190",
    ned_id="ios",
)
print(f"Status: {status}")
```
