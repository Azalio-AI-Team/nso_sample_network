"""
Cisco NSO RESTCONF Client Helper Module.
Provides clean wrappers for querying devices, services, configuration,
managing device lifecycles (add, edit, rename, delete), port blocking (ACL, shutdown),
and running operational actions (check-sync, compare-config, sync-from, fetch-ssh-host-keys).
"""

import os
from typing import Any

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _load_env_defaults():
    """Load defaults from local .env if present without external dependencies."""
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.isfile(env_path):
        try:
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k not in os.environ:
                            os.environ[k] = v
        except OSError:
            pass


_load_env_defaults()


class NSOClient:
    """RESTCONF client for Cisco Network Services Orchestrator (NSO)."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        username: str | None = None,
        password: str | None = None,
        scheme: str | None = None,
    ):
        self.host = (
            host
            or os.getenv("NSO_HOST")
            or os.getenv("RESTCONF_HOST")
            or (os.getenv("nso1_web", "").split("://")[-1].split(":")[0] if os.getenv("nso1_web") else None)
            or "sandbox-nso-1.cisco.com"
        )
        
        # Default port: check env var, else infer from host (8080 for private lab IP, 443 for public sandbox)
        if port is not None:
            self.port = port
        elif os.getenv("NSO_PORT"):
            self.port = int(os.environ["NSO_PORT"])
        elif self.host.startswith("10.10.20."):
            self.port = 8080
        else:
            self.port = 443

        self.username = (
            username
            or os.getenv("NSO_USER")
            or os.getenv("nso_username")
            or os.getenv("RESTCONF_USER", "developer")
        )
        # Strict zero-hardcoded-secrets: read from environment or empty default
        self.password = (
            password
            or os.getenv("NSO_PASSWORD")
            or os.getenv("nso_password")
            or os.getenv("DEVNET_RESTCONF_PASSWORD")
            or os.getenv("RESTCONF_PASSWORD")
            or ""
        )

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
        data: dict[str, Any] | None = None,
        timeout: int = 60,
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

    def get_devices(self) -> tuple[int, Any]:
        """Retrieve the list of all managed devices."""
        resp = self.request("GET", "tailf-ncs:devices/device?fields=name;address;port;authgroup;device-type")
        return resp.status_code, resp.json() if resp.status_code == 200 else resp.text

    def get_device(self, device_name: str) -> tuple[int, Any]:
        """Retrieve a single device from NSO CDB."""
        resp = self.request("GET", f"tailf-ncs:devices/device={device_name}")
        return resp.status_code, resp.json() if resp.status_code == 200 else resp.text

    def get_services(self) -> tuple[int, Any]:
        """Retrieve defined router services."""
        resp = self.request("GET", "router:router")
        return resp.status_code, resp.json() if resp.status_code == 200 else resp.text

    def get_device_interfaces(self, device_name: str) -> tuple[int, Any]:
        """Retrieve interface configuration for a specific Cisco IOS device."""
        resp = self.request("GET", f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-ios:interface")
        return resp.status_code, resp.json() if resp.status_code == 200 else resp.text

    def _detect_platform(self, device_name: str, platform: str | None = None) -> str:
        """Infer target platform family (ios, iosxr, nx) from platform or device name."""
        if platform:
            p = platform.lower()
            if "xr" in p:
                return "iosxr"
            if "nx" in p:
                return "nx"
            return "ios"
        dev = device_name.lower()
        if "core" in dev or "xr" in dev:
            return "iosxr"
        if "sw01" in dev or "nx" in dev:
            return "nx"
        return "ios"

    def get_loopback_interface(
        self, device_name: str, loopback_id: str, platform: str | None = None
    ) -> tuple[int, Any]:
        """Retrieve details of a specific Loopback interface across IOS-XE, IOS-XR, or NX-OS."""
        plat = self._detect_platform(device_name, platform)
        if plat == "iosxr":
            path = f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-ios-xr:interface/Loopback={loopback_id}"
        elif plat == "nx":
            path = f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-nx:interface/loopback={loopback_id}"
        else:
            path = f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-ios:interface/Loopback={loopback_id}"
        resp = self.request("GET", path)
        return resp.status_code, resp.json() if resp.status_code == 200 else resp.text

    def set_loopback_interface(
        self,
        device_name: str,
        loopback_id: str,
        ip_address: str,
        netmask: str,
        description: str = "",
        platform: str | None = None,
    ) -> tuple[int, str]:
        """Create or replace a Loopback interface using PUT across IOS-XE, IOS-XR, or NX-OS."""
        plat = self._detect_platform(device_name, platform)
        if plat == "iosxr":
            path = f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-ios-xr:interface/Loopback={loopback_id}"
            payload = {
                "tailf-ned-cisco-ios-xr:Loopback": {
                    "id": str(loopback_id),
                    "description": description,
                    "ipv4": {
                        "address": {
                            "ip": ip_address,
                            "mask": netmask,
                        }
                    },
                }
            }
        elif plat == "nx":
            # Convert subnet mask to CIDR prefix length if needed
            prefix_len = 32
            if netmask:
                try:
                    prefix_len = sum(int(x).bit_count() for x in netmask.split("."))
                except (ValueError, AttributeError):
                    prefix_len = 32
            path = f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-nx:interface/loopback={loopback_id}"
            payload = {
                "tailf-ned-cisco-nx:loopback": {
                    "name": int(loopback_id) if str(loopback_id).isdigit() else loopback_id,
                    "description": description,
                    "ip": {
                        "address": {
                            "ipaddr": f"{ip_address}/{prefix_len}",
                        }
                    },
                }
            }
        else:
            path = f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-ios:interface/Loopback={loopback_id}"
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
        resp = self.request("PUT", path, data=payload)
        return resp.status_code, resp.text

    def delete_loopback_interface(
        self, device_name: str, loopback_id: str, platform: str | None = None
    ) -> tuple[int, str]:
        """Delete a Loopback interface from an IOS-XE, IOS-XR, or NX-OS device."""
        plat = self._detect_platform(device_name, platform)
        if plat == "iosxr":
            path = f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-ios-xr:interface/Loopback={loopback_id}"
        elif plat == "nx":
            path = f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-nx:interface/loopback={loopback_id}"
        else:
            path = f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-ios:interface/Loopback={loopback_id}"
        resp = self.request("DELETE", path)
        return resp.status_code, resp.text

    def update_interface_description(
        self,
        device_name: str,
        interface_type: str,
        interface_name: str,
        description: str,
        platform: str | None = None,
    ) -> tuple[int, str]:
        """Update interface description using atomic PATCH across platforms."""
        plat = self._detect_platform(device_name, platform)
        encoded_name = interface_name.replace("/", "%2F")
        if plat == "iosxr":
            path = f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-ios-xr:interface/{interface_type}={encoded_name}"
            payload = {f"tailf-ned-cisco-ios-xr:{interface_type}": {"id": interface_name, "description": description}}
        elif plat == "nx":
            path = f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-nx:interface/{interface_type}={encoded_name}"
            payload = {f"tailf-ned-cisco-nx:{interface_type}": {"id": interface_name, "description": description}}
        else:
            path = f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-ios:interface/{interface_type}={encoded_name}"
            payload = {f"tailf-ned-cisco-ios:{interface_type}": {"name": interface_name, "description": description}}
        resp = self.request("PATCH", path, data=payload)
        return resp.status_code, resp.text

    # --- Device Lifecycle Management Methods (US1) ---

    def add_device(
        self,
        name: str,
        address: str,
        port: int = 23,
        authgroup: str = "labadmin",
        ned_id: str = "cisco-ios-cli-6.109:cisco-ios-cli-6.109",
        protocol: str = "telnet",
        admin_state: str = "unlocked",
    ) -> tuple[int, str]:
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
        address: str | None = None,
        port: int | None = None,
        authgroup: str | None = None,
        description: str | None = None,
    ) -> tuple[int, str]:
        """Update configuration parameters of an existing device in NSO."""
        device_data: dict[str, Any] = {"name": name}
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

    def rename_device(self, old_name: str, new_name: str) -> tuple[int, str]:
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
        keys_to_keep = ["name", "address", "port", "authgroup", "device-type", "description"]
        new_entry = {k: dev_entry[k] for k in keys_to_keep if k in dev_entry}
        new_entry["name"] = new_name

        # Create device under new name via POST
        post_resp = self.request("POST", "tailf-ncs:devices", data={"tailf-ncs:device": [new_entry]})
        if post_resp.status_code not in (200, 201, 204):
            return post_resp.status_code, f"Failed creating device under new name: {post_resp.text}"

        # Delete old device
        del_status, _del_text = self.delete_device(old_name)
        return 200 if del_status in (200, 204) else del_status, f"Device renamed from {old_name} to {new_name}"

    def delete_device(self, device_name: str) -> tuple[int, str]:
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
    ) -> tuple[int, str]:
        """
        Create an extended ACL on a Cisco IOS device blocking a specific TCP/UDP port.
        Rule 1: deny <protocol> any any eq <port>
        Rule 2: permit ip any any
        """
        payload = {
            "tailf-ned-cisco-ios:ext-named-acl": {
                "name": acl_name,
                "ext-access-list-rule": [
                    {"rule": f"deny {protocol} any any eq {port_number}"},
                    {"rule": "permit ip any any"},
                ],
            }
        }
        resp = self.request(
            "PUT",
            f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-ios:ip/access-list/extended/ext-named-acl={acl_name}",
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
    ) -> tuple[int, str]:
        """Apply an access-list filter to an interface (GigabitEthernet, FastEthernet, etc.)."""
        # RESTCONF path encoding for interface name e.g. "0/1" -> "0%2F1"
        encoded_name = interface_name.replace("/", "%2F")
        payload = {
            f"tailf-ned-cisco-ios:{interface_type}": {
                "name": interface_name,
                "ip": {
                    "access-group": [
                        {
                            "direction": direction,
                            "access-list": acl_name,
                        }
                    ]
                },
            }
        }
        resp = self.request(
            "PATCH",
            f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-ios:interface/{interface_type}={encoded_name}",
            data=payload,
        )
        return resp.status_code, resp.text

    def remove_port_block_acl(self, device_name: str, acl_name: str) -> tuple[int, str]:
        """Delete an extended ACL from NSO device config."""
        resp = self.request(
            "DELETE",
            f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-ios:ip/access-list/extended/ext-named-acl={acl_name}"
        )
        return resp.status_code, resp.text

    def shutdown_interface(
        self,
        device_name: str,
        interface_type: str,
        interface_name: str,
    ) -> tuple[int, str]:
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
    ) -> tuple[int, str]:
        """Re-enable (no shutdown) an interface."""
        encoded_name = interface_name.replace("/", "%2F")
        resp = self.request(
            "DELETE",
            f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-ios:interface/{interface_type}={encoded_name}/shutdown"
        )
        return resp.status_code, resp.text

    # --- NSO Operational Actions ---

    def check_sync(self, device_name: str) -> tuple[int, Any]:
        """Trigger check-sync action on a device."""
        resp = self.request(
            "POST",
            f"tailf-ncs:devices/device={device_name}/check-sync",
            is_operation=True,
            data={},
        )
        return resp.status_code, resp.json() if resp.status_code == 200 else resp.text

    def sync_from(self, device_name: str) -> tuple[int, Any]:
        """Trigger sync-from action to pull device configuration into NSO CDB."""
        resp = self.request(
            "POST",
            f"tailf-ncs:devices/device={device_name}/sync-from",
            is_operation=True,
            data={},
        )
        return resp.status_code, resp.json() if resp.status_code == 200 else resp.text

    def fetch_host_keys(self, device_name: str) -> tuple[int, Any]:
        """Fetch SSH host keys from device into NSO."""
        resp = self.request(
            "POST",
            f"tailf-ncs:devices/device={device_name}/ssh/fetch-host-keys",
            is_operation=True,
            data={},
        )
        return resp.status_code, resp.json() if resp.status_code == 200 else resp.text

    def compare_config(self, device_name: str) -> tuple[int, Any]:
        """Compare device config between NSO CDB and actual device (diff)."""
        resp = self.request(
            "POST",
            f"tailf-ncs:devices/device={device_name}/compare-config",
            is_operation=True,
            data={},
        )
        return resp.status_code, resp.json() if resp.status_code == 200 else resp.text
