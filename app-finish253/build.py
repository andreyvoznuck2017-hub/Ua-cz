#!/usr/bin/env python3
import os,re,shutil,subprocess,zipfile,hashlib
from pathlib import Path

BASE=Path("app-finish253/baseline252.apk")
SRC=Path("app-finish253/SocialFinish253.java")
OUT=Path("app-finish253/releases"); W=Path("app-finish253/.build")
OUT.mkdir(parents=True,exist_ok=True)
if W.exists(): shutil.rmtree(W)
W.mkdir(parents=True)
assert BASE.is_file()
assert hashlib.sha256(BASE.read_bytes()).hexdigest()=="3ba77212dd78df87338c77b4bdfb93c1471f3a11d30fa646fe88cdae4b30d5da"

sdk=Path(os.environ["ANDROID_HOME"])
plats=[]
for p in (sdk/"platforms").glob("android-*"):
    m=re.fullmatch(r"android-(\d+)",p.name)
    if m: plats.append((int(m.group(1)),p))
plats.sort(); android=plats[-1][1]/"android.jar"
bt=sorted((sdk/"build-tools").glob("*"),key=lambda p:[int(x) for x in re.findall(r"\d+",p.name)])[-1]
def run(*a): subprocess.run([str(x) for x in a],check=True)
def zread(z,name):
    info=z.getinfo(name)
    with z.open(info) as f:
        f._expected_crc=None
        return f.read()

for d in ["classes","dex","helper","smali"]: (W/d).mkdir()
run("javac","-source","8","-target","8","-cp",android,"-d",W/"classes",SRC)
classes=list((W/"classes").rglob("*.class")); assert classes
run(bt/"d8","--min-api","26","--lib",android,"--output",W/"dex",*classes)
run("baksmali","disassemble",W/"dex/classes.dex","-o",W/"helper")

z=zipfile.ZipFile(BASE)
(W/"base.dex").write_bytes(zread(z,"classes3.dex"))
run("baksmali","disassemble",W/"base.dex","-o",W/"smali")
target=W/"smali/eu/svoyi/nativeapp/Batch20Ui.smali"
src=target.read_text()
blocks=[m for m in re.finditer(r"(?ms)^\.method[^\n]*\n.*?^\.end method",src) if m.group().splitlines()[0].endswith("remember(Landroid/app/Activity;Lorg/json/JSONObject;)V")]
assert len(blocks)==1
m=blocks[0]; old=m.group()
hook="    invoke-static {p0, p1}, Leu/svoyi/nativeapp/SocialFinish253;->apply(Landroid/app/Activity;Lorg/json/JSONObject;)V\n"
assert "SocialFinish253;->apply" not in old
target.write_text(src[:m.start()]+old.replace("    return-void",hook+"    return-void")+src[m.end():])

for p in (W/"helper").rglob("*.smali"):
    rel=p.relative_to(W/"helper"); dst=W/"smali"/rel
    if dst.exists():
        if dst.read_bytes()==p.read_bytes(): continue
        if "com/android/tools/r8/annotations" in str(rel) or "$$ExternalSynthetic" in p.name: continue
        raise RuntimeError("collision "+str(rel))
    dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,dst)
run("smali","assemble",W/"smali","-o",W/"classes3.dex")

unsigned=OUT/"Svoyi-Final-2.5.3-QA-unsigned.apk"
with zipfile.ZipFile(unsigned,"w",zipfile.ZIP_DEFLATED) as o:
    for info in z.infolist():
        if info.filename.startswith("META-INF/"): continue
        data=zread(z,info.filename)
        if info.filename=="classes3.dex": data=(W/"classes3.dex").read_bytes()
        zi=zipfile.ZipInfo(info.filename,info.date_time); zi.compress_type=info.compress_type; zi.external_attr=info.external_attr; zi.create_system=info.create_system
        o.writestr(zi,data)
print(hashlib.sha256(unsigned.read_bytes()).hexdigest())
