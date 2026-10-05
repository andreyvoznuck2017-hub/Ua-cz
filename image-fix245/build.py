#!/usr/bin/env python3
"""2.4.5 image-cancellation hotfix. No redesign, no server mutations, no signing keys.
Only the worker may close its InputStream/HttpURLConnection; cancellation is a signal.
The worker already owns all streams with try/finally and has 7s connect/10s read timeouts.
This is a bounded DEX rebuild, not a full-source Gradle build.
"""
import hashlib,json,os,re,shutil,struct,subprocess,zipfile
from pathlib import Path
ROOT=Path('build245');OUT=Path('candidate245');ROOT.mkdir(exist_ok=True);OUT.mkdir(exist_ok=True)
APK=Path('input244.apk');BASE='7c6441b64f81ad461eb763016bfab2d3b0cf0726b8db8705da96d1ad97907e10'
assert hashlib.sha256(APK.read_bytes()).hexdigest()==BASE,'Unexpected baseline; refusing to overwrite newer code'
sdk=Path(os.environ['ANDROID_HOME']);android=sdk/'platforms/android-35/android.jar';bt=sorted((sdk/'build-tools').glob('*'),key=lambda p:[int(x) for x in re.findall(r'\d+',p.name)])[-1]
def run(*args):subprocess.run([str(a) for a in args],check=True)
z=zipfile.ZipFile(APK);(ROOT/'original.dex').write_bytes(z.read('classes3.dex'))
run('baksmali','disassemble',ROOT/'original.dex','-o',ROOT/'smali')
base=ROOT/'smali/eu/svoyi/nativeapp';before={p.relative_to(ROOT/'smali').as_posix():p.read_bytes() for p in (ROOT/'smali').rglob('*.smali')};changes=[]
def change(file,sig,transform):
 p=base/file;s=p.read_text();ms=[m for m in re.finditer(r'(?ms)^\.method[^\n]*\n.*?^\.end method',s) if m.group().splitlines()[0].endswith(sig)]
 assert len(ms)==1,(file,sig,len(ms));m=ms[0];old=m.group();new=transform(old);assert old!=new
 p.write_text(s[:m.start()]+new+s[m.end():]);changes.append({'class':file,'method':sig,'before_sha256':hashlib.sha256(old.encode()).hexdigest(),'after_sha256':hashlib.sha256(new.encode()).hexdigest()})
# The cancellation runnable previously disconnected AND closed while the worker was reading.
# Keep disposal of an unpublished Drawable, but never touch either network resource here.
change('NativeImageLoad.smali','lambda$cancel$2(Ljava/net/HttpURLConnection;Ljava/io/InputStream;Landroid/graphics/drawable/Drawable;)V',lambda s:''' .method static synthetic lambda$cancel$2(Ljava/net/HttpURLConnection;Ljava/io/InputStream;Landroid/graphics/drawable/Drawable;)V
    .locals 2
    :dispose_start
    invoke-static {p2}, Leu/svoyi/nativeapp/NativeImageLoad;->dispose(Landroid/graphics/drawable/Drawable;)V
    :dispose_end
    return-void
    .catch Ljava/lang/RuntimeException; {:dispose_start .. :dispose_end} :dispose_failed
    :dispose_failed
    move-exception v0
    const/4 v1, 0x0
    invoke-static {v0, v1}, Leu/svoyi/nativeapp/MailDiagnostics;->record(Ljava/lang/Throwable;Z)V
    return-void
.end method'''.lstrip())
# Registration races are also worker-owned: the caller has already entered its finally scope.
for method,descriptor,field in [('stream','Ljava/io/InputStream;','stream'),('connection','Ljava/net/HttpURLConnection;','connection')]:
 def registration(s,method=method,descriptor=descriptor,field=field):
  return '.method declared-synchronized '+method+'('+descriptor+')V\n    .locals 2\n    monitor-enter p0\n    :start\n    invoke-virtual {p0}, Leu/svoyi/nativeapp/NativeImageLoad;->valid()Z\n    move-result v0\n    if-eqz v0, :cancelled\n    iput-object p1, p0, Leu/svoyi/nativeapp/NativeImageLoad;->'+field+':'+descriptor+'\n    monitor-exit p0\n    return-void\n    :cancelled\n    new-instance v0, Ljava/io/InterruptedIOException;\n    const-string v1, "Photo request cancelled"\n    invoke-direct {v0, v1}, Ljava/io/InterruptedIOException;-><init>(Ljava/lang/String;)V\n    throw v0\n    :end\n    .catchall {:start .. :end} :release\n    :release\n    move-exception v0\n    monitor-exit p0\n    throw v0\n.end method'
 change('NativeImageLoad.smali',method+'('+descriptor+')V',registration)
