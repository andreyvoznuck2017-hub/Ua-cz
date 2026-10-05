#!/usr/bin/env python3
"""Rebuild only classes3 with javac/D8/smali, preserving other APK entries.
Compile-only signatures are excluded from D8/output. Original QA key is unavailable:
this build deliberately uses separate package eu.svoyi.testapp02, not a fake update.
"""
import base64,hashlib,json,os,re,secrets,shutil,struct,subprocess,zipfile
from pathlib import Path
from cryptography.hazmat.primitives import serialization,hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ROOT=Path('tooling/build');ROOT.mkdir(parents=True,exist_ok=True)
OUT=Path('candidate-output');OUT.mkdir(exist_ok=True)
APK=next(iter(sorted(Path('qa-input').glob('*.apk'))))
assert hashlib.sha256(APK.read_bytes()).hexdigest()=='b719f8a45f47bbc12ef7872d2119100e733cf48f9e4ad8ce27f96310890ca6b8','Wrong baseline APK'
sdk=Path(os.environ['ANDROID_HOME']);bt=sorted((sdk/'build-tools').glob('*'),key=lambda p:[int(x) for x in re.findall(r'\d+',p.name)])[-1]
android=sdk/'platforms/android-35/android.jar'
assert android.exists(), 'Android compile SDK missing'
def cmd(*args,env=None): subprocess.run(list(map(str,args)),check=True,env=env)

stub='''package eu.svoyi.nativeapp;
import android.app.*;import android.content.*;import android.graphics.drawable.*;import android.net.*;import android.view.*;import android.widget.*;import org.json.*;import java.util.function.*;
class ThemePalette {int accent,background,border,error,field,muted,ownBubble,ownText,primaryText,surface,text;boolean dark;String key;}
class NativeWelcome {Activity activity;ThemePalette colors;NativeJobsScreen.Host host;}
class NativeIcons {static Drawable get(Context c,String key,int color){return null;}}
class NativeJobsScreen {interface Host {boolean alive();void navigate(String route);View image(String url);View form(JSONObject model);}}
class NativeProfileContent {Activity activity;ThemePalette colors;Host host;void identity(LinearLayout p,JSONArray n,int d){}void actions(LinearLayout p,JSONArray n){}interface Host {boolean alive();Drawable cover(JSONObject o);View image(String u,boolean a,JSONObject s);void name(TextView v,JSONObject s);void navigate(String r);View nodes(JSONArray n);void photo(String u,JSONObject n);}}
class NativeMailScreen {Activity activity;ThemePalette theme;Host host;LinearLayout root,header,inboxList,composer;ScrollView scroll;EditText search,input;Button allInbox,unreadInbox;TextView inboxScope;View tools;boolean canSend,sending,staging;boolean alive(){return false;}void toggleHistorySearch(){}void threadTools(){}void emoji(){}void record(String k){}void format(){}void composeTools(){}public void acceptAttachment(Uri u){}interface Host {void chooseAttachment(String kind,Consumer<Uri> done);}}
'''
(ROOT/'Signatures.java').write_text(stub)
for path in ['stub-classes','classes','dex','helper-smali','smali']:(ROOT/path).mkdir(exist_ok=True)
cmd('javac','-source','8','-target','8','-cp',android,'-d',ROOT/'stub-classes',ROOT/'Signatures.java')
source=Path('repair/NativeSiteUi.java').read_text().replace('ПРОСУВВАННЯ','ПРОСУВАННЯ')
(ROOT/'NativeSiteUi.java').write_text(source)
cmd('javac','-source','8','-target','8','-cp',str(android)+os.pathsep+str(ROOT/'stub-classes'),'-d',ROOT/'classes',ROOT/'NativeSiteUi.java')
class_files=list((ROOT/'classes').rglob('*.class'))
assert class_files and all(p.name.startswith('NativeSiteUi') for p in class_files),'Compile signature leaked into payload'
cmd(bt/'d8','--min-api','26','--lib',android,'--classpath',ROOT/'stub-classes','--output',ROOT/'dex',*class_files)
z=zipfile.ZipFile(APK);(ROOT/'original.dex').write_bytes(z.read('classes3.dex'))
cmd('baksmali','disassemble',ROOT/'original.dex','-o',ROOT/'smali')
cmd('baksmali','disassemble',ROOT/'dex/classes.dex','-o',ROOT/'helper-smali')
BASE=ROOT/'smali/eu/svoyi/nativeapp';changes=[]
def method(path,signature,transform):
    src=path.read_text();blocks=list(re.finditer(r'(?ms)^\.method[^\n]*\n.*?^\.end method',src));selected=[m for m in blocks if m.group().splitlines()[0].endswith(signature)]
    assert len(selected)==1,(path,signature,len(selected));m=selected[0];old=m.group();new=transform(old);assert new!=old
    path.write_text(src[:m.start()]+new+src[m.end():]);changes.append({'class':path.name,'method':signature,'before':hashlib.sha256(old.encode()).hexdigest(),'after':hashlib.sha256(new.encode()).hexdigest()})

