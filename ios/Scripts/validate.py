#!/usr/bin/env python3
"""Dependency-free checks; the CI separately performs a real Apple SDK build."""
from pathlib import Path
import json, plistlib, re, struct, xml.etree.ElementTree as ET
root = Path(__file__).resolve().parents[1]
info = plistlib.loads((root/'Svoyi/Info.plist').read_bytes())
plistlib.loads((root/'Svoyi/Resources/PrivacyInfo.xcprivacy').read_bytes())
assert not info['NSAppTransportSecurity']['NSAllowsArbitraryLoads']
assert 'UIBackgroundModes' not in info, 'Background calls are not implemented.'
for key in ['NSCameraUsageDescription','NSMicrophoneUsageDescription','NSLocationWhenInUseUsageDescription']:
    assert info[key].strip()
pbx = (root/'Svoyi.xcodeproj/project.pbxproj').read_text()
paths = ['Svoyi/AppDelegate.swift','Svoyi/NotificationCoordinator.swift','Svoyi/SiteViewController.swift','Svoyi/SettingsViewController.swift','Svoyi/Core/SitePolicy.swift','Svoyi/Resources/HostBridge.js','Svoyi/Resources/PrivacyInfo.xcprivacy','Svoyi/Resources/Assets.xcassets']
for name in paths:
    assert (root/name).exists(), name
    assert name in pbx, name
ids = re.findall(r'"([A-F0-9]{24})" = \{', pbx)
refs = re.findall(r'= "([A-F0-9]{24})";', pbx)
assert all(ref in ids for ref in refs)
assert 'CODE_SIGN_ENTITLEMENTS' not in pbx
for name in ['Svoyi.xcodeproj/xcshareddata/xcschemes/Svoyi.xcscheme','Svoyi.xcodeproj/project.xcworkspace/contents.xcworkspacedata']:
    ET.parse(root/name)
iconset = root/'Svoyi/Resources/Assets.xcassets/AppIcon.appiconset'
for item in json.loads((iconset/'Contents.json').read_text())['images']:
    data = (iconset/item['filename']).read_bytes()
    assert data[:8] == b'\x89PNG\r\n\x1a\n'
    assert struct.unpack('>II', data[16:24]) == (1024,1024)
    assert data[25] == 2, 'Icon must be opaque RGB.'
print('PASS: plist, permissions, privacy manifest, PBX references, scheme XML and opaque icon')
