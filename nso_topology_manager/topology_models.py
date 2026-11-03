"""
Topology Data Models and Sandbox Definitions for Cisco DevNet Reservable NSO Sandbox.
Maps all 9 managed devices across tiers, NEDs, and role definitions.
Reference: https://developer.cisco.com/sandbox/detail/nso-sandbox
"""

from typing import Any

TOPOLOGY_TIERS = {
    "CORE": "Core Backbone Tier",
    "DISTRIBUTION": "Distribution & Aggregation Tier",
    "DC_SWITCH": "Data Center Switching Tier",
    "ACCESS": "Edge & Access Switching Tier",
    "SECURITY": "Perimeter Security & Firewall Tier",
    "WAN": "Internet & WAN Gateway Tier",
}

TOPOLOGY_DEVICES: dict[str, dict[str, Any]] = {
    "core-rtr01": {
        "name": "core-rtr01",
        "ip": "10.10.20.173",
        "tier": "CORE",
        "os": "IOS-XR",
        "protocol": "telnet",
        "port": 23,
        "ned_id": "tailf-ned-cisco-iosxr-id:cisco-iosxr-cli-7.65",
        "platform_family": "iosxr",
        "description": "Primary Core Router (Cisco IOS-XR 7.4.1)",
        "default_loopback_ip": "172.16.0.1",
        "default_loopback_mask": "255.255.255.255",
        "uplinks": ["dev-core-rtr01", "dist-rtr01"],
    },
    "dev-core-rtr01": {
        "name": "dev-core-rtr01",
        "ip": "10.10.20.174",
        "tier": "CORE",
        "os": "IOS-XR",
        "protocol": "telnet",
        "port": 23,
        "ned_id": "tailf-ned-cisco-iosxr-id:cisco-iosxr-cli-7.65",
        "platform_family": "iosxr",
        "description": "Secondary Core Router (Cisco IOS-XR 7.4.1)",
        "default_loopback_ip": "172.16.0.2",
        "default_loopback_mask": "255.255.255.255",
        "uplinks": ["core-rtr01", "dev-dist-rtr01"],
    },
    "dist-rtr01": {
        "name": "dist-rtr01",
        "ip": "10.10.20.175",
        "tier": "DISTRIBUTION",
        "os": "IOS-XE",
        "protocol": "ssh",
        "port": 22,
        "ned_id": "tailf-ned-cisco-ios-id:cisco-ios-cli-6.109",
        "platform_family": "ios",
        "description": "Primary Distribution Router (Cisco IOS-XE 17.6.1a)",
        "default_loopback_ip": "172.16.1.1",
        "default_loopback_mask": "255.255.255.255",
        "uplinks": ["core-rtr01", "dev-dist-rtr01", "dist-sw01"],
    },
    "dev-dist-rtr01": {
        "name": "dev-dist-rtr01",
        "ip": "10.10.20.176",
        "tier": "DISTRIBUTION",
        "os": "IOS-XE",
        "protocol": "ssh",
        "port": 22,
        "ned_id": "tailf-ned-cisco-ios-id:cisco-ios-cli-6.109",
        "platform_family": "ios",
        "description": "Secondary Distribution Router (Cisco IOS-XE 17.6.1a)",
        "default_loopback_ip": "172.16.1.2",
        "default_loopback_mask": "255.255.255.255",
        "uplinks": ["dev-core-rtr01", "dist-rtr01", "dev-dist-sw01"],
    },
    "dist-sw01": {
        "name": "dist-sw01",
        "ip": "10.10.20.177",
        "tier": "DC_SWITCH",
        "os": "NX-OS",
        "protocol": "ssh",
        "port": 22,
        "ned_id": "tailf-ned-cisco-nx-id:cisco-nx-cli-5.27",
        "platform_family": "nx",
        "description": "Primary Distribution Switch (Cisco Nexus NX-OS 9.3)",
        "default_loopback_ip": "172.16.2.1",
        "default_loopback_mask": "255.255.255.255",
        "uplinks": ["dist-rtr01", "dev-dist-sw01"],
    },
    "dev-dist-sw01": {
        "name": "dev-dist-sw01",
        "ip": "10.10.20.178",
        "tier": "DC_SWITCH",
        "os": "NX-OS",
        "protocol": "ssh",
        "port": 22,
        "ned_id": "tailf-ned-cisco-nx-id:cisco-nx-cli-5.27",
        "platform_family": "nx",
        "description": "Secondary Distribution Switch (Cisco Nexus NX-OS 9.3)",
        "default_loopback_ip": "172.16.2.2",
        "default_loopback_mask": "255.255.255.255",
        "uplinks": ["dev-dist-rtr01", "dist-sw01"],
    },
    "edge-firewall01": {
        "name": "edge-firewall01",
        "ip": "10.10.20.171",
        "tier": "SECURITY",
        "os": "ASA",
        "protocol": "telnet",
        "port": 23,
        "ned_id": "tailf-ned-cisco-asa-id:cisco-asa-cli-6.18",
        "platform_family": "asa",
        "description": "Perimeter Firewall (Cisco ASAv 9.16)",
        "default_loopback_ip": "172.16.254.1",
        "default_loopback_mask": "255.255.255.255",
        "uplinks": ["internet-rtr01", "edge-sw01"],
    },
    "edge-sw01": {
        "name": "edge-sw01",
        "ip": "10.10.20.172",
        "tier": "ACCESS",
        "os": "IOS",
        "protocol": "telnet",
        "port": 23,
        "ned_id": "tailf-ned-cisco-ios-id:cisco-ios-cli-6.109",
        "platform_family": "ios",
        "description": "Edge Access Switch (Cisco IOS 15.2)",
        "default_loopback_ip": "172.16.10.1",
        "default_loopback_mask": "255.255.255.255",
        "uplinks": ["edge-firewall01"],
    },
    "internet-rtr01": {
        "name": "internet-rtr01",
        "ip": "10.10.20.181",
        "tier": "WAN",
        "os": "IOS-XE",
        "protocol": "ssh",
        "port": 22,
        "ned_id": "tailf-ned-cisco-ios-id:cisco-ios-cli-6.109",
        "platform_family": "ios",
        "description": "Internet / WAN Gateway Router (Cisco IOS-XE 17.6.1a)",
        "default_loopback_ip": "198.51.100.1",
        "default_loopback_mask": "255.255.255.255",
        "uplinks": ["edge-firewall01"],
    },
}


def get_nodes_by_tier(tier: str) -> list[dict[str, Any]]:
    """Return all topology nodes belonging to a specific tier."""
    tier_upper = tier.upper()
    return [d for d in TOPOLOGY_DEVICES.values() if d["tier"] == tier_upper]


def get_device_metadata(name: str) -> dict[str, Any]:
    """Retrieve metadata for a device, with safe defaults if not found."""
    return TOPOLOGY_DEVICES.get(name, {
        "name": name,
        "ip": "unknown",
        "tier": "UNKNOWN",
        "os": "IOS-XE",
        "ned_id": "tailf-ned-cisco-ios-id:cisco-ios-cli-6.109",
        "platform_family": "ios",
        "description": f"Custom device {name}",
        "default_loopback_ip": "172.16.99.1",
        "default_loopback_mask": "255.255.255.255",
        "uplinks": [],
    })
