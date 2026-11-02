"""
Unit/Integration Tests for Cisco NSO RESTCONF Automation Scenarios.
Run with: uv run python -m unittest tests/test_nso.py
"""

import unittest
from nso_client import NSOClient


class TestNSOScenarios(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = NSOClient()

    def test_01_fleet_discovery(self):
        """Scenario 1: Test discovering devices from NSO CDB."""
        status, data = self.client.get_devices()
        self.assertEqual(status, 200)
        self.assertIn("tailf-ncs:device", data)
        device_names = [d["name"] for d in data["tailf-ncs:device"]]
        self.assertIn("dist-rtr00", device_names)
        self.assertIn("core-rtr00", device_names)
        self.assertGreaterEqual(len(device_names), 10)

    def test_02_get_interface_config(self):
        """Scenario 2: Test retrieving interface configuration from dist-rtr00."""
        status, data = self.client.get_device_interfaces("dist-rtr00")
        self.assertEqual(status, 200)
        interfaces = data.get("tailf-ned-cisco-ios:interface", {})
        self.assertIn("FastEthernet", interfaces)
        self.assertIn("Loopback", interfaces)

    def test_03_loopback_lifecycle(self):
        """Scenarios 3, 4, 5, 7: Test full lifecycle (Provision, Verify, Check-Sync, Delete)."""
        device = "dist-rtr00"
        lb_id = "100"
        test_ip = "10.100.100.1"
        test_mask = "255.255.255.255"
        test_desc = "Test Loopback Lifecycle via UV"

        # 1. Provision Loopback 100
        status, _ = self.client.set_loopback_interface(
            device_name=device,
            loopback_id=lb_id,
            ip_address=test_ip,
            netmask=test_mask,
            description=test_desc,
        )
        self.assertIn(status, (200, 201, 204))

        # 2. Verify Loopback 100
        status, data = self.client.get_loopback_interface(device, lb_id)
        self.assertEqual(status, 200)
        lb_entry = data["tailf-ned-cisco-ios:Loopback"][0]
        self.assertEqual(lb_entry["description"], test_desc)
        self.assertEqual(lb_entry["ip"]["address"]["primary"]["address"], test_ip)
        self.assertEqual(lb_entry["ip"]["address"]["primary"]["mask"], test_mask)

        # 3. Check Sync
        status, sync_data = self.client.check_sync(device)
        self.assertEqual(status, 200)
        self.assertEqual(sync_data["tailf-ncs:output"]["result"], "in-sync")

        # 4. Delete Loopback 100
        del_status, _ = self.client.delete_loopback_interface(device, lb_id)
        self.assertIn(del_status, (200, 204))

        # 5. Verify 404 after deletion
        get_status, _ = self.client.get_loopback_interface(device, lb_id)
        self.assertEqual(get_status, 404)

        # 6. Verify device remains in-sync
        status, sync_data = self.client.check_sync(device)
        self.assertEqual(status, 200)
        self.assertEqual(sync_data["tailf-ncs:output"]["result"], "in-sync")

    def test_04_compare_config_drift(self):
        """Scenario 6: Test drift detection on out-of-sync core-rtr01."""
        status, data = self.client.compare_config("core-rtr01")
        self.assertEqual(status, 200)
        diff = data.get("tailf-ncs:output", {}).get("diff", "")
        self.assertTrue(len(diff) > 0)
        self.assertIn("core-rtr01", diff)

    def test_05_router_services(self):
        """Scenario 8: Test router service models."""
        status, data = self.client.get_services()
        self.assertEqual(status, 200)
        services = data.get("router:router", [])
        service_names = [s["name"] for s in services]
        self.assertIn("CoreDevices", service_names)
        self.assertIn("DistDevices", service_names)


if __name__ == "__main__":
    unittest.main()
