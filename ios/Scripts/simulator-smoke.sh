#!/bin/bash
set -euo pipefail
xcodebuild -project Svoyi.xcodeproj -scheme Svoyi -configuration Debug -sdk iphonesimulator \
 -destination 'generic/platform=iOS Simulator' -derivedDataPath build/Simulator ARCHS="$(uname -m)" \
 CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO CODE_SIGN_IDENTITY='' build > build/xcode-simulator.log 2>&1
xcrun simctl list devices available --json > build/simulator-devices.json
SIM=$(python3 - <<'PY'
import json
from pathlib import Path
j=json.loads(Path('build/simulator-devices.json').read_text())
choices=[d for k,v in sorted(j['devices'].items(),reverse=True) if 'iOS' in k for d in v if d.get('isAvailable') and 'iPhone' in d['name']]
if not choices: raise SystemExit('No available iPhone simulator')
d=choices[0]
Path('build/simulator-selected.json').write_text(json.dumps(d,indent=2)+'\n')
print(d['udid'])
PY
)
xcrun simctl boot "$SIM" || true
xcrun simctl bootstatus "$SIM" -b
xcrun simctl status_bar "$SIM" override --time '9:41' --dataNetwork wifi --wifiMode active --wifiBars 3 --batteryState charged --batteryLevel 100
xcrun simctl install "$SIM" build/Simulator/Build/Products/Debug-iphonesimulator/Svoyi.app
xcrun simctl launch "$SIM" eu.jkunis.svoyi.ios | tee build/simulator-launch.txt
sleep 20
xcrun simctl io "$SIM" screenshot build/iPhone-simulator.png
xcrun simctl spawn "$SIM" launchctl list | grep eu.jkunis.svoyi.ios | tee build/simulator-process.txt
xcrun simctl shutdown "$SIM"
