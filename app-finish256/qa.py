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
OUT=Path(os.environ.get("QA_OUT","finish256-qa"));OUT.mkdir(parents=True,exist_ok=True)
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
    adb("shell","uiautomator","dump","/sdcard/f256.xml")
    import xml.etree.ElementTree as ET
    return ET.fromstring(adb("shell","cat","/sdcard/f256.xml"))
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
    if keyboard():adb("shell","input","keyevent","KEYCODE_BACK");time.sleep(.8)
def api(session,body):
    r=session.post(ORIGIN+"/native.php",json=body,timeout=45,headers={"User-Agent":"SvoyiNative/2.5.6 QA"})
    r.raise_for_status();return r.json()

def account(tag):
    s=requests.Session();run=os.environ.get("GITHUB_RUN_ID",secrets.token_hex(4))+"."+os.environ.get("QA_API","36")
    email=f"qa.finish256.{run}.{tag}@example.com";pw="Qa"+secrets.token_hex(14);SECRETS.extend([email,pw])
    r=s.get(ORIGIN+"/?p=register",timeout=45);r.raise_for_status()
    soup=BeautifulSoup(r.text,"html.parser");csrf=soup.select_one('input[name=csrf]');assert csrf
    r=s.post(ORIGIN+"/?p=register",data={"csrf":csrf.get("value",""),"action":"register","start_goal":"all","name":"QA256 "+tag.upper(),"email":email,"city":"Praha","password":pw},timeout=45);r.raise_for_status()
    st=api(s,{"op":"session","route":"/?p=home"})["state"];assert st.get("signedIn")
    SECRETS.append(st.get("csrf",""))
    return {"s":s,"email":email,"pw":pw,"id":st["user"]["id"],"name":st["user"].get("name","QA256 "+tag.upper()),"state":st}

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
    adb("uninstall",PKG,allow_fail=True);adb("install","-g",str(apk),timeout=120);adb("logcat","-c")
    adb("shell","monkey","-p",PKG,"-c","android.intent.category.LAUNCHER","1");time.sleep(9);retry_connection()
    ed=[n for n in nodes() if n.get("class")=="android.widget.EditText"]
    must("login-fields-"+apk.stem,len(ed)>=2,str(len(ed)))
    for i,val in [(0,a["email"]),(1,a["pw"])]:
        hide_keyboard()
        current=[n for n in nodes() if n.get("class")=="android.widget.EditText"]
        tap_node(current[i]);time.sleep(.5);adb("shell","input","text",val);time.sleep(.3)
        current=[n for n in nodes() if n.get("class")=="android.widget.EditText"]
        must("login-field-value-"+str(i),current[i].get("text","")==val if i==0 else len(current[i].get("text",""))==len(val))
    hide_keyboard();must("login-submit-"+apk.stem,tap("Увійти"));time.sleep(7);retry_connection()
    must("login-success-"+apk.stem,wait(lambda:"Увійти" not in blob() and ("Головна" in blob() or "Кабінет" in blob()),30),blob()[:700])

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
    textfile=Path("/tmp/qa256.txt");textfile.write_text("Svoyi 2.5.6 real attachment roundtrip\n",encoding="utf-8")
    photo=Path("/tmp/qa256.png");im=Image.new("RGB",(360,240),(235,240,248));ImageDraw.Draw(im).text((65,110),"SVOYI QA256 PHOTO",fill=(25,45,70));im.save(photo)
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
    d.text((18,18),"ДО — 2.5.4",fill="black");d.text((a.width+18,18),"ПІСЛЯ — 2.5.6",fill="black");d.text((18,52),title,fill="black")
    canvas.save(OUT/out)

