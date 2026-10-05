#!/usr/bin/env python3
"""Actions are driven through Android UI; server reads independently verify their effects.
Only two disposable accounts. No real user's conversations or browser are touched.
"""
import hashlib,json,os,re,secrets,time,traceback,subprocess,shutil
from pathlib import Path
src=Path('qa-runtime/diagnose.py').read_text().split('\ntry:run()')[0]
src=src.replace("PACKAGE='eu.svoyi.testapp01'","PACKAGE='eu.svoyi.nativeapp'")
src=src.replace("'qa.repair.'+os.environ['GITHUB_RUN_ID']+'.'+tag","'qa.actions244.'+os.environ['GITHUB_RUN_ID']+'.'+os.environ['QA_API']+'.'+tag")
ns={};exec(compile(src,'qa-runtime/diagnose.py','exec'),ns)
adb,ui,tap,capture,save,check,api,account=[ns[n] for n in ['adb','ui','tap','capture','save','check','api','account']]
PACKAGE=ns['PACKAGE'];OUT=ns['OUT'];APK=Path('signed-input/app.apk')
def must(name,ok,detail=''):
 check(name,ok,detail)
 if not ok:raise AssertionError(name)
def wait(fn,seconds=25):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  try:
   if fn():return True
  except Exception:pass
  time.sleep(1)
 return False
def nodes():return list(ui().iter('node'))
def has(value,attr='text'):return any(value in n.get(attr,'') for n in nodes())
def click(value,attr='text',contains=False):return tap(attr,value,contains=contains)
def longpress(value):
 for n in nodes():
  if value in n.get('text','') and n.get('class')=='android.widget.TextView':
   b=list(map(int,re.findall(r'\d+',n.get('bounds',''))));
   if len(b)==4:
    x,y=(b[0]+b[2])//2,(b[1]+b[3])//2;adb('shell','input','swipe',str(x),str(y),str(x),str(y),'900');time.sleep(1);return True
 return False
def keyboard():return 'mInputShown=true' in adb('shell','dumpsys','input_method',allow_fail=True).decode(errors='replace')
def hide_keyboard():
 if keyboard():adb('shell','input','keyevent','KEYCODE_BACK');time.sleep(1)
def write(value,clear=False):
 must('composer-field-accessible',tap('class','android.widget.EditText',0));time.sleep(.5)
 if clear:adb('shell','input','keyevent','KEYCODE_MOVE_END');adb('shell','input','keyevent',*(['KEYCODE_DEL']*160))
 adb('shell','input','text',value.replace(' ','%s'));time.sleep(.5)
def msgs(who,peer):return api(who['s'],{'op':'screen','route':'/?p=messages&with='+str(peer['id'])}).get('chat',{}).get('messages',[])
def find_msg(who,peer,text=None,mid=None):return next((m for m in msgs(who,peer) if (m.get('id')==mid if mid is not None else text in m.get('body',''))),{})
def get_id(text):return find_msg(a,b,text=text).get('id',0)
def to_thread():
 hide_keyboard()
 if has('Повернутися до діалогів','content-desc'):return True
 must('tap-mail',click('Повідомлення','content-desc',True));must('mail-loaded',wait(lambda:has(b['name'])));must('tap-peer',click(b['name'],contains=True));return wait(lambda:has('Надіслати','content-desc'))
def group(name,fn):
 try:fn();check(name,True)
 except Exception as e:
  check(name,False,type(e).__name__+': '+str(e));save(name+'-error.txt',traceback.format_exc())
  try:capture(name+'-failure')
  except Exception:pass
  # Dismiss one dialog; do not hide a failed assertion or substitute an API action.
  adb('shell','input','keyevent','KEYCODE_BACK',allow_fail=True);time.sleep(1)
def action_menu(text):
 hide_keyboard();must('long-press-message',longpress(text));must('action-sheet-visible',wait(lambda:has('Копіювати')))
