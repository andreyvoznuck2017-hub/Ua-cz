#!/bin/bash
# Compile a real ARM64 iPhone application. This does NOT pretend to sign it for installation.
set -euo pipefail
cd "$(dirname "$0")/.."
[ "$(uname -s)" = Darwin ] || { echo 'Apple SDK on macOS is required'; exit 1; }
mkdir -p build
swift Scripts/prepare-icon.swift ../icon-source.png Svoyi/Resources/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png
bash Scripts/check.sh 2>&1 | tee build/source-checks.log
if ! xcodebuild -project Svoyi.xcodeproj -scheme Svoyi -configuration Release -sdk iphoneos \
  -destination 'generic/platform=iOS' -derivedDataPath build/Device \
  CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO CODE_SIGN_IDENTITY='' \
  build > build/xcode-device.log 2>&1; then
  tail -n 180 build/xcode-device.log
  exit 1
fi
tail -n 8 build/xcode-device.log
APP=build/Device/Build/Products/Release-iphoneos/Svoyi.app
test -x "$APP/Svoyi"
file "$APP/Svoyi" | tee build/binary-info.txt
xcrun lipo -info "$APP/Svoyi" | tee -a build/binary-info.txt
/usr/libexec/PlistBuddy -c 'Print :CFBundleSupportedPlatforms:0' "$APP/Info.plist" | grep -x iPhoneOS
codesign -dv --verbose=2 "$APP" > build/signature-status.txt 2>&1 || true
mkdir -p build/Package/Payload
ditto --norsrc --noextattr "$APP" build/Package/Payload/Svoyi.app
(cd build/Package && zip -qry ../Svoyi-1.0.1-UNSIGNED.ipa Payload)
shasum -a 256 build/Svoyi-1.0.1-UNSIGNED.ipa | tee build/SHA256SUMS.txt
python3 - <<'PY'
import json, os, plistlib, hashlib
from pathlib import Path
app=Path('build/Device/Build/Products/Release-iphoneos/Svoyi.app')
p=plistlib.loads((app/'Info.plist').read_bytes())
ipa=Path('build/Svoyi-1.0.1-UNSIGNED.ipa')
report={'bundle_id':p['CFBundleIdentifier'],'version':p['CFBundleShortVersionString'],
'build':p['CFBundleVersion'],'platform':p['CFBundleSupportedPlatforms'],'minimum_ios':p['MinimumOSVersion'],
'device_sdk_build':True,'apple_distribution_signed':False,'installable_without_personal_signing':False,
'real_iphone_tested':False,'server_push_implemented':False,'background_calls_implemented':False,
'commit':os.environ.get('GITHUB_SHA'),'sha256':hashlib.sha256(ipa.read_bytes()).hexdigest()}
Path('build/build-report.json').write_text(json.dumps(report,indent=2)+'\n')
PY
if bash Scripts/simulator-smoke.sh > build/simulator-smoke.log 2>&1; then
  printf 'Simulator install and launch completed; inspect screenshot. Not a full functional test.\n' | tee build/simulator-result.txt
else
  printf 'Simulator smoke test did not complete. See simulator-smoke.log. Device IPA build succeeded.\n' | tee build/simulator-result.txt
  tail -n 100 build/simulator-smoke.log
fi
