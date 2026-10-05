#!/usr/bin/env python3
"""Acceptance of the exact locally signed APK. No browser interaction on user's computer.
Only disposable QA accounts; actual screens, server receipts, ART and instrumentation.
"""
import hashlib,json,os,re,secrets,time,traceback
from pathlib import Path
import xml.etree.ElementTree as ET
source=Path('qa-runtime/diagnose.py').read_text().split('\ntry:run()')[0]
source=source.replace("PACKAGE='eu.svoyi.testapp01'","PACKAGE='eu.svoyi.nativeapp'")
source=source.replace("email='qa.repair.'+os.environ['GITHUB_RUN_ID']+'.'+tag+'@example.com'","email='qa.final.'+os.environ['GITHUB_RUN_ID']+'.'+os.environ['QA_API']+'.'+tag+'@example.com'")
ns={};exec(compile(source,'qa-runtime/diagnose.py','exec'),ns)
adb,ui,tap,capture,save,check,api,account=[ns[n] for n in ['adb','ui','tap','capture','save','check','api','account']]
PACKAGE=ns['PACKAGE'];APK=Path('signed-input/Svoyi-Android-2.4.3.apk');OUT=ns['OUT']
def must(name,passed,detail=''):
 check(name,passed,detail)
 if not passed:raise AssertionError(name)
def wait(predicate,seconds=25):
 deadline=time.monotonic()+seconds
 while time.monotonic()<deadline:
  try:
   root=ui()
   if predicate(root):return True
  except Exception:pass
  time.sleep(1)
 return False
def texts(root):return ' '.join(n.get('text','') for n in root.iter('node'))
def hasdesc(root,label):return any(label in n.get('content-desc','') for n in root.iter('node'))
def login(a):
 must('login-form-visible',wait(lambda r:len([n for n in r.iter('node') if n.get('class')=='android.widget.EditText'])>=2))
 time.sleep(2)
 for attempt in range(2):
  for idx,value in [(0,a['email']),(1,a['password'])]:
   must('focus-login-field-'+str(attempt)+'-'+str(idx),tap('class','android.widget.EditText',idx))
   time.sleep(1);adb('shell','input','keyevent','KEYCODE_MOVE_END');adb('shell','input','keyevent',*(['KEYCODE_DEL']*100))
   adb('shell','input','text',value);time.sleep(1)
  # Verify email reached the field; never emit or capture the password value.
  r=ui();edits=[n for n in r.iter('node') if n.get('class')=='android.widget.EditText'];must('email-entered-'+str(attempt),bool(edits) and edits[0].get('text')==a['email'])
  adb('shell','input','keyevent','KEYCODE_BACK');time.sleep(1);must('submit-login-'+str(attempt),tap('text','Увійти'))
  if wait(lambda r:a['name'] in texts(r) and not any(n.get('password')=='true' for n in r.iter('node')),30):return
  # A second attempt is input retry, not a silently accepted authentication failure.
  capture('login-attempt-'+str(attempt)+'-failed')
 must('authenticated-home',False)
def open_inbox(peer):
 if hasdesc(ui(),'Повернутися до діалогів'):tap('content-desc','Повернутися до діалогів');time.sleep(1)
 if not tap('content-desc','Повідомлення',contains=True):adb('shell','input','keyevent','KEYCODE_BACK');time.sleep(1);must('inbox-navigation',tap('content-desc','Повідомлення',contains=True))
 return wait(lambda r:peer['name'] in texts(r) and hasdesc(r,'Фільтри діалогів'),30)
def editor():return [n for n in ui().iter('node') if n.get('class')=='android.widget.EditText']
def clear_editor():
 must('focus-message-input',tap('class','android.widget.EditText',0));adb('shell','input','keyevent','KEYCODE_MOVE_END');adb('shell','input','keyevent',*(['KEYCODE_DEL']*100))
