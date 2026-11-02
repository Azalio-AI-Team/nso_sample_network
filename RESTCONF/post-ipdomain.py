#!/usr/bin/python
#
# Copyright (c) 2018  Krishna Kotha <krkotha@cisco.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.
#
# This script configures IP domain using POST/PUT operation via RESTCONF

import os
import sys
import argparse
import requests

# disable warnings from SSL/TLS certificates
requests.packages.urllib3.disable_warnings()

# Configuration defaults (supports NSO and direct device)
DEFAULT_HOST = os.getenv('RESTCONF_HOST', os.getenv('NSO_HOST', 'sandbox-nso-1.cisco.com'))
DEFAULT_USER = os.getenv('RESTCONF_USER', os.getenv('NSO_USER', 'namansin'))
DEFAULT_PASS = os.getenv('RESTCONF_PASSWORD', os.getenv('NSO_PASSWORD', '#u*^x6^3t6DGEcD'))
DEFAULT_DEVICE = os.getenv('RESTCONF_DEVICE', 'dist-rtr00')


def main():
    """Main method that configures the IP domain name via RESTCONF."""
    parser = argparse.ArgumentParser(description="Configure IP domain name via RESTCONF")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Hostname/IP of device or NSO")
    parser.add_argument("--user", default=DEFAULT_USER, help="Username")
    parser.add_argument("--password", default=DEFAULT_PASS, help="Password")
    parser.add_argument("--device", default=DEFAULT_DEVICE, help="Target device name (for NSO)")
    parser.add_argument("--domain", default="cisco.com", help="Domain name to set")
    args = parser.parse_args()

    headers = {
        'Content-Type': 'application/yang-data+json',
        'Accept': 'application/yang-data+json'
    }

    if "nso" in args.host.lower() or args.device:
        url = f"https://{args.host}/restconf/data/tailf-ncs:devices/device={args.device}/config/tailf-ned-cisco-ios:ip/domain"
        payload = {"tailf-ned-cisco-ios:domain": {"name": args.domain}}
        method = "PUT"
    else:
        url = f"https://{args.host}/restconf/data/Cisco-IOS-XE-native:native/ip/domain"
        payload = {"name": args.domain}
        method = "POST"

    print(f"Sending {method} to {url}...")
    response = requests.request(
        method,
        url,
        auth=(args.user, args.password),
        json=payload,
        headers=headers,
        verify=False,
        timeout=25
    )

    print(f"HTTP Status: {response.status_code}")
    if response.text:
        print(response.text)
    return 0 if response.status_code in (200, 201, 204) else 1


if __name__ == '__main__':
    sys.exit(main())
