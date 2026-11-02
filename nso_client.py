"""
Cisco NSO RESTCONF Client Helper Module.
Provides clean wrappers for querying devices, services, configuration,
and running operational actions (check-sync, compare-config, sync-from).
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
    ):
        self.host = host or os.getenv("NSO_HOST", "sandbox-nso-1.cisco.com")
        self.port = port or int(os.getenv("NSO_PORT", "443"))
        self.username = username or os.getenv("NSO_USER", "namansin")
        self.password = password or os.getenv("NSO_PASSWORD", "#u*^x6^3t6DGEcD")

        self.base_data_url = f"https://{self.host}:{self.port}/restconf/data"
        self.base_ops_url = f"https://{self.host}:{self.port}/restconf/operations"

        self.session = requests.Session()
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
        """Execute a RESTCONF HTTP request."""
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
        resp = self.request("GET", "tailf-ncs:devices/device?fields=name")
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

    def compare_config(self, device_name: str) -> Tuple[int, Any]:
        """Compare device config between NSO CDB and actual device (diff)."""
        resp = self.request(
            "POST",
            f"tailf-ncs:devices/device={device_name}/compare-config",
            is_operation=True,
            data={},
        )
        return resp.status_code, resp.json() if resp.status_code == 200 else resp.text
