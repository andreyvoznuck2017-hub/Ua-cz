#!/usr/bin/env python3
from pathlib import Path
p=Path('mail-stability/build_unsigned.py');s=p.read_text()
old="""for p in (ROOT/'helper').rglob('*.smali'):
 dest=ROOT/'smali'/p.relative_to(ROOT/'helper');assert not dest.exists();dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)"""
new="""helper_files=list((ROOT/'helper').rglob('*.smali'));aliases={};reuse=set()
for p in helper_files:
 dest=ROOT/'smali'/p.relative_to(ROOT/'helper')
 if dest.exists():
  print('Generated helper collision:',str(p.relative_to(ROOT/'helper')))
  if dest.read_bytes()==p.read_bytes():reuse.add(p);continue
  r8_annotation=str(p.relative_to(ROOT/'helper')).startswith('com/android/tools/r8/annotations/') and '.implements Ljava/lang/annotation/Annotation;' in p.read_text()
  assert '$$ExternalSynthetic' in p.name or r8_annotation,'Unexpected application class collision: '+str(p)
  desc=re.search(r'(?m)^\\.class[^\\n]* (L[^;]+;)',p.read_text()).group(1)
  aliases[desc]=desc[:-1]+'_Mail243;'
for p in helper_files:
 if p in reuse:continue
 text=p.read_text();desc=re.search(r'(?m)^\\.class[^\\n]* (L[^;]+;)',text).group(1)
 for a,b in aliases.items():text=text.replace(a,b)
 own=aliases.get(desc,desc);dest=ROOT/'smali'/(own[1:-1]+'.smali')
 assert not dest.exists(),'Refusing to overwrite preserved class: '+str(dest)
 dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text)
(OUT/'synthetic-helper-renames.json').write_text(json.dumps({'aliases':aliases,'identical_reused':[str(p.relative_to(ROOT/'helper')) for p in reuse]},indent=2))"""
assert old in s,'Build source changed; inspect before applying'
p.write_text(s.replace(old,new))
exec(compile(p.read_text(),str(p),'exec'),{'__name__':'__main__'})
