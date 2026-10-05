#!/usr/bin/env python3
"""Bounded DEX overlay on the checked 2.4.6 candidate, not a full source rebuild.
Wire protocol and stored-draft serialization stay backward compatible. No signing secrets.
"""
import difflib,hashlib,json,os,re,shutil,struct,subprocess,zipfile
from pathlib import Path
ROOT=Path('build247');OUT=Path('candidate247');ROOT.mkdir(exist_ok=True);OUT.mkdir(exist_ok=True)
APK=Path('baseline246/Svoyi-2.4.6-unsigned.apk');BASE='d1e0ec9e62519ff5bcc7a717ba3fbec3eaa841ea7f6bbb5aadeea4672e14a9de'
assert hashlib.sha256(APK.read_bytes()).hexdigest()==BASE,'Wrong 2.4.6 base'
sdk=Path(os.environ['ANDROID_HOME']);android=sdk/'platforms/android-35/android.jar';bt=sorted((sdk/'build-tools').glob('*'),key=lambda p:[int(x) for x in re.findall(r'\d+',p.name)])[-1]
def run(*a):subprocess.run([str(x) for x in a],check=True)
for d in ['stub','classes','dex','smali','helper']:(ROOT/d).mkdir(exist_ok=True)
(ROOT/'Signatures.java').write_text('''package eu.svoyi.nativeapp;
import android.app.*;import android.os.*;import android.widget.*;import android.text.*;import android.view.*;import org.json.*;
class NativeMailScreen {Activity activity;EditText input;String replyPrefix,replySender;JSONObject partner;int account;boolean canSend,sending,staging,loadingDraft,failedSend;long draftRevision,lastTyping;LinearLayout replyRow;ThemePalette theme;Handler ui;Runnable draftSaver,typingStop;boolean alive(){return false;}JSONObject currentMessage(JSONObject j){return null;}void status(String s,boolean b){}void paintReply(){}void updateComposer(){}public void saveDraft(){}void typing(boolean b){}View icon(String k,String d,Runnable r){return null;}}
class ThemePalette {int field,accent,muted;}
class NativeMailPresentation {static String quote(String s){return null;}}
class NativeMailPolicy {static int sender(JSONObject j){return 0;}}
class NativeMailTextFilter implements InputFilter {NativeMailTextFilter(int n,Runnable r){}static int count(CharSequence s){return 0;}public CharSequence filter(CharSequence s,int a,int b,Spanned d,int c,int e){return null;}}
class RichMessage {static Result parse(String s){return null;}static class Result {String text;}}
''')
run('javac','-source','8','-target','8','-cp',android,'-d',ROOT/'stub',ROOT/'Signatures.java')
run('javac','-source','8','-target','8','-cp',str(android)+os.pathsep+str(ROOT/'stub'),'-d',ROOT/'classes','mail-compose247/MailCompose247.java')
classes=list((ROOT/'classes').rglob('*.class'));assert classes and all(p.name.startswith('MailCompose247') for p in classes)
run(bt/'d8','--min-api','26','--lib',android,'--classpath',ROOT/'stub','--output',ROOT/'dex',*classes)
z=zipfile.ZipFile(APK);(ROOT/'original.dex').write_bytes(z.read('classes3.dex'));run('baksmali','disassemble',ROOT/'original.dex','-o',ROOT/'smali');run('baksmali','disassemble',ROOT/'dex/classes.dex','-o',ROOT/'helper')
base=ROOT/'smali/eu/svoyi/nativeapp';before={str(p.relative_to(ROOT/'smali')):p.read_bytes() for p in (ROOT/'smali').rglob('*.smali')};changes=[]
def change(file,sig,fn):
 p=base/file;s=p.read_text();ms=[m for m in re.finditer(r'(?ms)^\.method[^\n]*\n.*?^\.end method',s) if m.group().splitlines()[0].endswith(sig)];assert len(ms)==1,(file,sig,len(ms));m=ms[0];old=m.group();new=fn(old);assert old!=new
 p.write_text(s[:m.start()]+new+s[m.end():]);changes.append({'class':file,'method':sig,'old':hashlib.sha256(old.encode()).hexdigest(),'new':hashlib.sha256(new.encode()).hexdigest()})
