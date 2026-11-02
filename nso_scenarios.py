"""
NSO Test Scenarios Module.
Executes test scenarios ported from CiscoDevNet/python_code_samples_network
against the Cisco NSO sandbox environment (sandbox-nso-1.cisco.com).
"""

import json
from typing import Dict, Any, List
from nso_client import NSOClient


class NSOScenarioRunner:
    """Runner for NSO test scenarios."""

    def __init__(self, client: NSOClient = None):
        self.client = client or NSOClient()
        self.results: List[Dict[str, Any]] = []

    def log_scenario(self, name: str, success: bool, details: Any):
        self.results.append({
            "scenario": name,
            "success": success,
            "details": details,
        })
        status_label = "PASS" if success else "FAIL"
        print(f"[{status_label}] {name}")

    def run_all(self) -> bool:
        """Run all test scenarios sequentially."""
        print("=" * 75)
        print(" STARTING CISCO NSO TEST SCENARIOS (CiscoDevNet Code Samples)")
        print(f" Target Host: {self.client.host}:{self.client.port}")
        print(f" User: {self.client.username}")
        print("=" * 75)

        s1 = self.scenario_1_fleet_discovery()
        s2 = self.scenario_2_get_interface_config()
        s3 = self.scenario_3_provision_interface()
        s4 = self.scenario_4_verify_provisioned_interface()
        s5 = self.scenario_5_verify_device_sync()
        s6 = self.scenario_6_out_of_band_drift_analysis()
        s7 = self.scenario_7_delete_interface_cleanup()
        s8 = self.scenario_8_router_services_inspection()

        print("\n" + "=" * 75)
        print(" TEST SCENARIOS EXECUTION SUMMARY")
        print("=" * 75)
        all_passed = True
        for r in self.results:
            mark = "✓" if r["success"] else "✗"
            print(f" {mark} {r['scenario']}")
            if not r["success"]:
                all_passed = False

        print("-" * 75)
        print(f" Total: {len(self.results)} | Passed: {sum(1 for r in self.results if r['success'])} | Failed: {sum(1 for r in self.results if not r['success'])}")
        print("=" * 75)
        return all_passed

    def scenario_1_fleet_discovery(self) -> bool:
        """Scenario 1: Fleet Discovery & Inventory Inspection."""
        print("\n--> Running Scenario 1: Fleet Discovery & Inventory Inspection")
        status, data = self.client.get_devices()
        if status == 200 and isinstance(data, dict):
            devices = data.get("tailf-ncs:device", [])
            device_names = [d.get("name") for d in devices]
            print(f"    Discovered {len(device_names)} devices: {', '.join(device_names[:6])}... ({len(device_names)} total)")
            success = len(devices) > 0 and "dist-rtr00" in device_names
            self.log_scenario(
                "Scenario 1: Fleet Discovery (devices list)",
                success,
                {"device_count": len(device_names), "devices": device_names},
            )
            return success
        else:
            self.log_scenario("Scenario 1: Fleet Discovery (devices list)", False, {"status": status, "data": data})
            return False

    def scenario_2_get_interface_config(self) -> bool:
        """Scenario 2: Device Interface Retrieval (Ported from RESTCONF/get-interface-config.py)."""
        print("\n--> Running Scenario 2: Interface Retrieval (dist-rtr00)")
        status, data = self.client.get_device_interfaces("dist-rtr00")
        if status == 200 and isinstance(data, dict):
            interfaces = data.get("tailf-ned-cisco-ios:interface", {})
            loopbacks = [item.get("name") for item in interfaces.get("Loopback", [])]
            fast_ethernets = [item.get("name") for item in interfaces.get("FastEthernet", [])]
            print(f"    dist-rtr00 Loopbacks: {loopbacks}")
            print(f"    dist-rtr00 FastEthernet interfaces: {fast_ethernets}")
            success = "0" in loopbacks and len(fast_ethernets) > 0
            self.log_scenario(
                "Scenario 2: Device Interface Retrieval (get-interface-config.py)",
                success,
                {"loopbacks": loopbacks, "fast_ethernets": fast_ethernets},
            )
            return success
        else:
            self.log_scenario(
                "Scenario 2: Device Interface Retrieval (get-interface-config.py)",
                False,
                {"status": status, "data": data},
            )
            return False

    def scenario_3_provision_interface(self) -> bool:
        """Scenario 3: Interface Provisioning (Ported from RESTCONF/patch-Ip-address-config.py)."""
        print("\n--> Running Scenario 3: Interface Provisioning (Create Loopback 100 on dist-rtr00)")
        status, text = self.client.set_loopback_interface(
            device_name="dist-rtr00",
            loopback_id="100",
            ip_address="10.100.100.1",
            netmask="255.255.255.255",
            description="Configured via DevNet RESTCONF Python Scenario",
        )
        # NSO returns 201 (Created) or 204 (No Content / updated)
        success = status in (200, 201, 204)
        print(f"    PUT Response Status: {status} (Expected 201 Created or 204 No Content)")
        self.log_scenario(
            "Scenario 3: Interface Provisioning (patch-Ip-address-config.py)",
            success,
            {"status": status, "response": text},
        )
        return success

    def scenario_4_verify_provisioned_interface(self) -> bool:
        """Scenario 4: Verify Provisioned Interface via GET."""
        print("\n--> Running Scenario 4: Verify Provisioned Interface (GET Loopback 100)")
        status, data = self.client.get_loopback_interface("dist-rtr00", "100")
        if status == 200 and isinstance(data, dict):
            lb_list = data.get("tailf-ned-cisco-ios:Loopback", [])
            lb_info = lb_list[0] if lb_list else {}
            configured_ip = lb_info.get("ip", {}).get("address", {}).get("primary", {}).get("address")
            configured_mask = lb_info.get("ip", {}).get("address", {}).get("primary", {}).get("mask")
            description = lb_info.get("description", "")
            print(f"    Verified Loopback100 -> IP: {configured_ip}/{configured_mask}, Description: '{description}'")
            success = configured_ip == "10.100.100.1" and configured_mask == "255.255.255.255"
            self.log_scenario(
                "Scenario 4: Verification of Provisioned Interface",
                success,
                {"ip": configured_ip, "mask": configured_mask, "description": description},
            )
            return success
        else:
            self.log_scenario(
                "Scenario 4: Verification of Provisioned Interface",
                False,
                {"status": status, "data": data},
            )
            return False

    def scenario_5_verify_device_sync(self) -> bool:
        """Scenario 5: In-Band Device Synchronization Verification (check-sync)."""
        print("\n--> Running Scenario 5: Check Device Sync (dist-rtr00)")
        status, data = self.client.check_sync("dist-rtr00")
        if status == 200 and isinstance(data, dict):
            sync_result = data.get("tailf-ncs:output", {}).get("result")
            print(f"    check-sync result: '{sync_result}' (Expected: 'in-sync')")
            success = sync_result == "in-sync"
            self.log_scenario(
                "Scenario 5: Device Synchronization (check-sync)",
                success,
                {"sync_result": sync_result},
            )
            return success
        else:
            self.log_scenario(
                "Scenario 5: Device Synchronization (check-sync)",
                False,
                {"status": status, "data": data},
            )
            return False

    def scenario_6_out_of_band_drift_analysis(self) -> bool:
        """Scenario 6: Out-of-Band Drift Analysis (compare-config on out-of-sync core-rtr01)."""
        print("\n--> Running Scenario 6: Out-of-Band Drift Analysis (compare-config on core-rtr01)")
        status, data = self.client.compare_config("core-rtr01")
        if status == 200 and isinstance(data, dict):
            diff = data.get("tailf-ncs:output", {}).get("diff", "")
            has_diff = len(diff.strip()) > 0
            preview = "\n".join(diff.strip().splitlines()[:10])
            print(f"    compare-config detected drift:\n{preview}\n    ... (truncated)")
            success = has_diff
            self.log_scenario(
                "Scenario 6: Out-of-Band Drift Analysis (compare-config)",
                success,
                {"has_diff": has_diff, "diff_snippet": preview},
            )
            return success
        else:
            self.log_scenario(
                "Scenario 6: Out-of-Band Drift Analysis (compare-config)",
                False,
                {"status": status, "data": data},
            )
            return False

    def scenario_7_delete_interface_cleanup(self) -> bool:
        """Scenario 7: Interface Deletion & State Cleanup (Ported from RESTCONF/delete-Ip-address.py)."""
        print("\n--> Running Scenario 7: Interface Deletion & Cleanup (dist-rtr00 Loopback 100)")
        del_status, _ = self.client.delete_loopback_interface("dist-rtr00", "100")
        print(f"    DELETE Status: {del_status} (Expected 204 No Content)")

        # Verify deletion returns 404
        get_status, _ = self.client.get_loopback_interface("dist-rtr00", "100")
        print(f"    GET after DELETE Status: {get_status} (Expected 404 Not Found)")

        # Verify device remains in-sync
        sync_status, sync_data = self.client.check_sync("dist-rtr00")
        sync_result = sync_data.get("tailf-ncs:output", {}).get("result") if isinstance(sync_data, dict) else None
        print(f"    check-sync after cleanup: '{sync_result}'")

        success = del_status in (200, 204) and get_status == 404 and sync_result == "in-sync"
        self.log_scenario(
            "Scenario 7: Interface Deletion & Cleanup (delete-Ip-address.py)",
            success,
            {"del_status": del_status, "verify_get_status": get_status, "sync_result": sync_result},
        )
        return success

    def scenario_8_router_services_inspection(self) -> bool:
        """Scenario 8: Router Service Instances Inspection."""
        print("\n--> Running Scenario 8: Router Service Instances Inspection (router:router)")
        status, data = self.client.get_services()
        if status == 200 and isinstance(data, dict):
            services = data.get("router:router", [])
            service_names = [s.get("name") for s in services]
            print(f"    Discovered {len(service_names)} router services: {', '.join(service_names)}")
            success = len(services) > 0 and "CoreDevices" in service_names
            self.log_scenario(
                "Scenario 8: Router Service Instances Inspection",
                success,
                {"service_count": len(service_names), "services": service_names},
            )
            return success
        else:
            self.log_scenario(
                "Scenario 8: Router Service Instances Inspection",
                False,
                {"status": status, "data": data},
            )
            return False
