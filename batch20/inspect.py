#!/usr/bin/env python3
"""Baseline inventory on disposable QA accounts. Never reads the owner's private account."""
import json,os,re,shutil,traceback
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
source=Path('qa-runtime/diagnose.py').read_text().split('\ntry:run()')[0]
source=source.replace("email='qa.repair.'+os.environ['GITHUB_RUN_ID']+'.'+tag+'@example.com'","email='qa.batch20.'+os.environ['GITHUB_RUN_ID']+'.'+tag+'@example.com'")
ns={};exec(compile(source,'qa-runtime/diagnose.py','exec'),ns)
OUT=ns['OUT'];api=ns['api'];save=ns['save']
try:
 a=ns['account']('a');b=ns['account']('b');save('accounts.json',{'a':a['id'],'b':b['id'],'disposableOnly':True})
 routes={'home':'/?p=home','cabinet':'/?p=profile','public-profile':'/?p=user&id='+str(a['id']),'peer-profile':'/?p=user&id='+str(b['id']),'mail':'/?p=messages','nearby':'/?p=nearby','friends':'/?p=friends','groups':'/?p=groups','gifts':'/?p=gifts','achievements':'/?p=achievements','activities':'/?p=activities'}
 results={}
 for label,route in routes.items():
  value=api(a['s'],{'op':'screen','route':route});save('api-'+label+'.json',value);results[label]={'route':route,'page':value.get('page'),'ok':value.get('ok')}
 save('routes.json',results)
 ns['web_capture'](a,b)
 # Public source snapshot for exact-byte comparison and local editing only.
 for directory in ['repair','repair-extra','qa-runtime','qa-fixes','mail-next244','mail-stability','mail-compose246','mail-compose247','docs','.github/workflows']:
  p=Path(directory)
  if p.exists():shutil.copytree(p,OUT/'source'/directory,dirs_exist_ok=True)
except Exception as e:
 save('inventory-error.txt',traceback.format_exc());raise
