#!/usr/bin/env python3
"""Known emulator launcher recovery, NOT a catch for application failures.
Only the exact android-owned 'Pixel Launcher isn't responding' dialog is dismissed.
The original failed attempt and its screenshot remain in GitHub artifacts.
"""
from pathlib import Path
code=Path('image-fix245/ui.py').read_text()
marker="adb,tap,ui,capture,check,save,alive=(ns[k] for k in ['adb','tap','ui','capture','check','save','alive'])"
assert code.count(marker)==1
setup='''
_raw_ui=ui
_environment_notes=[]
def isolated_ui():
 root=_raw_ui()
 title=next((n.get('text','') for n in root.iter('node') if n.get('package')=='android' and n.get('resource-id')=='android:id/alertTitle'),'')
 if title=="Pixel Launcher isn't responding" and len(_environment_notes)<3:
  close=next((n for n in root.iter('node') if n.get('package')=='android' and n.get('resource-id')=='android:id/aerr_close'),None)
  if close is not None:
   b=list(map(int,re.findall(r'\\d+',close.get('bounds',''))))
   if len(b)==4:
    _environment_notes.append({'title':title,'action':'close emulator launcher only','app_error_ignored':False})
    save('environment-notes.json',_environment_notes)
    adb('shell','input','tap',str((b[0]+b[2])//2),str((b[1]+b[3])//2));time.sleep(2)
    return _raw_ui()
 return root
ui=isolated_ui
ns['ui']=ui
'''
exec(compile(code.replace(marker,marker+'\n'+setup),'image-fix245/ui.py','exec'))
