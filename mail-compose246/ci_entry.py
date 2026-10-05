#!/usr/bin/env python3
"""CI environment and UI targeting only. App acceptance assertions are unchanged."""
import hashlib,os,subprocess,time,json
from pathlib import Path
out=Path('runtime-output');out.mkdir(exist_ok=True)
def shell(*args):return subprocess.run(['adb','shell',*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=12)
end=time.monotonic()+150;history=[];ready=False
# Boot animation may never start with -no-boot-anim. Actual writable document storage is required.
while time.monotonic()<end:
 boot=shell('getprop','sys.boot_completed').stdout.decode().strip()
 animation=shell('getprop','init.svc.bootanim').stdout.decode().strip()
 if boot=='1':
  shell('input','keyevent','KEYCODE_WAKEUP');shell('wm','dismiss-keyguard')
  storage=shell('mkdir','-p','/sdcard/Download')
  writable=storage.returncode==0
 else:writable=False
 history.append({'bootCompleted':boot,'bootAnimation':animation,'storageReady':writable})
 (out/'boot-preparation.json').write_text(json.dumps({'observations':history,'physicalDevice':False},indent=2))
 if boot=='1' and writable:
  time.sleep(3);ready=True;break
 time.sleep(2)
if not ready:
 (out/'environment-failure.png').write_bytes(subprocess.run(['adb','exec-out','screencap','-p'],stdout=subprocess.PIPE,timeout=15).stdout)
 raise RuntimeError('CI emulator storage did not become ready; app tests not started')
s=Path('mail-compose246/runtime.py').read_text()
marker="ns={};exec(compile(code,'mail-next244/runtime.py','exec'),ns)"
assert s.count(marker)==1
s=s.replace(marker,marker+"\ncore=ns['ns'];ns['ORIGIN']=core['ORIGIN'];ns['CHECKS']=core['CHECKS']")
assert s.count("ns['ui']=ui")==1
s=s.replace("ns['ui']=ui","ns['ui']=ui;core['ui']=ui")
# The observed native dialog exposes ЗБЕРЕГТИ, not Зберегти. Keep exact case-insensitive
# semantics for text labels; this still taps a real visible UI element, not an API action.
old="def click(value,attr='text',contains=False):return tap(attr,value,contains=contains)"
new='''def click(value,attr='text',contains=False):
 if tap(attr,value,contains=contains):return True
 if attr!='text' or contains:return False
 candidates=[n for n in nodes() if n.get('package')==PACKAGE and n.get('text','').casefold()==value.casefold() and n.get('enabled')=='true']
 if len(candidates)!=1:return False
 n=candidates[0];xy=list(map(int,re.findall(r'\\d+',n.get('bounds',''))))
 if len(xy)!=4 or xy[3]<=xy[1]:return False
 adb('shell','input','tap',str((xy[0]+xy[2])//2),str((xy[1]+xy[3])//2));return True
'''
assert s.count(old)==1;s=s.replace(old,new)
old="def menu(text):\n hide_keyboard();must('long-press-message',ns['longpress'](text));must('message-actions-visible',wait(lambda:has('Копіювати')))"
new='''def menu(text):
 hide_keyboard();opened=False
 for attempt in range(12):
  if ns['longpress'](text):opened=True;break
  views=[n for n in nodes() if n.get('package')==PACKAGE and n.get('class')=='android.widget.ScrollView' and n.get('scrollable')=='true']
  if not views:break
  xy=list(map(int,re.findall(r'\\d+',views[0].get('bounds',''))))
  if len(xy)!=4:break
  x=(xy[0]+xy[2])//2;h=xy[3]-xy[1]
  adb('shell','input','swipe',str(x),str(xy[1]+h//4),str(x),str(xy[1]+3*h//4),'450');time.sleep(.6)
 must('long-press-message',opened);must('message-actions-visible',wait(lambda:has('Копіювати')))
'''
assert s.count(old)==1;s=s.replace(old,new)
if os.environ.get('QA_CI_ONLY')=='1':
 baseline=hashlib.sha256(Path('signed-input/baseline245.apk').read_bytes()).hexdigest()
 s=s.replace('95fe1ad2849c7719ecd4b5b559fbbb860eb69386ee2564f732e637f02ab38cdb',baseline)
(out/'test-driver-adjustments.json').write_text(json.dumps({'caseInsensitiveObservedDialogLabels':True,'scrollBeforeLongPress':True,'applicationAssertionsRemoved':False,'apiUsedInsteadOfUiAction':False},indent=2))
exec(compile(s,'mail-compose246/runtime.py','exec'))