def delegate(helper,registers,params,types):
 def f(old):return old.splitlines()[0]+'\n    .locals '+str(registers)+'\n    invoke-static/range {'+params+'}, Leu/svoyi/nativeapp/MailCompose247;->'+helper+'('+types+')V\n    return-void\n.end method'
 return f
T='Leu/svoyi/nativeapp/NativeMailScreen;'
change('NativeMailScreen.smali','replyToTextOwner246(Lorg/json/JSONObject;Ljava/lang/String;)V',delegate('reply',0,'p0 .. p2',T+'Lorg/json/JSONObject;Ljava/lang/String;'))
change('NativeMailScreen.smali','lambda$paintReply$54()V',delegate('cancel',0,'p0 .. p0',T))
change('NativeMailScreen.smali','paintReply()V',delegate('paint',0,'p0 .. p0',T))
# The original watcher assumed the quote existed in editable text. Preserve its revision,
# delayed persistence and typing behavior while retaining the now-separate quote context.
change('NativeMailScreen$3.smali','onTextChanged(Ljava/lang/CharSequence;III)V',lambda old:old.splitlines()[0]+'''\n    .locals 1
    iget-object v0, p0, Leu/svoyi/nativeapp/NativeMailScreen$3;->this$0:Leu/svoyi/nativeapp/NativeMailScreen;
    invoke-static {v0,p1}, Leu/svoyi/nativeapp/MailCompose247;->changed(Leu/svoyi/nativeapp/NativeMailScreen;Ljava/lang/CharSequence;)V
    return-void
.end method''')
# Only read-only wire/draft boundaries receive prefix+text. Formatting/selection stays
# on the real editable content and therefore keeps correct cursor indexes.
def wire(old):
 pat=r'(iget-object (v\d+|p\d+), (v\d+|p\d+), Leu/svoyi/nativeapp/NativeMailScreen;->input:Landroid/widget/EditText;\s*)invoke-virtual \{\2\}, Landroid/widget/EditText;->getText\(\)Landroid/text/Editable;'
 new,n=re.subn(pat,lambda m:m.group(1)+'invoke-static/range {'+m.group(3)+' .. '+m.group(3)+'}, Leu/svoyi/nativeapp/MailCompose247;->wire('+T+')Landroid/text/Editable;',old)
 assert n>0,old.splitlines()[0];return new
wire_sigs=['saveDraft()V','send(Z)V','lambda$send$51(Lorg/json/JSONObject;JLjava/lang/String;Ljava/lang/String;Ljava/lang/String;Lorg/json/JSONObject;Lorg/json/JSONObject;)V','retryFailedSend()V','lambda$retryFailedSend$55(Landroid/content/DialogInterface;I)V','previewMessage()V','updateComposer()V','priority()V','record(Ljava/lang/String;)V']
for sig in wire_sigs:change('NativeMailScreen.smali',sig,wire)
# Install only after original createThread() has restored a persisted full wire draft.
def append_owned(old,helper,newname):
 signature=old.splitlines()[0].split()[-1];name=signature.split('(')[0];renamed=old.replace(signature,newname+signature[len(name):],1)
 return renamed+'\n\n'+old.splitlines()[0]+'\n    .locals 0\n    invoke-virtual {p0}, '+T+'->'+newname+'()V\n    invoke-static {p0}, Leu/svoyi/nativeapp/MailCompose247;->'+helper+'('+T+')V\n    return-void\n.end method'
change('NativeMailScreen.smali','createThread()V',lambda old:append_owned(old,'attached','createThreadOwner247'))
# Normalize only the branch that explicitly loaded a newer serialized draft after send.
send_sig=wire_sigs[2]
def restored_receipt(old):
 start=old.index('Leu/svoyi/nativeapp/NativeMailPresentation;->leadingQuote(')
 m=re.search(r'invoke-virtual(?:/range)? \{([^}]+)\}, Leu/svoyi/nativeapp/NativeMailScreen;->paintReply\(\)V',old[start:]);assert m
 owner=m.group(1).split(' .. ')[0];a=start+m.start();b=start+m.end()
 return old[:a]+'invoke-static/range {'+owner+' .. '+owner+'}, Leu/svoyi/nativeapp/MailCompose247;->restored('+T+')V'+old[b:]
