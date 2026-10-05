#!/usr/bin/env python3
"""Drive actual Android UI; check every transmitted result from the independent peer.
No personal browser, no real users, no mock acceptance. Failures remain failures.
"""
import hashlib,json,os,re,secrets,time,traceback,subprocess,shutil
from pathlib import Path
from urllib.parse import urljoin,urlparse
from PIL import Image,ImageDraw
code=Path('mail-next244/runtime.py').read_text().split('\ntry:run()')[0]
code=code.replace("'qa.actions244.'","'qa.compose246.'")
ns={};exec(compile(code,'mail-next244/runtime.py','exec'),ns)
adb,tap,save,check,api,account=[ns[n] for n in ['adb','tap','save','check','api','account']]
OUT=ns['OUT'];PACKAGE=ns['PACKAGE'];ORIGIN=ns['ORIGIN'];raw_ui=ns['ui'];notes=[]
def ui():
 root=raw_ui()
 title=next((n.get('text','') for n in root.iter('node') if n.get('package')=='android' and n.get('resource-id')=='android:id/alertTitle'),'')
 if title=="Pixel Launcher isn't responding" and len(notes)<3:
  n=next((n for n in root.iter('node') if n.get('package')=='android' and n.get('resource-id')=='android:id/aerr_close'),None)
  if n is not None:
   xy=list(map(int,re.findall(r'\d+',n.get('bounds',''))))
   if len(xy)==4:
    notes.append({'environmentDialog':title,'action':'dismiss launcher only','appErrorsIgnored':False});save('environment.json',notes)
    adb('shell','input','tap',str((xy[0]+xy[2])//2),str((xy[1]+xy[3])//2));time.sleep(2);return raw_ui()
 return root
ns['ui']=ui
capture=ns['capture'];wait=ns['wait'];must=ns['must'];keyboard=ns['keyboard'];hide_keyboard=ns['hide_keyboard'];msgs=ns['msgs'];find_msg=ns['find_msg']
def nodes():return list(ui().iter('node'))
def has(value,attr='text'):return any(value in n.get(attr,'') for n in nodes())
def click(value,attr='text',contains=False):return tap(attr,value,contains=contains)
def editors():return [n for n in nodes() if n.get('class')=='android.widget.EditText' and n.get('package')==PACKAGE]
def current_input():return next((n.get('text','') for n in editors() if n.get('focused')=='true'),next((n.get('text','') for n in editors()),''))
def enter(value,clear=False,require_already_focused=False):
 fields=editors();must('editor-present',bool(fields));n=next((n for n in fields if n.get('focused')=='true'),fields[0])
 if require_already_focused:must('reply-editor-already-focused',n.get('focused')=='true')
 if n.get('focused')!='true':
  xy=list(map(int,re.findall(r'\d+',n.get('bounds',''))));adb('shell','input','tap',str(xy[0]+15),str((xy[1]+xy[3])//2));time.sleep(.5)
 if clear:
  adb('shell','input','keycombination','113','29');adb('shell','input','keyevent','KEYCODE_DEL');time.sleep(.4)
  # Empty EditText exposes its hint as text on some versions.
  must('clear-editor',current_input() in ('','Повідомлення…'))
 else:adb('shell','input','keyevent','KEYCODE_MOVE_END')
 if value:adb('shell','input','text',value.replace(' ','%s'))
 time.sleep(.4)
def thread():
 hide_keyboard()
 if has('Повернутися до діалогів','content-desc'):return
 must('open-mail',click('Повідомлення','content-desc',True));must('inbox-peer-visible',wait(lambda:has(b['name'])));must('open-peer',click(b['name'],contains=True));must('thread-send-visible',wait(lambda:has('Надіслати','content-desc')))
def menu(text):
 hide_keyboard();must('long-press-message',ns['longpress'](text));must('message-actions-visible',wait(lambda:has('Копіювати')))
def send_marker(text):
 enter(text);must('tap-send',click('Надіслати','content-desc',True));must('peer-received-'+text,wait(lambda:bool(find_msg(b,a,text=text)),30));must('composer-cleared-after-send',wait(lambda:current_input() in ('','Повідомлення…')))
 return find_msg(b,a,text=text)
def pick_file(filename):
 hide_keyboard();must('attachment-menu',click('Фото, файли, голос','content-desc',True));must('file-choice',click('Фото або файл'));time.sleep(2)
 if not has(filename):
  click('Show roots','content-desc') or click('Показати кореневі папки','content-desc');time.sleep(.8)
  click('Downloads') or click('Завантаження');time.sleep(1)
 must('picker-has-'+filename,wait(lambda:has(filename),12));must('select-'+filename,click(filename,contains=True))
 must('returned-from-picker',wait(lambda:any(n.get('package')==PACKAGE and n.get('class')=='android.widget.EditText' for n in nodes()),15))
def staged(name):return any(name in n.get('text','') and n.get('package')==PACKAGE for n in nodes())
def check_download(message,path):
 attachment=message.get('attachment') or {};url=attachment.get('url','') if isinstance(attachment,dict) else attachment
 full=urljoin(ORIGIN,url);must('attachment-origin',urlparse(full).netloc==urlparse(ORIGIN).netloc and urlparse(full).scheme=='https')
 r=b['s'].get(full,timeout=30);must('peer-download-byte-match-'+path.name,r.ok and r.content==path.read_bytes())
def group(name,fn):
 try:fn();check(name,True)
 except Exception as e:
  check(name,False,type(e).__name__+': '+str(e));save(name+'-error.txt',traceback.format_exc())
  try:capture(name+'-failure')
  except Exception:pass
  # Recovery is logged; never turns a failed test into a pass.
  for _ in range(2):
   if has('Надіслати','content-desc'):break
   adb('shell','input','keyevent','KEYCODE_BACK',allow_fail=True);time.sleep(.5)
def run():
 global a,b
 apk=Path('signed-input/app.apk');baseline=Path('signed-input/baseline245.apk')
 must('exact-final-apk',hashlib.sha256(apk.read_bytes()).hexdigest()==os.environ['QA_SHA256'])
 must('exact-baseline',hashlib.sha256(baseline.read_bytes()).hexdigest()=='95fe1ad2849c7719ecd4b5b559fbbb860eb69386ee2564f732e637f02ab38cdb')
 save('apk.json',{'version':'2.4.6-compose','versionCode':346,'sha256':os.environ['QA_SHA256'],'package':PACKAGE,'api':os.environ['QA_API']})
 a,b=account('a'),account('b');ns['a']=a;ns['b']=b;save('accounts.json',{'a':a['id'],'b':b['id'],'disposableOnly':True})
 seed='Web seed QA246 — повідомлення для відповіді'
 res=api(b['s'],{'op':'mail-action','action':'send','route':'/?p=messages&with='+str(a['id']),'peer':a['id'],'body':seed,'nonce':secrets.token_hex(16),'csrf':b['state']['csrf'],'expectedAccount':b['id'],'kind':'text'});must('seed-accepted',res.get('ok'))
 textfile=Path('/tmp/qa246.txt');textfile.write_text('Svoyi actual Android document picker QA246\n')
 photo=Path('/tmp/qa246.png');im=Image.new('RGB',(320,220),(227,237,247));ImageDraw.Draw(im).text((50,100),'SVOYI QA246 PHOTO',fill=(20,40,70));im.save(photo)
 for f in [textfile,photo]:adb('push',str(f),'/sdcard/Download/'+f.name)
 save('install-baseline.txt',adb('install','-r','-g',str(baseline),timeout=90).decode());adb('logcat','-c',allow_fail=True);adb('shell','am','start','-n',PACKAGE+'/eu.svoyi.nativeapp.MainActivity')
 must('login-fields',wait(lambda:len(editors())>=2,35))
 for i,value in [(0,a['email']),(1,a['password'])]:
  must('focus-login-'+str(i),tap('class','android.widget.EditText',i));time.sleep(.4);adb('shell','input','text',value)
 hide_keyboard();must('login-submit',click('Увійти'));must('login-success',wait(lambda:has('Профіль','content-desc'),35));thread();must('seed-shown',wait(lambda:has('Web seed QA246')))
 menu('Web seed QA246');must('baseline-reply-action',click('Відповісти','content-desc'));time.sleep(3);capture('before245-reply');baseline_ime=keyboard();save('baseline-reply.json',{'keyboardShown':baseline_ime})
 hide_keyboard();click('Скасувати відповідь цитатою','content-desc');enter('',True);hide_keyboard()
 pick_file(textfile.name);baseline_staged=wait(lambda:staged(textfile.name),5);capture('before245-picker-return');save('baseline-picker.json',{'staged':baseline_staged})
 # No uninstall or data clear; update the user's exact previous application identity.
 save('install-update.txt',adb('install','-r','-g',str(apk),timeout=90).decode());adb('shell','am','start','-n',PACKAGE+'/eu.svoyi.nativeapp.MainActivity');must('session-survives-update',wait(lambda:has('Профіль','content-desc'),35));thread();must('seed-after-update',wait(lambda:has('Web seed QA246')))
 def reply():
  menu('Web seed QA246');must('reply-action',click('Відповісти','content-desc'));must('quote-preview',wait(lambda:has('Скасувати відповідь цитатою','content-desc'),10));must('reply-opens-ime-without-extra-tap',wait(keyboard,8));capture('after246-reply-keyboard')
  enter(' Reply QA246',require_already_focused=True);must('send-reply',click('Надіслати','content-desc',True));must('reply-received-peer',wait(lambda:bool(find_msg(b,a,text='Reply QA246')),30));m=find_msg(b,a,text='Reply QA246');must('quote-and-reply-kept','[quote]' in m.get('body','') and 'Web seed QA246' in m.get('body',''));must('keyboard-retained-after-send',keyboard());capture('after246-reply-sent');must('reply-input-cleared',wait(lambda:current_input() in ('','Повідомлення…')))
 group('reply-roundtrip',reply)
 def file_case(f,kind):
  enter('',True);pick_file(f.name);must(kind+'-staged',wait(lambda:staged(f.name),20));capture('after246-'+kind+'-staged');must(kind+'-send',click('Надіслати','content-desc',True));must(kind+'-received-peer',wait(lambda:any(m.get('attachmentName')==f.name for m in msgs(b,a)),35));m=next(m for m in msgs(b,a) if m.get('attachmentName')==f.name);check_download(m,f);capture('after246-'+kind+'-sent')
 group('file-picker-roundtrip',lambda:file_case(textfile,'file'))
 group('photo-picker-roundtrip',lambda:file_case(photo,'photo'))
 def edit_delete():
  enter('',True);m=send_marker('Edit target QA246');mid=m['id'];menu('Edit target QA246');must('own-edit-action',click('Редагувати','content-desc'));must('edit-dialog-open',wait(lambda:has('Редагувати повідомлення')));enter('Edited QA246',True);hide_keyboard();must('edit-save',click('Зберегти'));must('edit-received-peer',wait(lambda:find_msg(b,a,mid=mid).get('body')=='Edited QA246'));must('edit-timestamp-present',bool(find_msg(b,a,mid=mid).get('editedAt')));must('edit-reflected-ui',wait(lambda:has('Edited QA246')));capture('after246-edited')
  menu('Edited QA246');must('delete-request',click('Видалити для обох','content-desc'));must('delete-confirm-visible',wait(lambda:has('Видалити для обох?')));must('delete-cancel',click('Скасувати'));must('cancel-did-not-delete',not find_msg(b,a,mid=mid).get('deleted'))
  menu('Edited QA246');must('delete-request-again',click('Видалити для обох','content-desc'));must('delete-confirm',click('Видалити'));must('delete-received-peer',wait(lambda:find_msg(b,a,mid=mid).get('deleted')));capture('after246-deleted')
 group('edit-delete-roundtrip',edit_delete)
 def cancellation():
  enter('Keep draft QA246',True);menu('Web seed QA246');must('reply-with-draft',click('Відповісти','content-desc'));must('draft-reply-ime',wait(keyboard,8));must('cancel-quote',click('Скасувати відповідь цитатою','content-desc'));must('cancel-quote-preserves-text',current_input()=='Keep draft QA246');hide_keyboard();must('cancel-picker-menu',click('Фото, файли, голос','content-desc',True));must('cancel-picker-open',click('Фото або файл'));time.sleep(2);adb('shell','input','keyevent','KEYCODE_BACK');must('cancel-picker-returned',wait(lambda:has('Надіслати','content-desc')));must('cancel-picker-preserves-text',current_input()=='Keep draft QA246');capture('after246-picker-cancel-draft');time.sleep(1)
  adb('shell','am','force-stop',PACKAGE);adb('shell','am','start','-n',PACKAGE+'/eu.svoyi.nativeapp.MainActivity');must('session-after-relaunch',wait(lambda:has('Профіль','content-desc'),30));thread();must('draft-after-relaunch',wait(lambda:current_input()=='Keep draft QA246'));capture('after246-draft-relaunch')
 group('cancel-draft-session',cancellation)
 def regression():
  hide_keyboard()
  for i in range(3):
   must('home-'+str(i),click('Головна','content-desc'));time.sleep(2);must('profile-'+str(i),click('Профіль','content-desc'));time.sleep(2);thread();must('thread-alive-'+str(i),bool(adb('shell','pidof',PACKAGE,allow_fail=True).strip()))
  menu('Web seed QA246');must('six-reactions-kept',sum(n.get('content-desc','').startswith('Реакція ') for n in nodes())==6);must('no-peer-edit',not has('Редагувати'));capture('after246-reactions');must('react-heart',click('Реакція ❤️','content-desc'));seedid=next(m['id'] for m in msgs(a,b) if 'Web seed QA246' in m.get('body',''));must('peer-sees-heart',wait(lambda:any(r.get('emoji')=='❤️' for r in find_msg(b,a,mid=seedid).get('reactions',[]))))
  click('Головна','content-desc');time.sleep(3);capture('after246-home');click('Профіль','content-desc');time.sleep(3);capture('after246-profile')
 group('imagefix-navigation-reactions',regression)
 save('peer-final-chat.json',api(b['s'],{'op':'screen','route':'/?p=messages&with='+str(a['id'])}));shutil.copy2(apk,OUT/'Svoyi-Android-2.4.6.apk')
try:run()
except Exception as e:
 check('runtime-completed',False,type(e).__name__+': '+str(e));save('runtime-error.txt',traceback.format_exc())
 try:capture('failure')
 except Exception:pass
finally:
 try:
  log=adb('logcat','-d','-v','threadtime',allow_fail=True).decode(errors='replace');save('logcat.txt',log);lines=log.splitlines();fatal=[i for i,l in enumerate(lines) if 'FATAL EXCEPTION' in l and PACKAGE in '\n'.join(lines[i:i+8])];check('no-uncaught-app-crash',not fatal)
 except Exception as e:check('log-capture',False,type(e).__name__)
 save('checks.json',ns['CHECKS']);print(json.dumps(ns['CHECKS'],ensure_ascii=False));raise SystemExit(0 if ns['CHECKS'] and all(x['passed'] for x in ns['CHECKS']) else 1)
