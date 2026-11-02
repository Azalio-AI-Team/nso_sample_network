"""
Offline Mock Unit Tests for NSODeviceManager.
Run with: PYTHONPATH=.venv/lib/python3.14/site-packages python3 -m unittest tests/test_device_manager.py
"""

import unittest
from unittest.mock import patch, MagicMock
from nso_device_manager.device_manager import NSODeviceManager


class TestNSODeviceManager(unittest.TestCase):
    def setUp(self):
        self.mgr = NSODeviceManager(host="10.10.20.49", port=8080, username="developer", password="dummy")

    def test_init_scheme_autodetection(self):
        mgr_http = NSODeviceManager(host="10.10.20.49", port=8080)
        self.assertEqual(mgr_http.scheme, "http")

        mgr_https = NSODeviceManager(host="sandbox-nso-1.cisco.com", port=443)
        self.assertEqual(mgr_https.scheme, "https")

    def test_list_devices_mock(self):
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {
            "tailf-ncs:device": [
                {"name": "dist-rtr01", "address": "10.10.20.175", "port": 23, "authgroup": "default"},
                {"name": "core-rtr01", "address": "10.10.20.173", "port": 23, "authgroup": "default"},
            ]
        }
        with patch.object(self.mgr.session, "request", return_value=mock_resp):
            status, data = self.mgr.list_devices()
            self.assertEqual(status, 200)
            self.assertEqual(len(data["tailf-ncs:device"]), 2)

    def test_add_device_mock(self):
        mock_resp = MagicMock(status_code=201, text="Created")
        with patch.object(self.mgr.session, "request", return_value=mock_resp):
            status, text = self.mgr.add_device(
                name="lab-rtr99",
                address="10.10.20.199",
                port=23,
                authgroup="default",
                ned_id="ios",
            )
            self.assertEqual(status, 201)
            self.assertEqual(text, "Created")

    def test_edit_device_mock(self):
        mock_resp = MagicMock(status_code=200, text="OK")
        with patch.object(self.mgr.session, "request", return_value=mock_resp):
            status, text = self.mgr.edit_device(
                name="lab-rtr99",
                description="Updated lab router",
            )
            self.assertEqual(status, 200)

    def test_rename_device_mock(self):
        mock_get = MagicMock(status_code=200)
        mock_get.json.return_value = {
            "tailf-ncs:device": [{"name": "lab-rtr99", "address": "10.10.20.199"}]
        }
        mock_put = MagicMock(status_code=201, text="Created")
        mock_del = MagicMock(status_code=204, text="")

        with patch.object(self.mgr.session, "request", side_effect=[mock_get, mock_put, mock_del]):
            status, msg = self.mgr.rename_device("lab-rtr99", "lab-rtr100")
            self.assertEqual(status, 200)
            self.assertIn("Device successfully renamed", msg)

    def test_delete_device_mock(self):
        mock_resp = MagicMock(status_code=204, text="")
        with patch.object(self.mgr.session, "request", return_value=mock_resp):
            status, _ = self.mgr.delete_device("lab-rtr100")
            self.assertEqual(status, 204)

    def test_sync_from_mock(self):
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {"tailf-ncs:output": {"result": True}}
        with patch.object(self.mgr.session, "request", return_value=mock_resp):
            status, data = self.mgr.sync_from("dist-rtr01")
            self.assertEqual(status, 200)
            self.assertTrue(data["tailf-ncs:output"]["result"])


if __name__ == "__main__":
    unittest.main()