change('NativeMailScreen.smali',send_sig,restored_receipt)
# Keep original editing/save/version-conflict logic. Only adjust the shown dialog with tagged editor.
change('NativeMailScreen.smali','show(Landroid/app/AlertDialog;)V',lambda old:old[:old.rfind('    return-void')]+'    invoke-static/range {p0 .. p1}, Leu/svoyi/nativeapp/MailCompose247;->dialog('+T+'Landroid/app/AlertDialog;)V\n'+old[old.rfind('    return-void'):])
aliases={};reuse=set();helpers=list((ROOT/'helper').rglob('*.smali'))
for p in helpers:
 dest=ROOT/'smali'/p.relative_to(ROOT/'helper')
 if dest.exists():
  if dest.read_bytes()==p.read_bytes():reuse.add(p);continue
  assert '$$ExternalSynthetic' in p.name or 'com/android/tools/r8/annotations' in str(p),'Unexpected helper collision'
  desc=re.search(r'(?m)^\.class[^\n]* (L[^;]+;)',p.read_text()).group(1);aliases[desc]=desc[:-1]+'_Compose247;'
for p in helpers:
 if p in reuse:continue
 s=p.read_text();desc=re.search(r'(?m)^\.class[^\n]* (L[^;]+;)',s).group(1)
 for a,b in aliases.items():s=s.replace(a,b)
 dest=ROOT/'smali'/(aliases.get(desc,desc)[1:-1]+'.smali');assert not dest.exists();dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(s)
changed=[n for n,b in before.items() if (ROOT/'smali'/n).read_bytes()!=b];assert set(changed)=={'eu/svoyi/nativeapp/NativeMailScreen.smali','eu/svoyi/nativeapp/NativeMailScreen$3.smali'},changed
for name in ['NativeImage.smali','NativeImageLoad.smali','MailActions244.smali','MailCompose246.smali','MainActivity.smali']:
 n='eu/svoyi/nativeapp/'+name;assert before[n]==(ROOT/'smali'/n).read_bytes(),name
run('smali','assemble',ROOT/'smali','-o',ROOT/'classes3.dex')
# Manifest serialization is unchanged except versionName and versionCode, package is preserved.
code=Path('mail-next244/build.py').read_text();start=code.index('def read8(');end=code.index('preserved=[]',start)
fragment=code[start:end].replace('2.4.3-stability','2.4.6-compose').replace('2.4.4-mail-actions','2.4.7-quote-editor').replace('val==343','val==346').replace('off+16,344','off+16,347')
exec(compile(fragment,'manifest-version-only','exec'))
preserved=[]
with zipfile.ZipFile(ROOT/'unsigned.apk','w') as out:
 for i in z.infolist():
  if i.filename.startswith('META-INF/'):continue
  data=z.read(i.filename)
  if i.filename=='classes3.dex':data=(ROOT/'classes3.dex').read_bytes()
  elif i.filename=='AndroidManifest.xml':data=manifest
  else:preserved.append({'path':i.filename,'sha256':hashlib.sha256(data).hexdigest()})
  out.writestr(i,data)
run(bt/'zipalign','-f','4',ROOT/'unsigned.apk',OUT/'Svoyi-2.4.7-unsigned.apk');shutil.copy2(bt/'lib/apksigner.jar',OUT/'apksigner.jar')
(OUT/'manifest.json').write_text(json.dumps({'version':'2.4.7-quote-editor','versionCode':347,'package':'eu.svoyi.nativeapp','baseline246_sha256':BASE,'unsigned_sha256':hashlib.sha256((OUT/'Svoyi-2.4.7-unsigned.apk').read_bytes()).hexdigest(),'modified_methods':changes,'modified_original_classes':changed,'unchanged_original_classes':len(before)-len(changed),'imagefix245_preserved':True,'fileLifecycle246_preserved':True,'full_gradle_build':False,'server_changes':False,'private_signing_material_included':False,'compile_stubs_included':False,'preserved_entries':preserved},indent=2))
for n in changed:(OUT/Path(n).name).write_bytes((ROOT/'smali'/n).read_bytes())
shutil.copytree('mail-compose247',OUT/'source',dirs_exist_ok=True)
print('2.4.7 unsigned candidate built with wire serialization and previous image fix preserved')
