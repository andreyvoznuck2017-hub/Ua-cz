#!/usr/bin/env python3
"""Real website + Android regression. Never treats a missing target as success."""
import hashlib,json,os,re,secrets,subprocess,time,traceback,xml.etree.ElementTree as ET
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

ORIGIN='https://test.jkunis.eu'
OUT=Path('runtime-output'); OUT.mkdir(exist_ok=True)
PACKAGE='eu.svoyi.testapp01'
CHECKS=[]; REDACT=[]

def save(name,value):
    text=json.dumps(value,ensure_ascii=False,indent=2) if not isinstance(value,str) else value
    for secret in REDACT:
        if secret: text=text.replace(secret,'[REDACTED]')
    (OUT/name).write_text(text,encoding='utf-8')

def check(name,passed,detail=''):
    CHECKS.append({'test':name,'passed':bool(passed),'detail':detail})
    save('checks.json',CHECKS)

def api(session,body):
    r=session.post(ORIGIN+'/native.php',json=body,timeout=40,headers={'User-Agent':'SvoyiNative/2.4 Android'})
    r.raise_for_status(); value=r.json()
    csrf=value.get('state',{}).get('csrf','')
    if csrf and csrf not in REDACT: REDACT.append(csrf)
    return value

def account(tag):
    session=requests.Session()
    email='qa.repair.'+os.environ['GITHUB_RUN_ID']+'.'+tag+'@example.com'
    password='Qa'+secrets.token_hex(15); REDACT.append(password)
    name='QA '+('Andrii' if tag=='a' else 'Viktoriia')
    page=session.get(ORIGIN+'/?p=register',timeout=40); page.raise_for_status()
    soup=BeautifulSoup(page.text,'html.parser'); csrf=soup.select_one('input[name=csrf]')
    if not csrf: raise RuntimeError('Registration CSRF missing')
    token=csrf.get('value',''); REDACT.append(token)
    r=session.post(ORIGIN+'/?p=register',data={'csrf':token,'action':'register','start_goal':'all','name':name,'email':email,'city':'Praha','password':password},timeout=40)
    r.raise_for_status()
    state=api(session,{'op':'session','route':'/?p=home'})['state']
    uid=int(state.get('user',{}).get('id',0))
    if not state.get('signedIn') or uid<=0: raise RuntimeError('Registration not authenticated')
    return {'s':session,'email':email,'password':password,'name':name,'id':uid,'state':state}

