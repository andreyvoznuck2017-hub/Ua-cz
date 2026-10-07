'use strict';
// Native delta against the exact owner-signed 2.5.6, preserving package and every unrelated ZIP entry.
const fs=require('fs'),path=require('path'),cp=require('child_process'),crypto=require('crypto');
const root=__dirname,work=path.join(root,'.build'),evidence=path.join(root,'evidence');
const home=process.env.SVOYI_TOOLS_ROOT||path.resolve(root,'../home249');
const t=JSON.parse(fs.readFileSync(path.join(home,'tools.json'),'utf8'));
const zip=require(path.join(home,'apk-zip.cjs')),smali=path.join(home,'tools/smali/*');
const baseline=process.env.SVOYI_BASE_APK||path.resolve(root,'../android-finish256/Svoyi-2.5.6.apk');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
function all(dir){return fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?all(path.join(dir,e.name)):[path.join(dir,e.name)]);}
function run(exe,args,name){const r=cp.spawnSync(exe,args,{cwd:root,encoding:'utf8',windowsHide:true,timeout:240000,maxBuffer:15e6});fs.writeFileSync(path.join(evidence,name+'.txt'),(r.stdout||'')+(r.stderr||''));console.log(name+': '+r.status);if(r.status!==0||r.error)throw Error(name+': '+(r.stderr||r.error));return r.stdout;}
function patchMethod(file,sig,transform){let s=fs.readFileSync(file,'utf8');const ms=[...s.matchAll(/^\.method[^\n]*\n[\s\S]*?^\.end method/gm)].filter(m=>m[0].split('\n')[0].trimEnd().endsWith(sig));if(ms.length!==1)throw Error('Method mismatch '+sig);const m=ms[0],updated=transform(m[0]);if(updated===m[0])throw Error('No patch '+sig);fs.writeFileSync(file,s.slice(0,m.index)+updated+s.slice(m.index+m[0].length));}
try{
fs.mkdirSync(evidence,{recursive:true});if(fs.existsSync(work))fs.rmSync(work,{recursive:true});for(const n of ['stub','classes','dex','helpers','smali'])fs.mkdirSync(path.join(work,n),{recursive:true});
const raw=fs.readFileSync(baseline);if(hash(raw)!=='9c63054162928225ec133d8062c7ddec600b7cd92a7df7cfb363e2025ae59bbe')throw Error('Baseline SHA mismatch');const entries=zip.read(raw);
run(t.javac,['-encoding','UTF-8','-source','8','-target','8','-cp',t.android,'-d',path.join(work,'stub'),'Signatures.java'],'compile-signatures');
run(t.javac,['-encoding','UTF-8','-source','8','-target','8','-cp',t.android+path.delimiter+path.join(work,'stub'),'-d',path.join(work,'classes'),'HomeScreen257.java','MailScreen257.java'],'compile-ui');
run(t.java,['-cp',t.d8,'com.android.tools.r8.D8','--min-api','26','--lib',t.android,'--classpath',path.join(work,'stub'),'--output',path.join(work,'dex'),...all(path.join(work,'classes')).filter(p=>p.endsWith('.class'))],'dex-ui');
fs.writeFileSync(path.join(work,'baseline.dex'),entries.find(e=>e.name==='classes3.dex').data);
run(t.java,['-cp',smali,'org.jf.baksmali.Main','disassemble',path.join(work,'baseline.dex'),'-o',path.join(work,'smali')],'decode-baseline');
run(t.java,['-cp',smali,'org.jf.baksmali.Main','disassemble',path.join(work,'dex/classes.dex'),'-o',path.join(work,'helpers')],'decode-ui');
const base=path.join(work,'smali/eu/svoyi/nativeapp');
const original=new Map(all(path.join(work,'smali')).filter(p=>p.endsWith('.smali')).map(p=>[path.relative(path.join(work,'smali'),p),fs.readFileSync(p)]));
patchMethod(path.join(base,'AppFinish252.smali'),'home(Leu/svoyi/nativeapp/NativeWelcome;Ljava/lang/String;Landroid/view/View;Landroid/view/View;Landroid/view/View;)Landroid/view/View;',s=>s.replace('Leu/svoyi/nativeapp/HomeScreen252;->buildSite','Leu/svoyi/nativeapp/HomeScreen257;->buildSite'));
patchMethod(path.join(base,'Batch20Ui.smali'),'remember(Landroid/app/Activity;Lorg/json/JSONObject;)V',s=>s.replace('    return-void','    invoke-static {p0, p1}, Leu/svoyi/nativeapp/MailScreen257;->remember(Landroid/app/Activity;Lorg/json/JSONObject;)V\n    return-void'));
for(const [sig,fn]of [['createInbox(Lorg/json/JSONObject;)V','inbox'],['paintInbox()V','inbox'],['createThread()V','thread'],['updateComposer()V','composer']])patchMethod(path.join(base,'NativeMailScreen.smali'),sig,s=>s.replace(/    return-void/g,'    invoke-static/range {p0 .. p0}, Leu/svoyi/nativeapp/MailScreen257;->'+fn+'(Leu/svoyi/nativeapp/NativeMailScreen;)V\n    return-void'));
for(const file of all(path.join(work,'helpers')).filter(p=>p.endsWith('.smali'))){const rel=path.relative(path.join(work,'helpers'),file),dst=path.join(work,'smali',rel);if(fs.existsSync(dst)){if(fs.readFileSync(file).equals(fs.readFileSync(dst)))continue;if(rel.includes('com'+path.sep+'android'+path.sep+'tools'+path.sep+'r8'+path.sep+'annotations'))continue;throw Error('Unexpected helper collision '+rel);}fs.mkdirSync(path.dirname(dst),{recursive:true});fs.copyFileSync(file,dst);}
const changed=[...original].filter(([p,b])=>!b.equals(fs.readFileSync(path.join(work,'smali',p)))).map(([p])=>p);if(changed.length!==3)throw Error('Unexpected modified class count '+changed.length);
run(t.java,['-cp',smali,'org.jf.smali.Main','assemble','--jobs','1',path.join(work,'smali'),'-o',path.join(work,'classes3.dex')],'assemble-ui');
// Same-length version string update in binary XML; attribute value changes are checked exactly once.
function manifest(input){const b=Buffer.from(input);let ver=0,code=0;for(const enc of ['utf8','utf16le']){const from=Buffer.from('2.5.6',enc),to=Buffer.from('2.5.7',enc);let at=b.indexOf(from);while(at>=0){to.copy(b,at);ver++;at=b.indexOf(from,at+from.length);}}for(let p=8;p<b.length;){const type=b.readUInt16LE(p),head=b.readUInt16LE(p+2),size=b.readUInt32LE(p+4);if(size<8||p+size>b.length)throw Error('Bad XML');if(type===0x102){const start=b.readUInt16LE(p+head+8),step=b.readUInt16LE(p+head+10),count=b.readUInt16LE(p+head+12);for(let i=0;i<count;i++){const a=p+head+start+i*step;if(b[a+15]===0x10&&b.readUInt32LE(a+16)===356){b.writeUInt32LE(357,a+16);code++;}}}p+=size;}if(ver!==1||code!==1)throw Error('Version patch ambiguous '+ver+'/'+code);return b;}
const output=entries.filter(e=>!e.name.startsWith('META-INF/')).map(e=>({...e,data:e.name==='classes3.dex'?fs.readFileSync(path.join(work,'classes3.dex')):e.name==='AndroidManifest.xml'?manifest(e.data):e.data}));
fs.writeFileSync(path.join(root,'unaligned257.apk'),zip.write(output));run(t.zipalign,['-f','4','unaligned257.apk','unsigned257.apk'],'align');
const verify=zip.read(fs.readFileSync(path.join(root,'unsigned257.apk')));for(const e of entries){if(e.name==='classes3.dex'||e.name==='AndroidManifest.xml'||e.name.startsWith('META-INF/'))continue;if(!verify.find(x=>x.name===e.name)?.data.equals(e.data))throw Error('Unrelated entry changed '+e.name);}
const report={version:'2.5.7',versionCode:357,package:'eu.svoyi.qa.finish255',baseSha256:hash(raw),unsignedSha256:hash(fs.readFileSync(path.join(root,'unsigned257.apk'))),modifiedOriginalClasses:changed,sourceSha256:Object.fromEntries(['HomeScreen257.java','MailScreen257.java','build.cjs','Signatures.java'].map(n=>[n,hash(fs.readFileSync(path.join(root,n)))])),serverChanged:false,signingKeyExported:false};fs.writeFileSync(path.join(evidence,'build.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
}catch(e){console.error(e.stack);process.exitCode=1;}
