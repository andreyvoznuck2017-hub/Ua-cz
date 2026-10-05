#!/usr/bin/env bash
set -u

mkdir -p qa-output

capture() {
  local name="$1"
  adb exec-out screencap -p > "qa-output/${name}.png" || true
  adb shell uiautomator dump "/sdcard/${name}.xml" > /dev/null 2>&1 || true
  adb pull "/sdcard/${name}.xml" "qa-output/${name}.xml" > /dev/null 2>&1 || true
}

dump_ui() {
  adb shell uiautomator dump /sdcard/current-ui.xml > /dev/null 2>&1 || true
  adb pull /sdcard/current-ui.xml /tmp/current-ui.xml > /dev/null 2>&1 || true
}

tap_node() {
  local attr="$1"
  local value="$2"
  local index="${3:-0}"
  dump_ui
  local xy
  xy="$(python3 - "$attr" "$value" "$index" <<'PY'
import re, sys, xml.etree.ElementTree as ET
attr, value, index = sys.argv[1], sys.argv[2], int(sys.argv[3])
try:
    root = ET.parse('/tmp/current-ui.xml').getroot()
except Exception:
    sys.exit(1)
matches=[]
for n in root.iter('node'):
    if n.attrib.get(attr,'') == value:
        matches.append(n)
if index >= len(matches):
    sys.exit(2)
b=matches[index].attrib.get('bounds','')
m=re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', b)
if not m:
    sys.exit(3)
x1,y1,x2,y2=map(int,m.groups())
print((x1+x2)//2, (y1+y2)//2)
PY
)" || return 1
  adb shell input tap $xy
}

tap_desc() { tap_node content-desc "$1" "${2:-0}"; }
tap_text() { tap_node text "$1" "${2:-0}"; }
tap_class() { tap_node class "$1" "${2:-0}"; }

echo "=== DEVICE ===" > qa-output/device.txt
adb shell getprop ro.product.model >> qa-output/device.txt 2>&1 || true
adb shell getprop ro.build.version.release >> qa-output/device.txt 2>&1 || true
adb shell wm size >> qa-output/device.txt 2>&1 || true
adb shell wm density >> qa-output/device.txt 2>&1 || true
adb shell settings get system font_scale >> qa-output/device.txt 2>&1 || true
echo "=== APK ===" >> qa-output/device.txt
sha256sum "$APK_PATH" >> qa-output/device.txt 2>&1 || true

PACKAGE="${QA_PACKAGE_NAME:-}"
if [ -z "$PACKAGE" ] && command -v apkanalyzer >/dev/null 2>&1; then
  PACKAGE="$(apkanalyzer manifest application-id "$APK_PATH" 2>/dev/null | tr -d '\r\n' || true)"
fi
if [ -z "$PACKAGE" ] && command -v aapt >/dev/null 2>&1; then
  PACKAGE="$(aapt dump badging "$APK_PATH" 2>/dev/null | sed -n "s/package: name='\\([^']*\\)'.*/\\1/p" | head -n1)"
fi
if [ -z "$PACKAGE" ] && command -v aapt2 >/dev/null 2>&1; then
  PACKAGE="$(aapt2 dump badging "$APK_PATH" 2>/dev/null | sed -n "s/package: name='\\([^']*\\)'.*/\\1/p" | head -n1)"
fi
if [ -z "$PACKAGE" ] && [ -f app/build.gradle ]; then
  PACKAGE="$(sed -n "s/.*applicationId[[:space:]]*['\"]\\([^'\"]*\\)['\"].*/\\1/p" app/build.gradle | head -n1)"
fi
if [ -z "$PACKAGE" ]; then
  echo "Could not determine application package" >&2
  exit 3
fi

echo "$PACKAGE" > qa-output/package.txt
echo "APK_PATH=$APK_PATH" >> qa-output/package.txt

# Create one disposable test account on the TEST site for this QA run.
# The random password exists only inside this runner and is never written to artifacts.
QA_EMAIL="qa.android.${GITHUB_RUN_ID:-$RANDOM}@example.com"
QA_PASSWORD="Qa$(openssl rand -hex 14)"
QA_NAME="Android QA ${GITHUB_RUN_NUMBER:-run}"
QA_CITY="Praha"

rm -f /tmp/qa-cookies.txt /tmp/register.html /tmp/register-result.html
REGISTER_OK=0
if curl --fail --silent --show-error --location     --cookie-jar /tmp/qa-cookies.txt --cookie /tmp/qa-cookies.txt     'https://test.jkunis.eu/?p=register' -o /tmp/register.html; then
  CSRF="$(python3 - <<'PY'
