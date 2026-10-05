#!/usr/bin/env python3
"""Scoped native 2.4.8 batch on exact 2.4.7. Original signing is deliberately not accessed."""
import difflib,hashlib,json,os,re,shutil,struct,subprocess,zipfile
from pathlib import Path
ROOT=Path('build248');OUT=Path('candidate248');ROOT.mkdir(exist_ok=True);OUT.mkdir(exist_ok=True)
APK=Path('baseline247/Svoyi-2.4.7-unsigned.apk');BASE='8ae3acf1150b6422ec8309e7477c398d7461082e9bda35d00877ffdb08f5af42'
assert hashlib.sha256(APK.read_bytes()).hexdigest()==BASE,'Wrong 2.4.7 baseline'
sdk=Path(os.environ['ANDROID_HOME']);android=sdk/'platforms/android-35/android.jar';bt=sorted((sdk/'build-tools').glob('*'),key=lambda p:[int(x) for x in re.findall(r'\d+',p.name)])[-1]
def run(*a):subprocess.run([str(x) for x in a],check=True)
for d in ['stub','classes','dex','smali','helper']:(ROOT/d).mkdir(exist_ok=True)
(ROOT/'Signatures.java').write_text('''package eu.svoyi.nativeapp;
import android.app.*;import android.content.*;import android.os.*;import android.view.*;import android.widget.*;import org.json.*;import java.util.*;
class ThemePalette {int background,surface,text,muted,accent,border;}
class MainActivity extends Activity {public View batch20Nodes(JSONArray nodes){return null;}}
class NativeWelcome {Activity activity;ThemePalette colors;NativeJobsScreen.Host host;}
class NativeJobsScreen {interface Host {boolean alive();void navigate(String r);View image(String u);}}
class NativeSiteUi {static final class Flow extends ViewGroup {Flow(Context c,int n){super(c);}protected void onLayout(boolean c,int l,int t,int r,int b){}}}
class NativeProfileScreen {Activity activity;ThemePalette colors;List<?> panes;HorizontalScrollView strip;}
class NativeMailPolicy {TreeMap<Integer,JSONObject> messages;int first(){return 0;}}
class NativeMailScreen {Activity activity;ThemePalette theme;LinearLayout root,historySearchRow,composer,list;EditText input,historySearch,search;TextView inboxScope;ScrollView scroll;Button newMessages,retrySend,allInbox;Handler ui;NativeMailPolicy model;ArrayList<Integer> historyMatches;int peer;boolean paused,historyBusy,hasOlder,sending,staging;boolean alive(){return false;}boolean atBottom(){return false;}void loadOlder(){}void jumpMessage(int id){}public void saveDraft(){}void status(String s,boolean b){}void messageTools(JSONObject m){} }
''')
run('javac','-source','8','-target','8','-cp',android,'-d',ROOT/'stub',ROOT/'Signatures.java')
files=[Path('batch20')/n for n in ['Batch20Ui.java','Batch20Mail.java']]
run('javac','-source','8','-target','8','-cp',str(android)+os.pathsep+str(ROOT/'stub'),'-d',ROOT/'classes',*files)
classes=list((ROOT/'classes').rglob('*.class'));assert classes and all(p.name.startswith('Batch20') for p in classes),'Compile signatures leaked'
run(bt/'d8','--min-api','26','--lib',android,'--classpath',ROOT/'stub','--output',ROOT/'dex',*classes)
z=zipfile.ZipFile(APK);(ROOT/'original.dex').write_bytes(z.read('classes3.dex'))
run('baksmali','disassemble',ROOT/'original.dex','-o',ROOT/'smali');run('baksmali','disassemble',ROOT/'dex/classes.dex','-o',ROOT/'helper')
base=ROOT/'smali/eu/svoyi/nativeapp';before={str(p.relative_to(ROOT/'smali')):p.read_bytes() for p in (ROOT/'smali').rglob('*.smali')};changes=[]
def change(file,sig,fn):
 p=base/file;s=p.read_text();ms=[m for m in re.finditer(r'(?ms)^\.method[^\n]*\n.*?^\.end method',s) if m.group().splitlines()[0].endswith(sig)]
 assert len(ms)==1,(file,sig,len(ms));m=ms[0];old=m.group();new=fn(old);assert old!=new
 p.write_text(s[:m.start()]+new+s[m.end():]);changes.append({'class':file,'method':sig,'before':hashlib.sha256(old.encode()).hexdigest(),'after':hashlib.sha256(new.encode()).hexdigest()})
M='Leu/svoyi/nativeapp/MainActivity;';S='Leu/svoyi/nativeapp/NativeMailScreen;';U='Leu/svoyi/nativeapp/Batch20Ui;';B='Leu/svoyi/nativeapp/Batch20Mail;'
def wrapper(file,sig,body):
 name=sig.split('(')[0];newname=name+'Owner248';newsig=newname+sig[len(name):]
 def f(old):return old.replace(sig,newsig,1)+'\n\n'+old.splitlines()[0]+'\n'+body.replace('@OWNER@',newname)+'\n.end method'
 change(file,sig,f)
