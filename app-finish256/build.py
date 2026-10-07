#!/usr/bin/env python3
import os,re,shutil,subprocess,zipfile,hashlib,struct,json,zlib
from pathlib import Path

BASE=Path("app-finish256/baseline254.apk")
SRC=Path("app-finish256/UiFinish256.java")
OUT=Path("app-finish256/releases");W=Path("app-finish256/.build")
OUT.mkdir(parents=True,exist_ok=True)
if W.exists():shutil.rmtree(W)
W.mkdir(parents=True)
assert BASE.is_file() and SRC.is_file()
BASE_SHA="7bd53cd66aad5aae50930119d61557067aa9de49f73f69f71181666e42dfe345"
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
                strings.append(s.replace("eu.svoyi.qa.finish252","eu.svoyi.qa.finish255"))
        pos+=size
    assert pool is not None and pos==len(data)
    for typ,head,raw in chunks:
        if typ!=0x102:continue
        ns,name_idx,attr_start,attr_step,attr_count,*_=struct.unpack_from("<IIHHHHHH",raw,head);element=strings[name_idx]
        for i in range(attr_count):
            off=head+attr_start+i*attr_step
            ans,aname_idx,araw,sz,zero,kind,val=struct.unpack_from("<IIIHBBI",raw,off);aname=strings[aname_idx]
            if element=="manifest" and aname=="versionCode":struct.pack_into("<I",raw,off+16,356)
            if kind==3 and val<len(strings):
                if element=="manifest" and aname=="versionName":strings[val]="2.5.6"
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

for d in ["classes","dex","helper","smali"]:(W/d).mkdir()
run("javac","-source","8","-target","8","-cp",android,"-d",W/"classes",SRC)
classes=sorted((W/"classes").rglob("*.class"));assert classes
run(bt/"d8","--min-api","26","--lib",android,"--output",W/"dex",*classes)
run("baksmali","disassemble",W/"dex/classes.dex","-o",W/"helper")

z=zipfile.ZipFile(BASE);(W/"base.dex").write_bytes(zread(z,"classes3.dex"))
run("baksmali","disassemble",W/"base.dex","-o",W/"smali")
target=W/"smali/eu/svoyi/nativeapp/Batch20Ui.smali";src=target.read_text()
blocks=[m for m in re.finditer(r"(?ms)^\.method[^\n]*\n.*?^\.end method",src) if m.group().splitlines()[0].endswith("remember(Landroid/app/Activity;Lorg/json/JSONObject;)V")]
assert len(blocks)==1
m=blocks[0];old=m.group()
hook="    invoke-static {p0, p1}, Leu/svoyi/nativeapp/UiFinish256;->apply(Landroid/app/Activity;Lorg/json/JSONObject;)V\n"
assert "UiFinish256;->apply" not in old
for name in ("SocialFinish253", "InteractionFinish254", "MediaCreateFinish255"):
    old=re.sub(r"(?m)^    invoke-static \{p0, p1\}, Leu/svoyi/nativeapp/"+name+r";->apply\(Landroid/app/Activity;Lorg/json/JSONObject;\)V\n", "", old)
target.write_text(src[:m.start()]+old.replace("    return-void",hook+"    return-void")+src[m.end():])

# Preserve AppFinish252's home/account/routes, remove its redundant view-tree pass.
owner=W/"smali/eu/svoyi/nativeapp/AppFinish252.smali"
source=owner.read_text()
source,count=re.subn(r"(?m)^    invoke-static \{[^}]+\}, Leu/svoyi/nativeapp/AppFinish252;->polish\(Landroid/app/Activity;Lorg/json/JSONObject;\)V\n", "", source)
assert count==1, ("old polish call count",count)
owner.write_text(source)

# Save while the old screen's generation is still current. newContent() runs
# after generation changes, so its close()/saveDraft() cannot flush recent typing.
activity=W/"smali/eu/svoyi/nativeapp/MainActivity.smali"
source=activity.read_text()
for signature in (r"load\(Ljava/lang/String;ZI\)V",r"settings\(\)V"):
    pat=r"(?m)(^\.method private "+signature+r"\n    \.(?:locals|registers) \d+\n)"
    source,count=re.subn(pat,lambda m:m[1]+"\n    invoke-direct {p0}, Leu/svoyi/nativeapp/MainActivity;->saveChatDraft()V\n",source)
    assert count==1, ("draft flush patch count",signature,count)
activity.write_text(source)

# These superseded classes contain API-29-only calls and are no longer reachable.
for pattern in ("SocialFinish253*.smali","InteractionFinish254*.smali","MediaCreateFinish255*.smali"):
    for path in (W/"smali/eu/svoyi/nativeapp").glob(pattern): path.unlink()

added=[]
for p in (W/"helper").rglob("*.smali"):
    rel=p.relative_to(W/"helper");dst=W/"smali"/rel
    if dst.exists():
        if dst.read_bytes()==p.read_bytes():continue
        if "com/android/tools/r8/annotations" in str(rel) or "$$ExternalSynthetic" in p.name:continue
        raise RuntimeError("collision "+str(rel))
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst);added.append(str(rel))
assert any("UiFinish256" in x for x in added)
run("smali","assemble","--jobs","1",W/"smali","-o",W/"classes3.dex")

def package_dex(data):
    old=b"eu.svoyi.qa.finish252";new=b"eu.svoyi.qa.finish255"
    assert len(old)==len(new)
    data=bytearray(data.replace(old,new))
    data[12:32]=hashlib.sha1(data[32:]).digest()
    struct.pack_into("<I",data,8,zlib.adler32(data[12:])&0xffffffff)
    return bytes(data)

manifest=rewrite_manifest(zread(z,"AndroidManifest.xml"))
unsigned=OUT/"Svoyi-2.5.6-unsigned.apk"
with zipfile.ZipFile(unsigned,"w",zipfile.ZIP_DEFLATED) as o:
    for info in z.infolist():
        if info.filename.startswith("META-INF/"):continue
        data=zread(z,info.filename)
        if info.filename=="classes3.dex":data=(W/"classes3.dex").read_bytes()
        elif info.filename=="AndroidManifest.xml":data=manifest
        if info.filename.endswith(".dex"):data=package_dex(data)
        if info.filename=="resources.arsc":
            for enc in ("utf-8","utf-16-le"):
                data=data.replace("eu.svoyi.qa.finish252".encode(enc),"eu.svoyi.qa.finish255".encode(enc))
        zi=zipfile.ZipInfo(info.filename,info.date_time);zi.compress_type=info.compress_type;zi.external_attr=info.external_attr;zi.create_system=info.create_system
        o.writestr(zi,data)
result={
    "version":"2.5.6","versionCode":356,"baseline_sha256":BASE_SHA,
    "unsigned_sha256":hashlib.sha256(unsigned.read_bytes()).hexdigest(),
    "package":"eu.svoyi.qa.finish255",
    "features":[
        "single lifecycle-guarded UI pass replaces four conflicting passes",
        "native focus and keyboard listeners preserved",
        "native account/route scroll restoration preserved",
        "native dating photos and avatars retain their own dimensions",
        "mail draft flushed before navigation or settings invalidates screen generation",
        "API 26 compatible UI code; no unguarded EditText.isSingleLine()"
    ],
    "server_changed":False,"owner_signing_key_used":False
}
(OUT/"build.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps(result,ensure_ascii=False))

