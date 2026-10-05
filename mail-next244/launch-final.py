#!/usr/bin/env python3
"""Run all independent cases on the signed candidate without masking UI failures.
Correct only harness navigation and empty input handling. A missing automatic
keyboard remains a failed assertion, but does not prevent edit/upload tests.
"""
from pathlib import Path
code=Path('mail-next244/runtime.py').read_text()
old="def write(value,clear=False):\n must('composer-field-accessible',tap('class','android.widget.EditText',0));time.sleep(.5)"
new="def write(value,clear=False):\n if not has('Редагувати повідомлення') and not has('Повернутися до діалогів','content-desc'):\n  must('recover-thread-context-before-input',to_thread())\n must('composer-field-accessible',tap('class','android.widget.EditText',0));time.sleep(.5)"
assert code.count(old)==1;code=code.replace(old,new)
old=" adb('shell','input','text',value.replace(' ','%s'));time.sleep(.5)"
new=" if value:adb('shell','input','text',value.replace(' ','%s'))\n time.sleep(.5)"
assert code.count(old)==1;code=code.replace(old,new)
old="must('reply-opens-keyboard',wait(keyboard))"
new="check('reply-opens-keyboard',wait(keyboard,8))"
assert code.count(old)==1;code=code.replace(old,new)
marker="PACKAGE=ns['PACKAGE'];OUT=ns['OUT'];APK=Path('signed-input/app.apk')"
assert code.count(marker)==1
setup='''
_raw_ui=ui
_environment_notes=[]
def _guarded_ui():
 root=_raw_ui()
 title=next((n.get('text','') for n in root.iter('node') if n.get('package')=='android' and n.get('resource-id')=='android:id/alertTitle'),'')
 if title=="Pixel Launcher isn't responding" and len(_environment_notes)<3:
  close=next((n for n in root.iter('node') if n.get('package')=='android' and n.get('resource-id')=='android:id/aerr_close'),None)
  if close is not None:
   bounds=list(map(int,re.findall(r'\\d+',close.get('bounds',''))))
   if len(bounds)==4:
    _environment_notes.append({'dialog':title,'action':'Close only Pixel Launcher','application_error_ignored':False})
    save('environment-notes.json',_environment_notes)
    adb('shell','input','tap',str((bounds[0]+bounds[2])//2),str((bounds[1]+bounds[3])//2));time.sleep(2)
    return _raw_ui()
 return root
ui=_guarded_ui
ns['ui']=ui
'''
exec(compile(code.replace(marker,marker+'\n'+setup),'mail-next244/runtime.py','exec'))
