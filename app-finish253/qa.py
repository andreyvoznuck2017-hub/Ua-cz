#!/usr/bin/env python3
import json,os,re,secrets,subprocess,time,traceback
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from PIL import Image,ImageDraw

ORIGIN="https://test.jkunis.eu"
OUT=Path(os.environ.get("QA_OUT","finish253-qa")); OUT.mkdir(parents=True,exist_ok=True)
APK=Path(os.environ["APK"])
PKG="eu.svoyi.qa.finish252"
CHECKS=[]; SECRETS=[]
def save(n,v):
    s=json.dumps(v,ensure_ascii=False,indent=2) if not isinstance(v,str) else v
    for x in SECRETS:s=s.replace(x,"[REDACTED]")
    (OUT/n).write_text(s,encoding="utf-8")
def check(n,ok,d=""):CHECKS.append({"test":n,"passed":bool(ok),"detail":d});save("checks.json",CHECKS)
def adb(*a,timeout=60,allow_fail=False):
    p=subprocess.run(["adb",*a],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
    if p.returncode and not allow_fail:raise RuntimeError(p.stderr.decode(errors="replace")[:500])
    return p.stdout
def ui():
    adb("shell","uiautomator","dump","/sdcard/f253.xml")
    import xml.etree.ElementTree as ET
    return ET.fromstring(adb("shell","cat","/sdcard/f253.xml"))
def blob():return "\n".join((n.get("text","")+" "+n.get("content-desc","")).strip() for n in ui().iter("node"))
def tap_text(s):
    for n in ui().iter("node"):
        if s.lower() in (n.get("text","")+" "+n.get("content-desc","")).lower():
            nums=list(map(int,re.findall(r"\d+",n.get("bounds",""))))
            if len(nums)==4:
                x1,y1,x2,y2=nums;adb("shell","input","tap",str((x1+x2)//2),str((y1+y2)//2));return True
    return False
def shot(n):
    (OUT/(n+".png")).write_bytes(adb("exec-out","screencap","-p"))
    save(n+".txt",blob())
def api(s,b):
    r=s.post(ORIGIN+"/native.php",json=b,timeout=45,headers={"User-Agent":"SvoyiNative/2.5.3 QA"});r.raise_for_status();return r.json()
def account():
    s=requests.Session(); tag=os.environ.get("GITHUB_RUN_ID",secrets.token_hex(4))
    email=f"qa.finish253.{tag}@example.com";pw="Qa"+secrets.token_hex(14);SECRETS.extend([email,pw])
    r=s.get(ORIGIN+"/?p=register",timeout=45);r.raise_for_status();soup=BeautifulSoup(r.text,"html.parser");csrf=soup.select_one('input[name=csrf]');assert csrf
    r=s.post(ORIGIN+"/?p=register",data={"csrf":csrf.get("value",""),"action":"register","start_goal":"all","name":"QA Finish253","email":email,"city":"Praha","password":pw},timeout=45);r.raise_for_status()
    assert api(s,{"op":"session","route":"/?p=home"})["state"].get("signedIn")
    return s,email,pw
def login(email,pw):
    adb("uninstall",PKG,allow_fail=True);adb("install","-g",str(APK),timeout=120);adb("logcat","-c")
    adb("shell","monkey","-p",PKG,"-c","android.intent.category.LAUNCHER","1");time.sleep(10)
    edits=[n for n in ui().iter("node") if n.get("class")=="android.widget.EditText"]
    if len(edits)>=2 and "Увійти" in blob():
        for idx,val in [(0,email),(1,pw)]:
            n=edits[idx];nums=list(map(int,re.findall(r"\d+",n.get("bounds",""))));x1,y1,x2,y2=nums;adb("shell","input","tap",str((x1+x2)//2),str((y1+y2)//2));adb("shell","input","text",val)
        adb("shell","input","keyevent","KEYCODE_BACK");time.sleep(1);tap_text("Увійти");time.sleep(10)
    check("login", "Увійти" not in blob(), blob()[:500])
def nav(label):
    if tap_text(label):time.sleep(7);return True
    # menu fallback
    if tap_text("Відкрити меню"):time.sleep(2)
    if tap_text(label):time.sleep(7);return True
    return False
def swipe_up(n=5):
    for _ in range(n):adb("shell","input","swipe","520","1850","520","650","400");time.sleep(.5)

try:
    s,email,pw=account();check("qa-account",True)
    for route in ["/?p=dating","/?p=nearby","/?p=housing","/?p=groups","/?p=feed","/?p=notifications"]:
        res=api(s,{"op":"screen","route":route});check("api-"+re.sub(r"\W+","-",route).strip("-"),bool(res.get("page") or res.get("nodes")),res.get("page",""))
    login(email,pw)
    for label,key in [("Знайомства","dating"),("Житло","housing"),("Групи","groups"),("Сповіщення","notifications"),("Повідомлення","mail")]:
        adb("shell","input","keyevent","KEYCODE_BACK",allow_fail=True);time.sleep(2)
        ok=nav(label);check("nav-"+key,ok)
        if ok:
            shot("after-"+key);txt=blob()
            check("alive-"+key,bool(adb("shell","pidof",PKG,allow_fail=True).strip()),txt[:500])
            if key=="mail":
                edits=[n for n in ui().iter("node") if n.get("class")=="android.widget.EditText"]
                check("mail-edit-field-present",len(edits)>0,str(len(edits)))
                if edits:
                    nums=list(map(int,re.findall(r"\d+",edits[-1].get("bounds",""))));check("mail-input-height",len(nums)==4 and nums[3]-nums[1]>=48,str(nums))
            if key=="dating":
                imgs=[n for n in ui().iter("node") if n.get("class")=="android.widget.ImageView"]
                check("dating-images-present",len(imgs)>0,str(len(imgs)))
            if key=="housing":
                check("housing-screen-content",any(x in txt for x in ["Житло","Квартира","кімнат","Прага","Praha"]),txt[:700])
    log=adb("logcat","-d","-v","threadtime").decode(errors="replace");save("logcat.txt",log)
    check("no-fatal","FATAL EXCEPTION" not in log)
except Exception as e:
    check("harness",False,type(e).__name__+": "+str(e));save("error.txt",traceback.format_exc())
finally:
    save("checks.json",CHECKS)
    print(json.dumps(CHECKS,ensure_ascii=False))
    raise SystemExit(0 if CHECKS and all(x["passed"] for x in CHECKS) else 1)
