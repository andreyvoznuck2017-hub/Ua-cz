#!/usr/bin/env python3
"""Dismiss only the observed Android system ANR dialog for Pixel Launcher.
Application error dialogs and all acceptance assertions remain unchanged.
"""
from pathlib import Path
code=Path('mail-next244/runtime.py').read_text()
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
