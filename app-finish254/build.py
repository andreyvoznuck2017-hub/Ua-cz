#!/usr/bin/env python3
import os,re,shutil,subprocess,zipfile,hashlib,struct,json
from pathlib import Path

BASE=Path("app-finish254/baseline252.apk")
SOURCES=[Path("app-finish253/SocialFinish253.java"),Path("app-finish254/InteractionFinish254.java")]
OUT=Path("app-finish254/releases");W=Path("app-finish254/.build")
OUT.mkdir(parents=True,exist_ok=True)
if W.exists():shutil.rmtree(W)
W.mkdir(parents=True)
assert BASE.is_file()
assert hashlib.sha256(BASE.read_bytes()).hexdigest()=="3ba77212dd78df87338c77b4bdfb93c1471f3a11d30fa646fe88cdae4b30d5da"
for p in SOURCES:assert p.is_file(),p

sdk=Path(os.environ["ANDROID_HOME"]);plats=[]
for p in (sdk/"platforms").glob("android-*"):
    m=re.fullmatch(r"android-(\d+)",p.name)
    if m:plats.append((int(m.group(1)),p))
plats.sort();android=plats[-1][1]/"android.jar"
bt=sorted((sdk/"build-tools").glob("*"),key=lambda p:[int(x) for x in re.findall(r"\d+",p.name)])[-1]
def run(*a):subprocess.run([str(x) for x in a],check=True)
def zread(z,name):
    info=z.getinfo(name)
    with z.open(info) as f:
        f._expected_crc=None
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
            if element=="manifest" and aname=="versionCode":struct.pack_into("<I",raw,off+16,354)
            if kind==3 and val<len(strings):
                if element=="manifest" and aname=="versionName":strings[val]="2.5.4-final-qa"
                elif element=="application" and aname=="label":strings[val]="Свої — Final QA 2.5.4"
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

for d in ["classes","dex","helper","smali"]:(W/d).mkdir()
run("javac","-source","8","-target","8","-cp",android,"-d",W/"classes",*SOURCES)
classes=list((W/"classes").rglob("*.class"));assert classes
run(bt/"d8","--min-api","26","--lib",android,"--output",W/"dex",*classes)
run("baksmali","disassemble",W/"dex/classes.dex","-o",W/"helper")

z=zipfile.ZipFile(BASE);(W/"base.dex").write_bytes(zread(z,"classes3.dex"))
run("baksmali","disassemble",W/"base.dex","-o",W/"smali")
target=W/"smali/eu/svoyi/nativeapp/Batch20Ui.smali";src=target.read_text()
blocks=[m for m in re.finditer(r"(?ms)^\.method[^\n]*\n.*?^\.end method",src) if m.group().splitlines()[0].endswith("remember(Landroid/app/Activity;Lorg/json/JSONObject;)V")]
assert len(blocks)==1;m=blocks[0];old=m.group()
hooks=""
if "SocialFinish253;->apply" not in old:hooks+="    invoke-static {p0, p1}, Leu/svoyi/nativeapp/SocialFinish253;->apply(Landroid/app/Activity;Lorg/json/JSONObject;)V\n"
if "InteractionFinish254;->apply" not in old:hooks+="    invoke-static {p0, p1}, Leu/svoyi/nativeapp/InteractionFinish254;->apply(Landroid/app/Activity;Lorg/json/JSONObject;)V\n"
assert hooks
target.write_text(src[:m.start()]+old.replace("    return-void",hooks+"    return-void")+src[m.end():])

added=[]
for p in (W/"helper").rglob("*.smali"):
    rel=p.relative_to(W/"helper");dst=W/"smali"/rel
    if dst.exists():
        if dst.read_bytes()==p.read_bytes():continue
        if "com/android/tools/r8/annotations" in str(rel) or "$$ExternalSynthetic" in p.name:continue
        raise RuntimeError("collision "+str(rel))
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst);added.append(str(rel))
assert any("SocialFinish253" in x for x in added)
assert any("InteractionFinish254" in x for x in added)
run("smali","assemble",W/"smali","-o",W/"classes3.dex")

manifest=rewrite_manifest(zread(z,"AndroidManifest.xml"))
unsigned=OUT/"Svoyi-Final-2.5.4-QA-unsigned.apk"
with zipfile.ZipFile(unsigned,"w",zipfile.ZIP_DEFLATED) as o:
    for info in z.infolist():
        if info.filename.startswith("META-INF/"):continue
        data=zread(z,info.filename)
        if info.filename=="classes3.dex":data=(W/"classes3.dex").read_bytes()
        elif info.filename=="AndroidManifest.xml":data=manifest
        zi=zipfile.ZipInfo(info.filename,info.date_time);zi.compress_type=info.compress_type;zi.external_attr=info.external_attr;zi.create_system=info.create_system
        o.writestr(zi,data)
result={"unsigned_sha256":hashlib.sha256(unsigned.read_bytes()).hexdigest(),"version":"2.5.4-final-qa","versionCode":354,
"features":["2.5.3 social visual pass","mail keyboard resize and composer visibility","per-account per-page scroll restore","dating touch targets","housing card sizing","comment action targets","notification row targets"],"server_changed":False}
(OUT/"build.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps(result,ensure_ascii=False))
