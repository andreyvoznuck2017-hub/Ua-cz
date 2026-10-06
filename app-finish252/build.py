#!/usr/bin/env python3
"""Build baseline and final 2.5.2 QA APKs from the repaired 2.4.9 candidate."""
import hashlib,json,os,re,shutil,struct,subprocess,zipfile
from pathlib import Path

BASE_APK=Path("app-finish252/baseline249.apk")
OUT=Path("app-finish252/releases"); WORK=Path("app-finish252/.build")
SOURCES=[Path("app-finish252/HomeScreen252.java"),Path("app-finish252/AccountScreen252.java"),Path("app-finish252/AppFinish252.java")]
OUT.mkdir(parents=True,exist_ok=True)
if WORK.exists(): shutil.rmtree(WORK)
WORK.mkdir(parents=True)
assert BASE_APK.is_file()
for p in SOURCES: assert p.is_file(),p

sdk=Path(os.environ["ANDROID_HOME"])
platforms=[]
for p in (sdk/"platforms").glob("android-*"):
    m=re.fullmatch(r"android-(\d+)",p.name)
    if m: platforms.append((int(m.group(1)),p))
platforms.sort(); assert platforms
android=platforms[-1][1]/"android.jar"
bts=sorted((sdk/"build-tools").glob("*"),key=lambda p:[int(x) for x in re.findall(r"\d+",p.name)])
bt=bts[-1]

def run(*args,env=None,capture=False):
    cmd=[str(x) for x in args]
    if capture:return subprocess.check_output(cmd,text=True,env=env)
    subprocess.run(cmd,check=True,env=env);return ""

def zread(z,item):
    info=z.getinfo(item) if isinstance(item,str) else item
    with z.open(info) as fp:
        fp._expected_crc=None
        return fp.read()

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

