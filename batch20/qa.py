#!/usr/bin/env python3
"""Shared live Android harness. No owner account, browser tab or signing key is accessed."""
import hashlib,json,os,re,secrets,subprocess,time,traceback,xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urljoin,urlsplit
from PIL import Image,ImageDraw
source=Path('qa-runtime/diagnose.py').read_text().split('\ntry:run()')[0]
source=source.replace("PACKAGE='eu.svoyi.testapp01'","PACKAGE='eu.svoyi.nativeapp'")
source=source.replace("email='qa.repair.'+os.environ['GITHUB_RUN_ID']+'.'+tag+'@example.com'","email='qa.b20.'+os.environ['GITHUB_RUN_ID']+'.'+os.environ['QA_API']+'.'+os.environ['QA_AREA']+'.'+tag+'@example.com'")
core={};exec(compile(source,'qa-runtime/diagnose.py','exec'),core)
adb,api,save,check,account=[core[k] for k in ['adb','api','save','check','account']]
OUT=core['OUT'];PACKAGE=core['PACKAGE'];ORIGIN=core['ORIGIN'];TASKS=[];NOTES=[]

def wait(fn,seconds=18):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  if fn():return True
  time.sleep(.45)
 return False

def must(name,ok,detail=''):
 check(name,bool(ok),detail)
 if not ok:raise AssertionError(name+(' — '+detail if detail else ''))

def ui():
 root=core['ui']()
 title=next((n.get('text','') for n in root.iter('node') if n.get('package')=='android' and n.get('resource-id')=='android:id/alertTitle'),'')
 if title=="Pixel Launcher isn't responding" and len(NOTES)<3:
  close=next((n for n in root.iter('node') if n.get('resource-id')=='android:id/aerr_close'),None)
  if close is not None:
   NOTES.append({'dismissed':'Pixel Launcher only','applicationErrorsIgnored':False});save('environment.json',NOTES);tap_node(close);time.sleep(1);return core['ui']()
 return root

def rect(n):
 xy=list(map(int,re.findall(r'\d+',n.get('bounds',''))));return xy if len(xy)==4 else [0,0,0,0]

def visible(n):
 x1,y1,x2,y2=rect(n);return x2>x1 and y2>y1 and n.get('enabled')=='true'

def nodes():return [n for n in ui().iter('node') if visible(n)]

