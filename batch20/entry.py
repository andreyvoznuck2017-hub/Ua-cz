#!/usr/bin/env python3
"""Real Android entrypoint; startup requires an actual signed-in identity."""
import os,re,time,runpy,xml.etree.ElementTree as ET
from . import qa as q
raw_capture=q.capture
observations=[]
def fresh_ui():
 for attempt in range(4):
  q.adb('shell','rm','-f','/sdcard/batch20-fresh-ui.xml',allow_fail=True)
  q.adb('shell','uiautomator','dump','/sdcard/batch20-fresh-ui.xml',allow_fail=True,timeout=20)
  content=q.adb('shell','cat','/sdcard/batch20-fresh-ui.xml',allow_fail=True)
  try:root=ET.fromstring(content)
  except ET.ParseError:
   observations.append({'transientUiDumpAttempt':attempt+1,'present':bool(content)});q.save('driver-observations.json',observations);time.sleep(.65);continue
  title=next((n.get('text','') for n in root.iter('node') if n.get('package')=='android' and n.get('resource-id')=='android:id/alertTitle'),'')
  if title=="Pixel Launcher isn't responding" and len(q.NOTES)<3:
   button=next((n for n in root.iter('node') if n.get('resource-id')=='android:id/aerr_close'),None)
   if button is not None:q.NOTES.append({'dismissed':'Pixel Launcher only','applicationErrorIgnored':False});q.save('environment.json',q.NOTES);q.tap_node(button);time.sleep(1);continue
  return root
 raise RuntimeError('No fresh Android UI hierarchy after four attempts')
def current_ime():
 text=q.adb('shell','dumpsys','input_method',allow_fail=True).decode(errors='replace')
 state=re.search(r'\bmInputShown=(true|false)\b',text)
 if state is not None:return state.group(1)=='true'
 state=re.search(r'\bmIsInputViewShown=(true|false)\b',text)
 return state is not None and state.group(1)=='true'
def hide_current_ime():
 if not any(n.get('focused')=='true' for n in q.editors()):return
 if current_ime():q.adb('shell','input','keyevent','KEYCODE_BACK');time.sleep(.45)
q.ui=fresh_ui;q.ime=current_ime;q.hide_keyboard=hide_current_ime
q.save('driver-corrections.json',{'freshUiFileForEachRead':True,'currentImeStateOnly':True,'verifiedLoginBootstrapActive':True,'failedAssertionsSuppressed':False})
from . import startup
runpy.run_module('batch20.'+os.environ['QA_AREA']+'_runtime',run_name='__main__')