def rewrite_manifest(data,package,label,version_code):
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
    oldpkgs=("eu.svoyi.nativeapp","eu.svoyi.qa.before252")
    for typ,head,raw in chunks:
        if typ!=0x102:continue
        ns,name_idx,attr_start,attr_step,attr_count,*_=struct.unpack_from("<IIHHHHHH",raw,head)
        element=strings[name_idx]
        for i in range(attr_count):
            off=head+attr_start+i*attr_step
            ans,aname_idx,araw,sz,zero,kind,val=struct.unpack_from("<IIIHBBI",raw,off)
            aname=strings[aname_idx]
            if element=="manifest" and aname=="versionCode":struct.pack_into("<I",raw,off+16,version_code)
            if kind!=3 or val>=len(strings):continue
            cur=strings[val];new=None
            if element=="manifest" and aname=="package":new=package
            elif aname in {"authorities","permission","readPermission","writePermission"}:
                for oldpkg in oldpkgs:
                    if cur.startswith(oldpkg):new=package+cur[len(oldpkg):];break
            elif element in {"permission","uses-permission","uses-permission-sdk-23"} and aname=="name":
                for oldpkg in oldpkgs:
                    if cur.startswith(oldpkg):new=package+cur[len(oldpkg):];break
            elif element=="application" and aname=="label":new=label
            elif element=="manifest" and aname=="versionName":new="2.5.2-final-qa"
            if new is not None:strings[val]=new
    blob=bytearray();offsets=[]
    for s in strings:
        offsets.append(len(blob));u=s.encode("utf-16-le")
        if utf8:b=s.encode("utf8");blob+=put8(len(u)//2)+put8(len(b))+b+b"\0"
        else:blob+=put16(len(u)//2)+u+b"\0\0"
    while len(blob)%4:blob.append(0)
    start=28+4*len(strings)
    poolraw=struct.pack("<HHI5I",1,28,start+len(blob),len(strings),0,flags&~1,start,0)+struct.pack("<"+"I"*len(strings),*offsets)+blob
    chunks[pool][2]=poolraw;payload=b"".join(bytes(raw) for _,_,raw in chunks)
    return struct.pack("<HHI",3,8,8+len(payload))+payload

stub='''package eu.svoyi.nativeapp;
import android.app.*;import android.content.*;import android.view.*;import android.widget.*;import org.json.*;
class ThemePalette {int background,surface,text,muted,accent,border;boolean dark;}
class MainActivity extends Activity {public View batch20Nodes(JSONArray n){return null;}}
class NativeWelcome {Activity activity;ThemePalette colors;NativeJobsScreen.Host host;}
class NativeJobsScreen {interface Host {boolean alive();void navigate(String r);View image(String u);}}
class NativeSiteUi {static final class Flow extends ViewGroup {Flow(Context c,int n){super(c);}protected void onLayout(boolean c,int l,int t,int r,int b){}}}
'''
(WORK/"Signatures.java").write_text(stub)
for d in ["stub","classes","dex","helper","smali"]:(WORK/d).mkdir(exist_ok=True)
run("javac","-source","8","-target","8","-cp",android,"-d",WORK/"stub",WORK/"Signatures.java")
run("javac","-source","8","-target","8","-cp",str(android)+os.pathsep+str(WORK/"stub"),"-d",WORK/"classes",*SOURCES)
classes=list((WORK/"classes").rglob("*.class"));assert classes
run(bt/"d8","--min-api","26","--lib",android,"--classpath",WORK/"stub","--output",WORK/"dex",*classes)
run("baksmali","disassemble",WORK/"dex/classes.dex","-o",WORK/"helper")

z=zipfile.ZipFile(BASE_APK)
(WORK/"original.dex").write_bytes(zread(z,"classes3.dex"))
run("baksmali","disassemble",WORK/"original.dex","-o",WORK/"smali")
base=WORK/"smali/eu/svoyi/nativeapp"

def replace_method(path,sig,newbody):
    src=path.read_text();ms=[m for m in re.finditer(r"(?ms)^\.method[^\n]*\n.*?^\.end method",src) if m.group().splitlines()[0].endswith(sig)]
    assert len(ms)==1,(path,sig,len(ms));m=ms[0];path.write_text(src[:m.start()]+newbody+src[m.end():])

p=base/"Batch20Ui.smali"
src=p.read_text();ms=[m for m in re.finditer(r"(?ms)^\.method[^\n]*\n.*?^\.end method",src) if m.group().splitlines()[0].endswith("remember(Landroid/app/Activity;Lorg/json/JSONObject;)V")]
assert len(ms)==1
m=ms[0];old=m.group();hook="    invoke-static {p0, p1}, Leu/svoyi/nativeapp/AppFinish252;->remember(Landroid/app/Activity;Lorg/json/JSONObject;)V\n"
assert "AppFinish252;->remember" not in old
new=old.replace("    return-void",hook+"    return-void")
p.write_text(src[:m.start()]+new+src[m.end():])

replace_method(p,"home(Leu/svoyi/nativeapp/NativeWelcome;Ljava/lang/String;Landroid/view/View;Landroid/view/View;Landroid/view/View;)Landroid/view/View;",
'''.method public static home(Leu/svoyi/nativeapp/NativeWelcome;Ljava/lang/String;Landroid/view/View;Landroid/view/View;Landroid/view/View;)Landroid/view/View;
    .registers 5
    invoke-static/range {p0 .. p4}, Leu/svoyi/nativeapp/AppFinish252;->home(Leu/svoyi/nativeapp/NativeWelcome;Ljava/lang/String;Landroid/view/View;Landroid/view/View;Landroid/view/View;)Landroid/view/View;
    move-result-object p0
    return-object p0
.end method''')
replace_method(p,"route(Ljava/lang/String;)Ljava/lang/String;",
'''.method public static route(Ljava/lang/String;)Ljava/lang/String;
    .registers 1
    invoke-static {p0}, Leu/svoyi/nativeapp/AppFinish252;->route(Ljava/lang/String;)Ljava/lang/String;
    move-result-object p0
    return-object p0
.end method''')

# Android 8/9 compatibility: every LocationListener must implement legacy abstract callbacks.
location_compat=[]
for q in (WORK/"smali").rglob("*.smali"):
    txt=q.read_text()
    if ".implements Landroid/location/LocationListener;" not in txt: continue
    methods=[]
    if "onStatusChanged(Ljava/lang/String;ILandroid/os/Bundle;)V" not in txt:
        methods.append(".method public onStatusChanged(Ljava/lang/String;ILandroid/os/Bundle;)V\n    .locals 0\n    return-void\n.end method\n")
    if "onProviderEnabled(Ljava/lang/String;)V" not in txt:
        methods.append(".method public onProviderEnabled(Ljava/lang/String;)V\n    .locals 0\n    return-void\n.end method\n")
    if "onProviderDisabled(Ljava/lang/String;)V" not in txt:
        methods.append(".method public onProviderDisabled(Ljava/lang/String;)V\n    .locals 0\n    return-void\n.end method\n")
    if methods:
        q.write_text(txt+"\n"+"\n".join(methods))
        location_compat.append(str(q.relative_to(WORK/"smali")))

added=[]
for hp in (WORK/"helper").rglob("*.smali"):
    rel=hp.relative_to(WORK/"helper");dest=WORK/"smali"/rel
    if dest.exists():
        if dest.read_bytes()==hp.read_bytes():continue
        if "$$ExternalSynthetic" in hp.name or "com/android/tools/r8/annotations" in str(rel):
            txt=hp.read_text()
            desc=re.search(r"(?m)^\.class[^\n]* (L[^;]+;)",txt)
            assert desc
            olddesc=desc.group(1);newdesc=olddesc[:-1]+"_Finish252;"
            txt=txt.replace(olddesc,newdesc)
            dest=WORK/"smali"/(newdesc[1:-1]+".smali")
            assert not dest.exists();dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(txt);added.append(str(dest.relative_to(WORK/"smali")));continue
        raise AssertionError("Unexpected helper collision "+str(rel))
    dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(hp,dest);added.append(str(rel))
assert any("AppFinish252" in x for x in added)
assert any("HomeScreen252" in x for x in added)
assert any("AccountScreen252" in x for x in added)
run("smali","assemble",WORK/"smali","-o",WORK/"classes3.dex")

base_manifest=zread(z,"AndroidManifest.xml")
password="svoyi-final-qa-252";ks=WORK/"qa.p12";env=dict(os.environ,QA_SIGNING_PASSWORD=password)
run("keytool","-genkeypair","-keystore",ks,"-storetype","PKCS12","-storepass",password,"-keypass",password,"-alias","finishqa","-keyalg","RSA","-keysize","3072","-validity","3650","-dname","CN=Svoyi Final QA 2.5.2",env=env)

def package(apk_name,package,label,patched):
    manifest=rewrite_manifest(base_manifest,package,label,352)
    unsigned=WORK/(apk_name+".unsigned")
    with zipfile.ZipFile(unsigned,"w",zipfile.ZIP_DEFLATED) as out:
        for info in z.infolist():
            if info.filename.startswith("META-INF/"):continue
            data=zread(z,info)
            if info.filename=="AndroidManifest.xml":data=manifest
            elif patched and info.filename=="classes3.dex":data=(WORK/"classes3.dex").read_bytes()
            zi=zipfile.ZipInfo(info.filename,info.date_time);zi.compress_type=info.compress_type;zi.external_attr=info.external_attr;zi.create_system=info.create_system
            out.writestr(zi,data)
    aligned=WORK/(apk_name+".aligned");run(bt/"zipalign","-f","4",unsigned,aligned)
    final=OUT/apk_name
    run(bt/"apksigner","sign","--ks",ks,"--ks-key-alias","finishqa","--ks-pass","env:QA_SIGNING_PASSWORD","--out",final,aligned,env=env)
    verify=run(bt/"apksigner","verify","--verbose","--print-certs",final,capture=True)
    badge=run(bt/"aapt","dump","badging",final,capture=True)
    assert package in badge
    return {"file":apk_name,"package":package,"sha256":hashlib.sha256(final.read_bytes()).hexdigest(),"bytes":final.stat().st_size,"signature":verify.splitlines()[:6]}

before=package("Svoyi-Before-2.4.9-QA.apk","eu.svoyi.qa.before252","Свої — Before 2.4.9",False)
final=package("Svoyi-Final-2.5.2-QA.apk","eu.svoyi.qa.finish252","Свої — Final QA 2.5.2",True)
(OUT/"build-manifest.json").write_text(json.dumps({
    "version":"2.5.2-final-qa","before":before,"final":final,
    "changed":["site-matched home","site-matched account","theme palette on home","localized generated labels","canonical local routes","jobs native route","cross-screen touch target polish","Android 8/9 LocationListener compatibility"],
    "location_listener_compat_files":location_compat,
    "server_changed":False,"owner_key_used":False
},ensure_ascii=False,indent=2))
(OUT/"SHA256SUMS.txt").write_text(f"{before['sha256']}  {before['file']}\n{final['sha256']}  {final['file']}\n")
print(json.dumps({"before":before,"final":final},ensure_ascii=False,indent=2))
