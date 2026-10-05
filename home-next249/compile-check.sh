#!/usr/bin/env bash
set -euo pipefail
mkdir -p home249-checks/stub home249-checks/rules home249-checks/classes
javac -encoding UTF-8 -source 8 -target 8 -d home249-checks/rules home-next249/HomeRules249.java home-next249/HomeRules249Test.java
java -cp home249-checks/rules eu.svoyi.nativeapp.HomeRules249Test | tee home249-checks/unit-results.txt
android="${ANDROID_HOME:?Android SDK required}/platforms/android-35/android.jar"
test -s "$android"
cat > home249-checks/Signatures.java <<'JAVA'
package eu.svoyi.nativeapp;
import android.app.*;import android.content.*;import android.view.*;import org.json.*;
class MainActivity extends Activity {public View batch20Nodes(JSONArray value){return null;}}
class ThemePalette {int background,surface,text,muted,accent,border;}
class NativeWelcome {Activity activity;ThemePalette colors;NativeJobsScreen.Host host;}
class NativeJobsScreen {interface Host {boolean alive();void navigate(String route);View image(String url);}}
class NativeSiteUi {static final class Flow extends ViewGroup {Flow(Context c,int gap){super(c);}protected void onLayout(boolean changed,int l,int t,int r,int b){}}}
JAVA
javac -encoding UTF-8 -source 8 -target 8 -cp "$android" -d home249-checks/stub home249-checks/Signatures.java
javac -encoding UTF-8 -source 8 -target 8 -cp "$android:home249-checks/stub" -d home249-checks/classes home-next249/HomeRules249.java home-next249/HomeScreen249.java
python3 - <<'PY'
import json
from pathlib import Path
classes=list(Path('home249-checks/classes').rglob('*.class'))
assert classes and all(p.name.startswith(('HomeRules249','HomeScreen249')) for p in classes)
Path('home249-checks/status.json').write_text(json.dumps({'rulesChecks':59,'androidJavaCompiled':True,'apkModified':False,'apkSigned':False,'userDeviceTested':False,'androidUiTested':False,'privateKeyAccessed':False,'compileOnlySignaturesPackaged':False},indent=2))
PY