# Defensive close for a residual helper. No cancellation/registration path invokes it now.
def guarded_close(s):
 line='    .catch Ljava/io/IOException;'
 assert s.count(line)==1
 return re.sub(r'(    \.catch Ljava/io/IOException; (\{[^\n]+))',lambda m:m.group(1)+'\n    .catch Ljava/lang/RuntimeException; '+m.group(2),s,count=1)
change('NativeImageLoad.smali','close(Ljava/io/InputStream;)V',guarded_close)
# Disconnect is still performed by the owner worker, including exceptional exits.
# Cleanup failure must not skip clearConnection or propagate from an otherwise finished Future.
p=base/'NativeImageLoad.smali';p.write_text(p.read_text()+'''

.method static disconnectOwned(Ljava/net/HttpURLConnection;)V
    .locals 2
    if-eqz p0, :done
    :disconnect_start
    invoke-virtual {p0}, Ljava/net/HttpURLConnection;->disconnect()V
    :disconnect_end
    return-void
    .catch Ljava/lang/RuntimeException; {:disconnect_start .. :disconnect_end} :disconnect_failed
    :disconnect_failed
    move-exception v0
    const/4 v1, 0x0
    invoke-static {v0, v1}, Leu/svoyi/nativeapp/MailDiagnostics;->record(Ljava/lang/Throwable;Z)V
    :done
    return-void
.end method
''')
def owner_cleanup(s):
 pattern=r'invoke-virtual \{(v\d+)\}, Ljava/net/HttpURLConnection;->disconnect\(\)V'
 new,n=re.subn(pattern,r'invoke-static {\1}, Leu/svoyi/nativeapp/NativeImageLoad;->disconnectOwned(Ljava/net/HttpURLConnection;)V',s)
 assert n==5,('Unexpected owner cleanup sites',n)
 assert s.count('Ljava/io/InputStream;->close()V')==4,'Reader stream-finally ownership changed'
 assert '->setReadTimeout(I)V' in s and '->setConnectTimeout(I)V' in s
 return new
change('NativeImage.smali','lambda$load$6(Leu/svoyi/nativeapp/NativeImageLoad;Ljava/lang/String;IZIJLjava/lang/String;)V',owner_cleanup)
# Every other class, including the 2.4.4 reaction panel and mail transport, stays byte-identical as smali.
allowed={'eu/svoyi/nativeapp/NativeImageLoad.smali','eu/svoyi/nativeapp/NativeImage.smali'}
unchanged=0
for name,data in before.items():
 if name not in allowed:assert (ROOT/'smali'/name).read_bytes()==data,name;unchanged+=1
run('smali','assemble',ROOT/'smali','-o',ROOT/'classes3.dex')
# Preserve binary manifest attributes/indexes; only versionName/versionCode change.
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
assert pos==len(m) and strings.count('2.4.4-mail-actions')==1
strings=[v.replace('2.4.4-mail-actions','2.4.5-imagefix') for v in strings]
for typ,head,raw in chunks:
 if typ!=0x102:continue
 ns,name,start,step,count,*_=struct.unpack_from('<IIHHHHHH',raw,head)
 for i in range(count):
  off=head+start+i*step;ans,aname,araw,sz,zero,kind,val=struct.unpack_from('<IIIHBBI',raw,off)
  if strings[name]=='manifest' and strings[aname]=='versionCode':assert val==344;struct.pack_into('<I',raw,off+16,345)
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
run(bt/'zipalign','-f','4',ROOT/'unsigned.apk',OUT/'Svoyi-2.4.5-unsigned.apk');shutil.copy2(bt/'lib/apksigner.jar',OUT/'apksigner.jar')
for sub in ['probe-classes','probe-dex']:(ROOT/sub).mkdir(exist_ok=True)
run('javac','-source','8','-target','8','-cp',android,'-d',ROOT/'probe-classes','image-fix245/CancellationProbe.java')
run(bt/'d8','--min-api','26','--lib',android,'--output',ROOT/'probe-dex',*list((ROOT/'probe-classes').rglob('*.class')))
with zipfile.ZipFile(OUT/'cancellation-probe.jar','w') as t:t.write(ROOT/'probe-dex/classes.dex','classes.dex')
(OUT/'manifest.json').write_text(json.dumps({'version':'2.4.5-imagefix','versionCode':345,'package':'eu.svoyi.nativeapp','baseline_sha256':BASE,'unsigned_sha256':hashlib.sha256((OUT/'Svoyi-2.4.5-unsigned.apk').read_bytes()).hexdigest(),'changes':changes,'unchanged_smali_classes':unchanged,'preserved_entries':preserved,'full_gradle_build':False,'server_changes':False,'private_keys_included':False,'reader_owned_cleanup':True,'existing_timeouts_unchanged':True},indent=2))
shutil.copytree('image-fix245',OUT/'source',dirs_exist_ok=True)
for name in allowed:
 dest=OUT/'smali'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/'smali'/name,dest)
print('Created bounded image ownership fix; unaffected class count:',unchanged)
