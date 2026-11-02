#!/usr/bin/env python3
"""
Cisco NSO Device Lifecycle Manager.
Provides programmatic and CLI-driven management of managed devices in Cisco NSO CDB:
- Onboard / Add new devices
- Modify / Edit device attributes (IP, port, authgroup, description)
- Rename existing devices
- Decommission / Delete devices
- Trigger operational synchronization (sync-from, fetch-ssh-host-keys, check-sync)
"""

import argparse
import json
import os
import sys
import urllib3
import requests
from typing import Any, Dict, Optional, Tuple

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Supported standard Cisco NED IDs
DEFAULT_NED_MAP = {
    "ios": "tailf-ned-cisco-ios-id:cisco-ios-cli-6.109",
    "iosxr": "tailf-ned-cisco-iosxr-id:cisco-iosxr-cli-7.65",
    "nx": "tailf-ned-cisco-nx-id:cisco-nx-cli-5.27",
    "asa": "tailf-ned-cisco-asa-id:cisco-asa-cli-6.18",
}


class NSODeviceManager:
    """Manager for Cisco NSO device inventory and lifecycle operations."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        scheme: Optional[str] = None,
    ):
        self.host = host or os.getenv("NSO_HOST", "10.10.20.49")
        
        if port is not None:
            self.port = port
        elif os.getenv("NSO_PORT"):
            self.port = int(os.environ["NSO_PORT"])
        elif self.host.startswith("10.10.20."):
            self.port = 8080
        else:
            self.port = 443

        self.username = username or os.getenv("NSO_USER", "developer")
        self.password = password or os.getenv("NSO_PASSWORD") or os.getenv("DEVNET_RESTCONF_PASSWORD") or ""

        if scheme:
            self.scheme = scheme.lower().rstrip(":/")
        elif os.getenv("NSO_SCHEME"):
            self.scheme = os.environ["NSO_SCHEME"].lower().rstrip(":/")
        elif self.port in (80, 8080):
            self.scheme = "http"
        else:
            self.scheme = "https"

        self.base_data_url = f"{self.scheme}://{self.host}:{self.port}/restconf/data"
        self.base_ops_url = f"{self.scheme}://{self.host}:{self.port}/restconf/operations"

        self.session = requests.Session()
        if self.username:
            self.session.auth = (self.username, self.password)
        self.session.verify = False
        self.session.headers.update({
            "Content-Type": "application/yang-data+json",
            "Accept": "application/yang-data+json",
        })

    def _request(
        self,
        method: str,
        path: str,
        is_operation: bool = False,
        data: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
    ) -> requests.Response:
        base = self.base_ops_url if is_operation else self.base_data_url
        clean_path = path.lstrip("/")
        url = f"{base}/{clean_path}"
        try:
            return self.session.request(
                method=method,
                url=url,
                json=data if data is not None else None,
                timeout=timeout,
            )
        except requests.exceptions.RequestException as err:
            sys.stderr.write(f"RESTCONF Request Error ({url}): {err}\n")
            raise

    def list_devices(self) -> Tuple[int, Any]:
        """List all devices currently managed in NSO."""
        resp = self._request("GET", "tailf-ncs:devices/device?fields=name;address;port;authgroup;device-type;state")
        return resp.status_code, resp.json() if resp.status_code == 200 else resp.text

    def get_device(self, name: str) -> Tuple[int, Any]:
        """Retrieve full details of a specific device."""
        resp = self._request("GET", f"tailf-ncs:devices/device={name}")
        return resp.status_code, resp.json() if resp.status_code == 200 else resp.text

    def add_device(
        self,
        name: str,
        address: str,
        port: int = 23,
        authgroup: str = "default",
        ned_id: str = "tailf-ned-cisco-ios-id:cisco-ios-cli-6.109",
        protocol: str = "telnet",
        admin_state: str = "unlocked",
    ) -> Tuple[int, str]:
        """Add a new device to NSO CDB."""
        # Resolve shorthand NED names
        resolved_ned = DEFAULT_NED_MAP.get(ned_id.lower(), ned_id)
        payload = {
            "tailf-ncs:device": [
                {
                    "name": name,
                    "address": address,
                    "port": int(port),
                    "authgroup": authgroup,
                    "device-type": {
                        "cli": {
                            "ned-id": resolved_ned,
                            "protocol": protocol,
                        }
                    },
                    "state": {
                        "admin-state": admin_state,
                    },
                }
            ]
        }
        resp = self._request("POST", "tailf-ncs:devices", data=payload)
        return resp.status_code, resp.text

    def edit_device(
        self,
        name: str,
        address: Optional[str] = None,
        port: Optional[int] = None,
        authgroup: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Tuple[int, str]:
        """Update fields on an existing device."""
        device_data: Dict[str, Any] = {"name": name}
        if address is not None:
            device_data["address"] = address
        if port is not None:
            device_data["port"] = int(port)
        if authgroup is not None:
            device_data["authgroup"] = authgroup
        if description is not None:
            device_data["description"] = description

        payload = {"tailf-ncs:device": device_data}
        resp = self._request("PATCH", f"tailf-ncs:devices/device={name}", data=payload)
        return resp.status_code, resp.text

    def rename_device(self, old_name: str, new_name: str) -> Tuple[int, str]:
        """Rename device in NSO CDB by migrating config and removing old entry."""
        status, dev_config = self.get_device(old_name)
        if status != 200 or not isinstance(dev_config, dict):
            return status, f"Device '{old_name}' not found or unreachable"

        dev_list = dev_config.get("tailf-ncs:device", [])
        if not dev_list:
            return 404, f"Device '{old_name}' not found"

        dev_entry = dict(dev_list[0])
        dev_entry["name"] = new_name

        put_resp = self._request(
            "PUT",
            f"tailf-ncs:devices/device={new_name}",
            data={"tailf-ncs:device": dev_entry},
        )
        if put_resp.status_code not in (200, 201, 204):
            return put_resp.status_code, f"Failed creating device '{new_name}': {put_resp.text}"

        del_status, _ = self.delete_device(old_name)
        return 200 if del_status in (200, 204) else del_status, f"Device successfully renamed: {old_name} -> {new_name}"

    def delete_device(self, name: str) -> Tuple[int, str]:
        """Delete device from NSO CDB."""
        resp = self._request("DELETE", f"tailf-ncs:devices/device={name}")
        return resp.status_code, resp.text

    def sync_from(self, name: str) -> Tuple[int, Any]:
        """Trigger sync-from RPC action."""
        resp = self._request("POST", f"tailf-ncs:devices/device={name}/sync-from", is_operation=True, data={})
        return resp.status_code, resp.json() if resp.status_code == 200 else resp.text

    def fetch_host_keys(self, name: str) -> Tuple[int, Any]:
        """Fetch SSH host keys for device."""
        resp = self._request("POST", f"tailf-ncs:devices/device={name}/ssh/fetch-host-keys", is_operation=True, data={})
        return resp.status_code, resp.json() if resp.status_code == 200 else resp.text

    def check_sync(self, name: str) -> Tuple[int, Any]:
        """Check sync state between NSO and device."""
        resp = self._request("POST", f"tailf-ncs:devices/device={name}/check-sync", is_operation=True, data={})
        return resp.status_code, resp.json() if resp.status_code == 200 else resp.text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Cisco NSO Device Lifecycle Manager CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--action",
        required=True,
        choices=["list", "get", "add", "edit", "rename", "delete", "sync-from", "fetch-keys", "check-sync"],
        help="Device lifecycle action to execute",
    )
    parser.add_argument("--device", help="Target device name in NSO CDB")
    parser.add_argument("--new-name", help="New device name (for rename action)")
    parser.add_argument("--ip", help="Device IP address")
    parser.add_argument("--port", type=int, default=23, help="Device port (default: 23)")
    parser.add_argument("--authgroup", default="default", help="NSO authgroup name (default: default)")
    parser.add_argument(
        "--ned-id",
        default="ios",
        help="NSO NED ID or shorthand: ios, iosxr, nx, asa (default: ios)",
    )
    parser.add_argument("--protocol", default="telnet", choices=["telnet", "ssh"], help="Transport protocol")
    parser.add_argument("--description", help="Device description string")
    parser.add_argument("--host", help="NSO server hostname/IP")
    parser.add_argument("--port-nso", type=int, help="NSO RESTCONF port")
    parser.add_argument("--user", help="NSO username")
    parser.add_argument("--password", help="NSO password")
    parser.add_argument("--scheme", choices=["http", "https"], help="HTTP transport scheme")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    manager = NSODeviceManager(
        host=args.host,
        port=args.port_nso,
        username=args.user,
        password=args.password,
        scheme=args.scheme,
    )

    action = args.action

    if action == "list":
        status, data = manager.list_devices()
        if status == 200 and isinstance(data, dict):
            devices = data.get("tailf-ncs:device", [])
            print(f"=== Cisco NSO Managed Devices ({len(devices)} total) ===")
            print(f"{'NAME':<20} {'ADDRESS':<18} {'PORT':<6} {'AUTHGROUP':<12}")
            print("-" * 60)
            for d in devices:
                print(f"{d.get('name', ''):<20} {d.get('address', ''):<18} {d.get('port', ''):<6} {d.get('authgroup', ''):<12}")
        else:
            print(f"Error ({status}): {data}")
            sys.exit(1)

    elif action == "get":
        if not args.device:
            parser.error("--device is required for 'get' action")
        status, data = manager.get_device(args.device)
        print(json.dumps(data, indent=2) if isinstance(data, dict) else f"Status {status}: {data}")

    elif action == "add":
        if not args.device or not args.ip:
            parser.error("--device and --ip are required for 'add' action")
        status, text = manager.add_device(
            name=args.device,
            address=args.ip,
            port=args.port,
            authgroup=args.authgroup,
            ned_id=args.ned_id,
            protocol=args.protocol,
        )
        if status in (200, 201, 204):
            print(f"Successfully added device '{args.device}' to NSO CDB (Status: {status})")
        else:
            print(f"Failed adding device '{args.device}' (Status: {status}): {text}")
            sys.exit(1)

    elif action == "edit":
        if not args.device:
            parser.error("--device is required for 'edit' action")
        status, text = manager.edit_device(
            name=args.device,
            address=args.ip,
            port=args.port if "--port" in sys.argv else None,
            authgroup=args.authgroup if "--authgroup" in sys.argv else None,
            description=args.description,
        )
        if status in (200, 204):
            print(f"Successfully edited device '{args.device}' (Status: {status})")
        else:
            print(f"Failed editing device '{args.device}' (Status: {status}): {text}")
            sys.exit(1)

    elif action == "rename":
        if not args.device or not args.new_name:
            parser.error("--device and --new-name are required for 'rename' action")
        status, text = manager.rename_device(args.device, args.new_name)
        if status in (200, 204):
            print(f"Successfully renamed device: {text}")
        else:
            print(f"Failed renaming device (Status: {status}): {text}")
            sys.exit(1)

    elif action == "delete":
        if not args.device:
            parser.error("--device is required for 'delete' action")
        status, text = manager.delete_device(args.device)
        if status in (200, 204):
            print(f"Successfully deleted device '{args.device}' from NSO CDB")
        else:
            print(f"Failed deleting device '{args.device}' (Status: {status}): {text}")
            sys.exit(1)

    elif action == "sync-from":
        if not args.device:
            parser.error("--device is required for 'sync-from' action")
        status, data = manager.sync_from(args.device)
        print(json.dumps(data, indent=2) if isinstance(data, dict) else f"Status {status}: {data}")

    elif action == "fetch-keys":
        if not args.device:
            parser.error("--device is required for 'fetch-keys' action")
        status, data = manager.fetch_host_keys(args.device)
        print(json.dumps(data, indent=2) if isinstance(data, dict) else f"Status {status}: {data}")

    elif action == "check-sync":
        if not args.device:
            parser.error("--device is required for 'check-sync' action")
        status, data = manager.check_sync(args.device)
        print(json.dumps(data, indent=2) if isinstance(data, dict) else f"Status {status}: {data}")


if __name__ == "__main__":
    main()
