#!/usr/bin/env python3
"""Scoped native patch on 2.4.5. Not a full Gradle source rebuild. Signing stays local."""
import difflib,hashlib,json,os,re,shutil,struct,subprocess,zipfile
from pathlib import Path
ROOT=Path('build246');OUT=Path('candidate246');ROOT.mkdir(exist_ok=True);OUT.mkdir(exist_ok=True)
APK=Path('input245.apk');BASE='95fe1ad2849c7719ecd4b5b559fbbb860eb69386ee2564f732e637f02ab38cdb'
assert hashlib.sha256(APK.read_bytes()).hexdigest()==BASE,'Wrong baseline APK'
sdk=Path(os.environ['ANDROID_HOME']);android=sdk/'platforms/android-35/android.jar';bt=sorted((sdk/'build-tools').glob('*'),key=lambda p:[int(x) for x in re.findall(r'\d+',p.name)])[-1]
def run(*args):subprocess.run([str(a) for a in args],check=True)
for d in ['stub','classes','dex','smali','helper']:(ROOT/d).mkdir(exist_ok=True)
(ROOT/'Signatures.java').write_text('''package eu.svoyi.nativeapp;
import android.app.*;import android.widget.*;import android.net.*;import android.content.*;
class NativeMailScreen {Activity activity;EditText input;String replyPrefix;boolean paused,canSend,sending,staging;boolean alive(){return false;}void stage(Uri u,String k,long d){}void status(String s,boolean e){}}
class NativeMailCapture {static void delete(Context c,Uri u){}}
''')
run('javac','-source','8','-target','8','-cp',android,'-d',ROOT/'stub',ROOT/'Signatures.java')
run('javac','-source','8','-target','8','-cp',str(android)+os.pathsep+str(ROOT/'stub'),'-d',ROOT/'classes','mail-compose246/MailCompose246.java')
classes=list((ROOT/'classes').rglob('*.class'));assert classes and all(p.name.startswith('MailCompose246') for p in classes),'Compile stubs leaked'
run(bt/'d8','--min-api','26','--lib',android,'--classpath',ROOT/'stub','--output',ROOT/'dex',*classes)
z=zipfile.ZipFile(APK);(ROOT/'original.dex').write_bytes(z.read('classes3.dex'))
run('baksmali','disassemble',ROOT/'original.dex','-o',ROOT/'smali');run('baksmali','disassemble',ROOT/'dex/classes.dex','-o',ROOT/'helper')
before={str(p.relative_to(ROOT/'smali')):p.read_bytes() for p in (ROOT/'smali').rglob('*.smali')}
p=ROOT/'smali/eu/svoyi/nativeapp/NativeMailScreen.smali';text=p.read_text();original=text;methods=[]
def wrap(signature,body):
 global text
 matches=[m for m in re.finditer(r'(?ms)^\.method[^\n]*\n.*?^\.end method',text) if m.group().splitlines()[0].endswith(signature)]
 assert len(matches)==1,(signature,len(matches));m=matches[0];old=m.group();name=signature.split('(')[0];renamed=old.replace(signature,name+'Owner246'+signature[len(name):],1)
 header=old.splitlines()[0]
 replacement=renamed+'\n\n'+header+'\n'+body.strip('\n')+'\n.end method'
 text=text[:m.start()]+replacement+text[m.end():];methods.append(signature)
wrap('stage(Landroid/net/Uri;Ljava/lang/String;J)V','''    .locals 1
    invoke-static/range {p0 .. p4}, Leu/svoyi/nativeapp/MailCompose246;->defer(Leu/svoyi/nativeapp/NativeMailScreen;Landroid/net/Uri;Ljava/lang/String;J)Z
    move-result v0
    if-eqz v0, :perform
    return-void
    :perform
    invoke-virtual/range {p0 .. p4}, Leu/svoyi/nativeapp/NativeMailScreen;->stageOwner246(Landroid/net/Uri;Ljava/lang/String;J)V
    return-void''')
wrap('resume()V','''    .locals 0
    invoke-virtual {p0}, Leu/svoyi/nativeapp/NativeMailScreen;->resumeOwner246()V
    invoke-static {p0}, Leu/svoyi/nativeapp/MailCompose246;->resumed(Leu/svoyi/nativeapp/NativeMailScreen;)V
    return-void''')
wrap('close()V','''    .locals 0
    invoke-static {p0}, Leu/svoyi/nativeapp/MailCompose246;->closing(Leu/svoyi/nativeapp/NativeMailScreen;)V
    invoke-virtual {p0}, Leu/svoyi/nativeapp/NativeMailScreen;->closeOwner246()V
    return-void''')
