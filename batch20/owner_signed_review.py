#!/usr/bin/env python3
"""Review an already-owner-signed artifact. No signing material, private account, or visible browser.
A smoke test is not completion of the 20-task backlog. Every failed assertion is retained.
"""
import os,re,time,json,hashlib,subprocess,traceback,xml.etree.ElementTree as ET
from pathlib import Path
source=Path('qa-runtime/diagnose.py').read_text().split('\ntry:run()')[0]
source=source.replace("PACKAGE='eu.svoyi.testapp01'","PACKAGE='eu.svoyi.nativeapp'")
source=source.replace("email='qa.repair.'+os.environ['GITHUB_RUN_ID']+'.'+tag+'@example.com'","email='qa.owner248.'+os.environ['GITHUB_RUN_ID']+'.'+tag+'@example.com'")
core={};exec(compile(source,'qa-runtime/diagnose.py','exec'),core)
adb,api,save,check,account=[core[k] for k in ['adb','api','save','check','account']]
OUT=core['OUT'];PACKAGE=core['PACKAGE'];snapshots=[]

def must(label,ok,detail=''):
 check(label,bool(ok),detail)
 if not ok:raise AssertionError(label)

def fresh():
 for attempt in range(3):
  adb('shell','rm','-f','/sdcard/owner248-ui.xml',allow_fail=True)
  adb('shell','uiautomator','dump','/sdcard/owner248-ui.xml',timeout=22,allow_fail=True)
  body=adb('shell','cat','/sdcard/owner248-ui.xml',allow_fail=True)
  try:return ET.fromstring(body)
  except ET.ParseError:time.sleep(.7)
 raise RuntimeError('No fresh UI hierarchy')

def rect(n):
 b=re.findall(r'\d+',n.get('bounds',''));return list(map(int,b)) if len(b)==4 else [0]*4

def valid(n):
 x1,y1,x2,y2=rect(n);return x2>x1 and y2>y1 and n.get('enabled')=='true'

def nodes():return [n for n in fresh().iter('node') if valid(n)]

def match(value,attr='text',contains=False,app=True):
 return [n for n in nodes() if (not app or n.get('package')==PACKAGE) and (value.casefold() in n.get(attr,'').casefold() if contains else value.casefold()==n.get(attr,'').casefold())]

def has(value,attr='text',contains=False):return bool(match(value,attr,contains))

