#!/usr/bin/env python3
import json,os,re,secrets,subprocess,time,traceback
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from PIL import Image,ImageOps,ImageDraw

ORIGIN="https://test.jkunis.eu"
OUT=Path(os.environ.get("QA_OUT","finish252-qa"));OUT.mkdir(parents=True,exist_ok=True)
CHECKS=[];SECRETS=[]

def save(name,value):
    text=json.dumps(value,ensure_ascii=False,indent=2) if not isinstance(value,str) else value
    for x in SECRETS:
        if x:text=text.replace(x,"[REDACTED]")
    (OUT/name).write_text(text,encoding="utf-8")
def check(name,ok,detail=""):
    CHECKS.append({"test":name,"passed":bool(ok),"detail":detail});save("checks.json",CHECKS)
def adb(*args,timeout=45,allow_fail=False):
    p=subprocess.run(["adb",*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
    if p.returncode and not allow_fail:raise RuntimeError("ADB: "+p.stderr.decode(errors="replace")[:300])
    return p.stdout
def ui():
    adb("shell","uiautomator","dump","/sdcard/f252.xml")
    import xml.etree.ElementTree as ET
    return ET.fromstring(adb("shell","cat","/sdcard/f252.xml"))
def text_blob():
    root=ui();return "\n".join((n.get("text","")+" "+n.get("content-desc","")).strip() for n in root.iter("node"))
def tap(attr,value,contains=False,index=0):
    nodes=[n for n in ui().iter("node") if (value in n.get(attr,"") if contains else n.get(attr,"")==value)]
    if len(nodes)<=index:return False
    nums=list(map(int,re.findall(r"\d+",nodes[index].get("bounds",""))))
    if len(nums)!=4:return False
    x1,y1,x2,y2=nums;adb("shell","input","tap",str((x1+x2)//2),str((y1+y2)//2));return True
def capture(name):
    (OUT/(name+".png")).write_bytes(adb("exec-out","screencap","-p"))
    save(name+".txt",text_blob())
def alive(pkg):return bool(adb("shell","pidof",pkg,allow_fail=True).strip())
def api(s,body):
    r=s.post(ORIGIN+"/native.php",json=body,timeout=45,headers={"User-Agent":"SvoyiNative/2.5.2 QA"})
    r.raise_for_status();return r.json()
def account():
    s=requests.Session();tag=os.environ.get("GITHUB_RUN_ID",secrets.token_hex(4))
    email=f"qa.finish252.{tag}@example.com";pw="Qa"+secrets.token_hex(15);SECRETS.extend([email,pw])
    page=s.get(ORIGIN+"/?p=register",timeout=45);page.raise_for_status();soup=BeautifulSoup(page.text,"html.parser")
    csrf=soup.select_one('input[name=csrf]');assert csrf
    r=s.post(ORIGIN+"/?p=register",data={"csrf":csrf.get("value",""),"action":"register","start_goal":"all","name":"QA Finish252","email":email,"city":"Praha","password":pw},timeout=45);r.raise_for_status()
    st=api(s,{"op":"session","route":"/?p=home"})["state"];assert st.get("signedIn")
    return s,email,pw,st

def login(apk,pkg,email,pw,prefix):
    adb("install","-r","-g",str(apk),timeout=100);adb("logcat","-c");adb("shell","monkey","-p",pkg,"-c","android.intent.category.LAUNCHER","1");time.sleep(11)
    capture(prefix+"-login")
    for attempt in range(3):
        current=text_blob()
        if "Вийти" in current or "Особистий кабінет" in current or "QA Finish252" in current:break
        edits=[n for n in ui().iter("node") if n.get("class","")=="android.widget.EditText"]
        if len(edits)<2:break
        if not tap("class","android.widget.EditText",False,0):break
        adb("shell","input","keyevent","KEYCODE_MOVE_END");adb("shell","input","text",email)
        if not tap("class","android.widget.EditText",False,1):break
        adb("shell","input","keyevent","KEYCODE_MOVE_END");adb("shell","input","text",pw);adb("shell","input","keyevent","KEYCODE_BACK");time.sleep(1)
        if not tap("text","Увійти"):break
        time.sleep(10)
        if "Неправильний email" not in text_blob():break
        time.sleep(2)
    check(prefix+"-login-succeeded","Неправильний email" not in text_blob() and alive(pkg),text_blob()[:500])
    went_home=tap("content-desc","Головна",contains=True) or tap("text","Головна")
    if went_home:time.sleep(8)
    capture(prefix+"-home");check(prefix+"-alive-home",alive(pkg))
def uninstall(pkg):adb("uninstall",pkg,allow_fail=True)
def scroll_top():
    for _ in range(8):
        adb("shell","input","swipe","520","650","520","1850","350");time.sleep(.25)
def tap_scroll(label):
    for _ in range(14):
        if tap("text",label,contains=True) or tap("content-desc",label,contains=True):return True
        adb("shell","input","swipe","520","1850","520","650","450");time.sleep(.6)
    return False

def montage(a,b,out,title):
    ia=Image.open(OUT/a).convert("RGB");ib=Image.open(OUT/b).convert("RGB")
    h=max(ia.height,ib.height);w=ia.width+ib.width
    canvas=Image.new("RGB",(w,h+90),"white");canvas.paste(ia,(0,90));canvas.paste(ib,(ia.width,90))
    d=ImageDraw.Draw(canvas);d.text((20,20),"ДО — 2.4.9",fill="black");d.text((ia.width+20,20),"ПІСЛЯ — 2.5.2",fill="black");d.text((20,50),title,fill="black")
    canvas.save(OUT/out)

try:
    s,email,pw,state=account();check("qa-account",True)
    expected=[
        ("/?p=home",["nodes"]),
        ("/?p=profile",["Особист","profile"]),
        ("/?p=nearby",["поруч","nearby"]),
        ("/?p=dating&tab=likes",["Знайом","dating","подоб"]),
        ("/?p=events&tab=activities",["Актив","activities","Зустріч"]),
        ("/?p=events&create=1",["поді","event"])
    ]
    for route,tokens in expected:
        result=api(s,{"op":"screen","route":route});raw=json.dumps(result,ensure_ascii=False).lower()
        check("api-"+re.sub(r"\W+","-",route).strip("-"),any(str(t).lower() in raw for t in tokens),result.get("page",""))
    before=Path(os.environ["BEFORE_APK"]);final=Path(os.environ["FINAL_APK"])
    login(before,"eu.svoyi.qa.before252",email,pw,"before")
    if tap("content-desc","Профіль",contains=True) or tap("text","Профіль"):
        time.sleep(7);capture("before-account");check("before-profile-nav",True)
    else:
        capture("before-account");check("before-profile-nav",False,"profile tab absent")
    uninstall("eu.svoyi.qa.before252")

    login(final,"eu.svoyi.qa.finish252",email,pw,"after")
    home_text=text_blob()
    check("after-home-site-sections",any(x in home_text for x in ["Дописи","Вакансії","Житло","Свої поруч"]),home_text[:600])
    scroll_top();went_near=tap_scroll("Люди поруч")
    check("nearby-link-clickable",went_near)
    if went_near:
        time.sleep(8);capture("after-nearby");near=text_blob()
        check("nearby-does-not-return-home",any(x in near for x in ["Люди поруч","Знайомства","Поруч","км"]),near[:800])
        check("alive-after-nearby",alive("eu.svoyi.qa.finish252"))
        adb("shell","input","keyevent","KEYCODE_BACK");time.sleep(4)
    if tap("content-desc","Профіль",contains=True) or tap("text","Профіль"):
        time.sleep(8);capture("after-account")
        acc=text_blob()
        check("account-site-match-visible","Особистий кабінет" in acc or "Швидкий доступ" in acc,acc[:800])
        for label in ["Знайомства","Житло","Сповіщення","Безпека"]:
            tap("content-desc","Профіль",contains=True) or tap("text","Профіль");time.sleep(3);scroll_top()
            ok=tap_scroll(label)
            check("account-action-"+label,ok)
            if ok:
                time.sleep(3);check("alive-after-"+label,alive("eu.svoyi.qa.finish252"));adb("shell","input","keyevent","KEYCODE_BACK");time.sleep(3)
                tap("content-desc","Профіль",contains=True) or tap("text","Профіль");time.sleep(3)
    else:
        capture("after-account");check("after-profile-nav",False,"profile tab absent")
    # Session must survive a normal process restart.
    adb("shell","am","force-stop","eu.svoyi.qa.finish252");time.sleep(2)
    adb("shell","monkey","-p","eu.svoyi.qa.finish252","-c","android.intent.category.LAUNCHER","1");time.sleep(8)
    persisted=text_blob()
    check("session-persists-after-restart","Увійти" not in persisted and ("Головна" in persisted or "Кабінет" in persisted),persisted[:700])
    check("alive-after-restart",alive("eu.svoyi.qa.finish252"))

    # Loaded content should not crash if connectivity disappears briefly.
    adb("shell","svc","wifi","disable",allow_fail=True);adb("shell","svc","data","disable",allow_fail=True);time.sleep(2)
    check("alive-offline-after-load",alive("eu.svoyi.qa.finish252"))
    adb("shell","svc","wifi","enable",allow_fail=True);adb("shell","svc","data","enable",allow_fail=True);time.sleep(2)

    log=adb("logcat","-d","-v","threadtime",timeout=50).decode(errors="replace");save("final-logcat.txt",log)
    check("no-final-fatal","FATAL EXCEPTION" not in log)
    check("no-location-abstract-method-error","AbstractMethodError" not in log or "LocationListener" not in log)
    montage("before-home.png","after-home.png","before-after-home.png","Головна")
    montage("before-account.png","after-account.png","before-after-account.png","Особистий кабінет")
    check("before-after-created",True)
except Exception as e:
    check("harness",False,type(e).__name__+": "+str(e));save("error.txt",traceback.format_exc())
finally:
    save("checks.json",CHECKS)
    print(json.dumps(CHECKS,ensure_ascii=False))
    raise SystemExit(0 if CHECKS and all(x["passed"] for x in CHECKS) else 1)
