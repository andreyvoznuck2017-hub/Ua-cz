"""Visible login and verified identity; guest bottom tabs are not proof of authentication."""
import hashlib,os,subprocess,time
from pathlib import Path
from . import qa as q

def settle_identity(a,seconds=40):
 return q.wait(lambda:q.has(a['name'],contains=True) and not q.has('Раді бачити знову'),seconds)

def profile(public=False):
 q.hide_keyboard();q.must('profile-tab',q.click('Профіль','content-desc'))
 q.must('cabinet-loaded',q.wait(lambda:q.has('Переглянути профіль',contains=True),20))
 if public:
  q.must('open-public-profile',q.click('Переглянути профіль',contains=True));q.must('public-profile-loaded',q.wait(lambda:q.has('Редагувати профіль',contains=True),20))

def start():
 end=time.monotonic()+100
 while time.monotonic()<end:
  if q.adb('shell','getprop','sys.boot_completed').decode().strip()=='1':
   q.adb('shell','input','keyevent','KEYCODE_WAKEUP');q.adb('shell','wm','dismiss-keyguard',allow_fail=True)
   if subprocess.run(['adb','shell','mkdir','-p','/sdcard/Download'],capture_output=True).returncode==0:break
  time.sleep(2)
 else:raise RuntimeError('Disposable emulator storage not ready')
 a,b=q.account('a'),q.account('b');q.save('accounts.json',{'a':a['id'],'b':b['id'],'disposableOnly':True})
 q.send_api(b,a,'Batch20 hello from the website')
 q.save('baseline-install.txt',q.adb('install','-r','-g','signed-input/baseline.apk',timeout=90).decode());q.adb('logcat','-c',allow_fail=True);q.adb('shell','am','start','-n',q.PACKAGE+'/eu.svoyi.nativeapp.MainActivity')
 ready=False
 for attempt in range(12):
  if len(q.editors())>=2:ready=True;break
  if q.click('Увійти',contains=True):time.sleep(2)
  elif q.click('Спробувати ще раз'):time.sleep(3)
  else:time.sleep(2)
 q.must('login-inputs',ready)
 for i,value in enumerate([a['email'],a['password']]):
  q.tap_node(q.editors()[i]);time.sleep(.5);q.adb('shell','input','keycombination','113','29');q.adb('shell','input','keyevent','KEYCODE_DEL');q.adb('shell','input','text',value);time.sleep(.6)
 q.must('login-email-entered',any(n.get('text')==a['email'] for n in q.editors()))
 q.hide_keyboard();q.must('login-button',q.click('Увійти'))
 q.must('actual-identity-after-login',settle_identity(a,45))
 q.goto_home();q.must('signed-in-home-greeting',q.wait(lambda:q.has(a['name'],contains=True),20));q.capture('before247-home-top');profile(True);q.capture('before247-profile-top');q.goto_home();q.thread(a,b);q.capture('before247-thread')
 q.must('candidate-hash',hashlib.sha256(Path('signed-input/app.apk').read_bytes()).hexdigest()==os.environ['QA_SHA256'])
 q.save('candidate-install.txt',q.adb('install','-r','-g','signed-input/app.apk',timeout=90).decode());q.adb('shell','am','start','-n',q.PACKAGE+'/eu.svoyi.nativeapp.MainActivity');q.must('actual-identity-survives-update',settle_identity(a,40));q.goto_home();q.must('new-home-ready',q.wait(lambda:q.has(a['name'],contains=True),20));q.capture('after248-home-top');profile(True);q.capture('after248-profile-top');q.goto_home();q.thread(a,b);q.capture('after248-thread');return a,b
q.start=start;q.goto_profile=profile
