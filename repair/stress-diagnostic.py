#!/usr/bin/env python3
"""Extend the independently verified round-trip test with files and lifecycle cases."""
import io,json,os,secrets,time,traceback
from pathlib import Path
import xml.etree.ElementTree as ET
from PIL import Image,ImageDraw
source=Path('qa-runtime/diagnose.py').read_text().split('\ntry:run()')[0]
source=source.replace("PACKAGE='eu.svoyi.testapp01'","PACKAGE=os.environ.get('QA_PACKAGE','eu.svoyi.testapp01')")
source=source.replace("OUT=Path('runtime-output')","OUT=Path(os.environ['QA_OUTPUT'])")
source=source.replace("email='qa.repair.'+os.environ['GITHUB_RUN_ID']+'.'+tag+'@example.com'","email='qa.repair.'+os.environ['GITHUB_RUN_ID']+'.'+os.environ['QA_PHASE']+'.'+tag+'@example.com'")
ns={};exec(compile(source,'qa-runtime/diagnose.py','exec'),ns)
original_capture=ns['capture'];original_api=ns['api'];tap=ns['tap'];adb=ns['adb'];check=ns['check'];save=ns['save'];alive=ns['alive'];ui=ns['ui'];PACKAGE=ns['PACKAGE'];seeded=False

def capture(name):
    if name=='android-01-login':
        for i in range(14):
            root=ui();txt=' '.join(n.get('text','') for n in root.iter('node'))
            if 'Pixel Launcher' in txt and ('responding' in txt or 'stopping' in txt):
                save('environment-note.txt','Unrelated Pixel Launcher dialog dismissed on disposable emulator')
                tap('text','Close app');adb('shell','am','start','-n',PACKAGE+'/eu.svoyi.nativeapp.MainActivity',allow_fail=True)
            elif any(n.get('class')=='android.widget.EditText' for n in root.iter('node')):break
            elif ('stopping' in txt or 'responding' in txt) and 'Свої' in txt:break
            time.sleep(3)
    original_capture(name)
ns['capture']=capture

def api(session,body):
    global seeded
    result=original_api(session,body)
    if body.get('op')=='mail-action' and body.get('action')=='send' and not seeded:
        seeded=True
        for text in ['[b]Жирний текст[/b] та українська мова: Ї Є Ґ 💙💛','[quote=QA]Відповідь на попереднє повідомлення[/quote] Перевірка довгої розмови.','Рядок 1\nРядок 2\nРядок 3 — перевірка перенесення.']:
            payload=dict(body,body=text,nonce=secrets.token_hex(16));original_api(session,payload)
        im=Image.new('RGB',(480,320),(221,234,249));dr=ImageDraw.Draw(im);dr.rectangle((25,25,455,295),outline=(40,82,147),width=8);dr.text((140,145),'QA ATTACHMENT',(20,40,70));stream=io.BytesIO();im.save(stream,format='PNG')
        for filename,data,mime,caption in [('qa-picture.png',stream.getvalue(),'image/png','Фото для перевірки'),('qa-document.txt',b'Svoyi QA attachment\n','text/plain','Файл для перевірки')]:
            payload=dict(body,body=caption,nonce=secrets.token_hex(16))
            r=session.post(ns['ORIGIN']+'/native.php',data={'_native_payload':json.dumps(payload,ensure_ascii=False)},files={'attachment':(filename,data,mime)},timeout=50,headers={'User-Agent':'SvoyiNative/2.4 Android'})
            reply=r.json();check('seed-'+filename,r.ok and reply.get('ok'),str(r.status_code));save('seed-'+filename+'.json',reply)
        original_api(session,dict(body,body='Готово до перевірки діалогу ✅',nonce=secrets.token_hex(16)))
    return result
ns['api']=api

try:
    ns['run']()
    # Re-entering a non-empty mailbox and a thread is a separate regression case.
    for i in range(3):
        adb('shell','input','keyevent','KEYCODE_BACK');time.sleep(2)
        if not tap('content-desc','Повернутися до діалогів'):
            tap('content-desc','Повідомлення',contains=True)
        time.sleep(5);capture('repeat-'+str(i)+'-inbox');check('repeat-'+str(i)+'-mail-alive',alive())
        opened=tap('text','QA Viktoriia',contains=True);check('repeat-'+str(i)+'-thread-open',opened)
        time.sleep(4);check('repeat-'+str(i)+'-thread-alive',alive())
    capture('android-09-thread-stress')
    adb('shell','input','keyevent','KEYCODE_BACK');time.sleep(1)
    tap('content-desc','Головна');time.sleep(7);capture('android-10-home-top')
    # Stable viewport fragments, not fabricated stitched screenshots.
    for i in range(1,4):
        adb('shell','input','swipe','530','1820','530','590','650');time.sleep(2);capture('android-10-home-scroll-'+str(i))
    tap('content-desc','Профіль');time.sleep(5);capture('android-11-cabinet')
    if tap('text','Переглянути профіль',contains=True):time.sleep(5);capture('android-12-public-profile')
    adb('shell','settings','put','system','font_scale','1.3');time.sleep(4);capture('android-13-large-font');check('large-font-process-alive',alive())
    adb('shell','settings','put','system','font_scale','1.0');time.sleep(3)
    adb('shell','am','force-stop',PACKAGE);adb('shell','am','start','-n',PACKAGE+'/eu.svoyi.nativeapp.MainActivity');time.sleep(12);capture('android-14-session-relaunch')
    check('session-survives-relaunch',any('Профіль' in n.get('content-desc','') for n in ui().iter('node')))
    tap('content-desc','Повідомлення',contains=True);time.sleep(6);capture('android-15-mail-after-relaunch');check('mail-after-relaunch-alive',alive())
except Exception as exc:
    check('stress-completed',False,type(exc).__name__+': '+str(exc));save('stress-error.txt',traceback.format_exc())
finally:
    try:
        log=adb('logcat','-d','-v','threadtime',allow_fail=True).decode(errors='replace');save('logcat-final.txt',log)
        check('fatal-exception-absent-final','FATAL EXCEPTION' not in log)
    except Exception:pass
    save('checks.json',ns['CHECKS']);print(json.dumps(ns['CHECKS'],ensure_ascii=False))
    raise SystemExit(0 if ns['CHECKS'] and all(c['passed'] for c in ns['CHECKS']) else 1)
