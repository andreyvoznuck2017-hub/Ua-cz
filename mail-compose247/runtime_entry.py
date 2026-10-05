#!/usr/bin/env python3
"""Extend the checked suite with quote/editor acceptance; writes use real Android UI.
Driver corrections target XML attributes and the original message, not its quote preview.
"""
from pathlib import Path
import json
p=Path('mail-compose246/runtime.py');s=p.read_text()
s=s.replace('2.4.6-compose','2.4.7-quote-editor').replace("'versionCode':346","'versionCode':347").replace('after246-','after247-').replace('QA246','QA247').replace('qa246','qa247').replace('Svoyi-Android-2.4.6.apk','Svoyi-Android-2.4.7.apk')
def once(old,new):
 global s
 assert s.count(old)==1,(old,s.count(old))
 s=s.replace(old,new)
# Match only a TextView in actual scrollable message history. A quote context label
# deliberately is not long-clickable and must never be used as a test message target.
helper='''def _message_longpress247(value):
 root=ui();parents={c:p for p in root.iter() for c in p}
 wanted='Web seed QA247 — повідомлення для відповіді' if value=='Web seed QA247' else value
 for n in root.iter('node'):
  if n.get('class')!='android.widget.TextView' or n.get('package')!=PACKAGE or n.get('text','').strip()!=wanted:continue
  ancestor=parents.get(n);history=False
  while ancestor is not None:
   if ancestor.get('class')=='android.widget.ScrollView':history=True;break
   ancestor=parents.get(ancestor)
  if not history or n.get('long-clickable')!='true':continue
  b=list(map(int,re.findall(r'\\d+',n.get('bounds',''))))
  if len(b)==4 and b[2]>b[0] and b[3]>b[1]:
   x,y=(b[0]+b[2])//2,(b[1]+b[3])//2;adb('shell','input','swipe',str(x),str(y),str(x),str(y),'900');time.sleep(1);return True
 return False
ns['longpress']=_message_longpress247
'''
once('def thread():',helper+'\ndef thread():')
old=" # No uninstall or data clear; update the user's exact previous application identity."
new=''' # Seed only disposable test content; the edit action itself is driven through UI.
 own=api(a['s'],{'op':'mail-action','action':'send','route':'/?p=messages&with='+str(b['id']),'peer':b['id'],'body':'Editor baseline QA247','nonce':secrets.token_hex(16),'csrf':a['state']['csrf'],'expectedAccount':a['id'],'kind':'text'});must('seed-own-editor',own.get('ok'))
 must('baseline-own-visible',wait(lambda:has('Editor baseline QA247'),20));menu('Editor baseline QA247');must('baseline-edit-action',click('Редагувати','content-desc'));must('baseline-edit-dialog',wait(lambda:has('Редагувати повідомлення')));capture('before245-editor');must('baseline-edit-cancel',click('Скасувати'))
 # No uninstall or data clear; update the user's exact previous application identity.'''
once(old,new)
old="must('seed-after-update',wait(lambda:has('Web seed QA247')))"
new="""must('seed-after-update',wait(lambda:has('Web seed QA247')))
 if has('Прибрати вкладення','content-desc'):
  must('clear-baseline-fixture-attachment',click('Прибрати вкладення','content-desc'));must('fixture-attachment-cleared',wait(lambda:not has('Прибрати вкладення','content-desc')))
"""
once(old,new)
old="must('reply-opens-ime-without-extra-tap',wait(keyboard,8));capture('after247-reply-keyboard')"
new="must('reply-opens-ime-without-extra-tap',wait(keyboard,8));must('reply-editor-has-no-quote-tags','[quote]' not in current_input() and '[/quote]' not in current_input());must('quote-not-duplicated-in-editor','Web seed QA247' not in current_input());capture('after247-reply-keyboard')"
once(old,new)
old="must('edit-dialog-open',wait(lambda:has('Редагувати повідомлення')));enter('Edited QA247',True)"
new="""must('edit-dialog-open',wait(lambda:has('Редагувати повідомлення')));must('edit-keyboard-open',wait(keyboard,8));capture('after247-compact-editor');editor=editors()[0];bounds=list(map(int,re.findall(r'\\d+',editor.get('bounds',''))));density=int(re.findall(r'\\d+',adb('shell','wm','density').decode())[-1])/160;must('editor-compact-height',len(bounds)==4 and 50*density<=bounds[3]-bounds[1]<=200*density);enter('Edited QA247',True)"""
once(old,new)
old="must('draft-reply-ime',wait(keyboard,8));must('cancel-quote',click('Скасувати відповідь цитатою','content-desc'))"
new="""must('draft-reply-ime',wait(keyboard,8));must('draft-only-user-text',current_input()=='Keep draft QA247');time.sleep(1);adb('shell','am','force-stop',PACKAGE);adb('shell','am','start','-n',PACKAGE+'/eu.svoyi.nativeapp.MainActivity');must('quoted-session-after-relaunch',wait(lambda:has('Профіль','content-desc'),30));thread();must('quoted-draft-restored',wait(lambda:has('Скасувати відповідь цитатою','content-desc') and current_input()=='Keep draft QA247'));capture('after247-quoted-draft-restored');menu('Web seed QA247');must('replace-quote',click('Відповісти','content-desc'));must('replace-quote-ime',wait(keyboard,8));must('quote-replacement-retains-draft',current_input()=='Keep draft QA247');must('cancel-quote',click('Скасувати відповідь цитатою','content-desc'))"""
once(old,new)
p.write_text(s)
Path('runtime-output/driver-fixes247.json').write_text(json.dumps({'elementTreeAttributeAccessCorrected':True,'longPressOnlyExactMessageInHistory':True,'quotePreviewExcludedFromTestTargets':True,'originalAcceptanceChecksRemoved':False,'apiUsedInsteadOfUiAction':False},indent=2))
exec(compile(Path('mail-compose246/ci_entry.py').read_text(),'mail-compose246/ci_entry.py','exec'))
