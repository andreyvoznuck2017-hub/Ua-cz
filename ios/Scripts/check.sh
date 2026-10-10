#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p build
python3 Scripts/validate.py
swiftc -frontend -parse Svoyi/*.swift Svoyi/Core/*.swift
swiftc Svoyi/Core/SitePolicy.swift Tests/PolicyTests.swift -o build/policy-tests
build/policy-tests | tee build/policy-tests.txt
node --check Svoyi/Resources/HostBridge.js
node --test Tests/bridge.test.cjs | tee build/bridge-tests.txt