def adb(*args,timeout=35,allow_fail=False):
    p=subprocess.run(['adb',*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
    if p.returncode and not allow_fail: raise RuntimeError('ADB failure: '+p.stderr.decode(errors='replace')[:200])
    return p.stdout

def ui():
    adb('shell','uiautomator','dump','/sdcard/qa-ui.xml')
    return ET.fromstring(adb('shell','cat','/sdcard/qa-ui.xml'))

def tap(attr,value,index=0,contains=False):
    root=ui(); nodes=[n for n in root.iter('node') if (value in n.get(attr,'') if contains else n.get(attr,'')==value)]
    if len(nodes)<=index: return False
    nums=list(map(int,re.findall(r'\d+',nodes[index].get('bounds',''))))
    if len(nums)!=4: return False
    x1,y1,x2,y2=nums
    adb('shell','input','tap',str((x1+x2)//2),str((y1+y2)//2)); return True

def capture(name):
    (OUT/(name+'.png')).write_bytes(adb('exec-out','screencap','-p'))
    try: save(name+'.xml',ET.tostring(ui(),encoding='unicode'))
    except Exception as e: save(name+'-dump-error.txt',str(e))
    state=adb('shell','dumpsys','activity','activities',allow_fail=True).decode(errors='replace')
    save(name+'-activity.txt','\n'.join(l for l in state.splitlines() if 'ResumedActivity' in l))

def alive():
    return bool(adb('shell','pidof',PACKAGE,allow_fail=True).strip())

def web_capture(a,b):
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
        context=browser.new_context(viewport={'width':412,'height':915},device_scale_factor=1,is_mobile=True,has_touch=True)
        context.add_cookies([{'name':c.name,'value':c.value,'url':ORIGIN} for c in a['s'].cookies])
        page=context.new_page(); page.on('pageerror',lambda e:check('website-js-error',False,str(e)))
        routes={'web-home':'/?p=home','web-cabinet':'/?p=profile','web-profile':'/?p=user&id='+str(a['id']),'web-mail':'/?p=messages','web-thread':'/?p=messages&with='+str(b['id'])}
        for label,route in routes.items():
            page.goto(ORIGIN+route,wait_until='domcontentloaded',timeout=45000); page.wait_for_timeout(2200)
            page.screenshot(path=str(OUT/(label+'.png')),full_page=True)
            html=page.content()
            for token in page.locator('input[name=csrf]').evaluate_all('(nodes)=>nodes.map(n=>n.value)'):
                if token not in REDACT:REDACT.append(token)
            save(label+'.html',html)
            styles=page.evaluate('''() => [...document.querySelectorAll('main,h1,h2,.profile-hero,.profile-card,.mail-app,.mail-layout,.chat-composer,.home-hero')].slice(0,50).map(e=>{const s=getComputedStyle(e),r=e.getBoundingClientRect();return {tag:e.tagName,cls:e.className,text:e.textContent.slice(0,130),font:s.fontSize,color:s.color,background:s.backgroundColor,border:s.borderRadius,padding:s.padding,width:r.width,height:r.height}})''')
            save(label+'-styles.json',styles)
        browser.close()

def run():
    a=account('a'); b=account('b')
    check('test-account-a',True); check('test-account-b',True)
    sent=api(b['s'],{'op':'mail-action','action':'send','route':'/?p=messages&with='+str(a['id']),'peer':a['id'],'body':'Перевірка пошти: повідомлення з сайту. Як справи?','nonce':secrets.token_hex(16),'csrf':b['state']['csrf'],'expectedAccount':b['id'],'kind':'text'})
    save('seed-message-result.json',sent)
    for label,route in [('home','/?p=home'),('cabinet','/?p=profile'),('profile','/?p=user&id='+str(a['id'])),('mail','/?p=messages'),('thread','/?p=messages&with='+str(b['id']))]:
        result=api(a['s'],{'op':'screen','route':route}); save('api-'+label+'.json',result)
    web_capture(a,b)
    apk=Path(os.environ.get('QA_APK',next(iter(Path('qa-input').glob('*.apk'))).as_posix()))
    save('apk.json',{'file':apk.name,'sha256':hashlib.sha256(apk.read_bytes()).hexdigest(),'package':PACKAGE})
    save('install.txt',adb('install','-r','-g',str(apk),timeout=90).decode())
    adb('logcat','-c'); adb('shell','monkey','-p',PACKAGE,'-c','android.intent.category.LAUNCHER','1');time.sleep(12)
    capture('android-01-login')
    if not tap('class','android.widget.EditText',0):raise RuntimeError('Email input absent')
    adb('shell','input','text',a['email'])
    if not tap('class','android.widget.EditText',1):raise RuntimeError('Password input absent')
    adb('shell','input','text',a['password']); adb('shell','input','keyevent','KEYCODE_BACK');time.sleep(1)
    if not tap('text','Увійти'):raise RuntimeError('Login button absent')
    time.sleep(12); capture('android-02-home')
    check('login-process-alive',alive())
    check('login-profile-tab-present',any('Профіль' in n.get('content-desc','') for n in ui().iter('node')))
    if tap('content-desc','Профіль'):
        time.sleep(7);capture('android-03-cabinet')
        if tap('text','Переглянути профіль'):
            time.sleep(7);capture('android-04-profile')
    clicked=tap('content-desc','Повідомлення',contains=True);check('tap-mail',clicked)
    time.sleep(9);capture('android-05-mail-with-message');check('mail-process-alive',alive())
    if alive():
        opened=tap('text',b['name'],contains=True);check('open-existing-thread',opened)
        if opened:
            time.sleep(6);capture('android-06-thread');check('thread-process-alive',alive())
            if alive() and tap('class','android.widget.EditText',0):
                adb('shell','input','text','Android%secho%sQA');time.sleep(1);capture('android-07-keyboard')
                found=tap('content-desc','Надіслати',contains=True);check('send-button',found)
                if found:
                    time.sleep(6);capture('android-08-sent')
                    response=api(b['s'],{'op':'screen','route':'/?p=messages&with='+str(a['id'])})
                    check('android-message-received-on-server','Android echo QA' in json.dumps(response,ensure_ascii=False))
    save('logcat.txt',adb('logcat','-d','-v','threadtime',timeout=40).decode(errors='replace'))
    log=(OUT/'logcat.txt').read_text();check('fatal-exception-absent','FATAL EXCEPTION' not in log)
    save('account-ids.json',{'a':a['id'],'b':b['id'],'only_disposable_test_accounts':True})

try:run()
except Exception as exc:
    check('harness-completed',False,type(exc).__name__+': '+str(exc))
    save('harness-error.txt',traceback.format_exc())
    try:save('logcat.txt',adb('logcat','-d','-v','threadtime',allow_fail=True).decode(errors='replace'))
    except Exception:pass
finally:
    save('checks.json',CHECKS)
    print(json.dumps(CHECKS,ensure_ascii=False))
    # Nonzero for a real failure; diagnostic outputs are still uploaded by always().
    raise SystemExit(0 if CHECKS and all(x['passed'] for x in CHECKS) else 1)
