#!/usr/bin/env python3
"""Fix observed client/server capability mismatch. Only home screen projection changes."""
from pathlib import Path
p=Path('repair/NativeSiteUi.java');s=p.read_text()
# Intrinsic pixels must not shrink a vector on high-density Android displays.
s=s.replace('public int getIntrinsicWidth(){return 24;}','public int getIntrinsicWidth(){return -1;}').replace('public int getIntrinsicHeight(){return 24;}','public int getIntrinsicHeight(){return -1;}')
method=r'''
    /** The legacy visual hint removes home-v3 for the obsolete welcome replacement.
     * Request full website home nodes; retain every hint for all other sections. */
    public static void prepareRequest(JSONObject request) throws org.json.JSONException {
        if(request==null||!"screen".equals(request.optString("op")))return;
        android.net.Uri route=android.net.Uri.parse(request.optString("route"));
        String page=route.getQueryParameter("p"),path=route.getPath();
        if(page!=null&&!page.equals("home"))return;
        if(path!=null&&!path.isEmpty()&&!path.equals("/")&&!path.equals("/index.php"))return;
        if(route.getQueryParameter("u")!=null||"jobs".equals(route.getQueryParameter("native")))return;
        JSONArray hints=request.optJSONArray("nativeScreens");if(hints==null)return;
        JSONArray kept=new JSONArray();for(int i=0;i<hints.length();i++)if(!"visual".equals(hints.optString(i)))kept.put(hints.get(i));
        request.put("nativeScreens",kept);
    }
'''
assert s.endswith('}\n');s=s[:-2]+method+'}\n'
old='presence.optBoolean("online")&&!presence.optBoolean("hidden")'
assert old in s;s=s.replace(old,old+'&&(!presence.has("visible")||presence.optBoolean("visible"))')
old='else if(type.equals("text")){TextView v=text(a,t,tx,13,false);'
assert old in s
s=s.replace(old,'else if(type.equals("text")){if(tx.equals("Перший кадр може бути твоїм")){LinearLayout empty=panel(a,t,18);empty.setGravity(Gravity.CENTER);empty.setMinimumHeight(dp(a,150));ImageView camera=icon(a,t,"camera",44);empty.addView(camera,new LinearLayout.LayoutParams(dp(a,48),dp(a,48)));TextView prompt=text(a,t,tx,14,true);prompt.setGravity(Gravity.CENTER);add(empty,prompt,12,0);add(box,empty,12,8);continue;}TextView v=text(a,t,tx,13,false);')
p.write_text(s)
b=Path('repair/build.py');s=b.read_text();marker="for p in (ROOT/'helper-smali').rglob('*.smali'):"
assert marker in s
patch='''def request_hint(old):
    needle='    invoke-virtual {v1, v6, v5}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;'
    assert old.count(needle)==1, 'Native capability injection ambiguous'
    return old.replace(needle,needle+'\\n\\n    invoke-static {v1}, Leu/svoyi/nativeapp/NativeSiteUi;->prepareRequest(Lorg/json/JSONObject;)V',1)
method(BASE/'Api.smali','transport(Lorg/json/JSONObject;Ljava/util/Map;II)Lorg/json/JSONObject;',request_hint)
'''
s=s.replace(marker,patch+'\n'+marker);b.write_text(s)
p=Path('repair/stress-diagnostic.py');s=p.read_text()
old="tap('content-desc','Головна');time.sleep(7);capture('android-10-home-top')"
assert old in s
s=s.replace(old,old+"\n    home_text=' '.join(n.get('text','') for n in ui().iter('node'))\n    check('home-website-welcome', 'Вітаємо' in home_text)\n    check('home-website-quick-links',all(label in home_text for label in ['Житло','Робота','Події','Групи']))\n    check('home-website-challenge','Фоточелендж' in home_text)")
old="tap('content-desc','Профіль');time.sleep(5);capture('android-11-cabinet')"
assert old in s
s=s.replace(old,old+"\n    nodes=list(ui().iter('node')); avatars=[n for n in nodes if n.get('content-desc')=='Відкрити фото профілю']; names=[n for n in nodes if n.get('text')=='QA Andrii']\n    if avatars and names:\n        import re\n        ab=list(map(int,re.findall(r'\\d+',avatars[0].get('bounds',''))));nb=list(map(int,re.findall(r'\\d+',names[0].get('bounds',''))))\n        overlap=max(ab[0],nb[0])<min(ab[2],nb[2]) and max(ab[1],nb[1])<min(ab[3],nb[3])\n        check('profile-avatar-name-no-overlap',not overlap)\n    else:check('profile-avatar-name-no-overlap',False,'Bounds targets missing')")
p.write_text(s)
print('Home projection, visible-presence policy, vector sizing and runtime assertions patched')
