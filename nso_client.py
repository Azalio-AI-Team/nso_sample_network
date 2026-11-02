"""
Cisco NSO RESTCONF Client Helper Module.
Provides clean wrappers for querying devices, services, configuration,
managing device lifecycles (add, edit, rename, delete), port blocking (ACL, shutdown),
and running operational actions (check-sync, compare-config, sync-from, fetch-ssh-host-keys).
"""

import os
import urllib3
import requests
from typing import Any, Dict, Optional, Tuple

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class NSOClient:
    """RESTCONF client for Cisco Network Services Orchestrator (NSO)."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        scheme: Optional[str] = None,
    ):
        self.host = host or os.getenv("NSO_HOST", "sandbox-nso-1.cisco.com")
        
        # Default port: check env var, else infer from host (8080 for private lab IP, 443 for public sandbox)
        if port is not None:
            self.port = port
        elif os.getenv("NSO_PORT"):
            self.port = int(os.environ["NSO_PORT"])
        elif self.host.startswith("10.10.20."):
            self.port = 8080
        else:
            self.port = 443

        self.username = username or os.getenv("NSO_USER", "developer")
        # Strict zero-hardcoded-secrets: read from environment or empty default
        self.password = password or os.getenv("NSO_PASSWORD") or os.getenv("DEVNET_RESTCONF_PASSWORD") or ""

        # Scheme autodetection: if port is 8080 or 80, default to http; otherwise https
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

    def request(
        self,
        method: str,
        path: str,
        is_operation: bool = False,
        data: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
    ) -> requests.Response:
        """Execute a RESTCONF HTTP request with explicit timeout."""
        base = self.base_ops_url if is_operation else self.base_data_url
        clean_path = path.lstrip("/")
        url = f"{base}/{clean_path}"
        return self.session.request(
            method=method,
            url=url,
            json=data if data is not None else None,
            timeout=timeout,
        )

    # --- High-level NSO Query Methods ---

    def get_devices(self) -> Tuple[int, Any]:
        """Retrieve the list of all managed devices."""
        resp = self.request("GET", "tailf-ncs:devices/device?fields=name;address;port;authgroup;device-type")
        return resp.status_code, resp.json() if resp.status_code == 200 else resp.text

    def get_device(self, device_name: str) -> Tuple[int, Any]:
        """Retrieve a single device from NSO CDB."""
        resp = self.request("GET", f"tailf-ncs:devices/device={device_name}")
        return resp.status_code, resp.json() if resp.status_code == 200 else resp.text

    def get_services(self) -> Tuple[int, Any]:
        """Retrieve defined router services."""
        resp = self.request("GET", "router:router")
        return resp.status_code, resp.json() if resp.status_code == 200 else resp.text

    def get_device_interfaces(self, device_name: str) -> Tuple[int, Any]:
        """Retrieve interface configuration for a specific Cisco IOS device."""
        resp = self.request("GET", f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-ios:interface")
        return resp.status_code, resp.json() if resp.status_code == 200 else resp.text

    def get_loopback_interface(self, device_name: str, loopback_id: str) -> Tuple[int, Any]:
        """Retrieve details of a specific Loopback interface on a Cisco IOS device."""
        resp = self.request(
            "GET",
            f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-ios:interface/Loopback={loopback_id}"
        )
        return resp.status_code, resp.json() if resp.status_code == 200 else resp.text

    def set_loopback_interface(
        self,
        device_name: str,
        loopback_id: str,
        ip_address: str,
        netmask: str,
        description: str = "",
    ) -> Tuple[int, str]:
        """Create or replace a Loopback interface using PUT."""
        payload = {
            "tailf-ned-cisco-ios:Loopback": {
                "name": str(loopback_id),
                "description": description,
                "ip": {
                    "address": {
                        "primary": {
                            "address": ip_address,
                            "mask": netmask,
                        }
                    }
                },
            }
        }
        resp = self.request(
            "PUT",
            f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-ios:interface/Loopback={loopback_id}",
            data=payload,
        )
        return resp.status_code, resp.text

    def delete_loopback_interface(self, device_name: str, loopback_id: str) -> Tuple[int, str]:
        """Delete a Loopback interface from a device."""
        resp = self.request(
            "DELETE",
            f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-ios:interface/Loopback={loopback_id}"
        )
        return resp.status_code, resp.text

    # --- Device Lifecycle Management Methods (US1) ---

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
        """Add a new managed device to Cisco NSO CDB."""
        payload = {
            "tailf-ncs:device": [
                {
                    "name": name,
                    "address": address,
                    "port": port,
                    "authgroup": authgroup,
                    "device-type": {
                        "cli": {
                            "ned-id": ned_id,
                            "protocol": protocol,
                        }
                    },
                    "state": {
                        "admin-state": admin_state,
                    },
                }
            ]
        }
        resp = self.request("POST", "tailf-ncs:devices", data=payload)
        return resp.status_code, resp.text

    def edit_device(
        self,
        name: str,
        address: Optional[str] = None,
        port: Optional[int] = None,
        authgroup: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Tuple[int, str]:
        """Update configuration parameters of an existing device in NSO."""
        device_data: Dict[str, Any] = {"name": name}
        if address is not None:
            device_data["address"] = address
        if port is not None:
            device_data["port"] = port
        if authgroup is not None:
            device_data["authgroup"] = authgroup
        if description is not None:
            device_data["description"] = description

        payload = {"tailf-ncs:device": device_data}
        resp = self.request("PATCH", f"tailf-ncs:devices/device={name}", data=payload)
        return resp.status_code, resp.text

    def rename_device(self, old_name: str, new_name: str) -> Tuple[int, str]:
        """
        Rename an existing device in NSO CDB.
        Fetches existing device config, instantiates under new name, and deletes the old name.
        """
        status, dev_config = self.get_device(old_name)
        if status != 200 or not isinstance(dev_config, dict):
            return status, f"Failed to retrieve original device '{old_name}'"

        dev_list = dev_config.get("tailf-ncs:device", [])
        if not dev_list:
            return 404, f"Device '{old_name}' not found"
        
        dev_entry = dict(dev_list[0])
        dev_entry["name"] = new_name

        # Create device under new name
        put_resp = self.request("PUT", f"tailf-ncs:devices/device={new_name}", data={"tailf-ncs:device": dev_entry})
        if put_resp.status_code not in (200, 201, 204):
            return put_resp.status_code, f"Failed creating device under new name: {put_resp.text}"

        # Delete old device
        del_status, del_text = self.delete_device(old_name)
        return 200 if del_status in (200, 204) else del_status, f"Device renamed from {old_name} to {new_name}"

    def delete_device(self, device_name: str) -> Tuple[int, str]:
        """Delete / decommission a managed device from Cisco NSO CDB."""
        resp = self.request("DELETE", f"tailf-ncs:devices/device={device_name}")
        return resp.status_code, resp.text

    # --- Port Blocking & ACL Management Methods (US2) ---

    def create_port_block_acl(
        self,
        device_name: str,
        acl_name: str,
        port_number: int,
        protocol: str = "tcp",
    ) -> Tuple[int, str]:
        """
        Create an extended ACL on a Cisco IOS device blocking a specific TCP/UDP port.
        Rule 10: deny <protocol> any any eq <port>
        Rule 20: permit ip any any
        """
        payload = {
            "tailf-ned-cisco-ios:extended": {
                "id": acl_name,
                "rule": [
                    {
                        "name": "10",
                        "action": "deny",
                        "protocol": protocol,
                        "source": {"any": [None]},
                        "destination": {
                            "any": [None],
                            "port": {"eq": port_number},
                        },
                    },
                    {
                        "name": "20",
                        "action": "permit",
                        "protocol": "ip",
                        "source": {"any": [None]},
                        "destination": {"any": [None]},
                    },
                ],
            }
        }
        resp = self.request(
            "PUT",
            f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-ios:ip/access-list/extended={acl_name}",
            data=payload,
        )
        return resp.status_code, resp.text

    def apply_interface_acl(
        self,
        device_name: str,
        interface_type: str,
        interface_name: str,
        acl_name: str,
        direction: str = "in",
    ) -> Tuple[int, str]:
        """Apply an access-list filter to an interface (GigabitEthernet, FastEthernet, etc.)."""
        # RESTCONF path encoding for interface name e.g. "0/1" -> "0%2F1"
        encoded_name = interface_name.replace("/", "%2F")
        payload = {
            f"tailf-ned-cisco-ios:{interface_type}": {
                "name": interface_name,
                "ip": {
                    "access-group": {
                        direction: {
                            "acl": acl_name,
                        }
                    }
                },
            }
        }
        resp = self.request(
            "PATCH",
            f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-ios:interface/{interface_type}={encoded_name}",
            data=payload,
        )
        return resp.status_code, resp.text

    def remove_port_block_acl(self, device_name: str, acl_name: str) -> Tuple[int, str]:
        """Delete an extended ACL from NSO device config."""
        resp = self.request(
            "DELETE",
            f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-ios:ip/access-list/extended={acl_name}"
        )
        return resp.status_code, resp.text

    def shutdown_interface(
        self,
        device_name: str,
        interface_type: str,
        interface_name: str,
    ) -> Tuple[int, str]:
        """Administratively disable (shutdown) an interface."""
        encoded_name = interface_name.replace("/", "%2F")
        payload = {
            f"tailf-ned-cisco-ios:{interface_type}": {
                "name": interface_name,
                "shutdown": [None],
            }
        }
        resp = self.request(
            "PATCH",
            f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-ios:interface/{interface_type}={encoded_name}",
            data=payload,
        )
        return resp.status_code, resp.text

    def enable_interface(
        self,
        device_name: str,
        interface_type: str,
        interface_name: str,
    ) -> Tuple[int, str]:
        """Re-enable (no shutdown) an interface."""
        encoded_name = interface_name.replace("/", "%2F")
        resp = self.request(
            "DELETE",
            f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-ios:interface/{interface_type}={encoded_name}/shutdown"
        )
        return resp.status_code, resp.text

    # --- NSO Operational Actions ---

    def check_sync(self, device_name: str) -> Tuple[int, Any]:
        """Trigger check-sync action on a device."""
        resp = self.request(
            "POST",
            f"tailf-ncs:devices/device={device_name}/check-sync",
            is_operation=True,
            data={},
        )
        return resp.status_code, resp.json() if resp.status_code == 200 else resp.text

    def sync_from(self, device_name: str) -> Tuple[int, Any]:
        """Trigger sync-from action to pull device configuration into NSO CDB."""
        resp = self.request(
            "POST",
            f"tailf-ncs:devices/device={device_name}/sync-from",
            is_operation=True,
            data={},
        )
        return resp.status_code, resp.json() if resp.status_code == 200 else resp.text

    def fetch_host_keys(self, device_name: str) -> Tuple[int, Any]:
        """Fetch SSH host keys from device into NSO."""
        resp = self.request(
            "POST",
            f"tailf-ncs:devices/device={device_name}/ssh/fetch-host-keys",
            is_operation=True,
            data={},
        )
        return resp.status_code, resp.json() if resp.status_code == 200 else resp.text

    def compare_config(self, device_name: str) -> Tuple[int, Any]:
        """Compare device config between NSO CDB and actual device (diff)."""
        resp = self.request(
            "POST",
            f"tailf-ncs:devices/device={device_name}/compare-config",
            is_operation=True,
            data={},
        )
        return resp.status_code, resp.json() if resp.status_code == 200 else resp.text
