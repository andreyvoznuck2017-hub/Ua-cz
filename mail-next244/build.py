#!/usr/bin/env python3
"""Compile the new native action sheet; retain every unrelated 2.4.3 method and asset.
Signing is performed separately on the authorized computer with the existing key.
"""
import hashlib,json,os,re,shutil,struct,subprocess,zipfile
from pathlib import Path
ROOT=Path('build244');OUT=Path('candidate244');ROOT.mkdir(exist_ok=True);OUT.mkdir(exist_ok=True)
APK=Path('input243.apk');assert hashlib.sha256(APK.read_bytes()).hexdigest()=='36071a614fece010136aba12917dfdfab95bbbe1ecd712a1d6b7a9c41cb95990'
sdk=Path(os.environ['ANDROID_HOME']);android=sdk/'platforms/android-35/android.jar';bt=sorted((sdk/'build-tools').glob('*'),key=lambda p:[int(x) for x in re.findall(r'\d+',p.name)])[-1]
def run(*args):subprocess.run([str(a) for a in args],check=True)
for d in ['stub','classes','dex','smali','helper']:(ROOT/d).mkdir(exist_ok=True)
(ROOT/'Signatures.java').write_text('''package eu.svoyi.nativeapp;
import android.app.*;import android.widget.*;import org.json.*;import java.util.*;
class ThemePalette {int border,surface,text,muted,accent,error,field;}
class NativeMailPolicy {TreeMap<Integer,JSONObject> messages;static boolean deleted(JSONObject o){return false;}static int sender(JSONObject o){return 0;}}
class NativeMailScreen {Activity activity;ThemePalette theme;NativeMailPolicy model;JSONArray reactionChoices;EditText input;int account;boolean canSend,actionBusy;boolean alive(){return false;}boolean canReact(JSONObject o){return false;}static boolean supportedReaction(String e){return false;}boolean mayEdit(JSONObject o){return false;}void react(JSONObject o,String e){}void replyTo(JSONObject o){}void selectMessageText(JSONObject o){}void edit(JSONObject o){}void delete(JSONObject o,boolean s){}void status(String s,boolean e){}void show(AlertDialog a){}AlertDialog.Builder dialogBuilder(){return null;}}
class RichMessage {static class Result{String text;}static Result parse(String s){return null;}}
class MailDiagnostics {static void record(Throwable t,boolean fatal){}}
''')
run('javac','-source','8','-target','8','-cp',android,'-d',ROOT/'stub',ROOT/'Signatures.java')
run('javac','-source','8','-target','8','-cp',str(android)+os.pathsep+str(ROOT/'stub'),'-d',ROOT/'classes','mail-next244/MailActions244.java')
classes=list((ROOT/'classes').rglob('*.class'));assert classes and all(p.name.startswith('MailActions244') for p in classes)
run(bt/'d8','--min-api','26','--lib',android,'--classpath',ROOT/'stub','--output',ROOT/'dex',*classes)
z=zipfile.ZipFile(APK);(ROOT/'original.dex').write_bytes(z.read('classes3.dex'))
run('baksmali','disassemble',ROOT/'original.dex','-o',ROOT/'smali');run('baksmali','disassemble',ROOT/'dex/classes.dex','-o',ROOT/'helper')
p=ROOT/'smali/eu/svoyi/nativeapp/NativeMailScreen.smali';s=p.read_text();sig='messageTools(Lorg/json/JSONObject;)V'
items=[m for m in re.finditer(r'(?ms)^\.method[^\n]*\n.*?^\.end method',s) if m.group().splitlines()[0].endswith(sig)];assert len(items)==1
m=items[0];old=m.group();new='.method '+sig+'\n    .registers 2\n    invoke-static {p0, p1}, Leu/svoyi/nativeapp/MailActions244;->open(Leu/svoyi/nativeapp/NativeMailScreen;Lorg/json/JSONObject;)V\n    return-void\n.end method';p.write_text(s[:m.start()]+new+s[m.end():])
aliases={};reuse=set();helper=list((ROOT/'helper').rglob('*.smali'))
for p in helper:
 dest=ROOT/'smali'/p.relative_to(ROOT/'helper')
 if dest.exists():
  if dest.read_bytes()==p.read_bytes():reuse.add(p);continue
  assert '$$ExternalSynthetic' in p.name or 'com/android/tools/r8/annotations' in str(p),'Unexpected application collision'
  desc=re.search(r'(?m)^\.class[^\n]* (L[^;]+;)',p.read_text()).group(1);aliases[desc]=desc[:-1]+'_Actions244;'
