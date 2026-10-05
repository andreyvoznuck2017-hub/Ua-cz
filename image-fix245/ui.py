#!/usr/bin/env python3
"""Test the final SIGNED artifact over installed 2.4.4, no session wipe.
Screenshots are real emulator pixels. Only disposable test accounts are used.
"""
import hashlib,json,os,re,time,traceback
from pathlib import Path
source=Path('qa-runtime/diagnose.py').read_text().split('\ntry:run()')[0]
source=source.replace("PACKAGE='eu.svoyi.testapp01'","PACKAGE='eu.svoyi.nativeapp'")
source=source.replace("email='qa.repair.'+os.environ['GITHUB_RUN_ID']+'.'+tag+'@example.com'","email='qa.imagefix.'+os.environ['GITHUB_RUN_ID']+'.'+os.environ['QA_API']+'.'+tag+'@example.com'")
old="apk=Path(os.environ.get('QA_APK',next(iter(Path('qa-input').glob('*.apk'))).as_posix()))"
assert source.count(old)==1
source=source.replace(old,"apk=Path('signed-input/baseline244.apk')")
marker="time.sleep(12); capture('android-02-home')"
assert source.count(marker)==1
source=source.replace(marker,"""time.sleep(12); capture('before244-home')
    check('baseline244-signed-in',any('Профіль' in n.get('content-desc','') for n in ui().iter('node')))
    save('baseline244-logcat.txt',adb('logcat','-d','-v','threadtime',allow_fail=True).decode(errors='replace'))
    adb('shell','am','force-stop',PACKAGE)
    candidate=Path('signed-input/app.apk')
    save('update-install.txt',adb('install','-r','-g',str(candidate),timeout=90).decode())
    adb('logcat','-c',allow_fail=True)
    adb('shell','am','start','-n',PACKAGE+'/eu.svoyi.nativeapp.MainActivity')
    time.sleep(12); capture('after245-home')
    check('session-preserved-from244',any('Профіль' in n.get('content-desc','') for n in ui().iter('node')))
    save('apk.json',{'file':candidate.name,'sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),'package':PACKAGE,'versionCode':345})""")
ns={};exec(compile(source,'qa-runtime/diagnose.py','exec'),ns);ns['web_capture']=lambda a,b:None
adb,tap,ui,capture,check,save,alive=(ns[k] for k in ['adb','tap','ui','capture','check','save','alive'])
def wait(test,timeout=20):
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  if test():return True
  time.sleep(1)
 return False
try:
 ns['run']()
 if not all(x['passed'] for x in ns['CHECKS']):raise RuntimeError('Basic mailbox or update acceptance failed')
 adb('shell','input','keyevent','KEYCODE_BACK');time.sleep(1)
 # Repeated changes of screen trigger cancellation of in-flight avatar/preview loads.
 for i in range(5):
  for desc in ['Головна','Профіль','Повідомлення']:
   ok=tap('content-desc',desc,contains=True);check('nav-'+str(i)+'-'+desc,ok)
   if not ok:raise RuntimeError('Navigation target absent: '+desc)
   time.sleep(0.5)
  ok=wait(lambda:any('QA Viktoriia' in n.get('text','') for n in ui().iter('node')))
  check('inbox-present-'+str(i),ok)
  if not ok:raise RuntimeError('Inbox did not load')
  check('thread-open-'+str(i),tap('text','QA Viktoriia',contains=True));time.sleep(2)
  check('thread-visible-'+str(i),any('Надіслати' in n.get('content-desc','') for n in ui().iter('node')))
  if i==4:capture('after245-thread')
 # Verify the actual 2.4.4 native action sheet is retained, not a reset to an older build.
 root=ui();nodes=[n for n in root.iter('node') if n.get('text','')=='Android echo QA'];opened=False
 if nodes:
  b=list(map(int,re.findall(r'\d+',nodes[-1].get('bounds',''))))
  if len(b)==4:
   x,y=str((b[0]+b[2])//2),str((b[1]+b[3])//2);adb('shell','input','swipe',x,y,x,y,'750');time.sleep(2)
   opened=any(n.get('content-desc','')=='Реакція ❤️' for n in ui().iter('node'))
 check('mail-actions244-retained',opened);capture('after245-reactions')
 adb('shell','input','keyevent','KEYCODE_BACK');time.sleep(1)
 adb('shell','am','force-stop',ns['PACKAGE']);adb('shell','am','start','-n',ns['PACKAGE']+'/eu.svoyi.nativeapp.MainActivity');time.sleep(10)
 check('session-after-relaunch',any('Профіль' in n.get('content-desc','') for n in ui().iter('node')))
 check('tap-mail-final',tap('content-desc','Повідомлення',contains=True))
 check('inbox-after-relaunch',wait(lambda:any('QA Viktoriia' in n.get('text','') for n in ui().iter('node'))))
 capture('after245-inbox-relaunch')
except Exception as e:
 check('imagefix-ui-completed',False,type(e).__name__+': '+str(e));save('error.txt',traceback.format_exc())
 try:capture('failure')
 except Exception:pass
finally:
 try:
  log=adb('logcat','-d','-v','threadtime',allow_fail=True).decode(errors='replace');save('logcat-final.txt',log);check('no-fatal-in-final-apk','FATAL EXCEPTION' not in log)
 except Exception as e:check('logcat-saved',False,str(e))
 save('checks.json',ns['CHECKS']);print(json.dumps(ns['CHECKS'],ensure_ascii=False))
 raise SystemExit(0 if ns['CHECKS'] and all(x['passed'] for x in ns['CHECKS']) else 1)
