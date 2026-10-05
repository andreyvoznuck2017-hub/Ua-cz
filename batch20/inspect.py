#!/usr/bin/env python3
"""Current reference on disposable QA accounts only. Run with python -P to avoid name shadowing."""
import json,shutil,traceback
from pathlib import Path
source=Path('qa-runtime/diagnose.py').read_text().split('\ntry:run()')[0]
source=source.replace("email='qa.repair.'+os.environ['GITHUB_RUN_ID']+'.'+tag+'@example.com'","email='qa.batch20.'+os.environ['GITHUB_RUN_ID']+'.'+tag+'@example.com'")
ns={};exec(compile(source,'qa-runtime/diagnose.py','exec'),ns)
OUT=ns['OUT'];api=ns['api'];save=ns['save']
for directory in ['repair','repair-extra','qa-runtime','qa-fixes','mail-next244','mail-stability','mail-compose246','mail-compose247','docs','.github/workflows']:
 p=Path(directory)
 if p.exists():shutil.copytree(p,OUT/'source'/directory,dirs_exist_ok=True)
a=ns['account']('a');b=ns['account']('b');save('accounts.json',{'a':a['id'],'b':b['id'],'disposableOnly':True})
routes={'home':'/?p=home','jobs':'/?p=home&native=jobs','housing':'/?p=housing','cabinet':'/?p=profile','edit-profile':'/?p=profile&section=profile','privacy':'/?p=profile&section=privacy','rewards':'/?p=profile&section=rewards','public-profile':'/?p=user&id='+str(a['id']),'peer-profile':'/?p=user&id='+str(b['id']),'mail':'/?p=messages','nearby':'/?p=nearby','activities':'/?p=nearby&tab=activities','challenges':'/?p=challenges','groups':'/?p=groups','gifts':'/?p=profile&section=services&tab=gifts'}
results={}
for label,route in routes.items():
 try:
  value=api(a['s'],{'op':'screen','route':route});save('api-'+label+'.json',value);results[label]={'route':route,'page':value.get('page'),'ok':value.get('ok')}
 except Exception as e:
  results[label]={'route':route,'error':type(e).__name__,'detail':str(e)}
 save('routes.json',results)
ns['web_capture'](a,b)
save('reference-status.json',{'completed':True,'unsupportedRoutes':[k for k,v in results.items() if 'error' in v],'releaseAccepted':False,'serverSourceChanged':False})