def remember_home(body):
    needle='    .registers 23\n';assert needle in body
    body=body.replace(needle,needle+'\n    invoke-static/range {p0 .. p1}, Leu/svoyi/nativeapp/NativeSiteUi;->remember(Landroid/app/Activity;Lorg/json/JSONObject;)V\n',1)
    match=re.search(r'invoke-direct[^\n]*->welcomeWithPreviews\(\)Landroid/view/View;\n\s+move-result-object v3\n\s+invoke-direct \{v7, v0, v3\}, Leu/svoyi/nativeapp/MainActivity;->add\(Landroid/widget/LinearLayout;Landroid/view/View;\)V',body)
    assert match,'Home insertion point changed';return body[:match.end()]+'\n\n    return-void'+body[match.end():]
method(BASE/'MainActivity.smali','renderContent(Lorg/json/JSONObject;)V',remember_home)
method(BASE/'NativeWelcome.smali','render(Ljava/lang/String;Landroid/view/View;Landroid/view/View;Landroid/view/View;)Landroid/view/View;',lambda old:'.method render(Ljava/lang/String;Landroid/view/View;Landroid/view/View;Landroid/view/View;)Landroid/view/View;\n    .registers 5\n    invoke-static {p0, p1, p2, p3, p4}, Leu/svoyi/nativeapp/NativeSiteUi;->home(Leu/svoyi/nativeapp/NativeWelcome;Ljava/lang/String;Landroid/view/View;Landroid/view/View;Landroid/view/View;)Landroid/view/View;\n    move-result-object p0\n    return-object p0\n.end method')
method(BASE/'NativeProfileContent.smali','header(Lorg/json/JSONObject;Z)Landroid/view/View;',lambda old:'.method header(Lorg/json/JSONObject;Z)Landroid/view/View;\n    .registers 3\n    invoke-static {p0, p1, p2}, Leu/svoyi/nativeapp/NativeSiteUi;->profile(Leu/svoyi/nativeapp/NativeProfileContent;Lorg/json/JSONObject;Z)Landroid/view/View;\n    move-result-object p0\n    return-object p0\n.end method')
for name,helper in [('createInbox(Lorg/json/JSONObject;)V','inbox'),('createThread()V','thread')]:
    def append(old,helper=helper):
        assert old.count('return-void')==1
        return old.replace('    return-void','    invoke-static/range {p0 .. p0}, Leu/svoyi/nativeapp/NativeSiteUi;->'+helper+'(Leu/svoyi/nativeapp/NativeMailScreen;)V\n\n    return-void')
    method(BASE/'NativeMailScreen.smali',name,append)
method(BASE/'NativeMailInboxRow.smali','update(Lorg/json/JSONObject;Ljava/lang/String;Ljava/lang/String;Z)V',lambda old:old.replace('    return-void','    invoke-static/range {p0 .. p1}, Leu/svoyi/nativeapp/NativeSiteUi;->inboxRow(Landroid/widget/LinearLayout;Lorg/json/JSONObject;)V\n\n    return-void'))
for p in (ROOT/'helper-smali').rglob('*.smali'):
    target=ROOT/'smali'/p.relative_to(ROOT/'helper-smali');assert not target.exists();target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
cmd('smali','assemble',ROOT/'smali','-o',ROOT/'classes3.dex')

# Rebuild binary XML pool with unchanged resource indexes and component class names.
def readlen8(d,p):
    n=d[p];p+=1
    if n&128:n=((n&127)<<8)|d[p];p+=1
    return n,p
def readlen16(d,p):
    n=struct.unpack_from('<H',d,p)[0];p+=2
    if n&32768:n=((n&32767)<<16)|struct.unpack_from('<H',d,p)[0];p+=2
    return n,p
def put8(n):return bytes([128|(n>>8),n&255]) if n>=128 else bytes([n])
def put16(n):return struct.pack('<HH',32768|(n>>16),n&65535) if n>=32768 else struct.pack('<H',n)
manifest=z.read('AndroidManifest.xml');chunks=[];pos=8;strings=[]
while pos<len(manifest):
    typ,head,size=struct.unpack_from('<HHI',manifest,pos);raw=bytearray(manifest[pos:pos+size]);chunks.append([typ,head,raw])
    if typ==1:
        pi=len(chunks)-1;count,styles,flags,start,style_start=struct.unpack_from('<5I',raw,8);utf8=bool(flags&256)
        assert styles==0,'Unsupported styled manifest pool'
        for i in range(count):
            q=start+struct.unpack_from('<I',raw,head+i*4)[0]
            if utf8:_,q=readlen8(raw,q);n,q=readlen8(raw,q);s=bytes(raw[q:q+n]).decode('utf8')
            else:n,q=readlen16(raw,q);s=bytes(raw[q:q+2*n]).decode('utf-16-le')
            strings.append(s)
    pos+=size