def tap_node(n,long=False):
 x1,y1,x2,y2=rect(n);x,y=str((x1+x2)//2),str((y1+y2)//2)
 if long:adb('shell','input','swipe',x,y,x,y,'650')
 else:adb('shell','input','tap',x,y)

def find(value,attr='text',contains=False,app=True):
 ns=nodes();return [n for n in ns if (not app or n.get('package')==PACKAGE) and (value.casefold() in n.get(attr,'').casefold() if contains else value.casefold()==n.get(attr,'').casefold())]

def has(value,attr='text',contains=False,app=True):return bool(find(value,attr,contains,app))

def click(value,attr='text',contains=False,app=True):
 ns=find(value,attr,contains,app)
 if not ns:return False
 clickables=[n for n in ns if n.get('clickable')=='true'];tap_node((clickables or ns)[0]);return True

def ime():return bool(re.search(r'mInputShown=true|mIsInputViewShown=true',adb('shell','dumpsys','input_method',allow_fail=True).decode(errors='replace')))

def hide_keyboard():
 if ime():adb('shell','input','keyevent','KEYCODE_BACK');time.sleep(.45)

def scroll(up=False):
 vs=[n for n in nodes() if n.get('package')==PACKAGE and n.get('class') in ['android.widget.ScrollView','androidx.recyclerview.widget.RecyclerView'] and n.get('scrollable')=='true']
 if not vs:return False
 v=max(vs,key=lambda n:(rect(n)[2]-rect(n)[0])*(rect(n)[3]-rect(n)[1]));x1,y1,x2,y2=rect(v);x=(x1+x2)//2;d=y2-y1
 a,b=y1+d*3//4,y1+d//4
 if up:a,b=b,a
 adb('shell','input','swipe',str(x),str(a),str(x),str(b),'430');time.sleep(.5);return True

def seek(value,attr='text',contains=False,up=False,limit=12):
 for _ in range(limit):
  if has(value,attr,contains):return True
  if not scroll(up):break
 return has(value,attr,contains)

def capture(name):
 (OUT/(name+'.png')).write_bytes(adb('exec-out','screencap','-p'))
 try:save(name+'.xml',ET.tostring(ui(),encoding='unicode'))
 except Exception as e:save(name+'-xml-error.txt',type(e).__name__)

def editors():return [n for n in nodes() if n.get('package')==PACKAGE and n.get('class')=='android.widget.EditText']

def type_into(value,name=None,clear=True):
 es=editors()
 if name:
  es=[n for n in es if n.get('content-desc','').startswith('Поле '+name+':')]
  if not es:
   must('find-field-'+name,seek('Поле '+name+':','content-desc',True));es=[n for n in editors() if n.get('content-desc','').startswith('Поле '+name+':')]
 must('editable-control',bool(es),str(name));n=next((n for n in es if n.get('focused')=='true'),es[0]);tap_node(n);time.sleep(.25)
 if clear:adb('shell','input','keycombination','113','29');adb('shell','input','keyevent','KEYCODE_DEL')
 else:adb('shell','input','keyevent','KEYCODE_MOVE_END')
 if value:adb('shell','input','text',value.replace(' ','%s'))
 time.sleep(.25)

def input_text():
 es=editors();return next((n.get('text','') for n in es if n.get('focused')=='true'),next((n.get('text','') for n in es),''))

def goto_home():
 hide_keyboard()
 for _ in range(4):
  if click('Головна','content-desc'):time.sleep(2);return
  adb('shell','input','keyevent','KEYCODE_BACK');time.sleep(.6)
 raise AssertionError('Home navigation unavailable')

def goto_profile(public=False):
 hide_keyboard();must('profile-tab',click('Профіль','content-desc'));time.sleep(2)
 if public:
  must('public-profile-link',seek('Переглянути профіль',contains=True));must('open-public-profile',click('Переглянути профіль',contains=True));time.sleep(2)

def thread(a,b):
 hide_keyboard()
 if has('Повернутися до діалогів','content-desc') and has('Надіслати','content-desc',True):return
 must('mail-tab',click('Повідомлення','content-desc',True));must('peer-inbox-row',wait(lambda:has(b['name'],contains=True)));must('open-thread',click(b['name'],contains=True));must('thread-composer',wait(lambda:has('Надіслати','content-desc',True)))

def messages(owner,peer):return api(owner['s'],{'op':'screen','route':'/?p=messages&with='+str(peer['id'])}).get('chat',{}).get('messages',[])

def send_api(owner,peer,text):
 r=api(owner['s'],{'op':'mail-action','action':'send','route':'/?p=messages&with='+str(peer['id']),'peer':peer['id'],'body':text,'nonce':secrets.token_hex(16),'csrf':owner['state']['csrf'],'expectedAccount':owner['id'],'kind':'text'});must('server-seed-accepted',r.get('ok'),str(r.get('error','')));return r

def case(number,name,fn):
 at=len(core['CHECKS'])
 try:fn();TASKS.append({'task':number,'name':name,'status':'passed','checks':len(core['CHECKS'])-at})
 except Exception as e:
  check(name,False,type(e).__name__+': '+str(e));TASKS.append({'task':number,'name':name,'status':'failed','reason':str(e)});save('task-'+str(number)+'-error.txt',traceback.format_exc())
  try:capture('task-'+str(number)+'-failure')
  except Exception:pass
  try:goto_home()
  except Exception:pass
 finally:save('tasks.json',TASKS)

def start():
 end=time.monotonic()+100
 while time.monotonic()<end:
  boot=adb('shell','getprop','sys.boot_completed').decode().strip()
  if boot=='1':
   adb('shell','input','keyevent','KEYCODE_WAKEUP');adb('shell','wm','dismiss-keyguard',allow_fail=True)
   p=subprocess.run(['adb','shell','mkdir','-p','/sdcard/Download'],capture_output=True)
   if p.returncode==0:break
  time.sleep(2)
 else:raise RuntimeError('Disposable emulator storage not ready')
 a,b=account('a'),account('b');save('accounts.json',{'a':a['id'],'b':b['id'],'disposableOnly':True})
 send_api(b,a,'Batch20 hello from the website')
 # Baseline and candidate share only a disposable CI key. No original installation is touched.
 save('baseline-install.txt',adb('install','-r','-g','signed-input/baseline.apk',timeout=90).decode());adb('logcat','-c',allow_fail=True);adb('shell','am','start','-n',PACKAGE+'/eu.svoyi.nativeapp.MainActivity');must('login-inputs',wait(lambda:len(editors())>=2,35))
 for i,value in enumerate([a['email'],a['password']]):tap_node(editors()[i]);adb('shell','input','text',value)
 hide_keyboard();must('login-button',click('Увійти'));must('session-authenticated',wait(lambda:has('Профіль','content-desc'),35));time.sleep(1)
 capture('before247-home-top');goto_profile(True);capture('before247-profile-top');goto_home();thread(a,b);capture('before247-thread')
 must('candidate-hash',hashlib.sha256(Path('signed-input/app.apk').read_bytes()).hexdigest()==os.environ['QA_SHA256'])
 save('candidate-install.txt',adb('install','-r','-g','signed-input/app.apk',timeout=90).decode());adb('shell','am','start','-n',PACKAGE+'/eu.svoyi.nativeapp.MainActivity');must('session-survives-ci-update',wait(lambda:has('Профіль','content-desc'),35));goto_home();capture('after248-home-top');goto_profile(True);capture('after248-profile-top');goto_home();thread(a,b);capture('after248-thread');return a,b

def finish():
 try:
  log=adb('logcat','-d','-v','threadtime',allow_fail=True).decode(errors='replace');save('logcat.txt',log);ls=log.splitlines();fatals=[i for i,l in enumerate(ls) if 'FATAL EXCEPTION' in l and PACKAGE in '\n'.join(ls[i:i+8])];check('no-uncaught-app-crash',not fatals)
 except Exception as e:check('final-log-capture',False,type(e).__name__)
 save('checks.json',core['CHECKS']);save('tasks.json',TASKS)
 save('limits.json',{'temporaryCiSignature':True,'originalSignerTested':False,'fullGradleBuild':False,'serverSourceChanged':False,'physicalXiaomiTested':False,'testCountsAreNotTaskCounts':True})