try:
    a,b=account("a"),account("b");check("two-disposable-accounts",True)
    seed="SeedQA256-"+secrets.token_hex(3)
    res=api(b["s"],{"op":"mail-action","action":"send","route":"/?p=messages&with="+str(a["id"]),"peer":a["id"],"body":seed,"nonce":secrets.token_hex(16),"csrf":b["state"]["csrf"],"expectedAccount":b["id"],"kind":"text"})
    must("seed-message",res.get("ok"),str(res)[:700]);seedid=res["message"]["id"]

    if os.environ.get("QA_MODE") == "remaining":
        install_login(APK,a)
    else:
        install_login(BEFORE,a)
        if os.environ.get("QA_API")=="36":
            open_thread(b);enter("UpgradeDraft256");hide_keyboard();time.sleep(1)
        adb("shell","am","force-stop",PKG)
        result=adb("install","-r",str(APK),timeout=120).decode()
        must("same-key-update-255-to-256","Success" in result,result)
        adb("shell","monkey","-p",PKG,"-c","android.intent.category.LAUNCHER","1");time.sleep(8);retry_connection()
        must("upgrade-keeps-session","Увійти" not in blob())
        must("installed-version-256","versionName=2.5.6" in adb("shell","dumpsys","package",PKG).decode())
        open_thread(b)
        if os.environ.get("QA_API")=="36":
            must("upgrade-keeps-draft",current_input()=="UpgradeDraft256",current_input());clear_current()
        must("seed-visible",wait(lambda:seed in blob(),20));shot("mail-thread")
    
        c=composer_node();cb=bounds(c) if c is not None else []
        must("composer-min-height",len(cb)==4 and cb[3]-cb[1]>=48,str(cb))
    
        if os.environ.get("QA_MODE") == "sections":
            send_text("ReleaseSmoke256",a,b)
        else:
            # Quoted reply is sent through UI and independently read by peer B.
            action(seedid);must("reply-action",tap("Відповісти","content-desc") or tap("Відповісти"))
            must("quote-preview",wait(lambda:"Скасувати відповідь цитатою" in blob(),10),blob()[:800])
            must("reply-keyboard",wait(keyboard,8));enter("QuoteReply256")
            must("reply-send",tap("Надіслати","content-desc") or tap("Надіслати"))
            must("reply-peer-visible",wait(lambda:bool(find_msg(b,a,text="QuoteReply256")),35))
            reply=find_msg(b,a,text="QuoteReply256")
            must("quote-wire-kept","[quote]" in reply.get("body","") and seed in reply.get("body",""),reply.get("body","")[:500])
            must("keyboard-stays-after-reply",keyboard());shot("quote-reply")
        
            # Real document + real photo attachment picker roundtrip.
            textfile,photo=push_files()
            attachment_case(textfile,a,b,"file")
            attachment_case(photo,a,b,"photo")
        
            # UI edit and delete for own message.
            clear_current();hide_keyboard();edit=send_text("EditTarget256",a,b);mid=edit["id"]
            action(mid);must("edit-action",tap("Редагувати","content-desc") or tap("Редагувати"))
            must("edit-dialog",wait(lambda:"Редагувати повідомлення" in blob(),10),blob()[:800])
            enter("Edited256",clear=True);hide_keyboard();must("edit-save",tap("Зберегти"))
            must("edit-peer-updated",wait(lambda:find_msg(b,a,mid=mid).get("body")=="Edited256",30))
            must("edit-timestamp",bool(find_msg(b,a,mid=mid).get("editedAt")));shot("edited")
        
            action(mid);must("delete-action",tap("Видалити для обох","content-desc") or tap("Видалити для обох"))
            must("delete-confirm-dialog",wait(lambda:"Видалити для обох?" in blob(),8))
            must("delete-cancel",tap("Скасувати"));must("delete-cancel-keeps-message",not find_msg(b,a,mid=mid).get("deleted"))
            action(mid);must("delete-action-again",tap("Видалити для обох","content-desc") or tap("Видалити для обох"))
            must("delete-dialog-present-again",wait(lambda:"Видалити для обох?" in blob(),8))
            shot("delete-confirmation")
            must("delete-confirm",tap("android:id/button1","resource-id",contains=False))
            # The server may return a deleted tombstone or omit the deleted message entirely.
            must("delete-peer-updated",wait(lambda:(lambda m:(not m) or bool(m.get("deleted")))(find_msg(b,a,mid=mid)),30))
            shot("deleted")
        
            # Picker cancellation and draft persistence.
            clear_current();enter("Draft256");hide_keyboard()
            opened=tap("Фото та файли","content-desc") or tap("Фото та файли") or tap("Фото, файли, голос","content-desc")
            must("draft-picker-open",opened);time.sleep(1.5)
            if "Фото або файл" in blob():tap("Фото або файл");time.sleep(2)
            adb("shell","input","keyevent","KEYCODE_BACK");must("draft-picker-return",wait(lambda:"Надіслати" in blob(),15))
            must("draft-preserved-after-picker",current_input()=="Draft256",current_input())
            shot("draft-after-picker")
            adb("shell","am","force-stop",PKG);time.sleep(1);adb("shell","monkey","-p",PKG,"-c","android.intent.category.LAUNCHER","1");time.sleep(8);retry_connection()
            must("session-after-restart","Увійти" not in blob(),blob()[:500]);open_thread(b)
            must("draft-after-restart",wait(lambda:current_input()=="Draft256",20),current_input())
        
            # Flush the last character immediately on navigation, before the 450ms debounce.
            c=composer_node();tap_node(c);time.sleep(.5)
            back=next(n for n in nodes() if n.get("content-desc")=="Повернутися до діалогів")
            x1,y1,x2,y2=bounds(back)
            adb("shell","input text X; input tap %d %d"%((x1+x2)//2,(y1+y2)//2))
            must("draft-navigation-left-thread",wait(lambda:"Повернутися до діалогів" not in blob(),20))
            open_thread(b)
            must("draft-keeps-last-character-on-navigation",wait(lambda:current_input()=="Draft256X",15),current_input())
            shot("draft-after-navigation")
            c=composer_node();tap_node(c);time.sleep(.5)
            adb("shell","input text Y; am start -n "+PKG+"/eu.svoyi.nativeapp.MainActivity -a android.intent.action.VIEW -d https://test.jkunis.eu/?native=settings --activity-single-top")
            must("settings-open",wait(lambda:"Налаштування" in blob(),15))
            hide_keyboard();adb("shell","input","keyevent","KEYCODE_BACK")
            must("return-from-settings",wait(lambda:"Надіслати" in blob(),20))
            must("draft-keeps-last-character-on-settings",wait(lambda:current_input()=="Draft256XY",10),current_input())
        
        
    # Open the actual native sections and inspect matching server models.
    routes=[("home","Головна"),("profile","Кабінет"),("groups","Групи"),
            ("feed","Спільнота"),("dating","Знайомства"),("nearby","поруч"),
            ("housing","Житло"),("events","Події"),("notifications","Сповіщення")]
    if os.environ.get("QA_MODE")=="remaining":routes=routes[4:]
    for page,title in routes:
        route="/?p="+page
        rr=api(a["s"],{"op":"screen","route":route,"nativeScreens":["catalog","detail","housing","groups","dating","form-drafts","shop","mail","home-previews","profile-sections","profile-tools","profile-wall"]})
        must("api-"+page,rr.get("page")==page,rr.get("page",""))
        save("model-"+page+".json",rr)
        hide_keyboard()
        adb("shell","am","start","-n",PKG+"/eu.svoyi.nativeapp.MainActivity","-a","android.intent.action.VIEW","-d",ORIGIN+route,"--activity-single-top")
        time.sleep(4);retry_connection();wait(lambda:"Завантаження…" not in blob(),20)
        text=blob();must("native-"+page,"Увійти" not in text and "Не вдалося" not in text,text[:900])
        must("native-visible-"+page,title.lower() in text.lower(),text[:900])
        shot("section-"+page)
        if page=="dating":
            before=rr["dating"]["items"]
            must("dating-has-server-items",len(before)>1)
            def hero():
                found=[n for n in nodes() if n.get("content-desc","").startswith("Відкрити анкету:") and n.get("clickable")=="true"]
                return max(found,key=lambda n:(bounds(n)[2]-bounds(n)[0])*(bounds(n)[3]-bounds(n)[1])) if found else None
            h=hero();must("dating-card-visible",h is not None)
            desc=h.get("content-desc");x1,y1,x2,y2=bounds(h)
            y=int(y1+(y2-y1)*.35)
            adb("shell","input","swipe",str(int(x1+(x2-x1)*.8)),str(y),str(int(x1+(x2-x1)*.2)),str(y),"350")
            must("dating-swipe-next",wait(lambda:hero() is not None and hero().get("content-desc")!=desc,10))
            h=hero();x1,y1,x2,y2=bounds(h);y=int(y1+(y2-y1)*.35)
            adb("shell","input","swipe",str(int(x1+(x2-x1)*.2)),str(y),str(int(x1+(x2-x1)*.8)),str(y),"350")
            must("dating-swipe-previous",wait(lambda:hero() is not None and hero().get("content-desc")==desc,10))
            after=api(a["s"],{"op":"screen","route":route,"nativeScreens":["dating"]})["dating"]["items"]
            def likes(items):
                return {i["id"]:[b.get("label") for f in i.get("forms",[]) if f.get("datingAction")=="dating_like" for b in f.get("buttons",[])] for i in items}
            must("dating-swipes-do-not-like-or-pass",likes(before)==likes(after))
            tap_node(hero());must("dating-profile-opens",wait(lambda:desc.replace("Відкрити анкету:","Відкрити фото:") in blob(),20))
            shot("dating-profile")
            must("dating-return-button",tap("До знайомств") or tap("До добірки"));must("dating-return-keeps-filters",wait(lambda:hero() is not None and "50 км" in blob(),20))
            shot("dating-catalog-after-return")
            for subtab in ("random","sent"):
                subroute="/?p=dating&tab="+subtab
                submodel=api(a["s"],{"op":"screen","route":subroute,"nativeScreens":["dating"]})
                must("api-dating-"+subtab,submodel.get("page")=="dating" and bool(submodel.get("dating")))
                save("model-dating-"+subtab+".json",submodel)
                adb("shell","am","start","-n",PKG+"/eu.svoyi.nativeapp.MainActivity","-a","android.intent.action.VIEW","-d",shlex.quote(ORIGIN+subroute),"--activity-single-top")
                time.sleep(4);wait(lambda:"Завантаження…" not in blob(),20)
                text=blob();must("native-dating-"+subtab,"Знайомства" in text and "Не вдалося" not in text,text[:900])
                shot("dating-"+subtab)


    for page in ("housing","events"):
        rr=api(a["s"],{"op":"screen","route":"/?p="+page+"&create=1"})
        must("creation-model-"+page,rr.get("page")==page)
        save("model-create-"+page+".json",rr)

    log=adb("logcat","-d","-v","threadtime").decode(errors="replace");save("logcat.txt",log)
    check("no-fatal","FATAL EXCEPTION" not in log)
except Exception as e:
    check("harness",False,type(e).__name__+": "+str(e));save("error.txt",traceback.format_exc())
finally:
    try: shot("final-screen")
    except Exception: pass
    try: save("logcat.txt",adb("logcat","-d","-v","threadtime",allow_fail=True).decode(errors="replace"))
    except Exception: pass
    save("checks.json",CHECKS);print(json.dumps(CHECKS,ensure_ascii=False))
    raise SystemExit(0 if CHECKS and all(x["passed"] for x in CHECKS) else 1)

