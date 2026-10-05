#!/usr/bin/env python3
import hashlib, json, os, time, traceback, xml.etree.ElementTree as ET
from pathlib import Path

source=Path('qa-runtime/diagnose.py').read_text().split('\ntry:run()')[0]
source=source.replace("PACKAGE='eu.svoyi.testapp01'","PACKAGE='eu.svoyi.nativeapp'")
source=source.replace("email='qa.repair.'+os.environ['GITHUB_RUN_ID']+'.'+tag+'@example.com'","email='qa.final248.'+os.environ['GITHUB_RUN_ID']+'.'+tag+'@example.com'")
ns={};exec(compile(source,'qa-runtime/diagnose.py','exec'),ns)
adb,save,check,account=[ns[k] for k in ['adb','save','check','account']]
OUT=ns['OUT']; PACKAGE=ns['PACKAGE']

def ui():
    adb('shell','rm','-f','/sdcard/final248.xml',allow_fail=True)
    adb('shell','uiautomator','dump','/sdcard/final248.xml',allow_fail=True,timeout=20)
    raw=adb('shell','cat','/sdcard/final248.xml',allow_fail=True)
    return ET.fromstring(raw)

def rect(n):
    import re
    xy=list(map(int,re.findall(r'\d+',n.get('bounds',''))))
    return xy if len(xy)==4 else [0,0,0,0]

def visible(n):
    x1,y1,x2,y2=rect(n)
    return x2>x1 and y2>y1 and n.get('enabled')=='true'

def find(value,attr='text',contains=False):
    out=[]
    for n in ui().iter('node'):
        if not visible(n): continue
        got=n.get(attr,'')
        ok=value.casefold() in got.casefold() if contains else value.casefold()==got.casefold()
        if ok: out.append(n)
    return out

def tap_node(n):
    x1,y1,x2,y2=rect(n)
    adb('shell','input','tap',str((x1+x2)//2),str((y1+y2)//2))

def click(value,attr='text',contains=False):
    xs=find(value,attr,contains)
    if not xs: return False
    tap_node(xs[0]); time.sleep(.7); return True

def wait(fn,secs=25):
    end=time.time()+secs
    while time.time()<end:
        try:
            if fn(): return True
        except Exception:
            pass
        time.sleep(.6)
    return False

def shot(name):
    (OUT/(name+'.png')).write_bytes(adb('exec-out','screencap','-p'))
    save(name+'.xml',ET.tostring(ui(),encoding='unicode'))

def editors():
    return [n for n in ui().iter('node') if n.get('class')=='android.widget.EditText' and visible(n)]

def hide_keyboard():
    text=adb('shell','dumpsys','input_method',allow_fail=True).decode(errors='replace')
    if 'mInputShown=true' in text or 'mIsInputViewShown=true' in text:
        adb('shell','input','keyevent','KEYCODE_BACK');time.sleep(.5)

def login(a):
    must=lambda n,v: check(n,bool(v)) or (None if v else (_ for _ in ()).throw(AssertionError(n)))
    must('login-fields',wait(lambda:len(editors())>=2,35))
    es=editors()
    for i,val in enumerate([a['email'],a['password']]):
        tap_node(es[i]);time.sleep(.3)
        adb('shell','input','text',val)
    hide_keyboard()
    must('login-submit',click('Увійти'))
    must('login-complete',wait(lambda:bool(find('Профіль','content-desc')) and bool(find(a['name'],contains=True)),40))

def home():
    if not click('Головна','content-desc'):
        adb('shell','input','keyevent','KEYCODE_BACK');time.sleep(.5);click('Головна','content-desc')
    wait(lambda:bool(find('Вітаємо,',contains=True)) or bool(find('Головна',contains=True)),15)
    time.sleep(1)

def profile():
    click('Профіль','content-desc')
    wait(lambda:bool(find('Переглянути профіль',contains=True)) or bool(find('Особистий кабінет',contains=True)),18)
    if click('Переглянути профіль',contains=True):
        wait(lambda:bool(find('Редагувати профіль',contains=True)),18)
    time.sleep(1)

def mail(peername):
    click('Повідомлення','content-desc',True)
    wait(lambda:bool(find(peername,contains=True)) or bool(find('Повідомлення',contains=True)),18)
    if find(peername,contains=True):
        click(peername,contains=True)
        wait(lambda:bool(find('Надіслати','content-desc',True)),18)
    time.sleep(1)

def record_version(prefix,a,b):
    home(); shot(prefix+'-home')
    profile(); shot(prefix+'-profile')
    home(); mail(b['name']); shot(prefix+'-mail')
    if find('Надіслати','content-desc',True):
        fields=editors()
        if fields:
            tap_node(fields[-1]);adb('shell','input','text','Final248%sQA');time.sleep(.4);shot(prefix+'-mail-keyboard');hide_keyboard()

try:
    expected='e8ed6574badea8b249195cec7a13791480a50b262246ca6e60fb5f9a528dcf28'
    final=Path('signed-input/final248.apk')
    base=Path('signed-input/base245.apk')
    check('final-apk-sha256',hashlib.sha256(final.read_bytes()).hexdigest()==expected)
    a,b=account('a'),account('b'); save('accounts.json',{'a':a['id'],'b':b['id'],'disposableOnly':True})
    save('install-base.txt',adb('install','-r','-g',str(base),timeout=90).decode())
    adb('shell','am','start','-n',PACKAGE+'/eu.svoyi.nativeapp.MainActivity')
    login(a)
    record_version('before245',a,b)
    save('install-final.txt',adb('install','-r','-g',str(final),timeout=90).decode())
    adb('shell','am','start','-n',PACKAGE+'/eu.svoyi.nativeapp.MainActivity')
    check('session-survives-update',wait(lambda:bool(find('Профіль','content-desc')) and bool(find(a['name'],contains=True)),40))
    record_version('after248',a,b)
    log=adb('logcat','-d','-v','threadtime',allow_fail=True).decode(errors='replace');save('logcat.txt',log)
    check('no-app-fatal','FATAL EXCEPTION' not in log)
    shutil=None
    import shutil as _shutil
    _shutil.copy2(final,OUT/'Svoyi-Android-2.4.8.apk')
    save('final.json',{'version':'2.4.8-batch20','versionCode':348,'package':PACKAGE,'sha256':expected,'exactOriginalSignedApkTested':True,'androidApi':36})
except Exception as e:
    check('runtime-completed',False,type(e).__name__+': '+str(e))
    save('error.txt',traceback.format_exc())
    try: shot('failure')
    except Exception: pass
finally:
    save('checks.json',ns['CHECKS'])
print(json.dumps(ns['CHECKS'],ensure_ascii=False))
raise SystemExit(0 if ns['CHECKS'] and all(c['passed'] for c in ns['CHECKS']) else 1)
