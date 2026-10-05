"""Focused visual regression, not acceptance of all twenty product tasks."""
from .qa import *

def run():
 a,b=start()
 goto_home();must('candidate-home-identity',wait(lambda:has(a['name'],contains=True),20));capture('after248-home-01')
 for i in range(3):
  if not scroll():break
  capture('after248-home-'+str(i+2).zfill(2))
 goto_profile(True);capture('after248-profile-01')
 must('public-avatar-header-present',has(a['name']))
 goto_home();thread(a,b);must('thread-seed-visible',wait(lambda:has('Batch20 hello from the website',contains=True),20))
 type_into('Batch20 visual release check',clear=True);must('candidate-send',click('Надіслати','content-desc',True));must('peer-received-on-server',wait(lambda:any(m.get('body')=='Batch20 visual release check' for m in messages(b,a)),25));capture('after248-sent-keyboard')
 hide_keyboard()
 rows=[n for n in nodes() if n.get('content-desc','').startswith('Дії повідомлення ')]
 must('message-action-row-visible',bool(rows));tap_node(rows[-1],long=True);must('reaction-menu-visible',wait(lambda:has('Копіювати','content-desc'),12));capture('after248-message-actions');must('six-quick-reactions',len([n for n in nodes() if n.get('content-desc','').startswith('Реакція ')])==6)
 click('Скасувати','content-desc');adb('shell','am','force-stop',PACKAGE);adb('shell','am','start','-n',PACKAGE+'/eu.svoyi.nativeapp.MainActivity');must('identity-after-restart',wait(lambda:has(a['name'],contains=True),30));capture('after248-restarted')
 save('scope.json',{'scope':'home profile mail visual plus independent send receipt','allTwentyTasksAccepted':False,'physicalXiaomiTested':False,'distributionSignatureTested':False})
try:run()
except Exception as e:
 check('visual-regression-completed',False,type(e).__name__+': '+str(e));save('visual-error.txt',traceback.format_exc())
 try:capture('visual-failure')
 except Exception:pass
finally:finish()
raise SystemExit(0 if core['CHECKS'] and all(c['passed'] for c in core['CHECKS']) else 1)