def run():
 global a,b,seedid
 digest=hashlib.sha256(APK.read_bytes()).hexdigest();must('exact-candidate-bytes',digest==os.environ['QA_SHA256'])
 save('apk.json',{'sha256':digest,'package':PACKAGE,'versionCode':344,'androidApi':os.environ['QA_API']})
 a,b=account('a'),account('b');save('accounts.json',{'a':a['id'],'b':b['id'],'disposable_only':True})
 response=api(b['s'],{'op':'mail-action','action':'send','route':'/?p=messages&with='+str(a['id']),'peer':a['id'],'body':'Web seed QA244 — перевірка відповіді 💙','nonce':secrets.token_hex(16),'csrf':b['state']['csrf'],'expectedAccount':b['id'],'kind':'text'});must('seed-accepted',response.get('ok'))
 save('install-baseline.txt',adb('install','-r','-g','signed-input/baseline243.apk',timeout=90).decode());adb('logcat','-c',allow_fail=True)
 adb('shell','am','start','-n',PACKAGE+'/eu.svoyi.nativeapp.MainActivity');must('login-fields',wait(lambda:sum(n.get('class')=='android.widget.EditText' for n in nodes())>=2))
 for i,v in [(0,a['email']),(1,a['password'])]:
  must('login-focus-'+str(i),tap('class','android.widget.EditText',i));time.sleep(1);adb('shell','input','text',v)
 hide_keyboard();must('submit-login',click('Увійти'));must('authenticated',wait(lambda:has('Профіль','content-desc'),35));must('baseline-thread',to_thread());must('seed-visible',wait(lambda:has('Web seed QA244')))
 seedid=get_id('Web seed QA244');must('seed-has-id',seedid>0);action_menu('Web seed QA244');capture('01-before-old-menu');adb('shell','input','keyevent','KEYCODE_BACK')
 # Install over the same package and signer; no uninstall or app-data clear.
 save('install-update.txt',adb('install','-r','-g',str(APK),timeout=90).decode());adb('shell','am','start','-n',PACKAGE+'/eu.svoyi.nativeapp.MainActivity');must('session-retained-after-update',wait(lambda:has('Профіль','content-desc'),35));capture('02-home-after-update');must('candidate-thread',to_thread());must('seed-after-update',wait(lambda:has('Web seed QA244')))
 def reactions():
  action_menu('Web seed QA244');must('six-quick-reactions',sum(n.get('content-desc','').startswith('Реакція ') for n in nodes())==6);must('no-edit-delete-for-peer',not has('Редагувати') and not has('Видалити для обох'));capture('03-new-reaction-sheet')
  must('choose-heart',click('Реакція ❤️','content-desc'));must('heart-persisted-server',wait(lambda:any(r.get('emoji')=='❤️' for r in find_msg(a,b,mid=seedid).get('reactions',[]))))
  action_menu('Web seed QA244');capture('04-selected-reaction');must('remove-selected-heart',click('Реакція ❤️','content-desc'));must('heart-removed-server',wait(lambda:not find_msg(a,b,mid=seedid).get('reactions')))
  action_menu('Web seed QA244');must('choose-thumbs-up',click('Реакція 👍','content-desc'));must('peer-sees-reaction',wait(lambda:any(r.get('emoji')=='👍' for r in find_msg(b,a,mid=seedid).get('reactions',[]))))
 group('reactions-roundtrip',reactions)
 def reply():
  action_menu('Web seed QA244');must('reply-action',click('Відповісти','content-desc'));must('reply-context-visible',wait(lambda:has('Скасувати відповідь цитатою','content-desc')));must('reply-opens-keyboard',wait(keyboard));capture('05-reply-keyboard')
  must('cancel-reply',click('Скасувати відповідь цитатою','content-desc'));must('cancel-preserves-empty-draft',wait(lambda:not has('Скасувати відповідь цитатою','content-desc')))
  action_menu('Web seed QA244');must('reply-again',click('Відповісти','content-desc'));write(' Reply QA244');must('send-reply',click('Надіслати','content-desc',True));must('reply-received-on-server',wait(lambda:bool(find_msg(b,a,text='Reply QA244'))));m=find_msg(b,a,text='Reply QA244');must('reply-keeps-source-quote','Web seed QA244' in m.get('body','') and '[quote]' in m.get('body',''));capture('06-reply-sent')
 group('reply-roundtrip',reply)
 def edit_delete():
  write('Edit target QA244',True);must('send-edit-target',click('Надіслати','content-desc',True));must('edit-target-received',wait(lambda:get_id('Edit target QA244')>0));mid=get_id('Edit target QA244')
  action_menu('Edit target QA244');capture('07-own-message-actions');must('edit-action',click('Редагувати','content-desc'));must('edit-dialog',wait(lambda:has('Редагувати повідомлення')));write('Edited QA244',True);hide_keyboard();must('save-edit',click('Зберегти'));must('edited-server-body',wait(lambda:find_msg(b,a,mid=mid).get('body')=='Edited QA244'));must('edited-server-timestamp',bool(find_msg(b,a,mid=mid).get('editedAt')));must('edited-ui',wait(lambda:has('Edited QA244')));capture('08-edited-message')
  action_menu('Edited QA244');must('delete-action',click('Видалити для обох','content-desc'));must('delete-confirmation',wait(lambda:has('Видалити для обох?')));must('cancel-delete',click('Скасувати'));must('cancel-does-not-delete',not find_msg(b,a,mid=mid).get('deleted'))
  action_menu('Edited QA244');must('delete-again',click('Видалити для обох','content-desc'));must('confirm-delete',click('Видалити'));must('deleted-server',wait(lambda:find_msg(b,a,mid=mid).get('deleted')));capture('09-deleted-message')
 group('edit-delete-roundtrip',edit_delete)
 def file_upload():
  write('',True);hide_keyboard();payload=Path('/tmp/qa244.txt');payload.write_text('Svoyi Android picker upload QA244\n');adb('push',str(payload),'/sdcard/Download/qa244.txt')
  must('attachment-button',click('Фото, файли, голос','content-desc',True));must('attachment-choice',click('Фото або файл'));time.sleep(3);capture('10-system-file-picker')
  if not has('qa244.txt'):
   if click('Show roots','content-desc') or click('Показати кореневі папки','content-desc'):time.sleep(1)
   if not click('Downloads'):click('Завантаження')
   time.sleep(2)
  must('select-real-file',click('qa244.txt',contains=True));must('attachment-staged',wait(lambda:has('qa244.txt'),30));capture('11-file-staged');must('send-file',click('Надіслати','content-desc',True));must('file-received-peer',wait(lambda:any(m.get('attachmentName')=='qa244.txt' for m in msgs(b,a)),35))
  m=next(m for m in msgs(b,a) if m.get('attachmentName')=='qa244.txt');url=m.get('attachment',{}).get('url','');r=b['s'].get(url,timeout=30);must('peer-file-exact-content',r.ok and r.content==payload.read_bytes());capture('12-file-delivered')
 group('file-picker-roundtrip',file_upload)
 def draft():
  write('Draft QA244',True);time.sleep(2);hide_keyboard();adb('shell','am','force-stop',PACKAGE);adb('shell','am','start','-n',PACKAGE+'/eu.svoyi.nativeapp.MainActivity');must('session-after-restart',wait(lambda:has('Профіль','content-desc'),30));must('thread-after-restart',to_thread());must('draft-after-restart',wait(lambda:has('Draft QA244')));capture('13-draft-restored')
 group('draft-and-session',draft)
 hide_keyboard();click('Головна','content-desc');time.sleep(4);capture('14-home');click('Профіль','content-desc');time.sleep(4);capture('15-profile')
 save('server-final-chat.json',api(b['s'],{'op':'screen','route':'/?p=messages&with='+str(a['id'])}))
 shutil.copy2(APK,OUT/'Svoyi-Android-2.4.4.apk')
try:run()
except Exception as e:
 check('runtime-completed',False,type(e).__name__+': '+str(e));save('runtime-error.txt',traceback.format_exc())
 try:capture('failure')
 except Exception:pass
finally:
 try:
  logs=adb('logcat','-d','-v','threadtime',allow_fail=True).decode(errors='replace');save('logcat.txt',logs);lines=logs.splitlines();fatal=[i for i,l in enumerate(lines) if 'FATAL EXCEPTION' in l and PACKAGE in '\n'.join(lines[i:i+8])];check('no-uncaught-app-crash',not fatal)
 except Exception as e:check('log-capture',False,type(e).__name__)
 save('checks.json',ns['CHECKS']);print(json.dumps(ns['CHECKS'],ensure_ascii=False));raise SystemExit(0 if ns['CHECKS'] and all(x['passed'] for x in ns['CHECKS']) else 1)
