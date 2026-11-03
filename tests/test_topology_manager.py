"""
Offline Unit Tests for Cisco NSO Topology Manager Package.
Validates multi-tier topology discovery, multi-NED loopback provisioning (IOS-XE, IOS-XR, NX-OS),
interface updates, and sync validation using mocked RESTCONF HTTP responses.
"""

import unittest
from unittest.mock import MagicMock, patch

from nso_topology_manager.topology_manager import NSOTopologyManager
from nso_topology_manager.topology_models import TOPOLOGY_DEVICES, get_device_metadata


class TestNSOTopologyManager(unittest.TestCase):
    def setUp(self):
        self.manager = NSOTopologyManager(host="10.10.20.47", port=8080, username="developer")

    def test_01_topology_models(self):
        """Test topology metadata lookup and tier mapping."""
        core_meta = get_device_metadata("core-rtr01")
        self.assertEqual(core_meta["os"], "IOS-XR")
        self.assertEqual(core_meta["tier"], "CORE")
        self.assertEqual(core_meta["platform_family"], "iosxr")

        dist_meta = get_device_metadata("dist-rtr01")
        self.assertEqual(dist_meta["os"], "IOS-XE")
        self.assertEqual(dist_meta["tier"], "DISTRIBUTION")

        nx_meta = get_device_metadata("dist-sw01")
        self.assertEqual(nx_meta["os"], "NX-OS")
        self.assertEqual(nx_meta["platform_family"], "nx")

        self.assertGreaterEqual(len(TOPOLOGY_DEVICES), 9)

    def test_02_audit_topology_mock(self):
        """Test auditing managed devices against the topology model."""
        mock_devices_resp = MagicMock(status_code=200)
        mock_devices_resp.json.return_value = {
            "tailf-ncs:device": [
                {"name": "core-rtr01", "address": "10.10.20.173"},
                {"name": "dist-rtr01", "address": "10.10.20.175"},
                {"name": "dist-sw01", "address": "10.10.20.177"},
            ]
        }
        mock_sync_resp = MagicMock(status_code=200)
        mock_sync_resp.json.return_value = {"tailf-ncs:output": {"result": "in-sync"}}

        with patch.object(self.manager.session, "request", side_effect=[mock_devices_resp, mock_sync_resp, mock_sync_resp, mock_sync_resp]):
            audit = self.manager.audit_topology()
            self.assertEqual(audit["device_count"], 3)
            dev_names = [d["device"] for d in audit["devices"]]
            self.assertIn("core-rtr01", dev_names)
            self.assertIn("dist-rtr01", dev_names)
            self.assertIn("dist-sw01", dev_names)
            for d in audit["devices"]:
                self.assertEqual(d["sync_state"], "in-sync")

    def test_03_configure_loopback_ios_mock(self):
        """Test configuring loopback on Cisco IOS-XE (dist-rtr01)."""
        mock_resp = MagicMock(status_code=201, text="Created")
        with patch.object(self.manager.session, "request", return_value=mock_resp) as mock_req:
            st, _ = self.manager.configure_loopback("dist-rtr01", "101", "172.16.1.1", "255.255.255.255", "Test IOS Loopback")
            self.assertEqual(st, 201)
            # Verify URL contains tailf-ned-cisco-ios
            call_url = mock_req.call_args[1]["url"]
            self.assertIn("tailf-ned-cisco-ios:interface/Loopback=101", call_url)
            # Verify payload contains primary address
            call_json = mock_req.call_args[1]["json"]
            self.assertIn("tailf-ned-cisco-ios:Loopback", call_json)
            self.assertEqual(call_json["tailf-ned-cisco-ios:Loopback"]["ip"]["address"]["primary"]["address"], "172.16.1.1")

    def test_04_configure_loopback_iosxr_mock(self):
        """Test configuring loopback on Cisco IOS-XR (core-rtr01)."""
        mock_resp = MagicMock(status_code=201, text="Created")
        with patch.object(self.manager.session, "request", return_value=mock_resp) as mock_req:
            st, _ = self.manager.configure_loopback("core-rtr01", "101", "172.16.0.1", "255.255.255.255", "Test XR Loopback")
            self.assertEqual(st, 201)
            # Verify URL contains tailf-ned-cisco-ios-xr
            call_url = mock_req.call_args[1]["url"]
            self.assertIn("tailf-ned-cisco-ios-xr:interface/Loopback=101", call_url)
            # Verify payload contains ipv4.address.ip
            call_json = mock_req.call_args[1]["json"]
            self.assertIn("tailf-ned-cisco-ios-xr:Loopback", call_json)
            self.assertEqual(call_json["tailf-ned-cisco-ios-xr:Loopback"]["ipv4"]["address"]["ip"], "172.16.0.1")

    def test_05_configure_loopback_nxos_mock(self):
        """Test configuring loopback on Cisco NX-OS (dist-sw01)."""
        mock_resp = MagicMock(status_code=201, text="Created")
        with patch.object(self.manager.session, "request", return_value=mock_resp) as mock_req:
            st, _ = self.manager.configure_loopback("dist-sw01", "101", "172.16.2.1", "255.255.255.255", "Test NX Loopback")
            self.assertEqual(st, 201)
            # Verify URL contains tailf-ned-cisco-nx:interface/loopback
            call_url = mock_req.call_args[1]["url"]
            self.assertIn("tailf-ned-cisco-nx:interface/loopback=101", call_url)
            # Verify payload contains ip.address.ipaddr
            call_json = mock_req.call_args[1]["json"]
            self.assertIn("tailf-ned-cisco-nx:loopback", call_json)
            self.assertEqual(call_json["tailf-ned-cisco-nx:loopback"]["ip"]["address"]["ipaddr"], "172.16.2.1/32")

    def test_06_update_interface_description_mock(self):
        """Test updating interface description via atomic PATCH."""
        mock_resp = MagicMock(status_code=200, text="OK")
        with patch.object(self.manager.session, "request", return_value=mock_resp) as mock_req:
            st, _ = self.manager.update_interface_description("dist-rtr01", "GigabitEthernet", "0/1", "Uplink to core")
            self.assertEqual(st, 200)
            call_url = mock_req.call_args[1]["url"]
            self.assertIn("GigabitEthernet=0%2F1", call_url)

    def test_07_deploy_and_teardown_baseline_mock(self):
        """Test deploying and tearing down baseline loopbacks."""
        mock_resp_201 = MagicMock(status_code=201, text="Created")
        mock_resp_204 = MagicMock(status_code=204, text="")

        # Deploy
        with patch.object(self.manager.session, "request", return_value=mock_resp_201):
            deploy_res = self.manager.deploy_baseline("100")
            self.assertTrue(all(r["success"] for r in deploy_res.values()))

        # Teardown
        with patch.object(self.manager.session, "request", return_value=mock_resp_204):
            teardown_res = self.manager.teardown_baseline("100")
            self.assertTrue(all(r["success"] for r in teardown_res.values()))

    def test_08_verify_sync_mock(self):
        """Test verify_sync method."""
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {"tailf-ncs:output": {"result": "in-sync"}}

        with patch.object(self.manager.session, "request", return_value=mock_resp):
            sync_res = self.manager.verify_sync("dist-rtr01")
            self.assertEqual(sync_res["dist-rtr01"], "in-sync")


if __name__ == "__main__":
    unittest.main()
