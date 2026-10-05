#!/usr/bin/env python3
"""Keep the observed baseline recovery screen as evidence and use its public login button.
This does not change app data, bypass authentication, or replace a failed login.
"""
from pathlib import Path
wrapper=Path('mail-next244/launch-final.py').read_text()
marker="marker=\"PACKAGE=ns['PACKAGE'];OUT=ns['OUT'];APK=Path('signed-input/app.apk')\""
assert wrapper.count(marker)==1
adjustment='''
old="adb('shell','am','start','-n',PACKAGE+'/eu.svoyi.nativeapp.MainActivity');must('login-fields',wait(lambda:sum(n.get('class')=='android.widget.EditText' for n in nodes())>=2))"
new="""adb('shell','am','start','-n',PACKAGE+'/eu.svoyi.nativeapp.MainActivity')
 ready=wait(lambda:sum(n.get('class')=='android.widget.EditText' for n in nodes())>=2,12)
 if not ready:
  capture('00-baseline-entry-screen')
  if click('Увійти'):
   save('baseline-entry-note.json',{'used_visible_login_button':True,'baseline':'2.4.3','credentials_entered_normally':True})
   ready=wait(lambda:sum(n.get('class')=='android.widget.EditText' for n in nodes())>=2,25)
 must('login-fields',ready)"""
assert code.count(old)==1;code=code.replace(old,new)
'''
exec(compile(wrapper.replace(marker,adjustment+'\n'+marker),'mail-next244/launch-final.py','exec'))
