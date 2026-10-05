#!/usr/bin/env python3
"""Bounded native patch of the exact 2.4.2 artifact. Signing stays on the user's machine.
NOT a full-source Gradle rebuild. No signing key is sent to GitHub.
"""
import hashlib,json,os,re,shutil,struct,subprocess,zipfile
from pathlib import Path
ROOT=Path('mail-build');OUT=Path('mail-candidate-output');ROOT.mkdir(exist_ok=True);OUT.mkdir(exist_ok=True)
APK=Path('compatibility-input/app.apk');BASE_SHA='32f42f59e8feef706a8b8c1aff7ac8852a6e9949e315d3cf942199e49f0b07bd'
assert hashlib.sha256(APK.read_bytes()).hexdigest()==BASE_SHA,'Wrong baseline'
sdk=Path(os.environ['ANDROID_HOME']);android=sdk/'platforms/android-35/android.jar';bt=sorted((sdk/'build-tools').glob('*'),key=lambda p:[int(x) for x in re.findall(r'\d+',p.name)])[-1]
def run(*args):subprocess.run([str(a) for a in args],check=True)
for d in ['stub','classes','dex','smali','helper','probe-classes','probe-dex','instrument-classes','instrument-dex']:(ROOT/d).mkdir(exist_ok=True)
(ROOT/'Signatures.java').write_text('''package eu.svoyi.nativeapp;
import android.app.*;import android.view.*;import android.widget.*;import org.json.*;
class MainActivity extends Activity {public void mailStabilityRetry(){} public void mailStabilityHome(){} public void mailStabilityFailure(NativeMailScreen s,Throwable t){} }
class ThemePalette {int background,surface,text,muted,accent,border,error;}
class NativeMailScreen {Activity activity;ThemePalette theme;LinearLayout root,composer,header,inboxList;EditText input,search;Button allInbox,unreadInbox;View tools;boolean canSend,closed;TextView presence;JSONObject partner;public void close(){} }
''')
run('javac','-source','8','-target','8','-cp',android,'-d',ROOT/'stub',ROOT/'Signatures.java')
sources=[Path('mail-stability')/n for n in ['MailDiagnostics.java','MailNulls.java','MailSafety.java']]
run('javac','-source','8','-target','8','-cp',str(android)+os.pathsep+str(ROOT/'stub'),'-d',ROOT/'classes',*sources)
classes=list((ROOT/'classes').rglob('*.class'));assert classes and all(p.name.startswith(('MailDiagnostics','MailNulls','MailSafety')) for p in classes)
run(bt/'d8','--min-api','26','--lib',android,'--classpath',ROOT/'stub','--output',ROOT/'dex',*classes)
z=zipfile.ZipFile(APK);(ROOT/'original.dex').write_bytes(z.read('classes3.dex'))
run('baksmali','disassemble',ROOT/'original.dex','-o',ROOT/'smali');run('baksmali','disassemble',ROOT/'dex/classes.dex','-o',ROOT/'helper')
base=ROOT/'smali/eu/svoyi/nativeapp';changes=[]
def change(file,sig,transform):
 p=base/file;s=p.read_text();items=[m for m in re.finditer(r'(?ms)^\.method[^\n]*\n.*?^\.end method',s) if m.group().splitlines()[0].endswith(sig)]
 assert len(items)==1,(file,sig,len(items));m=items[0];old=m.group();new=transform(old);assert old!=new
 p.write_text(s[:m.start()]+new+s[m.end():]);changes.append({'class':file,'method':sig,'before':hashlib.sha256(old.encode()).hexdigest(),'after':hashlib.sha256(new.encode()).hexdigest()})