for p in helper:
 if p in reuse:continue
 text=p.read_text();desc=re.search(r'(?m)^\.class[^\n]* (L[^;]+;)',text).group(1)
 for a,b in aliases.items():text=text.replace(a,b)
 dest=ROOT/'smali'/(aliases.get(desc,desc)[1:-1]+'.smali');assert not dest.exists();dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text)
run('smali','assemble',ROOT/'smali','-o',ROOT/'classes3.dex')
# Preserve binary XML resource indexes, all attributes, and the application/package identity.
def read8(b,p):
 n=b[p];p+=1
 if n&128:n=((n&127)<<8)|b[p];p+=1
 return n,p
def read16(b,p):
 n=struct.unpack_from('<H',b,p)[0];p+=2
 if n&32768:n=((n&32767)<<16)|struct.unpack_from('<H',b,p)[0];p+=2
 return n,p
def out8(n):return bytes([128|(n>>8),n&255]) if n>=128 else bytes([n])
def out16(n):return struct.pack('<HH',32768|(n>>16),n&65535) if n>=32768 else struct.pack('<H',n)
m=z.read('AndroidManifest.xml');chunks=[];pos=8;strings=[]
while pos<len(m):
 typ,head,size=struct.unpack_from('<HHI',m,pos);raw=bytearray(m[pos:pos+size]);chunks.append([typ,head,raw])
 if typ==1:
  pi=len(chunks)-1;count,styles,flags,start,style=struct.unpack_from('<5I',raw,8);assert styles==0;utf8=bool(flags&256)
  for i in range(count):
   q=start+struct.unpack_from('<I',raw,head+4*i)[0]
   if utf8:_,q=read8(raw,q);n,q=read8(raw,q);v=bytes(raw[q:q+n]).decode('utf8')
   else:n,q=read16(raw,q);v=bytes(raw[q:q+2*n]).decode('utf-16-le')
   strings.append(v)
 pos+=size
assert pos==len(m) and strings.count('2.4.3-stability')==1
strings=[v.replace('2.4.3-stability','2.4.4-mail-actions') for v in strings]
for typ,head,raw in chunks:
 if typ!=0x102:continue
 ns,name,start,step,count,*_=struct.unpack_from('<IIHHHHHH',raw,head)
 for i in range(count):
  off=head+start+i*step;ans,aname,araw,sz,zero,kind,val=struct.unpack_from('<IIIHBBI',raw,off)
  if strings[name]=='manifest' and strings[aname]=='versionCode':assert val==343;struct.pack_into('<I',raw,off+16,344)
blob=bytearray();offsets=[]
for v in strings:
 offsets.append(len(blob));u=v.encode('utf-16-le')
 if utf8:b=v.encode('utf8');blob+=out8(len(u)//2)+out8(len(b))+b+b'\0'
 else:blob+=out16(len(u)//2)+u+b'\0\0'
while len(blob)%4:blob.append(0)
start=28+4*len(strings);chunks[pi][2]=struct.pack('<HHI5I',1,28,start+len(blob),len(strings),0,flags&~1,start,0)+struct.pack('<'+'I'*len(strings),*offsets)+blob
payload=b''.join(bytes(c[2]) for c in chunks);manifest=struct.pack('<HHI',3,8,8+len(payload))+payload
preserved=[]
with zipfile.ZipFile(ROOT/'unsigned.apk','w') as out:
 for i in z.infolist():
  if i.filename.startswith('META-INF/'):continue
  data=z.read(i.filename)
  if i.filename=='classes3.dex':data=(ROOT/'classes3.dex').read_bytes()
  elif i.filename=='AndroidManifest.xml':data=manifest
  else:preserved.append({'path':i.filename,'sha256':hashlib.sha256(data).hexdigest()})
  out.writestr(i,data)
run(bt/'zipalign','-f','4',ROOT/'unsigned.apk',OUT/'Svoyi-2.4.4-unsigned.apk');shutil.copy2(bt/'lib/apksigner.jar',OUT/'apksigner.jar')
(OUT/'manifest.json').write_text(json.dumps({'version':'2.4.4-mail-actions','versionCode':344,'package':'eu.svoyi.nativeapp','baseline_sha256':hashlib.sha256(APK.read_bytes()).hexdigest(),'unsigned_sha256':hashlib.sha256((OUT/'Svoyi-2.4.4-unsigned.apk').read_bytes()).hexdigest(),'changed_existing_methods':[sig],'new_helper':'MailActions244','preserved_entries':preserved,'full_gradle_build':False,'server_changes':False,'private_keys_included':False,'compile_stubs_packaged':False},indent=2))
shutil.copytree('mail-next244',OUT/'source',dirs_exist_ok=True)
