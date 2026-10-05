#!/usr/bin/env python3
"""Run the regression with bounded startup readiness; never dismiss an app crash."""
import os
from pathlib import Path
source=Path('qa-runtime/diagnose.py').read_text()
source=source.replace("PACKAGE='eu.svoyi.testapp01'", "PACKAGE=os.environ.get('QA_PACKAGE','eu.svoyi.testapp01')")
source=source.replace("OUT=Path('runtime-output')", "OUT=Path(os.environ.get('QA_OUTPUT','runtime-output'))")
source=source.replace("name='QA '+('Andrii' if tag=='a' else 'Viktoriia')", "name='QA '+('Andrii' if tag=='a' else 'Viktoriia')")
source=source.replace("email='qa.repair.'+os.environ['GITHUB_RUN_ID']+'.'+tag+'@example.com'", "email='qa.repair.'+os.environ['GITHUB_RUN_ID']+'.'+os.environ.get('QA_PHASE','baseline')+'.'+tag+'@example.com'")
extra='''
def prepare_login():
    notes=[]
    for attempt in range(12):
        try:
            root=ui()
            text=' '.join(n.get('text','') for n in root.iter('node'))
            if 'Pixel Launcher' in text and ('responding' in text or 'stopping' in text):
                notes.append('Unrelated Pixel Launcher dialog dismissed in disposable emulator')
                tap('text','Close app')
                adb('shell','am','start','-n',PACKAGE+'/eu.svoyi.nativeapp.MainActivity',allow_fail=True)
            elif any(n.get('class')=='android.widget.EditText' for n in root.iter('node')):
                save('emulator-environment-notes.json',notes)
                return
            elif 'keeps stopping' in text or 'is not responding' in text:
                capture('startup-application-error')
                raise RuntimeError('Application error dialog: '+text)
        except ET.ParseError:
            pass
        time.sleep(3)
    capture('startup-not-ready')
    raise RuntimeError('Native login did not become ready in 36 seconds')
'''
source=source.replace('def run():',extra+'\ndef run():')
source=source.replace("capture('android-01-login')", "prepare_login(); capture('android-01-login')")
# Class and package name differ intentionally in the existing native QA build.
# Keep all assertions from diagnose.py. Preparation does not turn failures green.
exec(compile(source,'qa-runtime/diagnose.py','exec'),{'__name__':'__main__'})