def after_registers(s,code):return re.sub(r'(?m)^(    \.registers \d+)$',lambda m:m.group()+'\n'+code,s,count=1)
change('MainActivity.smali','onCreate(Landroid/os/Bundle;)V',lambda s:after_registers(s,'    invoke-static/range {p0 .. p0}, Leu/svoyi/nativeapp/MailDiagnostics;->install(Landroid/app/Activity;)V\n'))
def guard_main(old):
 unsafe=old.replace('renderChat(Lorg/json/JSONObject;)V','renderChatUnsafe243(Lorg/json/JSONObject;)V',1)
 return unsafe+'''

.method private renderChat(Lorg/json/JSONObject;)V
    .locals 5
    invoke-static {p1}, Leu/svoyi/nativeapp/MailSafety;->before(Lorg/json/JSONObject;)V
    :try_start_mail
    invoke-direct {p0, p1}, Leu/svoyi/nativeapp/MainActivity;->renderChatUnsafe243(Lorg/json/JSONObject;)V
    :try_end_mail
    return-void
    .catch Ljava/lang/Exception; {:try_start_mail .. :try_end_mail} :catch_mail
    .catch Ljava/lang/LinkageError; {:try_start_mail .. :try_end_mail} :catch_mail
    :catch_mail
    move-exception v4
    iget-object v3, p0, Leu/svoyi/nativeapp/MainActivity;->mailScreen:Leu/svoyi/nativeapp/NativeMailScreen;
    invoke-virtual {p0, v3, v4}, Leu/svoyi/nativeapp/MainActivity;->mailStabilityFailure(Leu/svoyi/nativeapp/NativeMailScreen;Ljava/lang/Throwable;)V
    return-void
.end method

.method public mailStabilityFailure(Leu/svoyi/nativeapp/NativeMailScreen;Ljava/lang/Throwable;)V
    .locals 5
    move-object v0, p0
    iget-object v1, p0, Leu/svoyi/nativeapp/MainActivity;->body:Landroid/widget/LinearLayout;
    iget-object v2, p0, Leu/svoyi/nativeapp/MainActivity;->colors:Leu/svoyi/nativeapp/ThemePalette;
    move-object v3, p1
    move-object v4, p2
    invoke-static {v0, v1, v2, v3, v4}, Leu/svoyi/nativeapp/MailSafety;->failed(Leu/svoyi/nativeapp/MainActivity;Landroid/widget/LinearLayout;Leu/svoyi/nativeapp/ThemePalette;Leu/svoyi/nativeapp/NativeMailScreen;Ljava/lang/Throwable;)V
    const/4 v0, 0x0
    iput-object v0, p0, Leu/svoyi/nativeapp/MainActivity;->mailScreen:Leu/svoyi/nativeapp/NativeMailScreen;
    return-void
.end method

.method public mailStabilityRetry()V
    .locals 3
    iget-object v0, p0, Leu/svoyi/nativeapp/MainActivity;->route:Ljava/lang/String;
    const/4 v1, 0x0
    const/4 v2, 0x0
    invoke-direct {p0, v0, v1, v2}, Leu/svoyi/nativeapp/MainActivity;->load(Ljava/lang/String;ZI)V
    return-void
.end method

.method public mailStabilityHome()V
    .locals 1
    const-string v0, "/?p=home"
    invoke-direct {p0, v0}, Leu/svoyi/nativeapp/MainActivity;->navigate(Ljava/lang/String;)V
    return-void
.end method'''
change('MainActivity.smali','renderChat(Lorg/json/JSONObject;)V',guard_main)
change('MainActivity.smali','settings()V',lambda s:s.replace('    return-void','    move-object/from16 v0, p0\n    iget-object v1, v0, Leu/svoyi/nativeapp/MainActivity;->content:Landroid/widget/LinearLayout;\n    invoke-static {v0, v1}, Leu/svoyi/nativeapp/MailSafety;->settings(Landroid/app/Activity;Landroid/widget/LinearLayout;)V\n    return-void'))
for sig,helper in [('inbox(Leu/svoyi/nativeapp/NativeMailScreen;)V','inbox'),('thread(Leu/svoyi/nativeapp/NativeMailScreen;)V','thread')]:
 def append(s,helper=helper):
  pos=s.rfind('    return-void');assert pos>=0
  return s[:pos]+'    invoke-static/range {p0 .. p0}, Leu/svoyi/nativeapp/MailSafety;->'+helper+'(Leu/svoyi/nativeapp/NativeMailScreen;)V\n\n'+s[pos:]
 change('NativeSiteUi.smali',sig,append)
for name in ['deleted','delivered']:
 change('NativeMailPolicy.smali',name+'(Lorg/json/JSONObject;)Z',lambda s,name=name:'.method static '+name+'(Lorg/json/JSONObject;)Z\n    .registers 1\n    invoke-static {p0}, Leu/svoyi/nativeapp/MailNulls;->'+name+'(Lorg/json/JSONObject;)Z\n    move-result p0\n    return p0\n.end method')
for sig,param in [('messageView(Lorg/json/JSONObject;)Landroid/view/View;','p1'),('updateMessageMeta(Landroid/view/View;Lorg/json/JSONObject;)V','p2')]:
 def edited(s,param=param):
  pattern=r'(const-string [vp]\d+, "edited"\s+)(invoke-virtual \{[^}]+\}, Lorg/json/JSONObject;->optBoolean\(Ljava/lang/String;Z\)Z)'
  new,n=re.subn(pattern,lambda m:m.group(1)+'invoke-static/range {'+param+' .. '+param+'}, Leu/svoyi/nativeapp/MailNulls;->edited(Lorg/json/JSONObject;)Z',s);assert n==1,(sig,n);return new
 change('NativeMailScreen.smali',sig,edited)
change('NativeMailScreen.smali','paintPresence()V',lambda s:'.method paintPresence()V\n    .registers 1\n    invoke-static {p0}, Leu/svoyi/nativeapp/MailSafety;->presence(Leu/svoyi/nativeapp/NativeMailScreen;)V\n    return-void\n.end method')
for p in (ROOT/'helper').rglob('*.smali'):
 dest=ROOT/'smali'/p.relative_to(ROOT/'helper');assert not dest.exists();dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
run('smali','assemble',ROOT/'smali','-o',ROOT/'classes3.dex')
def len8(b,p):
 n=b[p];p+=1
 if n&128:n=((n&127)<<8)|b[p];p+=1
 return n,p
