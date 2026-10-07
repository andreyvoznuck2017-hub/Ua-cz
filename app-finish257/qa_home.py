"""Targeted home/install regression after mail passed in run 37682264730."""
from qa_support import *

try:
    a=account("home")
    install_login(BEFORE,a)
    result=adb("install","-r",str(APK),timeout=120).decode();must("update-256-to-final257","Success" in result,result)
    route("/?p=home")
    must("version-257","versionName=2.5.7" in adb("shell","dumpsys","package",PKG).decode())
    must("session-retained",a["name"] in blob() and "Увійти" not in blob())
    shot("home-top");seen="\n".join(n.get("text","") for n in nodes())
    for i in range(36):
        adb("shell","input","swipe","500","1850","500","850","700");time.sleep(.3)
        part="\n".join(n.get("text","") for n in nodes());seen+="\n"+part
        if i%4==0 or "Маркет" in part or "Послуги своїх" in part:shot("home-"+str(i+1))
        if "Відпочинок після дня" in part:shot("home-bottom");break
    for label in ["Активні групи","Розмова в чаті","Дописи спільноти","Свіжі вакансії","Нове житло","Фотобатл","Маркет","Послуги своїх","Корисне для вас","Відпочинок після дня"]:must("home-section-"+label,label in seen)
    must("market-visible-title-and-price","Рюкзак для прогулянок" in seen and "500 Kč" in seen)
    must("service-visible-title-and-price","QA Фото & контент" in seen and "від 600 Kč" in seen)
    route("/?p=home&lang=en");must("english-home","Welcome" in blob());shot("home-english")
    route("/?p=messages");must("english-mail","Your conversations" in blob());shot("mail-english")
    route("/?p=home&lang=uk");route("/?native=settings")
    dark=next((n for n in nodes() if "Українська ніч" in n.get("content-desc","") and n.get("clickable")=="true"),None)
    must("night-theme-control",dark is not None);tap_node(dark);time.sleep(.8)
    route("/?p=home");shot("home-night");route("/?p=messages");shot("mail-night")
    log=adb("logcat","-d","-b","crash").decode(errors="replace");save("crashes.txt",log);must("no-fatal","FATAL EXCEPTION" not in log)
    adb("uninstall",PKG);result=adb("install","-g",str(APK),timeout=120).decode();must("fresh-install-final257","Success" in result,result)
    adb("shell","monkey","-p",PKG,"-c","android.intent.category.LAUNCHER","1");time.sleep(5)
    must("fresh-launch-final257",wait(lambda:any(n.get("package")==PKG for n in nodes()),20));shot("fresh-install")
except Exception as e:
    check("harness",False,type(e).__name__+": "+str(e));save("error.txt",traceback.format_exc())
finally:
    try:shot("final-screen")
    except Exception:pass
    save("checks.json",CHECKS);print(json.dumps(CHECKS,ensure_ascii=False));raise SystemExit(0 if CHECKS and all(c["passed"] for c in CHECKS) else 1)
