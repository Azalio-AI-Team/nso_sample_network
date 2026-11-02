#!/usr/bin/env python3
"""
Main entry point for running Cisco NSO Network Automation Scenarios.
Ported from CiscoDevNet/python_code_samples_network to Cisco NSO sandbox.
"""

import sys
from nso_scenarios import NSOScenarioRunner


def main():
    runner = NSOScenarioRunner()
    success = runner.run_all()
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