def run():
 digest=hashlib.sha256(APK.read_bytes()).hexdigest();must('exact-signed-apk',digest==os.environ['QA_SHA256'])
 save('apk.json',{'sha256':digest,'package':PACKAGE,'versionCode':343,'api':os.environ['QA_API']})
 # Execute packaged policy with genuine Android JSONObject in ART, not JVM doubles.
 for src,dst in [(APK,'/data/local/tmp/svoyi-candidate.apk'),(Path('signed-input/status-probe.jar'),'/data/local/tmp/status-probe.jar'),(Path('signed-input/baseline242.apk'),'/data/local/tmp/svoyi-baseline.apk')]:adb('push',str(src),dst)
 for name,apk,extra in [('baseline','/data/local/tmp/svoyi-baseline.apk',['baseline']),('candidate','/data/local/tmp/svoyi-candidate.apk',[])]:
  out=adb('shell','dalvikvm','-cp','/data/local/tmp/status-probe.jar:'+apk,'eu.svoyi.qa.StatusProbe',*extra,timeout=70).decode(errors='replace');save('art-'+name+'.txt',out);must('art-'+name,'ART_CHECKS_PASSED' in out)
 a,b=account('a'),account('b');save('accounts.json',{'self':a['id'],'peer':b['id'],'disposable_only':True})
 seed=api(b['s'],{'op':'mail-action','action':'send','route':'/?p=messages&with='+str(a['id']),'peer':a['id'],'body':'Привіт! Перевіряємо нову пошту 💙💛','nonce':secrets.token_hex(16),'csrf':b['state']['csrf'],'expectedAccount':b['id'],'kind':'text'});must('seed-server-message',seed.get('ok'));save('seed-receipt.json',seed)
 if Path('signed-input/original-main.apk').exists():
  save('install-original.txt',adb('install','-r','-g','signed-input/original-main.apk',timeout=90).decode());must('install-original-main',True)
 save('install-candidate.txt',adb('install','-r','-g',str(APK),timeout=90).decode());must('install-candidate',True)
 adb('logcat','-c',allow_fail=True);adb('shell','am','start','-n',PACKAGE+'/eu.svoyi.nativeapp.MainActivity');login(a);capture('01-home')
 must('authenticated-home',True);must('open-nonempty-inbox',open_inbox(b));capture('02-inbox')
 must('open-diagnostic-menu',tap('content-desc','Фільтри діалогів'));must('diagnostic-menu-item',tap('text','Діагностика застосунку'))
 must('diagnostic-version',wait(lambda r:'2.4.3-stability' in texts(r)));capture('03-local-diagnostic');must('close-diagnostic',tap('text','Закрити'))
 must('open-thread',tap('text',b['name'],contains=True));must('received-seed-visible',wait(lambda r:'Перевіряємо нову пошту' in texts(r)));capture('04-thread')
 clear_editor();message='QA243-'+os.environ['QA_API']+'-'+os.environ['GITHUB_RUN_ID'];adb('shell','input','text',message);time.sleep(2)
 r=ui();must('typed-message-visible',message in texts(r));must('compact-attachment-visible',hasdesc(r,'Фото, файли, голос'));must('large-toolbar-hidden-with-keyboard',not hasdesc(r,'Голосове повідомлення'));capture('05-typing')
 must('send-button',tap('content-desc','Надіслати повідомлення'));time.sleep(5)
 received=api(b['s'],{'op':'screen','route':'/?p=messages&with='+str(a['id'])});save('server-roundtrip.json',received);must('delivered-to-peer-server',message in json.dumps(received,ensure_ascii=False))
 must('composer-still-present',hasdesc(ui(),'Надіслати повідомлення'));capture('06-sent-with-keyboard')
 # Persist a local draft through reinstall/update using the same signing identity.
 clear_editor();draft='draft243-'+os.environ['QA_API'];adb('shell','input','text',draft);time.sleep(2);adb('shell','input','keyevent','KEYCODE_BACK')
 save('reinstall.txt',adb('install','-r',str(APK),timeout=90).decode());adb('shell','am','force-stop',PACKAGE);adb('shell','am','start','-n',PACKAGE+'/eu.svoyi.nativeapp.MainActivity');time.sleep(8)
 must('session-after-reinstall',open_inbox(b));must('thread-after-reinstall',tap('text',b['name'],contains=True));must('draft-after-reinstall',wait(lambda r:draft in texts(r)));capture('07-draft-after-update')
 for n in range(2):
  must('repeat-inbox-'+str(n),open_inbox(b));must('repeat-thread-'+str(n),tap('text',b['name'],contains=True));must('repeat-composer-'+str(n),wait(lambda r:hasdesc(r,'Надіслати повідомлення')))
 adb('shell','input','keyevent','KEYCODE_BACK');time.sleep(1)
 # Network outage must not clear the draft or close the application.
 adb('shell','svc','wifi','disable');adb('shell','svc','data','disable');time.sleep(6);capture('08-network-unavailable')
 must('draft-survives-offline',draft in texts(ui()));must('process-survives-offline',bool(adb('shell','pidof',PACKAGE,allow_fail=True).strip()))
 adb('shell','svc','wifi','enable');adb('shell','svc','data','enable');time.sleep(7)
 must('network-recovered-inbox',open_inbox(b));capture('09-reconnected-inbox')
 # Test-only instrumentation shares the original signer and is not part of the delivered APK.
 adb('install','-r','signed-input/qa-instrumentation.apk',timeout=60)
 out=adb('shell','am','instrument','-w','eu.svoyi.qa.stabilityprobe/eu.svoyi.qa.RecoveryProbe',timeout=90).decode(errors='replace');save('injected-recovery-instrumentation.txt',out)
 must('malformed-model-recovery',all(x in out for x in ['caught-malformed-model=true','recovery-panel-visible=true','local-sanitized-report=true','home-action-dispatched=true','INSTRUMENTATION_CODE: -1']))
 adb('pull','/sdcard/Android/data/'+PACKAGE+'/files/qa-recovery.png',str(OUT/'10-injected-error-recovery.png'))
 adb('shell','am','start','-n',PACKAGE+'/eu.svoyi.nativeapp.MainActivity');time.sleep(6);must('mail-after-recovery',open_inbox(b));capture('11-inbox-after-recovery')
 # Final file copied unchanged into evidence, so the delivered download is byte-identical to the runtime test.
 import shutil;shutil.copy2(APK,OUT/'Svoyi-Europe-Android-v2.4.3-Stability.apk')
try:run()
except Exception as exc:
 check('final-runtime-completed',False,type(exc).__name__+': '+str(exc));save('error.txt',traceback.format_exc())
 try:capture('failure-screen')
 except Exception:pass
finally:
 try:
  adb('shell','svc','wifi','enable',allow_fail=True);adb('shell','svc','data','enable',allow_fail=True)
  log=adb('logcat','-d','-v','threadtime',allow_fail=True).decode(errors='replace');save('logcat-final.txt',log)
  lines=log.splitlines();fatal=[]
  for n,line in enumerate(lines):
   if 'FATAL EXCEPTION' in line and PACKAGE in '\n'.join(lines[n:n+8]):fatal.append('\n'.join(lines[n:n+24]))
  save('application-crashes.txt','\n\n'.join(fatal));check('no-uncaught-application-crash',not fatal)
 except Exception as exc:check('final-log-capture',False,type(exc).__name__)
 save('checks.json',ns['CHECKS']);print(json.dumps(ns['CHECKS'],ensure_ascii=False));raise SystemExit(0 if ns['CHECKS'] and all(x['passed'] for x in ns['CHECKS']) else 1)