wrapper('MainActivity.smali','renderContent(Lorg/json/JSONObject;)V','    .locals 1\n    invoke-static {p1}, '+U+'->prepare(Lorg/json/JSONObject;)Lorg/json/JSONObject;\n    move-result-object v0\n    invoke-direct {p0,v0}, '+M+'->@OWNER@(Lorg/json/JSONObject;)V\n    return-void')
change('MainActivity.smali','renderContentOwner248(Lorg/json/JSONObject;)V',lambda s:s.replace('Leu/svoyi/nativeapp/NativeSiteUi;->remember','Leu/svoyi/nativeapp/Batch20Ui;->remember'))
wrapper('MainActivity.smali','navigate(Ljava/lang/String;)V','    .locals 1\n    invoke-static {p1}, '+U+'->route(Ljava/lang/String;)Ljava/lang/String;\n    move-result-object v0\n    invoke-direct {p0,v0}, '+M+'->@OWNER@(Ljava/lang/String;)V\n    return-void')
wrapper('MainActivity.smali','renderForm(Lorg/json/JSONObject;Ljava/util/function/BooleanSupplier;)Landroid/view/View;','    .locals 1\n    invoke-direct {p0,p1,p2}, '+M+'->@OWNER@(Lorg/json/JSONObject;Ljava/util/function/BooleanSupplier;)Landroid/view/View;\n    move-result-object v0\n    invoke-static {p1,v0}, '+U+'->form(Lorg/json/JSONObject;Landroid/view/View;)Landroid/view/View;\n    move-result-object v0\n    return-object v0')
p=base/'MainActivity.smali';s=p.read_text();assert 'batch20Nodes(' not in s
s+='''
.method public batch20Nodes(Lorg/json/JSONArray;)Landroid/view/View;
    .locals 2
    new-instance v0, Landroid/widget/LinearLayout;
    invoke-direct {v0,p0}, Landroid/widget/LinearLayout;-><init>(Landroid/content/Context;)V
    const/4 v1, 0x1
    invoke-virtual {v0,v1}, Landroid/widget/LinearLayout;->setOrientation(I)V
    const/4 v1, 0x0
    invoke-direct {p0,p1,v0,v1}, Leu/svoyi/nativeapp/MainActivity;->renderNodes(Lorg/json/JSONArray;Landroid/widget/LinearLayout;I)V
    return-object v0
.end method
''';p.write_text(s)
change('NativeSiteUi.smali','home(Leu/svoyi/nativeapp/NativeWelcome;Ljava/lang/String;Landroid/view/View;Landroid/view/View;Landroid/view/View;)Landroid/view/View;',lambda old:old.splitlines()[0]+'\n    .locals 0\n    invoke-static/range {p0 .. p4}, '+U+'->home(Leu/svoyi/nativeapp/NativeWelcome;Ljava/lang/String;Landroid/view/View;Landroid/view/View;Landroid/view/View;)Landroid/view/View;\n    move-result-object p0\n    return-object p0\n.end method')
change('NativeSiteUi$ProfileHeader.smali','onMeasure(II)V',lambda s:s.replace('0x42840000    # 66.0f','0x42d80000    # 108.0f'))
wrapper('NativeProfileScreen.smali','render(Lorg/json/JSONArray;)Landroid/view/View;','    .locals 1\n    invoke-virtual {p0,p1}, Leu/svoyi/nativeapp/NativeProfileScreen;->@OWNER@(Lorg/json/JSONArray;)Landroid/view/View;\n    move-result-object v0\n    invoke-static {p0,v0}, '+U+'->profilePanes(Leu/svoyi/nativeapp/NativeProfileScreen;Landroid/view/View;)Landroid/view/View;\n    move-result-object v0\n    return-object v0')
for sig,helper in [('createThread()V','attached'),('paintInbox()V','inbox'),('updateComposer()V','composerUpdated'),('loadOlder()V','searchUpdated'),('closeHistorySearch()V','searchFailed')]:
 wrapper('NativeMailScreen.smali',sig,'    .locals 0\n    invoke-virtual {p0}, '+S+'->@OWNER@()V\n    invoke-static {p0}, '+B+'->'+helper+'('+S+')V\n    return-void')