def len16(b,p):
 n=struct.unpack_from('<H',b,p)[0];p+=2
 if n&32768:n=((n&32767)<<16)|struct.unpack_from('<H',b,p)[0];p+=2
 return n,p
def out8(n):return bytes([128|(n>>8),n&255]) if n>=128 else bytes([n])
def out16(n):return struct.pack('<HH',32768|(n>>16),n&65535) if n>=32768 else struct.pack('<H',n)
m=z.read('AndroidManifest.xml');chunks=[];pos=8;strings=[]
while pos<len(m):
 typ,head,size=struct.unpack_from('<HHI',m,pos);raw=bytearray(m[pos:pos+size]);chunks.append([typ,head,raw])
 if typ==1:
  poolindex=len(chunks)-1;count,styles,flags,start,style=struct.unpack_from('<5I',raw,8);utf8=bool(flags&256);assert styles==0
  for i in range(count):
   p=start+struct.unpack_from('<I',raw,head+4*i)[0]
   if utf8:_,p=len8(raw,p);n,p=len8(raw,p);s=bytes(raw[p:p+n]).decode('utf8')
   else:n,p=len16(raw,p);s=bytes(raw[p:p+2*n]).decode('utf-16-le')
   strings.append(s)
 pos+=size
assert pos==len(m)
strings=[s.replace('eu.svoyi.testapp02','eu.svoyi.nativeapp').replace('2.4.2-sitefix01','2.4.3-stability').replace('Свої — перевірка 2.4.2','Свої у Європі') for s in strings]
for typ,head,raw in chunks:
 if typ!=0x102:continue
 ns,name,start,step,count,*_=struct.unpack_from('<IIHHHHHH',raw,head)
 for i in range(count):
  off=head+start+i*step;ans,aname,araw,sz,zero,kind,val=struct.unpack_from('<IIIHBBI',raw,off)
  if strings[name]=='manifest' and strings[aname]=='versionCode':struct.pack_into('<I',raw,off+16,343)
blob=bytearray();offsets=[]
for s in strings:
 offsets.append(len(blob));u=s.encode('utf-16-le')
 if utf8:b=s.encode('utf8');blob+=out8(len(u)//2)+out8(len(b))+b+b'\0'
 else:blob+=out16(len(u)//2)+u+b'\0\0'
while len(blob)%4:blob.append(0)
start=28+4*len(strings);chunks[poolindex][2]=struct.pack('<HHI5I',1,28,start+len(blob),len(strings),0,flags&~1,start,0)+struct.pack('<'+'I'*len(strings),*offsets)+blob
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
run(bt/'zipalign','-f','4',ROOT/'unsigned.apk',OUT/'Svoyi-2.4.3-unsigned-aligned.apk');shutil.copy2(bt/'lib/apksigner.jar',OUT/'apksigner.jar')
# Separate ART test harness, never included in the delivered application.
run('javac','-source','8','-target','8','-cp',android,'-d',ROOT/'probe-classes','mail-stability/StatusProbe.java')
run(bt/'d8','--min-api','26','--lib',android,'--output',ROOT/'probe-dex',*list((ROOT/'probe-classes').rglob('*.class')))
with zipfile.ZipFile(OUT/'status-probe.jar','w') as t:t.write(ROOT/'probe-dex/classes.dex','classes.dex')
run('javac','-source','8','-target','8','-cp',android,'-d',ROOT/'instrument-classes','mail-stability/RecoveryProbe.java')
run(bt/'d8','--min-api','26','--lib',android,'--output',ROOT/'instrument-dex',*list((ROOT/'instrument-classes').rglob('*.class')))
(ROOT/'TestManifest.xml').write_text('<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="eu.svoyi.qa.stabilityprobe"><uses-sdk android:minSdkVersion="26" android:targetSdkVersion="35"/><application android:label="Svoyi QA instrumentation"/><instrumentation android:name="eu.svoyi.qa.RecoveryProbe" android:targetPackage="eu.svoyi.nativeapp" android:functionalTest="true"/></manifest>')
run(bt/'aapt','package','-f','-M',ROOT/'TestManifest.xml','-I',android,'-F',ROOT/'test.apk')
with zipfile.ZipFile(ROOT/'test.apk','a') as t:t.write(ROOT/'instrument-dex/classes.dex','classes.dex')
run(bt/'zipalign','-f','4',ROOT/'test.apk',OUT/'qa-instrumentation-unsigned.apk')
(OUT/'change-manifest.json').write_text(json.dumps({'baseline_sha256':BASE_SHA,'version':'2.4.3-stability','versionCode':343,'package':'eu.svoyi.nativeapp','signing':'local original key required','full_gradle_build':False,'compile_only_signatures_packaged':False,'modified_methods':changes,'preserved_entries':preserved,'server_changed':False},indent=2))
shutil.copytree('mail-stability',OUT/'source',dirs_exist_ok=True)
print('Unsigned native candidate assembled; no new signing identity was generated.')
