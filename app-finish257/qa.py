from qa_support import *

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