wrapper('NativeMailScreen.smali','close()V','    .locals 0\n    invoke-static {p0}, '+B+'->close('+S+')V\n    invoke-virtual {p0}, '+S+'->@OWNER@()V\n    return-void')
wrapper('NativeMailScreen.smali','apply(Lorg/json/JSONObject;ZZ)V','    .locals 0\n    invoke-virtual {p0,p1,p2,p3}, '+S+'->@OWNER@(Lorg/json/JSONObject;ZZ)V\n    invoke-static {p0}, '+B+'->applied('+S+')V\n    return-void')
wrapper('NativeMailScreen.smali','refreshHistorySearch(Z)V','    .locals 0\n    invoke-virtual {p0,p1}, '+S+'->@OWNER@(Z)V\n    invoke-static {p0}, '+B+'->searchUpdated('+S+')V\n    return-void')
wrapper('NativeMailScreen.smali','messageView(Lorg/json/JSONObject;)Landroid/view/View;','    .locals 1\n    invoke-virtual {p0,p1}, '+S+'->@OWNER@(Lorg/json/JSONObject;)Landroid/view/View;\n    move-result-object v0\n    invoke-static {p0,p1,v0}, '+B+'->message('+S+'Lorg/json/JSONObject;Landroid/view/View;)Landroid/view/View;\n    move-result-object v0\n    return-object v0')
wrapper('NativeMailScreen.smali','send(Z)V','    .locals 1\n    invoke-static {p0}, '+B+'->beforeSend('+S+')Z\n    move-result v0\n    if-eqz v0, :done\n    invoke-virtual {p0,p1}, '+S+'->@OWNER@(Z)V\n    :done\n    return-void')
change('NativeMailScreen.smali','lambda$createThread$25()V',lambda old:old.splitlines()[0]+'\n    .locals 0\n    invoke-static {p0}, '+B+'->viewportBottom('+S+')V\n    return-void\n.end method')
# Namespace only new synthetic helpers, never overwrite an existing implementation.
aliases={};reuse=set();helpers=list((ROOT/'helper').rglob('*.smali'))
for p in helpers:
 dest=ROOT/'smali'/p.relative_to(ROOT/'helper')
 if dest.exists():
  if dest.read_bytes()==p.read_bytes():reuse.add(p);continue
  assert '$$ExternalSynthetic' in p.name or 'com/android/tools/r8/annotations' in str(p),'Unexpected collision'
  desc=re.search(r'(?m)^\.class[^\n]* (L[^;]+;)',p.read_text()).group(1);aliases[desc]=desc[:-1]+'_Batch248;'
for p in helpers:
 if p in reuse:continue
 s=p.read_text();desc=re.search(r'(?m)^\.class[^\n]* (L[^;]+;)',s).group(1)
 for a,b in aliases.items():s=s.replace(a,b)
 dest=ROOT/'smali'/(aliases.get(desc,desc)[1:-1]+'.smali');assert not dest.exists();dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(s)
changed=[n for n,data in before.items() if (ROOT/'smali'/n).read_bytes()!=data]
allowed={'eu/svoyi/nativeapp/'+n for n in ['MainActivity.smali','NativeSiteUi.smali','NativeSiteUi$ProfileHeader.smali','NativeProfileScreen.smali','NativeMailScreen.smali']};assert set(changed)==allowed,changed
for prefix in ['NativeImage','NativeImageLoad','MailCompose246','MailCompose247','MailActions244','ChatAttachmentStore','NativeMailRecorder','NativeMailVideoRecorder','NativeMailStaging']:
 for n,data in before.items():
  if Path(n).name.startswith(prefix):assert data==(ROOT/'smali'/n).read_bytes(),n
run('smali','assemble',ROOT/'smali','-o',ROOT/'classes3.dex')
code=Path('mail-next244/build.py').read_text();start=code.index('def read8(');end=code.index('preserved=[]',start)
fragment=code[start:end].replace('2.4.3-stability','2.4.7-quote-editor').replace('2.4.4-mail-actions','2.4.8-batch20').replace('val==343','val==347').replace('off+16,344','off+16,348');exec(compile(fragment,'manifest-version-only','exec'))
preserved=[]
with zipfile.ZipFile(ROOT/'unsigned.apk','w') as out:
 for i in z.infolist():
  if i.filename.startswith('META-INF/'):continue
  data=z.read(i.filename)
  if i.filename=='classes3.dex':data=(ROOT/'classes3.dex').read_bytes()
  elif i.filename=='AndroidManifest.xml':data=manifest
  else:preserved.append({'path':i.filename,'sha256':hashlib.sha256(data).hexdigest()})
  out.writestr(i,data)
run(bt/'zipalign','-f','4',ROOT/'unsigned.apk',OUT/'Svoyi-2.4.8-unsigned.apk');shutil.copy2(bt/'lib/apksigner.jar',OUT/'apksigner.jar')
(OUT/'manifest.json').write_text(json.dumps({'version':'2.4.8-batch20','versionCode':348,'package':'eu.svoyi.nativeapp','baseline247Sha256':BASE,'unsignedSha256':hashlib.sha256((OUT/'Svoyi-2.4.8-unsigned.apk').read_bytes()).hexdigest(),'changedMethods':changes,'changedOriginalClasses':changed,'unchangedOriginalClasses':len(before)-len(changed),'imagefix245Preserved':True,'compose246247Preserved':True,'wireTransportUnchanged':True,'recorderImplementationsUnchanged':True,'fullGradleBuild':False,'privateSigningMaterialIncluded':False,'serverCodeChanged':False,'preservedEntries':preserved},indent=2))
shutil.copytree('batch20',OUT/'source',dirs_exist_ok=True)
for name in changed:(OUT/Path(name).name).write_bytes((ROOT/'smali'/name).read_bytes())
print('2.4.8 unsigned integrated candidate assembled; original key untouched')
