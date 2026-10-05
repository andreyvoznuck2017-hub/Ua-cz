#!/usr/bin/env bash
set -u

mkdir -p qa-output

echo "=== DEVICE ===" > qa-output/device.txt
adb shell getprop ro.product.model >> qa-output/device.txt 2>&1 || true
adb shell getprop ro.build.version.release >> qa-output/device.txt 2>&1 || true
adb shell wm size >> qa-output/device.txt 2>&1 || true
adb shell wm density >> qa-output/device.txt 2>&1 || true
adb shell settings get system font_scale >> qa-output/device.txt 2>&1 || true
echo "=== APK ===" >> qa-output/device.txt
sha256sum "$APK_PATH" >> qa-output/device.txt 2>&1 || true

PACKAGE="${QA_PACKAGE_NAME:-}"
if [ -z "$PACKAGE" ]; then
  PACKAGE="$(aapt dump badging "$APK_PATH" 2>/dev/null | sed -n "s/package: name='\([^']*\)'.*/\1/p" | head -n1)"
fi

echo "$PACKAGE" > qa-output/package.txt
echo "APK_PATH=$APK_PATH" >> qa-output/package.txt

adb logcat -c || true

if ! adb install -r -g "$APK_PATH" > qa-output/install.txt 2>&1; then
  adb install -r "$APK_PATH" >> qa-output/install.txt 2>&1 || true
fi

adb shell pm list packages | grep -F "$PACKAGE" >> qa-output/install.txt 2>&1 || true

adb shell monkey -p "$PACKAGE" -c android.intent.category.LAUNCHER 1 > qa-output/launch.txt 2>&1 || true

sleep 3
adb exec-out screencap -p > qa-output/01-launch-3s.png || true
adb shell uiautomator dump /sdcard/window-3s.xml > /dev/null 2>&1 || true
adb pull /sdcard/window-3s.xml qa-output/01-window-3s.xml > /dev/null 2>&1 || true

sleep 12
adb exec-out screencap -p > qa-output/02-launch-15s.png || true
adb shell uiautomator dump /sdcard/window-15s.xml > /dev/null 2>&1 || true
adb pull /sdcard/window-15s.xml qa-output/02-window-15s.xml > /dev/null 2>&1 || true

adb shell dumpsys activity activities > qa-output/dumpsys-activity.txt 2>&1 || true
adb shell dumpsys window windows > qa-output/dumpsys-window.txt 2>&1 || true
adb shell dumpsys package "$PACKAGE" > qa-output/dumpsys-package.txt 2>&1 || true
adb logcat -d -v threadtime > qa-output/logcat.txt 2>&1 || true

adb shell input keyevent KEYCODE_BACK || true
sleep 2
adb exec-out screencap -p > qa-output/03-after-back.png || true

echo "=== CRASH / ANR SCAN ===" > qa-output/crash-scan.txt
grep -E -i 'FATAL EXCEPTION|ANR in |Process: .* has died|AndroidRuntime' qa-output/logcat.txt >> qa-output/crash-scan.txt || true

echo "=== TOP ACTIVITY ===" > qa-output/top-activity.txt
adb shell dumpsys activity activities | grep -E 'mResumedActivity|topResumedActivity|ResumedActivity' >> qa-output/top-activity.txt 2>&1 || true