def tapnode(n,long=False):
 x1,y1,x2,y2=rect(n);x,y=str((x1+x2)//2),str((y1+y2)//2)
 if long:adb('shell','input','swipe',x,y,x,y,'650')
 else:adb('shell','input','tap',x,y)

def tap(value,attr='text',contains=False):
 result=match(value,attr,contains)
 if not result:return False
 tapnode(next((n for n in result if n.get('clickable')=='true'),result[0]));return True

def wait(fn,seconds=25):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  if fn():return True
  time.sleep(.6)
 return False

def editors():return [n for n in nodes() if n.get('package')==PACKAGE and n.get('class')=='android.widget.EditText']

def ime():
 text=adb('shell','dumpsys','input_method',allow_fail=True).decode(errors='replace');m=re.search(r'\bmInputShown=(true|false)',text)
 return bool(m and m.group(1)=='true')

def hide():
 if ime():adb('shell','input','keyevent','KEYCODE_BACK');time.sleep(.8)

def capture(name):
 data=adb('exec-out','screencap','-p');must('screenshot-'+name,data.startswith(b'\x89PNG'))
 (OUT/(name+'.png')).write_bytes(data);save(name+'.xml',ET.tostring(fresh(),encoding='unicode'))
 top=adb('shell','dumpsys','activity','activities',allow_fail=True).decode(errors='replace');save(name+'-top.txt','\n'.join(l for l in top.splitlines() if 'ResumedActivity' in l))
 snapshots.append(name);save('screenshots.json',snapshots)

def home():
 hide();must('home-navigation',tap('Головна','content-desc'));must('home-actual-user',wait(lambda:has(a['name'],contains=True),30));time.sleep(1)

def scroll_once():
 views=[n for n in nodes() if n.get('package')==PACKAGE and n.get('class')=='android.widget.ScrollView' and n.get('scrollable')=='true']
 if not views:return False
 x1,y1,x2,y2=rect(max(views,key=lambda v:rect(v)[3]-rect(v)[1]));h=y2-y1;adb('shell','input','swipe',str((x1+x2)//2),str(y1+h*4//5),str((x1+x2)//2),str(y1+h//5),'480');time.sleep(.8);return True

def cabin():
 hide();must('cabinet-navigation',tap('Профіль','content-desc'));must('cabinet-ready',wait(lambda:has('Переглянути профіль',contains=True),25));time.sleep(1)

def public_profile():
 cabin();must('public-profile-navigation',tap('Переглянути профіль',contains=True));must('public-profile-ready',wait(lambda:has('Редагувати профіль',contains=True),25));time.sleep(1)

def thread():
 hide();must('mail-navigation',tap('Повідомлення','content-desc',True));must('mail-peer-ready',wait(lambda:has(b['name'],contains=True),25));must('mail-open-peer',tap(b['name'],contains=True));must('mail-composer-ready',wait(lambda:has('Надіслати','content-desc',True),25));time.sleep(1)

def send_text(value):
 fs=editors();must('compose-editor-present',bool(fs));tapnode(fs[-1]);time.sleep(.4);adb('shell','input','text',value.replace(' ','%s'));time.sleep(.6)

def group(name,fn):
 try:fn();check(name,True)
 except Exception as exc:
  check(name,False,type(exc).__name__+': '+str(exc));save(name+'-error.txt',traceback.format_exc())
  try:capture(name+'-failure')
  except Exception:pass

def screens(prefix):
 home();capture(prefix+'-home-top');scroll_once();capture(prefix+'-home-middle');scroll_once();capture(prefix+'-home-lower')
 cabin();capture(prefix+'-cabinet');public_profile();capture(prefix+'-profile');home();thread();capture(prefix+'-thread')

def run():
 global a,b
 candidate=Path('signed-input/app.apk');baseline=Path('signed-input/baseline.apk')
 must('exact-owner-signed-apk',hashlib.sha256(candidate.read_bytes()).hexdigest()=='e8ed6574badea8b249195cec7a13791480a50b262246ca6e60fb5f9a528dcf28')
 must('exact-delivered-245',hashlib.sha256(baseline.read_bytes()).hexdigest()=='95fe1ad2849c7719ecd4b5b559fbbb860eb69386ee2564f732e637f02ab38cdb')
 ready=False
 for _ in range(60):
  if adb('shell','getprop','sys.boot_completed',allow_fail=True).decode().strip()=='1':
   adb('shell','input','keyevent','KEYCODE_WAKEUP');adb('shell','wm','dismiss-keyguard',allow_fail=True)
   if subprocess.run(['adb','shell','mkdir','-p','/sdcard/Download'],capture_output=True).returncode==0:ready=True;break
  time.sleep(2)
 must('emulator-ready',ready);time.sleep(3)
 a,b=account('a'),account('b');save('qa-identities.json',{'a':a['id'],'b':b['id'],'disposableOnly':True})
 r=api(b['s'],{'op':'mail-action','action':'send','peer':a['id'],'route':'/?p=messages&with='+str(a['id']),'body':'Повідомлення з сайту для перевірки 2.4.8','nonce':core['secrets'].token_hex(16),'csrf':b['state']['csrf'],'expectedAccount':b['id'],'kind':'text'});must('website-message-seeded',r.get('ok'))
 save('baseline-install.txt',adb('install','-r','-g',str(baseline),timeout=90).decode());adb('logcat','-c',allow_fail=True);adb('shell','am','start','-n',PACKAGE+'/eu.svoyi.nativeapp.MainActivity');time.sleep(8)
 for _ in range(10):
  if len(editors())>=2:break
  tap('Увійти',contains=True) or tap('Спробувати ще раз');time.sleep(2)
 must('baseline-login-fields',len(editors())>=2)
 for index,value in enumerate([a['email'],a['password']]):
  fs=editors();tapnode(fs[index]);time.sleep(.4);adb('shell','input','text',value);time.sleep(.5)
 must('login-email-typed',any(n.get('text')==a['email'] for n in editors()));hide();must('login-submit',tap('Увійти'));must('authenticated-user-not-guest-tabs',wait(lambda:has(a['name'],contains=True) and len(editors())<2,40))
 group('baseline-visuals',lambda:screens('before245'))
 result=adb('install','-r','-g',str(candidate),timeout=90).decode();save('upgrade-install.txt',result);must('original-signer-inplace-update','Success' in result)
 adb('shell','am','start','-n',PACKAGE+'/eu.svoyi.nativeapp.MainActivity');time.sleep(6);must('sign-in-preserved-after-update',wait(lambda:has(a['name'],contains=True) and not has('Раді бачити знову'),35))
 package=adb('shell','dumpsys','package',PACKAGE).decode(errors='replace');save('package.txt',package);must('version348-installed','versionCode=348' in package);must('version248-installed','2.4.8-batch20' in package)
 group('candidate-visuals',lambda:screens('after248'))
 def reply():
  thread();must('seed-visible',wait(lambda:has('Повідомлення з сайту для перевірки 2.4.8',contains=True)));n=match('Повідомлення з сайту для перевірки 2.4.8',contains=True)[0];tapnode(n,long=True);must('message-actions',wait(lambda:has('Відповісти','content-desc')));capture('after248-actions');tap('Відповісти','content-desc');must('reply-ime-opens',wait(ime,8));send_text('Owner signed248 reply');capture('after248-reply-keyboard');must('compose-without-quote-tags',all('[quote]' not in n.get('text','') for n in editors()));must('reply-send',tap('Надіслати','content-desc',True))
  def receipt():
   r=api(b['s'],{'op':'screen','route':'/?p=messages&with='+str(a['id'])});return any('Owner signed248 reply' in m.get('body','') for m in r.get('chat',{}).get('messages',[]))
  must('peer-received-from-actual-apk',wait(receipt,25));capture('after248-message-sent')
 group('quoted-message-roundtrip',reply)
 def restart():
  for i in range(3):home();cabin();thread();must('navigation-process-'+str(i),bool(adb('shell','pidof',PACKAGE,allow_fail=True).strip()))
  adb('shell','am','force-stop',PACKAGE);adb('shell','am','start','-n',PACKAGE+'/eu.svoyi.nativeapp.MainActivity');must('session-after-restart',wait(lambda:has(a['name'],contains=True),30));thread();capture('after248-restart-mail')
 group('repeat-navigation-and-restart',restart)
 save('review-limits.json',{'exactOwnerSignedArtifact':True,'physicalXiaomi':False,'api':36,'testType':'focused signed smoke and visual review','twentyTasksFullyAccepted':False,'serverSourceChanged':False,'signingKeysRead':False})
try:run()
except Exception as exc:
 check('signed-runtime-completed',False,type(exc).__name__+': '+str(exc));save('runtime-error.txt',traceback.format_exc())
 try:capture('signed-runtime-failure')
 except Exception:pass
finally:
 log=adb('logcat','-d','-v','threadtime',allow_fail=True).decode(errors='replace');save('logcat.txt',log);ls=log.splitlines();fatal=[i for i,l in enumerate(ls) if 'FATAL EXCEPTION' in l and PACKAGE in '\n'.join(ls[i:i+10])];check('no-unhandled-application-crash',not fatal);save('checks.json',core['CHECKS']);print(json.dumps(core['CHECKS'],ensure_ascii=False));raise SystemExit(0 if core['CHECKS'] and all(c['passed'] for c in core['CHECKS']) else 1)
