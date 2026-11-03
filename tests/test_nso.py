"""
Unit/Integration Tests for Cisco NSO RESTCONF Automation Scenarios.
Run with: uv run python -m unittest tests/test_nso.py
"""

import os
import unittest
from unittest.mock import MagicMock, patch

from nso_client import NSOClient


class TestNSOScenarios(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.target_device = os.getenv("RESTCONF_DEVICE", "dist-rtr01")
        cls.client = NSOClient()

    def test_01_fleet_discovery_mock(self):
        """Scenario 1: Test discovering devices from NSO CDB (offline mock)."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tailf-ncs:device": [
                {"name": "dist-rtr01", "address": "10.10.20.175"},
                {"name": "core-rtr01", "address": "10.10.20.173"},
                {"name": "edge-firewall01", "address": "10.10.20.171"},
                {"name": "edge-sw01", "address": "10.10.20.172"},
                {"name": "dev-dist-rtr01", "address": "10.10.20.176"},
                {"name": "dev-core-rtr01", "address": "10.10.20.174"},
                {"name": "dist-sw01", "address": "10.10.20.177"},
                {"name": "dev-dist-sw01", "address": "10.10.20.178"},
                {"name": "internet-rtr01", "address": "10.10.20.181"},
            ]
        }

        with patch.object(self.client.session, "request", return_value=mock_response):
            status, data = self.client.get_devices()
            self.assertEqual(status, 200)
            self.assertIn("tailf-ncs:device", data)
            device_names = [d["name"] for d in data["tailf-ncs:device"]]
            self.assertIn("dist-rtr01", device_names)
            self.assertIn("core-rtr01", device_names)
            self.assertGreaterEqual(len(device_names), 9)

    def test_02_device_lifecycle_mock(self):
        """Scenario 9: Test Device Lifecycle methods (add, edit, delete, rename)."""
        mock_resp_201 = MagicMock(status_code=201, text="Created")
        mock_resp_200 = MagicMock(status_code=200, text="OK")
        mock_resp_204 = MagicMock(status_code=204, text="")

        # 1. Add device
        with patch.object(self.client.session, "request", return_value=mock_resp_201):
            st, _ = self.client.add_device("test-rtr01", "10.10.20.190")
            self.assertEqual(st, 201)

        # 2. Edit device
        with patch.object(self.client.session, "request", return_value=mock_resp_200):
            st, _ = self.client.edit_device("test-rtr01", description="Updated description")
            self.assertEqual(st, 200)

        # 3. Rename device
        mock_get_dev = MagicMock(status_code=200)
        mock_get_dev.json.return_value = {
            "tailf-ncs:device": [{"name": "test-rtr01", "address": "10.10.20.190"}]
        }
        with patch.object(self.client.session, "request", side_effect=[mock_get_dev, mock_resp_201, mock_resp_204]):
            st, _ = self.client.rename_device("test-rtr01", "test-rtr02")
            self.assertEqual(st, 200)

        # 4. Delete device
        with patch.object(self.client.session, "request", return_value=mock_resp_204):
            st, _ = self.client.delete_device("test-rtr02")
            self.assertEqual(st, 204)

    def test_03_port_blocking_mock(self):
        """Scenario 10 & 11: Test Port Blocking methods (ACL and shutdown)."""
        mock_resp_201 = MagicMock(status_code=201, text="Created")
        mock_resp_200 = MagicMock(status_code=200, text="OK")
        mock_resp_204 = MagicMock(status_code=204, text="")

        # Create ACL
        with patch.object(self.client.session, "request", return_value=mock_resp_201):
            st, _ = self.client.create_port_block_acl("dist-rtr01", "BLOCK_TELNET", 23, "tcp")
            self.assertEqual(st, 201)

        # Apply ACL
        with patch.object(self.client.session, "request", return_value=mock_resp_200):
            st, _ = self.client.apply_interface_acl("dist-rtr01", "GigabitEthernet", "0/1", "BLOCK_TELNET")
            self.assertEqual(st, 200)

        # Remove ACL
        with patch.object(self.client.session, "request", return_value=mock_resp_204):
            st, _ = self.client.remove_port_block_acl("dist-rtr01", "BLOCK_TELNET")
            self.assertEqual(st, 204)

        # Shutdown interface
        with patch.object(self.client.session, "request", return_value=mock_resp_200):
            st, _ = self.client.shutdown_interface("dist-rtr01", "GigabitEthernet", "0/2")
            self.assertEqual(st, 200)

        # Enable interface
        with patch.object(self.client.session, "request", return_value=mock_resp_204):
            st, _ = self.client.enable_interface("dist-rtr01", "GigabitEthernet", "0/2")
            self.assertEqual(st, 204)

    def test_04_multi_platform_loopbacks_mock(self):
        """Scenario 12: Test multi-platform loopback creation across IOS-XE, IOS-XR, NX-OS."""
        mock_resp_201 = MagicMock(status_code=201, text="Created")
        mock_resp_200 = MagicMock(status_code=200)
        mock_resp_200.json.return_value = {"status": "ok"}

        # IOS-XE
        with patch.object(self.client.session, "request", return_value=mock_resp_201) as mock_req:
            st, _ = self.client.set_loopback_interface("dist-rtr01", "105", "172.16.1.5", "255.255.255.255")
            self.assertEqual(st, 201)
            self.assertIn("tailf-ned-cisco-ios:interface/Loopback=105", mock_req.call_args[1]["url"])

        # IOS-XR
        with patch.object(self.client.session, "request", return_value=mock_resp_201) as mock_req:
            st, _ = self.client.set_loopback_interface("core-rtr01", "105", "172.16.0.5", "255.255.255.255", platform="iosxr")
            self.assertEqual(st, 201)
            self.assertIn("tailf-ned-cisco-ios-xr:interface/Loopback=105", mock_req.call_args[1]["url"])

        # NX-OS
        with patch.object(self.client.session, "request", return_value=mock_resp_201) as mock_req:
            st, _ = self.client.set_loopback_interface("dist-sw01", "105", "172.16.2.5", "255.255.255.255", platform="nx")
            self.assertEqual(st, 201)
            self.assertIn("tailf-ned-cisco-nx:interface/loopback=105", mock_req.call_args[1]["url"])

        # Interface description update
        with patch.object(self.client.session, "request", return_value=mock_resp_200):
            st, _ = self.client.update_interface_description("dist-rtr01", "GigabitEthernet", "0/1", "Test desc")
            self.assertEqual(st, 200)


if __name__ == "__main__":
    unittest.main()
