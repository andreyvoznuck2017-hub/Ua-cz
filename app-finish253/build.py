#!/usr/bin/env python3
"""Build 2.5.3 social-core QA from the verified 2.5.2 artifact."""
import hashlib,json,os,re,shutil,struct,subprocess,zipfile
from pathlib import Path

BASE=Path("app-finish253/baseline252.apk")
OUT=Path("app-finish253/releases");WORK=Path("app-finish253/.build")
SOURCES=[Path("app-finish253/SocialUi253.java"),Path("app-finish253/AppFinish253.java"),Path("app-finish253/DatingFix253.java")]
OUT.mkdir(parents=True,exist_ok=True)
if WORK.exists():shutil.rmtree(WORK)
WORK.mkdir(parents=True)
assert BASE.is_file()
for p in SOURCES:assert p.is_file(),p

sdk=Path(os.environ["ANDROID_HOME"])
plats=[]
for p in (sdk/"platforms").glob("android-*"):
 m=re.fullmatch(r"android-(\d+)",p.name)
 if m:plats.append((int(m.group(1)),p))
plats.sort();assert plats
android=plats[-1][1]/"android.jar"
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

def rewrite_manifest(data,package,label,version_code,version_name):
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
 oldpkgs=("eu.svoyi.qa.finish252","eu.svoyi.nativeapp")
 for typ,head,raw in chunks:
  if typ!=0x102:continue
  ns,name_idx,attr_start,attr_step,attr_count,*_=struct.unpack_from("<IIHHHHHH",raw,head);element=strings[name_idx]
  for i in range(attr_count):
   off=head+attr_start+i*attr_step
   ans,aname_idx,araw,sz,zero,kind,val=struct.unpack_from("<IIIHBBI",raw,off);aname=strings[aname_idx]
   if element=="manifest" and aname=="versionCode":struct.pack_into("<I",raw,off+16,version_code)
   if kind!=3 or val>=len(strings):continue
   cur=strings[val];new=None
   if element=="manifest" and aname=="package":new=package
   elif element=="manifest" and aname=="versionName":new=version_name
   elif aname in {"authorities","permission","readPermission","writePermission"}:
    for old in oldpkgs:
     if cur.startswith(old):new=package+cur[len(old):];break
   elif element in {"permission","uses-permission","uses-permission-sdk-23"} and aname=="name":
    for old in oldpkgs:
     if cur.startswith(old):new=package+cur[len(old):];break
   elif element=="application" and aname=="label":new=label
   if new is not None:strings[val]=new
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

stub='''package eu.svoyi.nativeapp;
class AppFinish252 { static String route(String s){return s;} }
'''
(WORK/"Stub.java").write_text(stub)
for d in ["stub","classes","dex","helper","smali"]:(WORK/d).mkdir(exist_ok=True)
run("javac","-source","8","-target","8","-cp",android,"-d",WORK/"stub",WORK/"Stub.java")
run("javac","-source","8","-target","8","-cp",str(android)+os.pathsep+str(WORK/"stub"),"-d",WORK/"classes",*SOURCES)
classes=list((WORK/"classes").rglob("*.class"));assert classes and any(p.name=="AppFinish253.class" for p in classes)
run(bt/"d8","--min-api","26","--lib",android,"--classpath",WORK/"stub","--output",WORK/"dex",*classes)
run("baksmali","disassemble",WORK/"dex/classes.dex","-o",WORK/"helper")

z=zipfile.ZipFile(BASE)
(WORK/"original.dex").write_bytes(zread(z,"classes3.dex"))
run("baksmali","disassemble",WORK/"original.dex","-o",WORK/"smali")
base=WORK/"smali/eu/svoyi/nativeapp"

def block(src,sig):
 ms=[m for m in re.finditer(r"(?ms)^\.method[^\n]*\n.*?^\.end method",src) if m.group().splitlines()[0].endswith(sig)]
 assert len(ms)==1,(sig,len(ms));return ms[0]

p=base/"Batch20Ui.smali";src=p.read_text()
sig="remember(Landroid/app/Activity;Lorg/json/JSONObject;)V";m=block(src,sig);old=m.group()
hook="    invoke-static {p0, p1}, Leu/svoyi/nativeapp/AppFinish253;->remember(Landroid/app/Activity;Lorg/json/JSONObject;)V\n"
assert "AppFinish253;->remember" not in old
new=old.replace("    return-void",hook+"    return-void")
p.write_text(src[:m.start()]+new+src[m.end():])

src=p.read_text();sig="route(Ljava/lang/String;)Ljava/lang/String;";m=block(src,sig)
first=m.group().splitlines()[0]
new=first+"\n    .locals 1\n    invoke-static {p0}, Leu/svoyi/nativeapp/AppFinish253;->route(Ljava/lang/String;)Ljava/lang/String;\n    move-result-object v0\n    return-object v0\n.end method"
p.write_text(src[:m.start()]+new+src[m.end():])

