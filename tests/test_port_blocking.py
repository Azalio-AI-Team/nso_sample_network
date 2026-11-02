"""
Offline Mock Unit Tests for NSOPortBlocker.
Run with: PYTHONPATH=.venv/lib/python3.14/site-packages python3 -m unittest tests/test_port_blocking.py
"""

import unittest
from unittest.mock import patch, MagicMock
from nso_port_blocking.port_blocker import NSOPortBlocker


class TestNSOPortBlocker(unittest.TestCase):
    def setUp(self):
        self.blocker = NSOPortBlocker(host="10.10.20.49", port=8080, username="developer", password="dummy")

    def test_create_port_block_acl_mock(self):
        mock_resp = MagicMock(status_code=201, text="Created")
        with patch.object(self.blocker.session, "request", return_value=mock_resp):
            status, text = self.blocker.create_port_block_acl("dist-rtr01", "BLOCK_TELNET", 23, "tcp")
            self.assertEqual(status, 201)
            self.assertEqual(text, "Created")

    def test_apply_interface_acl_mock(self):
        mock_resp = MagicMock(status_code=200, text="OK")
        with patch.object(self.blocker.session, "request", return_value=mock_resp):
            status, text = self.blocker.apply_interface_acl(
                "dist-rtr01", "GigabitEthernet", "0/1", "BLOCK_TELNET", "in"
            )
            self.assertEqual(status, 200)

    def test_block_port_flow_success(self):
        mock_resp_create = MagicMock(status_code=201, text="Created")
        mock_resp_apply = MagicMock(status_code=200, text="OK")
        with patch.object(self.blocker.session, "request", side_effect=[mock_resp_create, mock_resp_apply]):
            ok, msg = self.blocker.block_port_flow(
                device_name="dist-rtr01",
                port_number=23,
                protocol="tcp",
                interface_type="GigabitEthernet",
                interface_name="0/1",
            )
            self.assertTrue(ok)
            self.assertIn("blocked on dist-rtr01", msg)

    def test_unblock_port_flow_success(self):
        mock_resp_remove = MagicMock(status_code=204, text="")
        mock_resp_delete = MagicMock(status_code=204, text="")
        with patch.object(self.blocker.session, "request", side_effect=[mock_resp_remove, mock_resp_delete]):
            ok, msg = self.blocker.unblock_port_flow(
                device_name="dist-rtr01",
                port_number=23,
                protocol="tcp",
                interface_type="GigabitEthernet",
                interface_name="0/1",
            )
            self.assertTrue(ok)
            self.assertIn("unblocked", msg)

    def test_shut_and_enable_interface(self):
        mock_resp_shut = MagicMock(status_code=200, text="OK")
        mock_resp_enable = MagicMock(status_code=204, text="")

        with patch.object(self.blocker.session, "request", return_value=mock_resp_shut):
            st, _ = self.blocker.shut_interface("dist-rtr01", "GigabitEthernet", "0/2")
            self.assertEqual(st, 200)

        with patch.object(self.blocker.session, "request", return_value=mock_resp_enable):
            st, _ = self.blocker.enable_interface("dist-rtr01", "GigabitEthernet", "0/2")
            self.assertEqual(st, 204)

    def test_list_acls_mock(self):
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {
            "tailf-ned-cisco-ios:extended": [
                {"id": "BLOCK_TELNET"}
            ]
        }
        with patch.object(self.blocker.session, "request", return_value=mock_resp):
            status, data = self.blocker.list_acls("dist-rtr01")
            self.assertEqual(status, 200)
            self.assertEqual(data["tailf-ned-cisco-ios:extended"][0]["id"], "BLOCK_TELNET")


if __name__ == "__main__":
    unittest.main()
