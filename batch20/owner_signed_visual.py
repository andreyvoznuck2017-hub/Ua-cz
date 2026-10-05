#!/usr/bin/env python3
import json,os,re,time,traceback,xml.etree.ElementTree as ET
from . import qa as q
raw_capture=q.capture
def fresh_ui():
    for _ in range(5):
        q.adb('shell','rm','-f','/sdcard/owner-visual.xml',allow_fail=True)
        q.adb('shell','uiautomator','dump','/sdcard/owner-visual.xml',allow_fail=True,timeout=20)
        raw=q.adb('shell','cat','/sdcard/owner-visual.xml',allow_fail=True)
        try:return ET.fromstring(raw)
        except ET.ParseError:time.sleep(.6)
    raise RuntimeError('No fresh UI hierarchy')
def current_ime():
    text=q.adb('shell','dumpsys','input_method',allow_fail=True).decode(errors='replace')
    m=re.search(r'\\bmInputShown=(true|false)\\b',text)
    return bool(m and m.group(1)=='true')
def hide_ime():
    if current_ime():q.adb('shell','input','keyevent','KEYCODE_BACK');time.sleep(.4)
q.ui=fresh_ui;q.ime=current_ime;q.hide_keyboard=hide_ime
from . import startup
def long_page(prefix):
    q.capture(prefix+'-top')
    for i in range(3):
        if not q.scroll():break
        q.capture(prefix+'-scroll-'+str(i+1))
def run():
    a,b=startup.start()
    # startup.start already captured before/after top home/profile/mail.
    q.goto_home();long_page('after248-home')
    startup.profile(True);long_page('after248-profile')
    q.goto_home();q.thread(a,b);q.capture('after248-mail-thread')
    q.type_into('Owner signed QA248 message');q.hide_keyboard();q.must('owner-signed-send',q.click('Надіслати','content-desc',True))
    q.must('owner-signed-peer-receipt',q.wait(lambda:any(m.get('body')=='Owner signed QA248 message' for m in q.messages(b,a)),25))
    q.capture('after248-mail-sent')
    q.save('owner-signed-result.json',{'apkSha256':os.environ['QA_SHA256'],'ownerSigned':True,'api':36,'package':q.PACKAGE})
try:run()
except Exception as e:
    q.check('owner-visual-runtime',False,type(e).__name__+': '+str(e));q.save('owner-visual-error.txt',traceback.format_exc())
    try:q.capture('owner-visual-failure')
    except Exception:pass
finally:q.finish()
raise SystemExit(0 if q.core['CHECKS'] and all(c['passed'] for c in q.core['CHECKS']) else 1)
