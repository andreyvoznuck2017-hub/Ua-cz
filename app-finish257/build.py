#!/usr/bin/env python3
import os,re,shutil,subprocess,zipfile,hashlib,struct,json,zlib
from pathlib import Path

BASE=Path("release256/Svoyi-2.5.6.apk")
SRC=Path("app-finish257/HomeScreen257.java")
MAIL=Path("app-finish257/MailScreen257.java")
OUT=Path("app-finish257/releases");W=Path("app-finish257/.build")
OUT.mkdir(parents=True,exist_ok=True)
if W.exists():shutil.rmtree(W)
W.mkdir(parents=True)
assert BASE.is_file() and SRC.is_file()
BASE_SHA="9c63054162928225ec133d8062c7ddec600b7cd92a7df7cfb363e2025ae59bbe"
assert hashlib.sha256(BASE.read_bytes()).hexdigest()==BASE_SHA

sdk=Path(os.environ["ANDROID_HOME"]);plats=[]
for p in (sdk/"platforms").glob("android-*"):
    m=re.fullmatch(r"android-(\d+)",p.name)
    if m:plats.append((int(m.group(1)),p))
plats.sort();assert plats
android=plats[-1][1]/"android.jar"
bt=sorted((sdk/"build-tools").glob("*"),key=lambda p:[int(x) for x in re.findall(r"\d+",p.name)])[-1]
def run(*a):subprocess.run([str(x) for x in a],check=True)
def zread(z,name):
    info=z.getinfo(name)
    with z.open(info) as f:
        return f.read()
def readlen8(d,p):
    n=d[p];p+=1
    if n&128:n=((n&127)<<8)|d[p];p+=1
    return n,p
def readlen16(d,p):
    n=struct.unpack_from("<H",d,p)[0];p+=2
    if n&32768:n=((n&32767)<<16)|struct.unpack_from("<H",d,p)[0];p+=2
    return n,p
def put8(n):return bytes([128|(n>>8),n&255]) if n>=128 else bytes([n])
def put16(n):return struct.pack("<HH",32768|(n>>16),n&65535) if n>=32768 else struct.pack("<H",n)