# Server dating nodes can have id="" while route contains the real numeric view id.
dating=base/"NativeDatingScreen.smali"
assert dating.is_file(),"NativeDatingScreen missing"
dating_src=dating.read_text()
old_ref="Leu/svoyi/nativeapp/DatingOwnProfile;->id(Lorg/json/JSONObject;)I"
new_ref="Leu/svoyi/nativeapp/DatingFix253;->profileId(Lorg/json/JSONObject;)I"
dating_count=dating_src.count(old_ref)
assert dating_count==3,("dating id reference count",dating_count)
dating.write_text(dating_src.replace(old_ref,new_ref))

added=[]
for hp in (WORK/"helper").rglob("*.smali"):
 rel=hp.relative_to(WORK/"helper");dest=WORK/"smali"/rel
 if dest.exists():
  if dest.read_bytes()==hp.read_bytes():continue
  if "$$ExternalSynthetic" in hp.name or "com/android/tools/r8/annotations" in str(rel):
   txt=hp.read_text();d=re.search(r"(?m)^\.class[^\n]* (L[^;]+;)",txt);assert d
   old=d.group(1);newd=old[:-1]+"_Finish253;";txt=txt.replace(old,newd);dest=WORK/"smali"/(newd[1:-1]+".smali")
   assert not dest.exists();dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(txt);added.append(str(dest.relative_to(WORK/"smali")));continue
  raise AssertionError("helper collision "+str(rel))
 dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(hp,dest);added.append(str(rel))
assert any("AppFinish253" in x for x in added) and any("SocialUi253" in x for x in added) and any("DatingFix253" in x for x in added)
run("smali","assemble",WORK/"smali","-o",WORK/"classes3.dex")

base_manifest=zread(z,"AndroidManifest.xml")
password="svoyi-social-253";ks=WORK/"qa.p12";env=dict(os.environ,QA_SIGNING_PASSWORD=password)
run("keytool","-genkeypair","-keystore",ks,"-storetype","PKCS12","-storepass",password,"-keypass",password,"-alias","socialqa","-keyalg","RSA","-keysize","3072","-validity","3650","-dname","CN=Svoyi Social QA 2.5.3",env=env)

def make(name,pkg,label,vc,vn,patched):
 manifest=rewrite_manifest(base_manifest,pkg,label,vc,vn);unsigned=WORK/(name+".unsigned")
 with zipfile.ZipFile(unsigned,"w",zipfile.ZIP_DEFLATED) as out:
  for info in z.infolist():
   if info.filename.startswith("META-INF/"):continue
   data=zread(z,info)
   if info.filename=="AndroidManifest.xml":data=manifest
   elif patched and info.filename=="classes3.dex":data=(WORK/"classes3.dex").read_bytes()
   zi=zipfile.ZipInfo(info.filename,info.date_time);zi.compress_type=info.compress_type;zi.external_attr=info.external_attr;zi.create_system=info.create_system
   out.writestr(zi,data)
 aligned=WORK/(name+".aligned");run(bt/"zipalign","-f","4",unsigned,aligned)
 final=OUT/(name+".apk")
 run(bt/"apksigner","sign","--ks",ks,"--ks-key-alias","socialqa","--ks-pass","env:QA_SIGNING_PASSWORD","--out",final,aligned,env=env)
 verify=run(bt/"apksigner","verify","--verbose","--print-certs",final,capture=True)
 badging=run(bt/"aapt","dump","badging",final,capture=True);assert pkg in badging
 return {"file":final.name,"package":pkg,"sha256":hashlib.sha256(final.read_bytes()).hexdigest(),"bytes":final.stat().st_size,"verified":True}

before=make("Svoyi-Before-2.5.2-QA","eu.svoyi.qa.before253","Свої — Before 2.5.2",352,"2.5.2-before",False)
after=make("Svoyi-Social-Core-2.5.3-QA","eu.svoyi.qa.finish253","Свої — Social Core 2.5.3",353,"2.5.3-social",True)
report={"version":"2.5.3-social-core","baseline_sha256":hashlib.sha256(BASE.read_bytes()).hexdigest(),"before":before,"after":after,
"tasks":[
"dating and nearby touch targets","dating tab readability","dating large-photo crop","super-like confirmation semantics label",
"housing tabs","housing photo crop","housing action targets","group tabs","group comment action targets","feed comment action targets",
"mail IME resize","mail composer multi-line visibility","mail composer 50dp minimum","hide bottom navigation while typing","hide mail toolbar while typing",
"restore navigation after typing","notification row targets","notification tabs","horizontal strip cleanup","button capitalization cleanup",
"edit field sizing","large media scaling","legacy people route normalization","dating legacy-view normalization","housing favorites route normalization",
"groups mine route normalization","dating profile id fallback from numeric view route","preserve all original click handlers","preserve server permissions and transport","no server/database change"
],"owner_key_used":False,"server_changed":False}
(OUT/"verification.json").write_text(json.dumps(report,ensure_ascii=False,indent=2))
(OUT/"SHA256SUMS.txt").write_text(before["sha256"]+"  "+before["file"]+"\n"+after["sha256"]+"  "+after["file"]+"\n")
print(json.dumps(report,ensure_ascii=False,indent=2))
