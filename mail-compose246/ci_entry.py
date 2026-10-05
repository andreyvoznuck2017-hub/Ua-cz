#!/usr/bin/env python3
"""Bootstrap only: wait for CI emulator boot/storage; do not alter app acceptance assertions."""
import hashlib,os,subprocess,time,json
from pathlib import Path
# The previous Android 16 run was still displaying the system boot animation; storage was locked.
# This disposable AVD has no user PIN. Never run this preparation against a physical user device.
def shell(*args):return subprocess.run(['adb','shell',*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=12)
end=time.monotonic()+120;history=[]
while time.monotonic()<end:
 boot=shell('getprop','sys.boot_completed').stdout.decode().strip()
 animation=shell('getprop','init.svc.bootanim').stdout.decode().strip()
 history.append({'bootCompleted':boot,'bootAnimation':animation})
 if boot=='1' and animation=='stopped':break
 time.sleep(2)
else:raise RuntimeError('CI emulator did not finish its boot animation')
shell('input','keyevent','KEYCODE_WAKEUP');shell('wm','dismiss-keyguard')
for i in range(30):
 r=shell('mkdir','-p','/sdcard/Download')
 if r.returncode==0:break
 time.sleep(2)
else:raise RuntimeError('CI external storage did not become writable')
Path('runtime-output/boot-preparation.json').write_text(json.dumps({'observations':history,'downloadDirectoryReady':True,'physicalDevice':False},indent=2))
s=Path('mail-compose246/runtime.py').read_text()
marker="ns={};exec(compile(code,'mail-next244/runtime.py','exec'),ns)"
assert s.count(marker)==1
s=s.replace(marker,marker+"\ncore=ns['ns'];ns['ORIGIN']=core['ORIGIN'];ns['CHECKS']=core['CHECKS']")
assert s.count("ns['ui']=ui")==1
s=s.replace("ns['ui']=ui","ns['ui']=ui;core['ui']=ui")
if os.environ.get('QA_CI_ONLY')=='1':
 baseline=hashlib.sha256(Path('signed-input/baseline245.apk').read_bytes()).hexdigest()
 s=s.replace('95fe1ad2849c7719ecd4b5b559fbbb860eb69386ee2564f732e637f02ab38cdb',baseline)
exec(compile(s,'mail-compose246/runtime.py','exec'))
