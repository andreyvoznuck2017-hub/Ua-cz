from .qa import *

def run():
 a,b=start()
 # A bounded set of disposable messages is needed to exercise real history pagination.
 send_api(b,a,'Batch20 HISTORIC needle')
 for batch in range(8):
  for j in range(10):send_api(b,a,'Batch20 history %03d — long test conversation with independent server receipts.'%(batch*10+j))
  snapshot=api(a['s'],{'op':'screen','route':'/?p=messages&with='+str(b['id'])})['chat']
  if snapshot.get('older') or snapshot.get('moreMessages'):break
 save('history-fixture.json',{'createdHistoryMessages':(batch+1)*10+1,'older':snapshot.get('older'),'moreMessages':snapshot.get('moreMessages')})
 adb('shell','am','force-stop',PACKAGE);adb('shell','am','start','-n',PACKAGE+'/eu.svoyi.nativeapp.MainActivity');must('session-after-history-reset',wait(lambda:has('Профіль','content-desc'),30));thread(a,b)
 def search_older():
  must('thread-actions-menu',click('Дії діалогу','content-desc',True));must('history-search-menu',click('Пошук у діалозі'));must('history-search-field',wait(lambda:len(editors())>=2))
  es=[n for n in editors() if 'Текст у' in n.get('text','') or n.get('focused')=='true'];must('history-query-input',bool(es));tap_node(es[0]);adb('shell','input','text','HISTORIC');hide_keyboard();capture('search-before-older')
  must('older-search-available',has('Шукати в давніших повідомленнях','content-desc'));must('run-older-search',click('Шукати в давніших повідомленнях','content-desc'));must('historic-match-found',wait(lambda:has('Batch20 HISTORIC needle',contains=True),25));capture('search-after-older')
  must('close-history-search',click('Закрити пошук в історії','content-desc'));must('composer-unchanged-after-search',input_text() in ('','Повідомлення…','Повідомлення...'))
 case(2,'history-search-earlier-pages',search_older)
 def old_actions():
  thread(a,b);must('find-old-needle',seek('Batch20 HISTORIC needle',contains=True,up=True,limit=18))
  tree=ui();parents={c:p for p in tree.iter() for c in p};n=next(n for n in tree.iter('node') if 'Batch20 HISTORIC needle' in n.get('text','') and visible(n))
  while n is not None and not n.get('content-desc','').startswith('Дії повідомлення '):n=parents.get(n)
  must('stable-old-message-control',n is not None);tap_node(n,long=True);must('old-message-menu',wait(lambda:has('Відповісти','content-desc')));must('quote-old-message',click('Відповісти','content-desc'));must('reply-keyboard-open',wait(ime,8));capture('old-message-quote')
  type_into('Quote text stays',clear=True);hide_keyboard();must('older-message-after-quote',seek('Batch20 history 00',contains=True,up=False,limit=10))
  tree=ui();parents={c:p for p in tree.iter() for c in p};n=next(n for n in tree.iter('node') if 'Batch20 history 00' in n.get('text','') and visible(n))
  while n is not None and not n.get('content-desc','').startswith('Дії повідомлення '):n=parents.get(n)
  must('second-message-control',n is not None);tap_node(n,long=True);must('replace-quote-action',wait(lambda:has('Відповісти','content-desc')));click('Відповісти','content-desc');must('quote-replacement-keeps-text',wait(lambda:input_text()=='Quote text stays'));capture('old-message-replaced-quote');hide_keyboard();click('Скасувати відповідь цитатою','content-desc');type_into('',clear=True);hide_keyboard()
 case(1,'old-message-actions-and-quote-replacement',old_actions)
 def scroll_position():
  thread(a,b);hide_keyboard();scroll(up=True);scroll(up=True)
  def anchor():
   rows=[n for n in nodes() if n.get('content-desc','').startswith('Дії повідомлення ') and rect(n)[1]>420 and rect(n)[3]<1900]
   return [(n.get('content-desc'),rect(n)[1]) for n in rows]
  before=anchor();must('visible-history-anchor',bool(before));send_api(b,a,'Batch20 incoming while reading history');time.sleep(4);after=dict(anchor());common=[(key,y,after[key]) for key,y in before if key in after];must('history-anchor-preserved',bool(common) and abs(common[0][1]-common[0][2])<16,str(common));capture('new-message-does-not-jump')
  must('new-message-button',has('Перейти до нових повідомлень','content-desc'));click('Перейти до нових повідомлень','content-desc');must('latest-message-opened',wait(lambda:has('Batch20 incoming while reading history',contains=True)))
 case(3,'reading-position-and-new-message-navigation',scroll_position)
 def unread():
  goto_home();send_api(b,a,'Batch20 unread check');time.sleep(3)
  before=api(a['s'],{'op':'session','route':'/?p=home'});must('server-unread-positive',before.get('state',{}).get('unread',0)>0);thread(a,b)
  must('read-receipt-peer',wait(lambda:any(m.get('body')=='Batch20 unread check' and m.get('read') and m.get('delivered') for m in messages(b,a)),20));must('unread-cleared-server',api(a['s'],{'op':'session','route':'/?p=home'}).get('state',{}).get('unread')==0);capture('read-counter-and-receipt')
 case(4,'unread-delivery-read-roundtrip',unread)
 def offline_send():
  thread(a,b);type_into('Batch20 offline preserved');hide_keyboard()
  try:
   adb('shell','svc','wifi','disable');adb('shell','svc','data','disable');time.sleep(2);must('tap-offline-send',click('Надіслати','content-desc',True));must('offline-text-retained',wait(lambda:input_text()=='Batch20 offline preserved',7));must('offline-not-on-server',not any(m.get('body')=='Batch20 offline preserved' for m in messages(b,a)));capture('offline-draft-kept')
  finally:adb('shell','svc','wifi','enable');adb('shell','svc','data','enable')
  time.sleep(5);must('retry-normal-send',click('Надіслати','content-desc',True));click('Надіслати','content-desc',True);must('retry-single-receipt',wait(lambda:sum(m.get('body')=='Batch20 offline preserved' for m in messages(b,a))==1,25));must('input-cleared-only-after-receipt',wait(lambda:input_text() in ('','Повідомлення…','Повідомлення...')));capture('offline-retry-one-message')
 case(5,'offline-and-duplicate-send',offline_send)
 def attachments():
  thread(a,b);type_into('',clear=True);hide_keyboard();fixture=Path('/tmp/batch20-attachment.txt');fixture.write_text('Batch20 actual document picker transfer\n');adb('push',str(fixture),'/sdcard/Download/'+fixture.name)
  must('attachment-tools',click('Фото, файли, голос','content-desc',True));must('file-picker-open',click('Фото або файл'));time.sleep(2)
  if not has(fixture.name,app=False):click('Show roots','content-desc',app=False);time.sleep(.6);click('Downloads',app=False);time.sleep(1)
  must('file-visible-in-system-picker',wait(lambda:has(fixture.name,app=False)));click(fixture.name,app=False);must('file-staged',wait(lambda:has(fixture.name,contains=True),20));capture('actual-file-staged');must('send-file',click('Надіслати','content-desc',True));must('file-received-peer',wait(lambda:any(m.get('attachmentName')==fixture.name for m in messages(b,a)),30))
  m=next(m for m in messages(b,a) if m.get('attachmentName')==fixture.name);att=m.get('attachment');url=att.get('url','') if isinstance(att,dict) else str(att or '');url=urljoin(ORIGIN,url);must('attachment-same-origin',urlsplit(url).netloc==urlsplit(ORIGIN).netloc);r=b['s'].get(url,timeout=25);must('attachment-byte-identical',r.ok and r.content==fixture.read_bytes());capture('actual-file-sent')
  type_into('Cancel picker keeps draft');hide_keyboard();click('Фото, файли, голос','content-desc',True);click('Фото або файл');time.sleep(1);adb('shell','input','keyevent','KEYCODE_BACK');must('cancel-preserves-draft',wait(lambda:input_text()=='Cancel picker keeps draft'));capture('picker-cancel-preserved');type_into('',clear=True)
 case(6,'attachment-selection-transfer-cancellation',attachments)

try:run()
except Exception as e:check('mail-suite-startup',False,str(e));save('startup-error.txt',traceback.format_exc());capture('startup-failure')
finally:
 try:adb('shell','svc','wifi','enable');adb('shell','svc','data','enable')
 except Exception:pass
 finish()
raise SystemExit(0 if TASKS and all(t['status']=='passed' for t in TASKS) and all(c['passed'] for c in core['CHECKS']) else 1)
