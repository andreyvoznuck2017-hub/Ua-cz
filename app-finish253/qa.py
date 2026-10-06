#!/usr/bin/env python3
import json,os,re,secrets,subprocess,time,traceback
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from PIL import Image,ImageDraw

ORIGIN="https://test.jkunis.eu";OUT=Path(os.environ.get("QA_OUT","finish253-qa"));OUT.mkdir(parents=True,exist_ok=True)
CHECKS=[];SECRET=[]
def save(name,value):
 text=json.dumps(value,ensure_ascii=False,indent=2) if not isinstance(value,str) else value
 for x in SECRET:
  if x:text=text.replace(x,"[REDACTED]")
 (OUT/name).write_text(text,encoding="utf-8")
def check(name,ok,detail=""):CHECKS.append({"test":name,"passed":bool(ok),"detail":detail});save("checks.json",CHECKS)
def adb(*args,timeout=60,allow_fail=False):
 p=subprocess.run(["adb",*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
 if p.returncode and not allow_fail:raise RuntimeError(p.stderr.decode(errors="replace")[:500])
 return p.stdout
def ui():
 adb("shell","uiautomator","dump","/sdcard/u.xml");import xml.etree.ElementTree as ET
 return ET.fromstring(adb("shell","cat","/sdcard/u.xml"))
def blob():return "\n".join((n.get("text","")+" "+n.get("content-desc","")).strip() for n in ui().iter("node"))
def tap(attr,val,contains=False,index=0):
 nodes=[n for n in ui().iter("node") if (val in n.get(attr,"") if contains else n.get(attr,"")==val)]
 if len(nodes)<=index:return False
 nums=list(map(int,re.findall(r"\d+",nodes[index].get("bounds",""))))
 if len(nums)!=4:return False
 x1,y1,x2,y2=nums;adb("shell","input","tap",str((x1+x2)//2),str((y1+y2)//2));return True
def capture(name):
 (OUT/(name+".png")).write_bytes(adb("exec-out","screencap","-p"));save(name+".txt",blob())
def alive(pkg):return bool(adb("shell","pidof",pkg,allow_fail=True).strip())
def api(s,body):
 r=s.post(ORIGIN+"/native.php",json=body,timeout=45,headers={"User-Agent":"SvoyiNative/2.5.3 QA"});r.raise_for_status();return r.json()
def account():
 s=requests.Session();tag=os.environ.get("GITHUB_RUN_ID",secrets.token_hex(4));email=f"qa.finish253.{tag}@example.com";pw="Qa"+secrets.token_hex(15);SECRET.extend([email,pw])
 page=s.get(ORIGIN+"/?p=register",timeout=45);soup=BeautifulSoup(page.text,"html.parser");csrf=soup.select_one('input[name=csrf]');assert csrf
 r=s.post(ORIGIN+"/?p=register",data={"csrf":csrf.get("value",""),"action":"register","start_goal":"all","name":"QA Social253","email":email,"city":"Praha","password":pw},timeout=45);r.raise_for_status()
 st=api(s,{"op":"session","route":"/?p=home"})["state"];assert st.get("signedIn")
 return s,email,pw
def login(apk,pkg,email,pw,prefix):
 adb("install","-r","-g",str(apk),timeout=120);adb("logcat","-c");adb("shell","monkey","-p",pkg,"-c","android.intent.category.LAUNCHER","1");time.sleep(10)
 for _ in range(3):
  txt=blob()
  if "QA Social253" in txt or "Вийти" in txt or "Особистий кабінет" in txt:break
  edits=[n for n in ui().iter("node") if n.get("class","")=="android.widget.EditText"]
  if len(edits)<2:break
  tap("class","android.widget.EditText",False,0);adb("shell","input","keyevent","KEYCODE_MOVE_END");adb("shell","input","text",email)
  tap("class","android.widget.EditText",False,1);adb("shell","input","keyevent","KEYCODE_MOVE_END");adb("shell","input","text",pw);adb("shell","input","keyevent","KEYCODE_BACK");time.sleep(1)
  if not tap("text","Увійти"):break
  time.sleep(10)
 signed=("QA Social253" in blob() or "Вийти" in blob() or "Особистий кабінет" in blob()) and "ВХІД" not in blob()
 check(prefix+"-login",alive(pkg) and signed,blob()[:700])
def menu_section(label):
 for _ in range(2):
  if tap("content-desc","Відкрити меню",True) or tap("text","☰",False):time.sleep(1.2)
  if tap("text",label,True):time.sleep(6);return True
  adb("shell","input","keyevent","KEYCODE_BACK");time.sleep(.6)
 return False
def screen(prefix,label,tokens):
 if label in ("Повідомлення","Сповіщення"):
  ok=tap("text",label,False) or tap("content-desc",label,True)
  if ok:time.sleep(6)
 else:ok=menu_section(label)
 check(prefix+"-"+label+"-open",ok)
 if not ok:return
 capture(prefix+"-"+label.lower().replace(" ","-"))
 txt=blob();check(prefix+"-"+label+"-content",any(t.lower() in txt.lower() for t in tokens),txt[:700])
 if prefix=="after" and label=="Знайомства":
  check("dating-profiles-render","Не вдалося показати анкети" not in txt and "Оновити розділ" not in txt,txt[:1200])
def montage(before,after,out,title):
 a=Image.open(OUT/before).convert("RGB");b=Image.open(OUT/after).convert("RGB");h=max(a.height,b.height);c=Image.new("RGB",(a.width+b.width,h+80),"white");c.paste(a,(0,80));c.paste(b,(a.width,80));d=ImageDraw.Draw(c);d.text((20,20),"ДО — 2.5.2",fill="black");d.text((a.width+20,20),"ПІСЛЯ — 2.5.3",fill="black");d.text((20,48),title,fill="black");c.save(OUT/out)

try:
 s,email,pw=account();check("qa-account",True)
 for route,toks in [
  ("/?p=dating",["dating","Знайом","Поруч"]),
  ("/?p=nearby",["nearby","поруч"]),
  ("/?p=housing",["housing","Житло"]),
  ("/?p=groups",["groups","Груп"]),
  ("/?p=messages",["messages","Повідом"]),
  ("/?p=notifications",["notifications","Сповіщ"])
 ]:
  result=api(s,{"op":"screen","route":route});raw=json.dumps(result,ensure_ascii=False).lower();check("api-"+re.sub(r"\W+","-",route).strip("-"),any(t.lower() in raw for t in toks),result.get("page",""))
 before=Path(os.environ["BEFORE_APK"]);after=Path(os.environ["AFTER_APK"])
 login(before,"eu.svoyi.qa.before253",email,pw,"before")
 for label,toks in [("Знайомства",["Знайом","Поруч","Лайк"]),("Житло",["Житло","Обране"]),("Групи",["Груп"]),("Повідомлення",["Повідом","діалог"]),("Сповіщення",["Сповіщ","Непроч"])]:
  screen("before",label,toks)
 adb("uninstall","eu.svoyi.qa.before253",allow_fail=True)

 login(after,"eu.svoyi.qa.finish253",email,pw,"after")
 for label,toks in [("Знайомства",["Знайом","Поруч","Лайк"]),("Житло",["Житло","Обране"]),("Групи",["Груп"]),("Повідомлення",["Повідом","діалог"]),("Сповіщення",["Сповіщ","Непроч"])]:
  screen("after",label,toks)
 # Focus the messages search/composer-like field and ensure app survives IME resize.
 (tap("text","Повідомлення",False) or tap("content-desc","Повідомлення",True));time.sleep(5)
 edits=[n for n in ui().iter("node") if n.get("class","")=="android.widget.EditText"]
 if edits:
  tap("class","android.widget.EditText",False,len(edits)-1);time.sleep(2);check("mail-ime-focus-survives",alive("eu.svoyi.qa.finish253"));adb("shell","input","keyevent","KEYCODE_BACK")
 else:check("mail-ime-focus-survives",True,"No editable field on empty inbox")
 # Short offline pass across a loaded social screen.
 menu_section("Групи");time.sleep(3);adb("shell","svc","wifi","disable",allow_fail=True);adb("shell","svc","data","disable",allow_fail=True);time.sleep(2);check("offline-loaded-screen-survives",alive("eu.svoyi.qa.finish253"));adb("shell","svc","wifi","enable",allow_fail=True);adb("shell","svc","data","enable",allow_fail=True)
 # Process restart keeps session.
 adb("shell","am","force-stop","eu.svoyi.qa.finish253");adb("shell","monkey","-p","eu.svoyi.qa.finish253","-c","android.intent.category.LAUNCHER","1");time.sleep(8);rt=blob();check("session-after-restart","Увійти" not in rt and alive("eu.svoyi.qa.finish253"),rt[:500])
 log=adb("logcat","-d","-v","threadtime").decode(errors="replace");save("after-logcat.txt",log);check("no-fatal","FATAL EXCEPTION" not in log)
 for label,key in [("Знайомства","знайомства"),("Житло","житло"),("Групи","групи"),("Повідомлення","повідомлення"),("Сповіщення","сповіщення")]:
  b="before-"+label.lower().replace(" ","-")+".png";a="after-"+label.lower().replace(" ","-")+".png"
  if (OUT/b).exists() and (OUT/a).exists():montage(b,a,"before-after-"+key+".png",label)
 check("before-after-montages",len(list(OUT.glob("before-after-*.png")))>=4,str(len(list(OUT.glob("before-after-*.png")))))
except Exception as e:
 check("harness",False,type(e).__name__+": "+str(e));save("error.txt",traceback.format_exc())
finally:
 save("checks.json",CHECKS);print(json.dumps(CHECKS,ensure_ascii=False));raise SystemExit(0 if CHECKS and all(x["passed"] for x in CHECKS) else 1)
