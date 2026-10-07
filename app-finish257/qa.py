#!/usr/bin/env python3
import json,os,re,secrets,subprocess,time,traceback,hashlib,shlex
from pathlib import Path
from urllib.parse import urljoin,urlparse
import requests
from bs4 import BeautifulSoup
from PIL import Image,ImageDraw

ORIGIN="https://test.jkunis.eu"
PKG=os.environ.get("APP_PACKAGE","eu.svoyi.qa.finish255")
APK=Path(os.environ["APK"])
BEFORE=Path(os.environ.get("BEFORE_APK",str(APK)))
OUT=Path(os.environ.get("QA_OUT","finish257-qa"));OUT.mkdir(parents=True,exist_ok=True)
CHECKS=[];SECRETS=[]

def save(name,value):
    s=json.dumps(value,ensure_ascii=False,indent=2) if not isinstance(value,str) else value
    for x in SECRETS:
        if x:s=s.replace(x,"[REDACTED]")
    (OUT/name).write_text(s,encoding="utf-8")
def check(name,ok,detail=""):
    CHECKS.append({"test":name,"passed":bool(ok),"detail":detail});save("checks.json",CHECKS)
def must(name,ok,detail=""):
    check(name,ok,detail)
    if not ok:raise AssertionError(name)
def adb(*args,timeout=80,allow_fail=False):
    p=subprocess.run(["adb",*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
    if p.returncode and not allow_fail:raise RuntimeError("ADB "+p.stderr.decode(errors="replace")[:800])
    return p.stdout
def ui():
    adb("shell","uiautomator","dump","/sdcard/f257.xml")
    import xml.etree.ElementTree as ET
    return ET.fromstring(adb("shell","cat","/sdcard/f257.xml"))
def nodes():return list(ui().iter("node"))
def blob():
    return "\n".join((n.get("text","")+" "+n.get("content-desc","")).strip() for n in nodes())
def bounds(n):return list(map(int,re.findall(r"\d+",n.get("bounds",""))))
def tap_node(n):
    b=bounds(n)
    if len(b)!=4:return False
    adb("shell","input","tap",str((b[0]+b[2])//2),str((b[1]+b[3])//2));return True
def tap(value,attr=None,contains=True,index=0):
    found=[]
    for n in nodes():
        hay=n.get(attr,"") if attr else n.get("text","")+" "+n.get("content-desc","")
        if (value.lower() in hay.lower()) if contains else (value==hay):found.append(n)
    if len(found)<=index:return False
    return tap_node(found[index])
def longpress_desc(value):
    for n in nodes():
        if n.get("content-desc","")==value or value in n.get("content-desc",""):
            b=bounds(n)
            if len(b)==4:
                x,y=(b[0]+b[2])//2,(b[1]+b[3])//2
                adb("shell","input","swipe",str(x),str(y),str(x),str(y),"900");time.sleep(1);return True
    return False
def wait(fn,seconds=30):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        try:
            if fn():return True
        except Exception:pass
        time.sleep(1)
    return False
def shot(name):
    (OUT/(name+".png")).write_bytes(adb("exec-out","screencap","-p"));save(name+".txt",blob())
def keyboard():
    return "mInputShown=true" in adb("shell","dumpsys","input_method",allow_fail=True).decode(errors="replace")
def hide_keyboard():
    visible=keyboard() or any(n.get("package","") in ("com.google.android.inputmethod.latin","com.android.inputmethod.latin") for n in nodes())
    if visible:adb("shell","input","keyevent","KEYCODE_BACK");time.sleep(.8)
def api(session,body):
    r=session.post(ORIGIN+"/native.php",json=body,timeout=45,headers={"User-Agent":"SvoyiNative/2.5.7 QA"})
    r.raise_for_status();return r.json()

def account(tag):
    s=requests.Session();run=os.environ.get("GITHUB_RUN_ID",secrets.token_hex(4))+"."+os.environ.get("QA_API","36")
    email=f"qa.finish257.{run}.{tag}@example.com";pw="Qa"+secrets.token_hex(14);SECRETS.extend([email,pw])
    r=s.get(ORIGIN+"/?p=register",timeout=45);r.raise_for_status()
    soup=BeautifulSoup(r.text,"html.parser");csrf=soup.select_one('input[name=csrf]');assert csrf
    r=s.post(ORIGIN+"/?p=register",data={"csrf":csrf.get("value",""),"action":"register","start_goal":"all","name":"QA257 "+tag.upper(),"email":email,"city":"Praha","password":pw},timeout=45);r.raise_for_status()
    st=api(s,{"op":"session","route":"/?p=home"})["state"];assert st.get("signedIn")
    SECRETS.append(st.get("csrf",""))
    return {"s":s,"email":email,"pw":pw,"id":st["user"]["id"],"name":st["user"].get("name","QA257 "+tag.upper()),"state":st}

def retry_connection():
    for _ in range(4):
        txt=blob()
        if "Не вдалося з’єднатися" not in txt and "Спробувати знову" not in txt:return True
        if tap("Спробувати знову"):time.sleep(7)
        else:
            adb("shell","am","force-stop",PKG,allow_fail=True)
            adb("shell","monkey","-p",PKG,"-c","android.intent.category.LAUNCHER","1");time.sleep(7)
    return "Не вдалося з’єднатися" not in blob()

def install_login(apk,a):
    adb("install","-g",str(apk),timeout=120);adb("logcat","-c")
    adb("shell","monkey","-p",PKG,"-c","android.intent.category.LAUNCHER","1");time.sleep(6)
    for i in range(14):
        ed=[n for n in nodes() if n.get("package")==PKG and n.get("class")=="android.widget.EditText"]
        if len(ed)>=2:break
        adb("shell","input","swipe","500","1600","500","500","250");time.sleep(.3)
    must("login-fields",len(ed)>=2)
    for field,val in [("email",a["email"]),("password",a["pw"])]:
        hide_keyboard()
        target=None
        for _ in range(10):
            ed=[n for n in nodes() if n.get("package")==PKG and n.get("class")=="android.widget.EditText"]
            target=next((n for n in ed if field in n.get("content-desc","").lower() or (field=="password" and n.get("password")=="true")),None)
            if target is not None:break
            adb("shell","input","swipe","500","1550","500","1050","650");time.sleep(.3)
        must("login-field-"+field,target is not None)
        tap_node(target);adb("shell","input","text",val);time.sleep(.4)
    hide_keyboard()
    for i in range(8):
        b=next((n for n in nodes() if n.get("class")=="android.widget.Button" and "Увійти" in n.get("text","")),None)
        if b is not None:tap_node(b);break
        adb("shell","input","swipe","500","1500","500","600","250");time.sleep(.3)
    must("login-success",wait(lambda:("Вітаємо" in blob() or a["name"] in blob()) and "Увійти" not in blob(),35))

def open_thread(peer):
    hide_keyboard()
    if "Повернутися до діалогів" in blob() and peer["name"] in blob():return
    must("open-mail",tap("Повідомлення","content-desc") or tap("Повідомлення"));time.sleep(6)
    must("peer-visible",wait(lambda:peer["name"] in blob(),25),blob()[:900])
    must("open-peer",tap(peer["name"]));must("thread-open",wait(lambda:"Надіслати" in blob(),20),blob()[:900])

def editors():
    return [n for n in nodes() if n.get("class")=="android.widget.EditText"]
def composer_node():
    e=editors()
    if not e:return None
    for n in reversed(e):
        h=(n.get("hint","")+" "+n.get("content-desc","")+" "+n.get("text","")).lower()
        if "повідом" in h or "message" in h or "zpráv" in h:return n
    return e[-1]
def current_input():
    es=editors()
    for n in es:
        if n.get("focused")=="true":return n.get("text","")
    c=composer_node();return "" if c is None else c.get("text","")
def clear_current():
    e=next((n for n in editors() if n.get("focused")=="true"),composer_node())
    must("clear-field-present",e is not None);tap_node(e)
    text=e.get("text","")
    adb("shell","input","keyevent","KEYCODE_MOVE_END")
    if text:adb("shell","input","keyevent",*(["KEYCODE_DEL"]*len(text)))
    time.sleep(.4)
def enter(text,clear=False):
    e=next((n for n in editors() if n.get("focused")=="true"),composer_node())
    must("editor-present",e is not None)
    if e.get("focused")!="true":tap_node(e);time.sleep(.4)
    if clear:clear_current()
    else:adb("shell","input","keyevent","KEYCODE_MOVE_END")
    if text:adb("shell","input","text",text.replace(" ","%s"))
    time.sleep(.5)

def msgs(who,peer):
    return api(who["s"],{"op":"screen","route":"/?p=messages&with="+str(peer["id"])}).get("chat",{}).get("messages",[])
def find_msg(who,peer,text=None,mid=None):
    for m in msgs(who,peer):
        if mid is not None and m.get("id")==mid:return m
        if text is not None and text in m.get("body",""):return m
    return {}
def send_text(text,a,b):
    enter(text);must("send-"+text,tap("Надіслати","content-desc") or tap("Надіслати"))
    must("peer-received-"+text,wait(lambda:bool(find_msg(b,a,text=text)),35))
    return find_msg(b,a,text=text)

def action(mid):
    hide_keyboard();must("longpress-"+str(mid),longpress_desc("Дії повідомлення "+str(mid)))
    must("action-sheet-"+str(mid),wait(lambda:"Копіювати" in blob(),10),blob()[:900])

def push_files():
    textfile=Path("/tmp/qa257.txt");textfile.write_text("Svoyi 2.5.7 real attachment roundtrip\n",encoding="utf-8")
    photo=Path("/tmp/qa257.png");im=Image.new("RGB",(360,240),(235,240,248));ImageDraw.Draw(im).text((65,110),"SVOYI QA257 PHOTO",fill=(25,45,70));im.save(photo)
    for f in [textfile,photo]:adb("push",str(f),"/sdcard/Download/"+f.name)
    return textfile,photo

def pick_file(filename):
    hide_keyboard()
    opened=tap("Фото та файли","content-desc") or tap("Фото та файли") or tap("Фото, файли, голос","content-desc")
    must("attachment-tool-"+filename,opened)
    time.sleep(1.5)
    # Some builds open an intermediate attachment sheet first.
    if "Фото або файл" in blob():
        must("photo-file-choice-"+filename,tap("Фото або файл"))
        time.sleep(2)
    if not wait(lambda:filename in blob(),12):
        tap("Show roots","content-desc") or tap("Показати кореневі папки","content-desc");time.sleep(1)
        tap("Downloads") or tap("Завантаження");time.sleep(2)
    must("picker-has-"+filename,wait(lambda:filename in blob(),15),blob()[:800])
    # Tap the visible filename text, not the DocumentsUI preview accessibility node.
    must("select-"+filename,tap(filename,"text"));must("picker-return-"+filename,wait(lambda:"Надіслати" in blob(),20),blob()[:800])
    must("staged-"+filename,wait(lambda:filename in blob(),15),blob()[:900])

def attachment_url(message):
    a=message.get("attachment")
    if isinstance(a,dict):return a.get("url","")
    if isinstance(a,str):return a
    return message.get("attachmentUrl","") or ""

def attachment_case(path,a,b,label):
    clear_current();hide_keyboard();pick_file(path.name);shot(label+"-staged")
    must(label+"-send",tap("Надіслати","content-desc") or tap("Надіслати"))
    must(label+"-peer-record",wait(lambda:any(m.get("attachmentName")==path.name for m in msgs(b,a)),40))
    m=next(m for m in msgs(b,a) if m.get("attachmentName")==path.name)
    url=attachment_url(m);full=urljoin(ORIGIN,url)
    must(label+"-url",bool(url) and urlparse(full).scheme=="https" and urlparse(full).netloc==urlparse(ORIGIN).netloc,full)
    rr=b["s"].get(full,timeout=30);must(label+"-byte-match",rr.ok and rr.content==path.read_bytes(),str(rr.status_code))
    shot(label+"-sent")

def montage(left,right,out,title):
    a=Image.open(OUT/left).convert("RGB");b=Image.open(OUT/right).convert("RGB")
    h=max(a.height,b.height);canvas=Image.new("RGB",(a.width+b.width,h+90),"white")
    canvas.paste(a,(0,90));canvas.paste(b,(a.width,90));d=ImageDraw.Draw(canvas)
    d.text((18,18),"ДО — 2.5.4",fill="black");d.text((a.width+18,18),"ПІСЛЯ — 2.5.7",fill="black");d.text((18,52),title,fill="black")
    canvas.save(OUT/out)

def route(value):
    adb("shell","am","start","-W","-n",PKG+"/eu.svoyi.nativeapp.MainActivity","-a","android.intent.action.VIEW","-d",shlex.quote(ORIGIN+value),"--activity-single-top")
    time.sleep(3)
    must("route-loaded",wait(lambda:"Завантаження…" not in blob(),25))

def open_thread(peer):
    route("/?p=messages&with="+str(peer["id"]))
    must("thread-open",wait(lambda:"Надіслати" in blob() and peer["name"] in blob(),25))

try:
    a,b=account("a"),account("b")
    seed="QA257-incoming-"+secrets.token_hex(3)
    res=api(b["s"],{"op":"mail-action","action":"send","route":"/?p=messages&with="+str(a["id"]),"peer":a["id"],"body":seed,"nonce":secrets.token_hex(16),"csrf":b["state"]["csrf"],"expectedAccount":b["id"],"kind":"text"})
    must("seed-incoming",res.get("ok"));seedid=res["message"]["id"]
    install_login(BEFORE,a)
    open_thread(b);enter("UpgradeDraft257");hide_keyboard();time.sleep(1)
    result=adb("install","-r",str(APK),timeout=120).decode();must("update-256-to-257","Success" in result,result)
    route("/?p=messages&with="+str(b["id"]))
    must("version-257","versionName=2.5.7" in adb("shell","dumpsys","package",PKG).decode())
    must("session-retained","Увійти" not in blob());must("draft-retained",wait(lambda:current_input()=="UpgradeDraft257",20))
    clear_current();hide_keyboard();must("incoming-rendered",seed in blob());shot("thread-incoming")
    sent=send_text("QA257 outgoing verified",a,b);hide_keyboard();shot("thread-outgoing")
    action(seedid);must("reply-action",tap("Відповісти","content-desc") or tap("Відповісти"));must("quote-visible",wait(lambda:"Скасувати відповідь цитатою" in blob(),10));enter("QA257 quoted reply");must("quote-send",tap("Надіслати","content-desc"));must("quote-received",wait(lambda:bool(find_msg(b,a,text="QA257 quoted reply")),35));must("quote-content",seed in find_msg(b,a,text="QA257 quoted reply").get("body",""));hide_keyboard();shot("quoted-reply")
    edited=send_text("QA257 edit target",a,b);hide_keyboard();action(edited["id"]);must("edit-action",tap("Редагувати","content-desc") or tap("Редагувати"));must("edit-dialog",wait(lambda:"Редагувати повідомлення" in blob(),10));enter("QA257 edited",clear=True);hide_keyboard();must("edit-save",tap("Зберегти"));must("edit-server",wait(lambda:find_msg(b,a,mid=edited["id"]).get("body")=="QA257 edited",30));shot("edited-message")
    textfile,photo=push_files();attachment_case(textfile,a,b,"file");attachment_case(photo,a,b,"photo");hide_keyboard()
    enter("PersistentDraft257");hide_keyboard();route("/?p=home");open_thread(b);must("draft-after-navigation",current_input()=="PersistentDraft257");clear_current();hide_keyboard()
    route("/?p=messages");must("inbox-peer",b["name"] in blob());must("inbox-single-heading",sum(n.get("text")=="Повідомлення" for n in nodes())==2);shot("inbox-populated")
    search=next(n for n in nodes() if n.get("class")=="android.widget.EditText");tap_node(search);adb("shell","input","text","ZZZ-no-match257");hide_keyboard();must("search-empty",wait(lambda:"Нічого не знайдено" in blob(),12));shot("inbox-search-empty");must("search-clear",tap("Очистити пошук діалогів","content-desc"));must("search-restores",wait(lambda:b["name"] in blob(),10))
    route("/?p=home");shot("home-top");seen=blob()
    for i in range(26):
        adb("shell","input","swipe","500","1450","500","900","700");time.sleep(.3);part=blob();seen+="\n"+part
        if i%3==0:shot("home-"+str(i+1))
        if "Відпочинок після дня" in part:break
    for label in ["Активні групи","Розмова в чаті","Дописи спільноти","Свіжі вакансії","Нове житло","Фотобатл","Маркет","Послуги своїх","Корисне для вас","Відпочинок після дня"]:must("home-section-"+label,label in seen)
    route("/?p=home&lang=en");must("english-home",wait(lambda:"Posts" in blob() or "Welcome" in blob() or "Home" in blob(),20));shot("home-english")
    route("/?p=home&lang=uk");route("/?native=settings");shot("theme-settings")
    dark=next((n for n in nodes() if ("Темна" in n.get("content-desc","") or "Українська ніч" in n.get("content-desc","") or "Українська ніч" in n.get("text","")) and n.get("clickable")=="true"),None)
    if dark is not None:
        tap_node(dark);time.sleep(1);route("/?p=home");must("dark-home","Вітаємо" in blob());shot("home-dark");open_thread(b);shot("mail-dark")
    else:check("theme-control",False,"Dark theme not found")
    log=adb("logcat","-d","-b","crash").decode(errors="replace");save("crashes.txt",log);must("no-fatal","FATAL EXCEPTION" not in log)
    # The runner is disposable. Check a fresh install after the data-preserving update tests.
    adb("uninstall",PKG);result=adb("install","-g",str(APK),timeout=120).decode();must("fresh-install-257","Success" in result,result)
    adb("shell","monkey","-p",PKG,"-c","android.intent.category.LAUNCHER","1");time.sleep(5)
    must("fresh-launch-257",wait(lambda:any(n.get("package")==PKG for n in nodes()),20));shot("fresh-install")
except Exception as e:
    check("harness",False,type(e).__name__+": "+str(e));save("error.txt",traceback.format_exc())
finally:
    try:shot("final-screen")
    except Exception:pass
    save("checks.json",CHECKS);print(json.dumps(CHECKS,ensure_ascii=False));raise SystemExit(0 if CHECKS and all(c["passed"] for c in CHECKS) else 1)