assert pos==len(manifest)
strings=[s.replace('eu.svoyi.testapp01','eu.svoyi.testapp02').replace('2.4.1-profile02','2.4.2-sitefix01').replace('Свої — тест 2.4.1','Свої — перевірка 2.4.2') for s in strings]
for typ,head,raw in chunks:
    if typ!=0x102:continue
    ns,name,start,step,count,*_=struct.unpack_from('<IIHHHHHH',raw,head)
    for i in range(count):
        off=head+start+i*step;ans,aname,araw,sz,zero,kind,val=struct.unpack_from('<IIIHBBI',raw,off)
        if strings[name]=='manifest' and strings[aname]=='versionCode':struct.pack_into('<I',raw,off+16,342)
        if strings[name]=='application' and strings[aname]=='label' and kind==3:strings[val]='Свої — перевірка 2.4.2'
blob=bytearray();offsets=[]
for s in strings:
    offsets.append(len(blob));u=s.encode('utf-16-le')
    if utf8:b=s.encode('utf8');blob+=put8(len(u)//2)+put8(len(b))+b+b'\0'
    else:blob+=put16(len(u)//2)+u+b'\0\0'
while len(blob)%4:blob.append(0)
start=28+4*len(strings);pool=struct.pack('<HHI5I',1,28,start+len(blob),len(strings),0,flags&~1,start,0)+struct.pack('<'+'I'*len(strings),*offsets)+blob
chunks[pi][2]=pool;payload=b''.join(bytes(raw) for _,_,raw in chunks);newmanifest=struct.pack('<HHI',3,8,8+len(payload))+payload
unsigned=ROOT/'unsigned.apk';preserved=[]
with zipfile.ZipFile(unsigned,'w',zipfile.ZIP_DEFLATED) as target:
    for info in z.infolist():
        if info.filename.startswith('META-INF/'):continue
        value=z.read(info.filename)
        if info.filename=='classes3.dex':value=(ROOT/'classes3.dex').read_bytes()
        elif info.filename=='AndroidManifest.xml':value=newmanifest
        else:preserved.append({'file':info.filename,'sha256':hashlib.sha256(value).hexdigest()})
        target.writestr(info,value)
cmd(bt/'zipalign','-f','4',unsigned,ROOT/'aligned.apk')
password=secrets.token_urlsafe(25);print('::add-mask::'+password)
env=dict(os.environ,QA_SIGNING_PASSWORD=password)
cmd('keytool','-genkeypair','-keystore',ROOT/'site-qa.p12','-storetype','PKCS12','-storepass',password,'-keypass',password,'-alias','siteqa','-keyalg','RSA','-keysize','3072','-validity','3650','-dname','CN=Svoyi Isolated QA 2.4.2',env=env)
final=OUT/'Svoyi-Europe-Android-v2.4.2-Site-Match-QA.apk'
cmd(bt/'apksigner','sign','--ks',ROOT/'site-qa.p12','--ks-key-alias','siteqa','--ks-pass','env:QA_SIGNING_PASSWORD','--out',final,ROOT/'aligned.apk',env=env)
verify=subprocess.check_output([str(bt/'apksigner'),'verify','--verbose','--print-certs',str(final)],text=True);(OUT/'signature-verification.txt').write_text(verify)
# Encrypt private signing material for the local custodian; never upload it in plaintext.
pub=serialization.load_pem_public_key(Path('repair/wrap-public.pem').read_bytes());aes=secrets.token_bytes(32);nonce=secrets.token_bytes(12)
secret=json.dumps({'pkcs12':base64.b64encode((ROOT/'site-qa.p12').read_bytes()).decode(),'password':password}).encode()
cipher=AESGCM(aes).encrypt(nonce,secret,b'Svoyi-QA-sitefix-342')
(OUT/'signing-envelope.json').write_text(json.dumps({'version':1,'wrapped_key':base64.b64encode(pub.encrypt(aes,padding.OAEP(mgf=padding.MGF1(hashes.SHA256()),algorithm=hashes.SHA256(),label=None))).decode(),'nonce':base64.b64encode(nonce).decode(),'ciphertext':base64.b64encode(cipher).decode()}))
(OUT/'change-manifest.json').write_text(json.dumps({'baseline':str(APK),'baseline_sha256':hashlib.sha256(APK.read_bytes()).hexdigest(),'apk_sha256':hashlib.sha256(final.read_bytes()).hexdigest(),'package':'eu.svoyi.testapp02','versionCode':342,'versionName':'2.4.2-sitefix01','new_qa_signer':True,'modified_methods':changes,'preserved_entries':preserved,'full_gradle_build':False,'compile_stubs_included':False,'server_changed':False},indent=2))
shutil.copy2(ROOT/'NativeSiteUi.java',OUT/'NativeSiteUi.java');shutil.copy2('repair/build.py',OUT/'build.py')
print('Built',final,hashlib.sha256(final.read_bytes()).hexdigest())
