#!/usr/bin/env python3
import json,traceback
from . import qa as q
from . import startup
try:
    a,b=startup.start()
    q.save('signed-visual.json',{'baseline':'2.4.5-imagefix','candidate':'2.4.8-batch20','api':q.os.environ.get('QA_API'),'samePackage':True,'disposableAccountsOnly':True})
    q.check('signed-before-after-captured',True)
except Exception as e:
    q.check('signed-before-after-captured',False,type(e).__name__+': '+str(e))
    q.save('signed-visual-error.txt',traceback.format_exc())
    try:q.capture('signed-visual-failure')
    except Exception:pass
finally:
    q.finish()
raise SystemExit(0 if all(x['passed'] for x in q.core['CHECKS']) else 1)