def rewrite_manifest(data):
    chunks=[];pos=8;strings=[];pool=None;utf8=False;flags=0
    while pos<len(data):
        typ,head,size=struct.unpack_from("<HHI",data,pos);raw=bytearray(data[pos:pos+size]);chunks.append([typ,head,raw])
        if typ==1:
            pool=len(chunks)-1;count,styles,flags,start,style_start=struct.unpack_from("<5I",raw,8);utf8=bool(flags&256);assert styles==0
            for i in range(count):
                q=start+struct.unpack_from("<I",raw,head+i*4)[0]
                if utf8:_,q=readlen8(raw,q);n,q=readlen8(raw,q);s=bytes(raw[q:q+n]).decode("utf8")
                else:n,q=readlen16(raw,q);s=bytes(raw[q:q+2*n]).decode("utf-16-le")
                strings.append(s)
        pos+=size
    assert pool is not None and pos==len(data)
    for typ,head,raw in chunks:
        if typ!=0x102:continue
        ns,name_idx,attr_start,attr_step,attr_count,*_=struct.unpack_from("<IIHHHHHH",raw,head);element=strings[name_idx]
        for i in range(attr_count):
            off=head+attr_start+i*attr_step
            ans,aname_idx,araw,sz,zero,kind,val=struct.unpack_from("<IIIHBBI",raw,off);aname=strings[aname_idx]
            if element=="manifest" and aname=="versionCode":struct.pack_into("<I",raw,off+16,357)
            if kind==3 and val<len(strings):
                if element=="manifest" and aname=="versionName":strings[val]="2.5.7"
                elif element=="application" and aname=="label":strings[val]="Свої в Європі"
    blob=bytearray();offs=[]
    for s in strings:
        offs.append(len(blob));u=s.encode("utf-16-le")
        if utf8:b=s.encode("utf8");blob+=put8(len(u)//2)+put8(len(b))+b+b"\0"
        else:blob+=put16(len(u)//2)+u+b"\0\0"
    while len(blob)%4:blob.append(0)
    start=28+4*len(strings)
    poolraw=struct.pack("<HHI5I",1,28,start+len(blob),len(strings),0,flags&~1,start,0)+struct.pack("<"+"I"*len(strings),*offs)+blob
    chunks[pool][2]=poolraw;payload=b"".join(bytes(raw) for _,_,raw in chunks)
    return struct.pack("<HHI",3,8,8+len(payload))+payload


for d in ["stub","classes","dex","helper","smali"]:(W/d).mkdir()
run("javac","-encoding","UTF-8","-source","8","-target","8","-cp",android,"-d",W/"stub","app-finish257/Signatures.java")
run("javac","-encoding","UTF-8","-source","8","-target","8","-cp",str(android)+os.pathsep+str(W/"stub"),"-d",W/"classes",SRC,MAIL)
classes=sorted((W/"classes").rglob("*.class"));assert classes
run(bt/"d8","--min-api","26","--lib",android,"--classpath",W/"stub","--output",W/"dex",*classes)
run("baksmali","disassemble",W/"dex/classes.dex","-o",W/"helper")
z=zipfile.ZipFile(BASE);(W/"base.dex").write_bytes(zread(z,"classes3.dex"))
run("baksmali","disassemble",W/"base.dex","-o",W/"smali")
base=W/"smali/eu/svoyi/nativeapp"
def patch(name,sig,fn):
    p=base/(name+".smali");s=p.read_text()
    ms=[m for m in re.finditer(r"(?ms)^\.method[^\n]*\n.*?^\.end method",s) if m.group().splitlines()[0].endswith(sig)]
    assert len(ms)==1,(name,sig)
    m=ms[0];v=fn(m.group());assert v!=m.group(),sig
    p.write_text(s[:m.start()]+v+s[m.end():])
patch("AppFinish252","home(Leu/svoyi/nativeapp/NativeWelcome;Ljava/lang/String;Landroid/view/View;Landroid/view/View;Landroid/view/View;)Landroid/view/View;",lambda s:s.replace("Leu/svoyi/nativeapp/HomeScreen252;->buildSite","Leu/svoyi/nativeapp/HomeScreen257;->buildSite"))
patch("Batch20Ui","remember(Landroid/app/Activity;Lorg/json/JSONObject;)V",lambda s:s.replace("    return-void","    invoke-static {p0, p1}, Leu/svoyi/nativeapp/MailScreen257;->remember(Landroid/app/Activity;Lorg/json/JSONObject;)V\n    return-void"))
for sig,fn in [("createInbox(Lorg/json/JSONObject;)V","inbox"),("paintInbox()V","inbox"),("createThread()V","thread"),("updateComposer()V","composer")]:
    patch("NativeMailScreen",sig,lambda s:s.replace("    return-void","    invoke-static/range {p0 .. p0}, Leu/svoyi/nativeapp/MailScreen257;->"+fn+"(Leu/svoyi/nativeapp/NativeMailScreen;)V\n    return-void"))
for p in (W/"helper").rglob("*.smali"):
    rel=p.relative_to(W/"helper");dst=W/"smali"/rel
    if dst.exists():
        if dst.read_bytes()==p.read_bytes() or "com/android/tools/r8/annotations" in str(rel):continue
        raise RuntimeError("collision "+str(rel))
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst)
run("smali","assemble","--jobs","1",W/"smali","-o",W/"classes3.dex")
unsigned=OUT/"Svoyi-2.5.7-unsigned.apk"
with zipfile.ZipFile(unsigned,"w",zipfile.ZIP_DEFLATED) as o:
    for info in z.infolist():
        if info.filename.startswith("META-INF/"):continue
        data=zread(z,info.filename)
        if info.filename=="classes3.dex":data=(W/"classes3.dex").read_bytes()
        elif info.filename=="AndroidManifest.xml":data=rewrite_manifest(data)
        zi=zipfile.ZipInfo(info.filename,info.date_time);zi.compress_type=info.compress_type;zi.external_attr=info.external_attr;zi.create_system=info.create_system;o.writestr(zi,data)
result={"version":"2.5.7","versionCode":357,"package":"eu.svoyi.qa.finish255","baseline_sha256":BASE_SHA,"unsigned_sha256":hashlib.sha256(unsigned.read_bytes()).hexdigest(),"server_changed":False}
(OUT/"build.json").write_text(json.dumps(result,indent=2));print(json.dumps(result))