wrap('replyToText(Lorg/json/JSONObject;Ljava/lang/String;)V','''    .locals 0
    invoke-virtual {p0,p1,p2}, Leu/svoyi/nativeapp/NativeMailScreen;->replyToTextOwner246(Lorg/json/JSONObject;Ljava/lang/String;)V
    invoke-static {p0}, Leu/svoyi/nativeapp/MailCompose246;->replyFocused(Leu/svoyi/nativeapp/NativeMailScreen;)V
    return-void''')
p.write_text(text)
(OUT/'changed-methods.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),text.splitlines(True),fromfile='2.4.5/NativeMailScreen.smali',tofile='2.4.6/NativeMailScreen.smali')))
aliases={};reused=set();helpers=list((ROOT/'helper').rglob('*.smali'))
for f in helpers:
 dest=ROOT/'smali'/f.relative_to(ROOT/'helper')
 if dest.exists():
  if dest.read_bytes()==f.read_bytes():reused.add(f);continue
  assert '$$ExternalSynthetic' in f.name or 'com/android/tools/r8/annotations' in str(f),'Unexpected helper collision'
  desc=re.search(r'(?m)^\.class[^\n]* (L[^;]+;)',f.read_text()).group(1);aliases[desc]=desc[:-1]+'_Compose246;'
for f in helpers:
 if f in reused:continue
 s=f.read_text();desc=re.search(r'(?m)^\.class[^\n]* (L[^;]+;)',s).group(1)
 for a,b in aliases.items():s=s.replace(a,b)
 dest=ROOT/'smali'/(aliases.get(desc,desc)[1:-1]+'.smali');assert not dest.exists();dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(s)
changed=[name for name,data in before.items() if (ROOT/'smali'/name).read_bytes()!=data]
assert changed==['eu/svoyi/nativeapp/NativeMailScreen.smali'],changed
for name in ['NativeImage.smali','NativeImageLoad.smali','MailActions244.smali','MainActivity.smali']:
 path='eu/svoyi/nativeapp/'+name;assert before[path]==(ROOT/'smali'/path).read_bytes(),name
run('smali','assemble',ROOT/'smali','-o',ROOT/'classes3.dex')
# Reuse only the manifest serializer from the reviewed prior build, not its build/sign steps.
code=Path('mail-next244/build.py').read_text();start=code.index('def read8(');end=code.index('preserved=[]',start)
fragment=code[start:end].replace('2.4.3-stability','2.4.5-imagefix').replace('2.4.4-mail-actions','2.4.6-compose').replace('val==343','val==345').replace("off+16,344","off+16,346")
exec(compile(fragment,'manifest-version-only','exec'))
preserved=[]
with zipfile.ZipFile(ROOT/'unsigned.apk','w') as out:
 for i in z.infolist():
  if i.filename.startswith('META-INF/'):continue
  data=z.read(i.filename)
  if i.filename=='classes3.dex':data=(ROOT/'classes3.dex').read_bytes()
  elif i.filename=='AndroidManifest.xml':data=manifest
  else:preserved.append({'path':i.filename,'sha256':hashlib.sha256(data).hexdigest()})
  out.writestr(i,data)
run(bt/'zipalign','-f','4',ROOT/'unsigned.apk',OUT/'Svoyi-2.4.6-unsigned.apk');shutil.copy2(bt/'lib/apksigner.jar',OUT/'apksigner.jar')
(OUT/'manifest.json').write_text(json.dumps({'version':'2.4.6-compose','versionCode':346,'package':'eu.svoyi.nativeapp','baseline_sha256':BASE,'unsigned_sha256':hashlib.sha256((OUT/'Svoyi-2.4.6-unsigned.apk').read_bytes()).hexdigest(),'changed_methods':methods,'unchanged_original_smali_classes':len(before)-1,'imagefix245_preserved':True,'actions244_preserved':True,'preserved_entries':preserved,'full_gradle_build':False,'server_changes':False,'private_keys_included':False,'compile_stubs_packaged':False},indent=2))
shutil.copytree('mail-compose246',OUT/'source',dirs_exist_ok=True)
# Real smali signatures retained for evidence; no private data are in this artifact.
shutil.copy2(p,OUT/'NativeMailScreen.smali')
print('Built scoped 2.4.6 candidate on preserved 2.4.5 imagefix')
