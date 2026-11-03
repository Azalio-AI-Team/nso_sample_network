#!/usr/bin/env python3
"""
Cisco NSO Topology Manager Package.
Automates multi-tier network topology discovery, baseline interface provisioning,
drift checking, and configuration rollbacks across Cisco IOS-XE, IOS-XR, NX-OS, and ASA.
Reference: https://developer.cisco.com/sandbox/detail/nso-sandbox
"""

import argparse
import json
import os
import sys
from typing import Any

import requests
import urllib3

from nso_topology_manager.topology_models import (
    TOPOLOGY_DEVICES,
    get_device_metadata,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _load_env_defaults():
    """Load defaults from local .env if present without external dependencies."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(base_dir, ".env")
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


class NSOTopologyManager:
    """Orchestrates multi-platform network topology configurations via Cisco NSO RESTCONF."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        username: str | None = None,
        password: str | None = None,
        scheme: str | None = None,
        timeout: int = 30,
    ):
        self.host = (
            host
            or os.getenv("NSO_HOST")
            or os.getenv("RESTCONF_HOST")
            or (os.getenv("nso1_web", "").split("://")[-1].split(":")[0] if os.getenv("nso1_web") else None)
            or "10.10.20.47"
        )
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
        self.password = (
            password
            or os.getenv("NSO_PASSWORD")
            or os.getenv("nso_password")
            or os.getenv("DEVNET_RESTCONF_PASSWORD")
            or os.getenv("RESTCONF_PASSWORD")
            or ""
        )
        if scheme:
            self.scheme = scheme.lower().rstrip(":/")
        elif os.getenv("NSO_SCHEME"):
            self.scheme = os.environ["NSO_SCHEME"].lower().rstrip(":/")
        elif self.port in (80, 8080):
            self.scheme = "http"
        else:
            self.scheme = "https"

        self.timeout = timeout
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
    ) -> requests.Response:
        """Execute a RESTCONF HTTP request."""
        base = self.base_ops_url if is_operation else self.base_data_url
        clean_path = path.lstrip("/")
        url = f"{base}/{clean_path}"
        return self.session.request(
            method=method,
            url=url,
            json=data if data is not None else None,
            timeout=self.timeout,
        )

    # --- Discovery & Audit Operations ---

    def audit_topology(self) -> dict[str, Any]:
        """Audit all managed devices in NSO against the topology model."""
        resp = self.request("GET", "tailf-ncs:devices/device?fields=name;address;port;authgroup;device-type;state")
        devices_in_nso = []
        if resp.status_code == 200:
            devices_in_nso = resp.json().get("tailf-ncs:device", [])

        audit_data = []
        for dev in devices_in_nso:
            name = dev.get("name")
            addr = dev.get("address", "N/A")
            meta = get_device_metadata(name)

            # Check sync state
            sync_resp = self.request("POST", f"tailf-ncs:devices/device={name}/check-sync", is_operation=True, data={})
            sync_state = "unknown"
            if sync_resp.status_code == 200:
                sync_state = sync_resp.json().get("tailf-ncs:output", {}).get("result", "unknown")

            audit_data.append({
                "device": name,
                "address": addr,
                "tier": meta.get("tier", "UNKNOWN"),
                "os": meta.get("os", "UNKNOWN"),
                "platform": meta.get("platform_family", "ios"),
                "sync_state": sync_state,
                "description": meta.get("description", ""),
            })

        return {
            "controller": f"{self.scheme}://{self.host}:{self.port}",
            "device_count": len(audit_data),
            "devices": audit_data,
        }

    # --- Multi-Platform Loopback Management ---

    def configure_loopback(
        self,
        device_name: str,
        loopback_id: str,
        ip_address: str,
        netmask: str = "255.255.255.255",
        description: str = "",
    ) -> tuple[int, str]:
        """Configure a Loopback interface using the platform-appropriate YANG model."""
        meta = get_device_metadata(device_name)
        platform = meta.get("platform_family", "ios")

        if platform == "iosxr":
            path = f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-ios-xr:interface/Loopback={loopback_id}"
            payload = {
                "tailf-ned-cisco-ios-xr:Loopback": {
                    "id": str(loopback_id),
                    "description": description or f"Loopback{loopback_id} on {device_name}",
                    "ipv4": {
                        "address": {
                            "ip": ip_address,
                            "mask": netmask,
                        }
                    },
                }
            }
        elif platform == "nx":
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
                    "description": description or f"Loopback{loopback_id} on {device_name}",
                    "ip": {
                        "address": {
                            "ipaddr": f"{ip_address}/{prefix_len}",
                        }
                    },
                }
            }
        else:  # ios / ios-xe default
            path = f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-ios:interface/Loopback={loopback_id}"
            payload = {
                "tailf-ned-cisco-ios:Loopback": {
                    "name": str(loopback_id),
                    "description": description or f"Loopback{loopback_id} on {device_name}",
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

    def delete_loopback(self, device_name: str, loopback_id: str) -> tuple[int, str]:
        """Delete a Loopback interface from a device."""
        meta = get_device_metadata(device_name)
        platform = meta.get("platform_family", "ios")

        if platform == "iosxr":
            path = f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-ios-xr:interface/Loopback={loopback_id}"
        elif platform == "nx":
            path = f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-nx:interface/loopback={loopback_id}"
        else:
            path = f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-ios:interface/Loopback={loopback_id}"

        resp = self.request("DELETE", path)
        return resp.status_code, resp.text

    # --- Interface Description & Baseline Orchestration ---

    def update_interface_description(
        self,
        device_name: str,
        interface_type: str,
        interface_name: str,
        description: str,
    ) -> tuple[int, str]:
        """Update interface description via atomic PATCH."""
        meta = get_device_metadata(device_name)
        platform = meta.get("platform_family", "ios")
        encoded_name = interface_name.replace("/", "%2F")

        if platform == "iosxr":
            path = f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-ios-xr:interface/{interface_type}={encoded_name}"
            payload = {f"tailf-ned-cisco-ios-xr:{interface_type}": {"id": interface_name, "description": description}}
        elif platform == "nx":
            path = f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-nx:interface/{interface_type}={encoded_name}"
            payload = {f"tailf-ned-cisco-nx:{interface_type}": {"id": interface_name, "description": description}}
        else:
            path = f"tailf-ncs:devices/device={device_name}/config/tailf-ned-cisco-ios:interface/{interface_type}={encoded_name}"
            payload = {f"tailf-ned-cisco-ios:{interface_type}": {"name": interface_name, "description": description}}

        resp = self.request("PATCH", path, data=payload)
        return resp.status_code, resp.text

    def deploy_baseline(self, loopback_id: str = "100") -> dict[str, Any]:
        """Deploy baseline Loopback addresses across all supported devices in the topology."""
        results = {}
        for name, meta in TOPOLOGY_DEVICES.items():
            # Skip ASA for loopbacks if not supported by its CLI NED
            if meta.get("platform_family") == "asa":
                continue
            ip = meta["default_loopback_ip"]
            mask = meta["default_loopback_mask"]
            desc = f"Baseline Management Loopback ({meta['tier']})"
            st, _text = self.configure_loopback(name, loopback_id, ip, mask, desc)
            results[name] = {"status": st, "ip": ip, "success": st in (200, 201, 204)}
        return results

    def teardown_baseline(self, loopback_id: str = "100") -> dict[str, Any]:
        """Teardown baseline Loopbacks across all supported devices (Rollback)."""
        results = {}
        for name, meta in TOPOLOGY_DEVICES.items():
            if meta.get("platform_family") == "asa":
                continue
            st, _text = self.delete_loopback(name, loopback_id)
            results[name] = {"status": st, "success": st in (200, 204)}
        return results

    def verify_sync(self, device_name: str | None = None) -> dict[str, str]:
        """Verify check-sync operational status across devices."""
        targets = [device_name] if device_name else list(TOPOLOGY_DEVICES.keys())
        results = {}
        for dev in targets:
            resp = self.request("POST", f"tailf-ncs:devices/device={dev}/check-sync", is_operation=True, data={})
            if resp.status_code == 200:
                res = resp.json().get("tailf-ncs:output", {}).get("result", "unknown")
            else:
                res = f"error-{resp.status_code}"
            results[dev] = res
        return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Cisco NSO Topology Manager CLI - Orchestrate multi-tier network topologies"
    )
    parser.add_argument(
        "--action",
        required=True,
        choices=[
            "audit",
            "configure-loopback",
            "delete-loopback",
            "update-interface",
            "deploy-baseline",
            "teardown-baseline",
            "verify-sync",
        ],
        help="Topology management action to perform",
    )
    parser.add_argument("--host", help="NSO host (default: 10.10.20.47 or NSO_HOST)")
    parser.add_argument("--port", type=int, help="NSO port (default: 8080)")
    parser.add_argument("--user", help="NSO username (default: developer or NSO_USER)")
    parser.add_argument("--password", help="NSO password (default: NSO_PASSWORD)")
    parser.add_argument("--device", help="Target device name (e.g. dist-rtr01, core-rtr01)")
    parser.add_argument("--loopback-id", default="100", help="Loopback ID (default: 100)")
    parser.add_argument("--ip", help="IP address for interface")
    parser.add_argument("--netmask", default="255.255.255.255", help="Netmask for interface")
    parser.add_argument("--interface-type", default="GigabitEthernet", help="Interface type (e.g. GigabitEthernet)")
    parser.add_argument("--interface-name", help="Interface name (e.g. 0/1)")
    parser.add_argument("--description", default="", help="Description for interface")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    manager = NSOTopologyManager(
        host=args.host,
        port=args.port,
        username=args.user,
        password=args.password,
    )

    if args.action == "audit":
        data = manager.audit_topology()
        if args.json:
            print(json.dumps(data, indent=2))
        else:
            print("=" * 80)
            print(f" CISCO DEVNET NSO SANDBOX TOPOLOGY AUDIT ({data['controller']})")
            print("=" * 80)
            print(f"{'DEVICE':<18} {'IP ADDRESS':<14} {'TIER':<14} {'OS':<8} {'SYNC STATUS':<12}")
            print("-" * 80)
            for d in data["devices"]:
                print(f"{d['device']:<18} {d['address']:<14} {d['tier']:<14} {d['os']:<8} {d['sync_state']:<12}")
            print("-" * 80)
            print(f"Total managed devices: {data['device_count']}")

    elif args.action == "configure-loopback":
        if not args.device or not args.ip:
            parser.error("--device and --ip are required for configure-loopback")
        st, _text = manager.configure_loopback(
            args.device, args.loopback_id, args.ip, args.netmask, args.description
        )
        msg = "SUCCESS" if st in (200, 201, 204) else f"FAILED ({st})"
        print(f"[{msg}] Configure Loopback{args.loopback_id} on {args.device} ({args.ip}): {st}")
        if st not in (200, 201, 204):
            sys.exit(1)

    elif args.action == "delete-loopback":
        if not args.device:
            parser.error("--device is required for delete-loopback")
        st, _text = manager.delete_loopback(args.device, args.loopback_id)
        msg = "SUCCESS" if st in (200, 204) else f"FAILED ({st})"
        print(f"[{msg}] Delete Loopback{args.loopback_id} on {args.device}: {st}")
        if st not in (200, 204):
            sys.exit(1)

    elif args.action == "update-interface":
        if not args.device or not args.interface_name:
            parser.error("--device and --interface-name are required for update-interface")
        st, _text = manager.update_interface_description(
            args.device, args.interface_type, args.interface_name, args.description
        )
        msg = "SUCCESS" if st in (200, 204) else f"FAILED ({st})"
        print(f"[{msg}] Update {args.interface_type}{args.interface_name} on {args.device}: {st}")
        if st not in (200, 204):
            sys.exit(1)

    elif args.action == "deploy-baseline":
        results = manager.deploy_baseline(args.loopback_id)
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print(f"Deploying baseline Loopback{args.loopback_id} across topology:")
            for dev, res in results.items():
                mark = "✓" if res["success"] else "✗"
                print(f"  {mark} {dev:<18} -> {res['ip']} (status {res['status']})")

    elif args.action == "teardown-baseline":
        results = manager.teardown_baseline(args.loopback_id)
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print(f"Tearing down baseline Loopback{args.loopback_id} across topology:")
            for dev, res in results.items():
                mark = "✓" if res["success"] else "✗"
                print(f"  {mark} {dev:<18} (status {res['status']})")

    elif args.action == "verify-sync":
        results = manager.verify_sync(args.device)
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print("Verifying check-sync state across topology:")
            for dev, res in results.items():
                print(f"  - {dev:<18} : {res}")


if __name__ == "__main__":
    main()
