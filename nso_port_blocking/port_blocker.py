#!/usr/bin/env python3
"""
Cisco NSO Network Port Blocking Tool.
Provides dual-mode port blocking and traffic isolation via Cisco NSO RESTCONF:
1. Layer 4 ACL Filtering: Provisions extended Access Control Lists (ACLs) to drop
   traffic on designated TCP/UDP ports (e.g., Telnet 23, HTTP 80, SMB 445)
   and binds them to target router/switch interfaces.
2. Interface Administrative Control: Disables (shutdown) or restores (no shutdown)
   physical/logical interface links for isolation.
"""

import argparse
import json
import os
import sys
import urllib3
import requests
from typing import Any, Dict, Optional, Tuple

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class NSOPortBlocker:
    """Port blocker for Cisco NSO managed network devices."""

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

    # --- Layer 4 ACL Filtering ---

    def create_port_block_acl(
        self,
        device_name: str,
        acl_name: str,
        port_number: int,
        protocol: str = "tcp",
    ) -> Tuple[int, str]:
        """Create extended ACL in NSO CDB to deny specified port and permit remaining traffic."""
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
                            "port": {"eq": int(port_number)},
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
        resp = self._request(
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
        """Apply an access-list filter to a specific interface."""
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
        resp = self._request(
            "PATCH",
            f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-ios:interface/{interface_type}={encoded_name}",
            data=payload,
        )
        return resp.status_code, resp.text

    def remove_interface_acl(
        self,
        device_name: str,
        interface_type: str,
        interface_name: str,
        direction: str = "in",
    ) -> Tuple[int, str]:
        """Remove an access-list filter binding from an interface."""
        encoded_name = interface_name.replace("/", "%2F")
        resp = self._request(
            "DELETE",
            f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-ios:interface/{interface_type}={encoded_name}/ip/access-group/{direction}"
        )
        return resp.status_code, resp.text

    def delete_acl(self, device_name: str, acl_name: str) -> Tuple[int, str]:
        """Delete extended ACL definition from NSO CDB."""
        resp = self._request(
            "DELETE",
            f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-ios:ip/access-list/extended={acl_name}"
        )
        return resp.status_code, resp.text

    def block_port_flow(
        self,
        device_name: str,
        port_number: int,
        protocol: str = "tcp",
        interface_type: str = "GigabitEthernet",
        interface_name: str = "0/1",
        direction: str = "in",
        acl_name: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """Full workflow: create ACL and attach to interface."""
        effective_acl = acl_name or f"BLOCK_{protocol.upper()}_{port_number}"
        
        # 1. Create ACL
        c_status, c_msg = self.create_port_block_acl(device_name, effective_acl, port_number, protocol)
        if c_status not in (200, 201, 204):
            return False, f"Failed creating ACL {effective_acl} (Status {c_status}): {c_msg}"

        # 2. Attach ACL to interface
        a_status, a_msg = self.apply_interface_acl(device_name, interface_type, interface_name, effective_acl, direction)
        if a_status not in (200, 204):
            # Rollback ACL creation
            self.delete_acl(device_name, effective_acl)
            return False, f"Failed applying ACL to {interface_type}{interface_name} (Status {a_status}): {a_msg}"

        return True, f"Port {port_number}/{protocol} blocked on {device_name} {interface_type}{interface_name} via ACL {effective_acl}"

    def unblock_port_flow(
        self,
        device_name: str,
        port_number: int,
        protocol: str = "tcp",
        interface_type: str = "GigabitEthernet",
        interface_name: str = "0/1",
        direction: str = "in",
        acl_name: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """Full workflow: detach ACL from interface and remove ACL definition."""
        effective_acl = acl_name or f"BLOCK_{protocol.upper()}_{port_number}"
        
        # 1. Detach from interface
        self.remove_interface_acl(device_name, interface_type, interface_name, direction)

        # 2. Delete ACL
        d_status, d_msg = self.delete_acl(device_name, effective_acl)
        if d_status in (200, 204):
            return True, f"Port {port_number}/{protocol} unblocked, ACL {effective_acl} removed"
        return False, f"Detached from interface but error deleting ACL {effective_acl} (Status {d_status}): {d_msg}"

    # --- Interface Administrative Control ---

    def shut_interface(
        self,
        device_name: str,
        interface_type: str,
        interface_name: str,
    ) -> Tuple[int, str]:
        """Administratively shutdown an interface."""
        encoded_name = interface_name.replace("/", "%2F")
        payload = {
            f"tailf-ned-cisco-ios:{interface_type}": {
                "name": interface_name,
                "shutdown": [None],
            }
        }
        resp = self._request(
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
        resp = self._request(
            "DELETE",
            f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-ios:interface/{interface_type}={encoded_name}/shutdown"
        )
        return resp.status_code, resp.text

    def get_interface_config(
        self,
        device_name: str,
        interface_type: str,
        interface_name: str,
    ) -> Tuple[int, Any]:
        """Retrieve full interface configuration."""
        encoded_name = interface_name.replace("/", "%2F")
        resp = self._request(
            "GET",
            f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-ios:interface/{interface_type}={encoded_name}"
        )
        return resp.status_code, resp.json() if resp.status_code == 200 else resp.text

    def list_acls(self, device_name: str) -> Tuple[int, Any]:
        """List all extended ACLs on device."""
        resp = self._request(
            "GET",
            f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-ios:ip/access-list/extended"
        )
        return resp.status_code, resp.json() if resp.status_code == 200 else resp.text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Cisco NSO Port Blocker CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--action",
        required=True,
        choices=["block-port", "unblock-port", "shut-interface", "enable-interface", "status", "list-acls"],
        help="Port blocking action to perform",
    )
    parser.add_argument("--device", default=os.getenv("RESTCONF_DEVICE", "dist-rtr01"), help="Target device name in NSO")
    parser.add_argument("--interface-type", default="GigabitEthernet", help="Interface type (default: GigabitEthernet)")
    parser.add_argument("--interface", default="0/1", help="Interface identifier (default: 0/1)")
    parser.add_argument("--port-number", type=int, default=23, help="TCP/UDP port number to block (default: 23)")
    parser.add_argument("--protocol", default="tcp", choices=["tcp", "udp"], help="Transport protocol (default: tcp)")
    parser.add_argument("--direction", default="in", choices=["in", "out"], help="ACL filter direction (default: in)")
    parser.add_argument("--acl-name", help="Custom ACL identifier (optional)")
    parser.add_argument("--host", help="NSO server hostname/IP")
    parser.add_argument("--port-nso", type=int, help="NSO RESTCONF port")
    parser.add_argument("--user", help="NSO username")
    parser.add_argument("--password", help="NSO password")
    parser.add_argument("--scheme", choices=["http", "https"], help="HTTP transport scheme")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    blocker = NSOPortBlocker(
        host=args.host,
        port=args.port_nso,
        username=args.user,
        password=args.password,
        scheme=args.scheme,
    )

    action = args.action

    if action == "block-port":
        ok, msg = blocker.block_port_flow(
            device_name=args.device,
            port_number=args.port_number,
            protocol=args.protocol,
            interface_type=args.interface_type,
            interface_name=args.interface,
            direction=args.direction,
            acl_name=args.acl_name,
        )
        print(f"[{'SUCCESS' if ok else 'FAILURE'}] {msg}")
        sys.exit(0 if ok else 1)

    elif action == "unblock-port":
        ok, msg = blocker.unblock_port_flow(
            device_name=args.device,
            port_number=args.port_number,
            protocol=args.protocol,
            interface_type=args.interface_type,
            interface_name=args.interface,
            direction=args.direction,
            acl_name=args.acl_name,
        )
        print(f"[{'SUCCESS' if ok else 'FAILURE'}] {msg}")
        sys.exit(0 if ok else 1)

    elif action == "shut-interface":
        status, text = blocker.shut_interface(args.device, args.interface_type, args.interface)
        if status in (200, 204):
            print(f"Successfully shut down interface {args.interface_type}{args.interface} on {args.device}")
        else:
            print(f"Failed to shut down interface (Status {status}): {text}")
            sys.exit(1)

    elif action == "enable-interface":
        status, text = blocker.enable_interface(args.device, args.interface_type, args.interface)
        if status in (200, 204):
            print(f"Successfully enabled (no shutdown) interface {args.interface_type}{args.interface} on {args.device}")
        else:
            print(f"Failed to enable interface (Status {status}): {text}")
            sys.exit(1)

    elif action == "status":
        status, data = blocker.get_interface_config(args.device, args.interface_type, args.interface)
        print(json.dumps(data, indent=2) if isinstance(data, dict) else f"Status {status}: {data}")

    elif action == "list-acls":
        status, data = blocker.list_acls(args.device)
        print(json.dumps(data, indent=2) if isinstance(data, dict) else f"Status {status}: {data}")


if __name__ == "__main__":
    main()
