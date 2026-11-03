"""
NSO Test Scenarios Module.
Executes test scenarios ported from CiscoDevNet/python_code_samples_network
against the Cisco NSO environment.
"""

import os
from typing import Any

from nso_client import NSOClient


class NSOScenarioRunner:
    """Runner for NSO test scenarios."""

    def __init__(self, client: NSOClient | None = None, target_device: str | None = None):
        self.client = client or NSOClient()
        self.target_device = target_device or os.getenv("RESTCONF_DEVICE", "dist-rtr01")
        self.results: list[dict[str, Any]] = []

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
        print(f" Target Host: {self.client.scheme}://{self.client.host}:{self.client.port}")
        print(f" User: {self.client.username}")
        print(f" Primary Target Device: {self.target_device}")
        print("=" * 75)

        self.scenario_1_fleet_discovery()
        self.scenario_2_get_interface_config()
        self.scenario_3_provision_interface()
        self.scenario_4_verify_provisioned_interface()
        self.scenario_5_verify_device_sync()
        self.scenario_6_out_of_band_drift_analysis()
        self.scenario_7_delete_interface_cleanup()
        self.scenario_8_router_services_inspection()
        self.scenario_9_device_lifecycle()
        self.scenario_10_port_blocking_acl()
        self.scenario_11_interface_shutdown()
        self.scenario_12_multi_platform_loopbacks()
        self.scenario_13_topology_audit()

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
            success = len(devices) >= 9 and any(d in device_names for d in ("dist-rtr01", "dist-rtr00"))
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
        print(f"\n--> Running Scenario 2: Interface Retrieval ({self.target_device})")
        status, data = self.client.get_device_interfaces(self.target_device)
        if status == 200 and isinstance(data, dict):
            interfaces = data.get("tailf-ned-cisco-ios:interface", {})
            loopbacks = [item.get("name") for item in interfaces.get("Loopback", [])]
            fast_ethernets = [item.get("name") for item in interfaces.get("FastEthernet", [])]
            gigabit_ethernets = [item.get("name") for item in interfaces.get("GigabitEthernet", [])]
            print(f"    {self.target_device} Loopbacks: {loopbacks}")
            print(f"    {self.target_device} Interfaces: FastEthernet={fast_ethernets}, GigabitEthernet={gigabit_ethernets}")
            success = len(loopbacks) > 0 or len(fast_ethernets) > 0 or len(gigabit_ethernets) > 0
            self.log_scenario(
                "Scenario 2: Device Interface Retrieval (get-interface-config.py)",
                success,
                {"loopbacks": loopbacks, "interfaces": fast_ethernets or gigabit_ethernets},
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
        print(f"\n--> Running Scenario 3: Interface Provisioning (Create Loopback 100 on {self.target_device})")
        status, text = self.client.set_loopback_interface(
            device_name=self.target_device,
            loopback_id="100",
            ip_address="10.100.100.1",
            netmask="255.255.255.255",
            description="Configured via DevNet RESTCONF Python Scenario",
        )
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
        print(f"\n--> Running Scenario 4: Verify Provisioned Interface (GET Loopback 100 on {self.target_device})")
        status, data = self.client.get_loopback_interface(self.target_device, "100")
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
        print(f"\n--> Running Scenario 5: Check Device Sync ({self.target_device})")
        status, data = self.client.check_sync(self.target_device)
        if status == 200 and isinstance(data, dict):
            sync_result = data.get("tailf-ncs:output", {}).get("result")
            print(f"    check-sync result: '{sync_result}'")
            success = sync_result in ("in-sync", "unknown")
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
        """Scenario 6: Out-of-Band Drift Analysis (compare-config on core router)."""
        target_core = "core-rtr01" if "dist-rtr01" in self.target_device else "core-rtr00"
        print(f"\n--> Running Scenario 6: Out-of-Band Drift Analysis (compare-config on {target_core})")
        status, data = self.client.compare_config(target_core)
        if status == 200 and isinstance(data, dict):
            diff = data.get("tailf-ncs:output", {}).get("diff", "")
            print(f"    compare-config executed, diff length: {len(diff)} chars")
            success = True
            self.log_scenario(
                "Scenario 6: Out-of-Band Drift Analysis (compare-config)",
                success,
                {"diff_length": len(diff)},
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
        """Scenario 7: Interface Deletion & State Cleanup."""
        print(f"\n--> Running Scenario 7: Interface Deletion & Cleanup ({self.target_device} Loopback 100)")
        del_status, _ = self.client.delete_loopback_interface(self.target_device, "100")
        print(f"    DELETE Status: {del_status} (Expected 204 No Content)")
        get_status, _ = self.client.get_loopback_interface(self.target_device, "100")
        success = del_status in (200, 204) and get_status in (404, 204)
        self.log_scenario(
            "Scenario 7: Interface Deletion & Cleanup (delete-Ip-address.py)",
            success,
            {"del_status": del_status, "verify_get_status": get_status},
        )
        return success

    def scenario_8_router_services_inspection(self) -> bool:
        """Scenario 8: Router Service Instances Inspection."""
        print("\n--> Running Scenario 8: Router Service Instances Inspection (router:router)")
        status, data = self.client.get_services()
        # In reservable sandbox, router services may be empty (204) or contain services (200)
        success = status in (200, 204)
        service_names = []
        if status == 200 and isinstance(data, dict):
            services = data.get("router:router", [])
            service_names = [s.get("name") for s in services]
        print(f"    Router services status: {status}, services: {service_names}")
        self.log_scenario(
            "Scenario 8: Router Service Instances Inspection",
            success,
            {"status": status, "services": service_names},
        )
        return success

    def scenario_9_device_lifecycle(self) -> bool:
        """Scenario 9: Device Lifecycle Management (Add, Edit, Rename, Delete)."""
        test_dev = "devnet-test-rtr01"
        renamed_dev = "devnet-test-rtr02"
        print(f"\n--> Running Scenario 9: Device Lifecycle (Add {test_dev} -> Edit -> Rename -> Delete)")

        # 1. Add device
        add_st, _ = self.client.add_device(
            name=test_dev,
            address="10.10.20.198",
            port=23,
            authgroup="labadmin",
            ned_id="cisco-ios-cli-6.109:cisco-ios-cli-6.109",
        )
        print(f"    Add device status: {add_st}")

        # 2. Edit device
        edit_st, _ = self.client.edit_device(
            name=test_dev,
            description="Temporary test router for scenario verification",
        )
        print(f"    Edit device status: {edit_st}")

        # 3. Rename device
        rename_st, _ = self.client.rename_device(test_dev, renamed_dev)
        print(f"    Rename device status: {rename_st}")

        # 4. Delete device
        del_st, _ = self.client.delete_device(renamed_dev)
        print(f"    Delete device status: {del_st}")

        success = add_st in (200, 201, 204) and edit_st in (200, 204) and rename_st in (200, 204) and del_st in (200, 204)
        self.log_scenario(
            "Scenario 9: Device Lifecycle Management (Add, Edit, Rename, Delete)",
            success,
            {"add": add_st, "edit": edit_st, "rename": rename_st, "delete": del_st},
        )
        return success

    def scenario_10_port_blocking_acl(self) -> bool:
        """Scenario 10: Port Blocking via Layer 4 Extended ACL (Block TCP 80)."""
        acl_name = "BLOCK_PORT_80"
        print(f"\n--> Running Scenario 10: Port Blocking via ACL (Block TCP Port 80 on {self.target_device})")

        # 1. Create ACL
        create_st, _ = self.client.create_port_block_acl(
            device_name=self.target_device,
            acl_name=acl_name,
            port_number=80,
            protocol="tcp",
        )
        print(f"    Create Port Block ACL status: {create_st}")

        # 2. Teardown / Cleanup ACL
        del_st, _ = self.client.remove_port_block_acl(self.target_device, acl_name)
        print(f"    Remove Port Block ACL status: {del_st}")

        success = create_st in (200, 201, 204) and del_st in (200, 204)
        self.log_scenario(
            "Scenario 10: Port Blocking via Layer 4 Extended ACL",
            success,
            {"create_acl": create_st, "delete_acl": del_st},
        )
        return success

    def scenario_11_interface_shutdown(self) -> bool:
        """Scenario 11: Interface Port Shutdown / Re-enable (Carrier Control)."""
        test_lb = "155"
        print(f"\n--> Running Scenario 11: Interface Administrative Shutdown & Recovery on {self.target_device} Loopback{test_lb}")

        # 1. Ensure test interface exists
        self.client.set_loopback_interface(
            device_name=self.target_device,
            loopback_id=test_lb,
            ip_address="172.16.250.1",
            netmask="255.255.255.255",
            description="Carrier Test Interface",
        )

        # 2. Shutdown interface
        shut_st, _ = self.client.shutdown_interface(
            device_name=self.target_device,
            interface_type="Loopback",
            interface_name=test_lb,
        )
        print(f"    Shutdown interface status: {shut_st}")

        # 3. Re-enable interface (no shutdown)
        enable_st, _ = self.client.enable_interface(
            device_name=self.target_device,
            interface_type="Loopback",
            interface_name=test_lb,
        )
        print(f"    Enable interface status: {enable_st}")

        # 4. Clean up test interface
        self.client.delete_loopback_interface(self.target_device, test_lb)

        success = shut_st in (200, 204) and enable_st in (200, 204)
        self.log_scenario(
            "Scenario 11: Interface Administrative Shutdown & Recovery",
            success,
            {"shutdown": shut_st, "enable": enable_st},
        )
        return success

    def scenario_12_multi_platform_loopbacks(self) -> bool:
        """Scenario 12: Declarative Multi-Platform Loopback Provisioning & Teardown."""
        print("\n--> Running Scenario 12: Multi-Platform Loopback Provisioning (IOS-XR, NX-OS, IOS-XE)")
        targets = [
            {"device": "dist-rtr01", "platform": "ios", "ip": "172.16.1.1", "mask": "255.255.255.255"},
            {"device": "core-rtr01", "platform": "iosxr", "ip": "172.16.0.1", "mask": "255.255.255.255"},
            {"device": "dist-sw01", "platform": "nx", "ip": "172.16.2.1", "mask": "255.255.255.255"},
        ]
        loopback_id = "199"
        results = {}
        all_passed = True

        for t in targets:
            dev = t["device"]
            plat = t["platform"]
            ip = t["ip"]
            mask = t["mask"]

            # Provision
            put_st, _ = self.client.set_loopback_interface(
                device_name=dev,
                loopback_id=loopback_id,
                ip_address=ip,
                netmask=mask,
                description=f"Auto-provisioned {plat.upper()} test loopback",
                platform=plat,
            )
            print(f"    [{dev} ({plat.upper()})] Provision Loopback{loopback_id}: status {put_st}")

            # Verify
            get_st, _ = self.client.get_loopback_interface(dev, loopback_id, platform=plat)
            print(f"    [{dev} ({plat.upper()})] Verify Loopback{loopback_id}: status {get_st}")

            # Teardown
            del_st, _ = self.client.delete_loopback_interface(dev, loopback_id, platform=plat)
            print(f"    [{dev} ({plat.upper()})] Teardown Loopback{loopback_id}: status {del_st}")

            passed = put_st in (200, 201, 204) and get_st == 200 and del_st in (200, 204)
            results[dev] = {"provision": put_st, "verify": get_st, "teardown": del_st}
            if not passed:
                all_passed = False

        self.log_scenario(
            "Scenario 12: Multi-Platform Loopback Provisioning & Teardown",
            all_passed,
            results,
        )
        return all_passed

    def scenario_13_topology_audit(self) -> bool:
        """Scenario 13: Full Topology Fleet Discovery & Sync Audit."""
        print("\n--> Running Scenario 13: Full Topology Fleet Discovery & Sync Audit")
        status, data = self.client.get_devices()
        if status != 200 or not isinstance(data, dict):
            self.log_scenario("Scenario 13: Topology Fleet Audit", False, {"status": status})
            return False

        devices = data.get("tailf-ncs:device", [])
        print(f"    Discovered {len(devices)} devices in NSO CDB:")
        audit_results = {}
        for dev in devices:
            name = dev.get("name")
            addr = dev.get("address", "N/A")
            check_st, check_data = self.client.check_sync(name)
            result = "unknown"
            if check_st == 200 and isinstance(check_data, dict):
                result = check_data.get("tailf-ncs:output", {}).get("result", "unknown")
            print(f"      - {name:<18} ({addr:<14}) | Sync: {result}")
            audit_results[name] = {"address": addr, "check_sync": result}

        success = len(devices) >= 9
        self.log_scenario("Scenario 13: Topology Fleet Audit", success, audit_results)
        return success
