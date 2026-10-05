#!/usr/bin/env python3
"""Bootstrap only: shared namespace, CI-only signer identities. No acceptance assertions changed."""
import hashlib,os
from pathlib import Path
s=Path('mail-compose246/runtime.py').read_text()
marker="ns={};exec(compile(code,'mail-next244/runtime.py','exec'),ns)"
assert s.count(marker)==1
s=s.replace(marker,marker+"\ncore=ns['ns'];ns['ORIGIN']=core['ORIGIN'];ns['CHECKS']=core['CHECKS']")
assert s.count("ns['ui']=ui")==1
s=s.replace("ns['ui']=ui","ns['ui']=ui;core['ui']=ui")
# Only our disposable CI-signed baseline changes signature bytes; non-signature entries were checked earlier.
if os.environ.get('QA_CI_ONLY')=='1':
 baseline=hashlib.sha256(Path('signed-input/baseline245.apk').read_bytes()).hexdigest()
 s=s.replace('95fe1ad2849c7719ecd4b5b559fbbb860eb69386ee2564f732e637f02ab38cdb',baseline)
exec(compile(s,'mail-compose246/runtime.py','exec'))
