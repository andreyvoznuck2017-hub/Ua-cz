#!/usr/bin/env python3
"""Run the exact already-delivered APK on older supported Android releases.
Uses disposable server accounts only. No changes to application bytes or server code.
"""
import json,os,time,traceback
from pathlib import Path
source=Path('qa-runtime/diagnose.py').read_text().split('\ntry:run()')[0]
source=source.replace("PACKAGE='eu.svoyi.testapp01'","PACKAGE='eu.svoyi.testapp02'")
source=source.replace("email='qa.repair.'+os.environ['GITHUB_RUN_ID']+'.'+tag+'@example.com'","email='qa.compat.'+os.environ['GITHUB_RUN_ID']+'.'+os.environ['QA_API']+'.'+tag+'@example.com'")
ns={};exec(compile(source,'qa-runtime/diagnose.py','exec'),ns)
ns['web_capture']=lambda a,b: None  # This run is Android compatibility, not a website visual audit.
track=[];original_account=ns['account']
def account(tag):
    value=original_account(tag);track.append(value);return value
ns['account']=account
try:
    ns['run']()
    if not all(x['passed'] for x in ns['CHECKS']):raise RuntimeError('Initial mail scenario failed')
    adb,tap,capture,ui,check=ns['adb'],ns['tap'],ns['capture'],ns['ui'],ns['check']
    adb('shell','input','keyevent','KEYCODE_BACK');time.sleep(2)
    for i in range(3):
        tap('content-desc','Повернутися до діалогів')
        tap('content-desc','Повідомлення',contains=True);time.sleep(5)
        check('repeat-mail-'+str(i),tap('text',track[1]['name'],contains=True))
        time.sleep(4);capture('compat-thread-'+str(i));check('thread-visible-'+str(i),any('Надіслати' in n.get('content-desc','') for n in ui().iter('node')))
        adb('shell','input','keyevent','KEYCODE_BACK');time.sleep(2)
    adb('shell','am','force-stop',ns['PACKAGE'])
    adb('shell','am','start','-n',ns['PACKAGE']+'/eu.svoyi.nativeapp.MainActivity');time.sleep(10)
    check('session-after-restart',any('Профіль' in n.get('content-desc','') for n in ui().iter('node')))
    check('tap-mail-after-restart',tap('content-desc','Повідомлення',contains=True));time.sleep(5);capture('compat-mail-after-restart')
    check('inbox-after-restart',any(track[1]['name'] in n.get('text','') for n in ui().iter('node')))
except Exception as exc:
    ns['check']('compatibility-completed',False,type(exc).__name__+': '+str(exc))
    ns['save']('compatibility-error.txt',traceback.format_exc())
finally:
    try:
        log=ns['adb']('logcat','-d','-v','threadtime',allow_fail=True).decode(errors='replace')
        ns['save']('logcat-final.txt',log)
        ns['check']('no-uncaught-fatal','FATAL EXCEPTION' not in log)
        ns['capture']('compat-final')
    except Exception as exc:ns['check']('final-evidence',False,type(exc).__name__)
    ns['save']('checks.json',ns['CHECKS'])
    print(json.dumps(ns['CHECKS'],ensure_ascii=False))
    raise SystemExit(0 if ns['CHECKS'] and all(x['passed'] for x in ns['CHECKS']) else 1)
