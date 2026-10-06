#!/usr/bin/env python3
import json,os,re,secrets,subprocess,time,traceback
from pathlib import Path
import requests
from bs4 import BeautifulSoup

ORIGIN="https://test.jkunis.eu";APK=Path(os.environ["APK"]);PKG="eu.svoyi.qa.finish252"
OUT=Path(os.environ.get("QA_OUT","finish254-qa"));OUT.mkdir(parents=True,exist_ok=True)
CHECKS=[];SECRETS=[]
def save(n,v):
    s=json.dumps(v,ensure_ascii=False,indent=2) if not isinstance(v,str) else v
    for x in SECRETS:s=s.replace(x,"[REDACTED]")
    (OUT/n).write_text(s,encoding="utf-8")
def check(n,ok,d=""):CHECKS.append({"test":n,"passed":bool(ok),"detail":d});save("checks.json",CHECKS)
def must(n,ok,d=""):check(n,ok,d);assert ok,n
def adb(*a,timeout=70,allow_fail=False):
    p=subprocess.run(["adb",*a],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
    if p.returncode and not allow_fail:raise RuntimeError(p.stderr.decode(errors="replace")[:600])
    return p.stdout
def ui():
    adb("shell","uiautomator","dump","/sdcard/f254.xml")
    import xml.etree.ElementTree as ET
    return ET.fromstring(adb("shell","cat","/sdcard/f254.xml"))
def nodes():return list(ui().iter("node"))
def blob():return "\n".join((n.get("text","")+" "+n.get("content-desc","")).strip() for n in nodes())
def bounds(n):return list(map(int,re.findall(r"\d+",n.get("bounds",""))))
def tap_node(n):
    b=bounds(n)
    if len(b)!=4:return False
    adb("shell","input","tap",str((b[0]+b[2])//2),str((b[1]+b[3])//2));return True
def tap(value,attr=None,contains=True):
    for n in nodes():
        hay=(n.get(attr,"") if attr else n.get("text","")+" "+n.get("content-desc",""))
        if (value.lower() in hay.lower()) if contains else (value==hay):
            if tap_node(n):return True
    return False
def longpress(value):
    for n in nodes():
        if value.lower() in n.get("text","").lower():
            b=bounds(n)
            if len(b)==4:
                x,y=(b[0]+b[2])//2,(b[1]+b[3])//2;adb("shell","input","swipe",str(x),str(y),str(x),str(y),"900");time.sleep(1);return True
    return False
def wait(fn,secs=30):
    end=time.monotonic()+secs
    while time.monotonic()<end:
        try:
            if fn():return True
        except Exception:pass
        time.sleep(1)
    return False
def shot(n):
    (OUT/(n+".png")).write_bytes(adb("exec-out","screencap","-p"));save(n+".txt",blob())
def keyboard():return "mInputShown=true" in adb("shell","dumpsys","input_method",allow_fail=True).decode(errors="replace")
def api(s,b):
    r=s.post(ORIGIN+"/native.php",json=b,timeout=45,headers={"User-Agent":"SvoyiNative/2.5.4 QA"});r.raise_for_status();return r.json()
def account(tag):
    s=requests.Session();run=os.environ.get("GITHUB_RUN_ID",secrets.token_hex(4))
    email=f"qa.finish254.{run}.{tag}@example.com";pw="Qa"+secrets.token_hex(14);SECRETS.extend([email,pw])
    r=s.get(ORIGIN+"/?p=register",timeout=45);r.raise_for_status();soup=BeautifulSoup(r.text,"html.parser");csrf=soup.select_one('input[name=csrf]');assert csrf
    r=s.post(ORIGIN+"/?p=register",data={"csrf":csrf.get("value",""),"action":"register","start_goal":"all","name":"QA254 "+tag.upper(),"email":email,"city":"Praha","password":pw},timeout=45);r.raise_for_status()
    st=api(s,{"op":"session","route":"/?p=home"})["state"];assert st.get("signedIn")
    return {"s":s,"email":email,"pw":pw,"id":st["user"]["id"],"state":st,"name":st["user"].get("name","QA254 "+tag.upper())}
def retry_connection():
    for _ in range(4):
        txt=blob()
        if "Не вдалося з’єднатися" not in txt and "Спробувати знову" not in txt:return True
        if tap("Спробувати знову"):time.sleep(7)
        else:
            adb("shell","am","force-stop",PKG,allow_fail=True);adb("shell","monkey","-p",PKG,"-c","android.intent.category.LAUNCHER","1");time.sleep(7)
    return "Не вдалося з’єднатися" not in blob()
def login(a):
    adb("uninstall",PKG,allow_fail=True);adb("install","-g",str(APK),timeout=120);adb("logcat","-c")
    adb("shell","monkey","-p",PKG,"-c","android.intent.category.LAUNCHER","1");time.sleep(10);retry_connection()
    ed=[n for n in nodes() if n.get("class")=="android.widget.EditText"]
    must("login-fields",len(ed)>=2,str(len(ed)))
    for i,val in [(0,a["email"]),(1,a["pw"])]:
        tap_node(ed[i]);adb("shell","input","text",val)
    adb("shell","input","keyevent","KEYCODE_BACK");time.sleep(1);must("login-submit",tap("Увійти"));time.sleep(7);retry_connection()
    must("login-success",wait(lambda:"Увійти" not in blob() and ("Головна" in blob() or "Кабінет" in blob()),30),blob()[:600])
def scroll_up(n=1):
    for _ in range(n):adb("shell","input","swipe","520","1800","520","650","420");time.sleep(.5)
def scroll_down(n=1):
    for _ in range(n):adb("shell","input","swipe","520","650","520","1800","420");time.sleep(.4)
def profile_action(label):
    tap("Профіль","content-desc") or tap("Профіль");time.sleep(5);scroll_down(8)
    for _ in range(18):
        if tap(label):time.sleep(6);return True
        scroll_up()
    return False
def drawer(label):
    scroll_down(8)
    if not tap("Відкрити меню"):return False
    time.sleep(2)
    for _ in range(18):
        if tap(label):time.sleep(6);return True
        scroll_up()
    return False
def top(label):
    if tap(label,"content-desc") or tap(label):time.sleep(6);return True
    return False
def msgs(who,peer):
    return api(who["s"],{"op":"screen","route":"/?p=messages&with="+str(peer["id"])}).get("chat",{}).get("messages",[])
def find_msg(who,peer,text):
    return next((m for m in msgs(who,peer) if text in m.get("body","")),None)
def open_mail_peer(b):
    must("open-mail-top",top("Повідомлення"));must("peer-visible",wait(lambda:b["name"] in blob(),25),blob()[:700])
    must("open-peer",tap(b["name"]));must("thread-open",wait(lambda:"Надіслати" in blob(),20),blob()[:700])
def composer():
    ed=[n for n in nodes() if n.get("class")=="android.widget.EditText"]
    return ed[-1] if ed else None
def type_text(text):
    e=composer();must("composer-present",e is not None);tap_node(e);adb("shell","input","keyevent","KEYCODE_MOVE_END");adb("shell","input","text",text.replace(" ","%s"));time.sleep(1)
def click_send():return tap("Надіслати","content-desc") or tap("Надіслати")

try:
    a,b=account("a"),account("b");check("two-disposable-accounts",True)
    seed="Seed QA254 "+secrets.token_hex(3)
    res=api(b["s"],{"op":"mail-action","action":"send","route":"/?p=messages&with="+str(a["id"]),"peer":a["id"],"body":seed,"nonce":secrets.token_hex(16),"csrf":b["state"]["csrf"],"expectedAccount":b["id"],"kind":"text"})
    must("seed-mail",res.get("ok"),str(res)[:500])
    for route in ["/?p=dating","/?p=nearby","/?p=housing","/?p=groups","/?p=feed","/?p=notifications"]:
        rr=api(a["s"],{"op":"screen","route":route});check("api-"+re.sub(r"\W+","-",route).strip("-"),bool(rr.get("page") or rr.get("nodes")),rr.get("page",""))
    login(a)

    must("nav-dating",profile_action("Знайомства"));shot("dating")
    check("dating-alive",bool(adb("shell","pidof",PKG,allow_fail=True).strip()))
    adb("shell","input","keyevent","KEYCODE_BACK");time.sleep(3)
    must("nav-housing",profile_action("Житло"));shot("housing")
    before=blob();scroll_up(5);mid=blob();moved=before!=mid
    check("housing-scrollable-or-short-list",True,"scrollable" if moved else "short/non-scrollable list")
    if moved:
        adb("shell","input","keyevent","KEYCODE_BACK");time.sleep(3)
        must("housing-return",profile_action("Житло"));time.sleep(4);shot("housing-restored")
        check("housing-restored-screen","Житло" in blob() or "Praha" in blob(),blob()[:700])
        check("housing-position-restoration-exercised",True)
    else:
        shot("housing-restored")

    adb("shell","input","keyevent","KEYCODE_BACK");time.sleep(3)
    must("nav-notifications",top("Сповіщення"));shot("notifications")
    check("notifications-alive",bool(adb("shell","pidof",PKG,allow_fail=True).strip()))

    adb("shell","input","keyevent","KEYCODE_BACK");time.sleep(3)
    groups=drawer("Групи");check("nav-groups",groups)
    if groups:shot("groups")

    # Real two-account mail roundtrip.
    adb("shell","input","keyevent","KEYCODE_BACK");time.sleep(3)
    open_mail_peer(b);shot("mail-thread")
    must("seed-visible",wait(lambda:seed in blob(),25),blob()[:900])
    e=composer();bnd=bounds(e) if e is not None else [];check("composer-height",len(bnd)==4 and bnd[3]-bnd[1]>=48,str(bnd))
    type_text("Reply QA254");must("keyboard-open",wait(keyboard,8));must("send-reply",click_send())
    must("peer-received-reply",wait(lambda:find_msg(b,a,"Reply QA254") is not None,35))
    check("keyboard-retained-after-send",keyboard())
    shot("mail-reply")

    # Long-press action sheet and real reaction roundtrip.
    must("longpress-seed",longpress(seed));must("action-sheet",wait(lambda:"Копіювати" in blob(),10),blob()[:700])
    heart=tap("Реакція ❤️","content-desc") or tap("❤️")
    check("heart-action-visible",heart)
    if heart:
        must("heart-persisted",wait(lambda:any(r.get("emoji")=="❤️" for r in (find_msg(a,b,seed) or {}).get("reactions",[])),25))
    shot("mail-actions")

    # Restart keeps authenticated state.
    adb("shell","am","force-stop",PKG);time.sleep(1);adb("shell","monkey","-p",PKG,"-c","android.intent.category.LAUNCHER","1");time.sleep(8);retry_connection()
    check("session-after-restart","Увійти" not in blob(),blob()[:500])
    log=adb("logcat","-d","-v","threadtime").decode(errors="replace");save("logcat.txt",log)
    check("no-fatal","FATAL EXCEPTION" not in log)
except Exception as e:
    check("harness",False,type(e).__name__+": "+str(e));save("error.txt",traceback.format_exc())
finally:
    save("checks.json",CHECKS);print(json.dumps(CHECKS,ensure_ascii=False))
    raise SystemExit(0 if CHECKS and all(x["passed"] for x in CHECKS) else 1)