import re
s=open('/tmp/register.html','r',encoding='utf-8',errors='ignore').read()
m=re.search(r'name=["\']csrf["\'][^>]*value=["\']([^"\']+)',s)
if not m:
    m=re.search(r'value=["\']([^"\']+)["\'][^>]*name=["\']csrf["\']',s)
print(m.group(1) if m else '')
PY
)"
  if [ -n "$CSRF" ]; then
    HTTP_INFO="$(curl --silent --show-error --location       --cookie-jar /tmp/qa-cookies.txt --cookie /tmp/qa-cookies.txt       --data-urlencode "csrf=$CSRF"       --data-urlencode "action=register"       --data-urlencode "start_goal=all"       --data-urlencode "name=$QA_NAME"       --data-urlencode "email=$QA_EMAIL"       --data-urlencode "city=$QA_CITY"       --data-urlencode "password=$QA_PASSWORD"       -o /tmp/register-result.html       -w '%{http_code} %{url_effective}'       'https://test.jkunis.eu/?p=register' || true)"
    if grep -qE 'Кабінет|Профіль|Вийти|Головна' /tmp/register-result.html 2>/dev/null; then
      REGISTER_OK=1
    fi
    printf 'register_http=%s\nregister_ok=%s\n' "$HTTP_INFO" "$REGISTER_OK" > qa-output/test-account-status.txt
  else
    printf 'register_error=csrf_not_found\n' > qa-output/test-account-status.txt
  fi
else
  printf 'register_error=page_fetch_failed\n' > qa-output/test-account-status.txt
fi

adb logcat -c || true

if ! adb install -r -g "$APK_PATH" > qa-output/install.txt 2>&1; then
  adb install -r "$APK_PATH" >> qa-output/install.txt 2>&1 || true
fi
adb shell pm list packages | grep -F "$PACKAGE" >> qa-output/install.txt 2>&1 || true

adb shell monkey -p "$PACKAGE" -c android.intent.category.LAUNCHER 1 > qa-output/launch.txt 2>&1 || true

sleep 3
capture 01-launch-3s
sleep 12
capture 02-login-ready

# Exercise login keyboard and authenticate with the disposable QA account.
if [ "$REGISTER_OK" = "1" ]; then
  if tap_class android.widget.EditText 0; then
    sleep 1
    adb shell input text "$QA_EMAIL" || true
    sleep 1
    capture 03-email-keyboard
    tap_class android.widget.EditText 1 || true
    sleep 1
    adb shell input text "$QA_PASSWORD" || true
    sleep 1
    capture 04-login-filled
    tap_text 'Увійти' 0 || true
    sleep 10
    capture 05-after-login
  fi
else
  echo "Registration failed; authenticated UI pass skipped." >> qa-output/test-account-status.txt
fi

# Authenticated navigation smoke pass. Missing targets are recorded by screenshots/dumps but do not abort the run.
for item in 'Головна:06-home' 'Профіль:07-profile' 'Повідомлення:08-messages' 'Сповіщення:09-notifications'; do
  label="${item%%:*}"
  shot="${item##*:}"
  if tap_desc "$label"; then
    sleep 5
    capture "$shot"
  fi
done

if tap_desc 'Відкрити меню'; then
  sleep 2
  capture 10-menu-open
  adb shell input keyevent KEYCODE_BACK || true
  sleep 1
fi

if tap_desc 'Пошук'; then
  sleep 3
  capture 11-search
  adb shell input keyevent KEYCODE_BACK || true
  sleep 1
fi

adb shell dumpsys activity activities > qa-output/dumpsys-activity.txt 2>&1 || true
adb shell dumpsys window windows > qa-output/dumpsys-window.txt 2>&1 || true
adb shell dumpsys package "$PACKAGE" > qa-output/dumpsys-package.txt 2>&1 || true
adb logcat -d -v threadtime > qa-output/logcat.txt 2>&1 || true

echo "=== CRASH / ANR SCAN ===" > qa-output/crash-scan.txt
grep -E -i 'FATAL EXCEPTION|ANR in |Process: .* has died|AndroidRuntime' qa-output/logcat.txt >> qa-output/crash-scan.txt || true

echo "=== TOP ACTIVITY ===" > qa-output/top-activity.txt
adb shell dumpsys activity activities | grep -E 'mResumedActivity|topResumedActivity|ResumedActivity' >> qa-output/top-activity.txt 2>&1 || true
