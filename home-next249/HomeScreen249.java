package eu.svoyi.nativeapp;

import android.app.*;
import android.content.*;
import android.graphics.Rect;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.SystemClock;
import android.text.*;
import android.view.*;
import android.widget.*;
import org.json.*;
import java.security.MessageDigest;
import java.util.*;

/** Home-only presentation. No new API, no private content persisted, no mail/profile hooks. */
public final class HomeScreen249 {
    private final Activity activity;
    private final MainActivity owner;
    private final ThemePalette theme;
    private final NativeJobsScreen.Host host;
    private final JSONObject model;
    private final LinearLayout root, sections;
    private final List<HomeRules249.Section> server = new ArrayList<>();
    private final Map<String,JSONObject> sources = new LinkedHashMap<>();
    private final Map<String,LinearLayout> wrappers = new LinkedHashMap<>();
    private final Map<String,View> bodies = new LinkedHashMap<>();
    private final Map<String,Button> headers = new LinkedHashMap<>();
    private final List<JSONObject> shortcuts = new ArrayList<>();
    private final Set<String> hidden = new HashSet<>(), collapsed = new HashSet<>(), pins = new HashSet<>();
    private List<String> order = new ArrayList<>();
    private final SharedPreferences prefs;
    private final String language;
    private boolean grid=true, attached=false;
    private ScrollView parentScroll;
    private ViewTreeObserver observer;
    private final ViewTreeObserver.OnScrollChangedListener scrollListener=this::rememberPosition;
    private EditText query;
    private TextView scope, emptyState;
    private NativeSiteUi.Flow quick;
    private Button resume;
    private long lastRefresh;
    private String resumeId="";
    private int resumeOffset, beforeSearchY;
    private long resumeTime;

    public static View build(NativeWelcome welcome, JSONObject model) {
        if (!(welcome.activity instanceof MainActivity)) {TextView v=new TextView(welcome.activity);v.setText("Головна недоступна");return v;}
        return new HomeScreen249(welcome,model).root;
    }
    private HomeScreen249(NativeWelcome w, JSONObject value) {
        activity=w.activity;owner=(MainActivity)w.activity;theme=w.colors;host=w.host;
        model=value==null?new JSONObject():value;
        JSONObject state=model.optJSONObject("state"),user=state==null?null:state.optJSONObject("user");
        long id=user==null?0:user.optLong("id");
        language=HomeRules249.locale(state==null?"uk":state.optString("language","uk"));
        prefs=id>0&&state.optBoolean("signedIn")?activity.getSharedPreferences(HomeRules249.preferenceKey(id),Context.MODE_PRIVATE):null;
        if(prefs!=null){
            hidden.addAll(readSet("hidden"));collapsed.addAll(readSet("collapsed"));pins.addAll(readSet("pins"));
            try {order=HomeRules249.decodeOrder(prefs.getString("order",""));grid=prefs.getBoolean("grid",true);resumeId=prefs.getString("resume-id","");resumeOffset=prefs.getInt("resume-offset",0);resumeTime=prefs.getLong("resume-time",0);}catch(ClassCastException e){order.clear();grid=true;resumeId="";}
        }
        root=column();root.setTag("home249-root");sections=column();
        JSONArray nodes=array(model,"nodes");
        if(nodes.length()==0){
            add(root,text(t("Головна не завантажилася. Дані не замінено порожнім списком.","Domovská stránka se nenačetla. Data nebyla nahrazena prázdným seznamem.","Home did not load. Data has not been replaced with an empty list."),16,false),0,12);
            add(root,button(t("Спробувати ще раз","Zkusit znovu","Try again"),this::refresh),0,8);return;
        }
        split(nodes);buildHeader();add(root,sections,12,8);
        emptyState=text(t("Немає відповідних блоків. Очистіть пошук або змініть налаштування головної.","Žádné odpovídající bloky. Vymažte hledání nebo upravte nastavení.","No matching blocks. Clear the search or adjust home settings."),16,false);emptyState.setVisibility(View.GONE);add(root,emptyState,8,12);buildSections();renderVisibility();
        add(root,button(t("↑ На початок","↑ Na začátek","↑ Back to top"),()->{hideIme();if(parentScroll!=null)parentScroll.smoothScrollTo(0,0);}),8,16);
        root.addOnAttachStateChangeListener(new View.OnAttachStateChangeListener(){
            public void onViewAttachedToWindow(View v){attached=true;root.post(()->{
                if(!attached)return;ViewParent p=root.getParent();while(p instanceof View&&!(p instanceof ScrollView))p=p.getParent();
                if(p instanceof ScrollView){parentScroll=(ScrollView)p;observer=parentScroll.getViewTreeObserver();if(observer.isAlive())observer.addOnScrollChangedListener(scrollListener);}
            });}
            public void onViewDetachedFromWindow(View v){persistPosition();attached=false;if(observer!=null&&observer.isAlive())observer.removeOnScrollChangedListener(scrollListener);observer=null;parentScroll=null;}
        });
    }
    private Set<String> readSet(String key){try{Set<String>s=prefs.getStringSet(key,Collections.emptySet());return s==null?Collections.emptySet():new HashSet<>(s);}catch(ClassCastException e){return Collections.emptySet();}}
    private String t(String uk,String cs,String en){return language.equals("cs")?cs:language.equals("en")?en:uk;}
    private int dp(float x){return Math.round(activity.getResources().getDisplayMetrics().density*x);}
    private LinearLayout column(){LinearLayout v=new LinearLayout(activity);v.setOrientation(LinearLayout.VERTICAL);return v;}
    private GradientDrawable shape(int color,int radius){GradientDrawable d=new GradientDrawable();d.setColor(color);d.setCornerRadius(dp(radius));d.setStroke(dp(1),theme.border);return d;}
    private TextView text(String value,int size,boolean bold){TextView v=new TextView(activity);v.setText(value);v.setTextColor(theme.text);v.setTextSize(size);if(bold)v.setTypeface(Typeface.DEFAULT,Typeface.BOLD);v.setLineSpacing(dp(2),1);return v;}
    private Button button(String title,Runnable action){Button v=new Button(activity);v.setText(title);v.setAllCaps(false);v.setTextColor(theme.text);v.setTextSize(14);v.setMinHeight(dp(48));v.setMinimumHeight(dp(48));v.setPadding(dp(12),dp(8),dp(12),dp(8));v.setBackground(shape(theme.surface,13));v.setOnClickListener(a->{if(host.alive())action.run();});return v;}
    private void add(LinearLayout parent,View child,int top,int bottom){if(child.getParent() instanceof ViewGroup)((ViewGroup)child.getParent()).removeView(child);LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);p.setMargins(0,dp(top),0,dp(bottom));parent.addView(child,p);}
    private static JSONArray array(JSONObject j,String k){JSONArray a=j==null?null:j.optJSONArray(k);return a==null?new JSONArray():a;}
    private static String heading(JSONObject n){String s=n.optString("text",n.optString("title",""));if(!s.isEmpty())return s;JSONArray c=array(n,"children");for(int i=0;i<c.length();i++){JSONObject v=c.optJSONObject(i);if(v!=null&&v.optString("type").equals("heading"))return v.optString("text");}return "";}
    private static boolean containsType(JSONObject n,String kind,int depth){if(depth>20)return false;if(n.optString("type").equals(kind))return true;JSONArray cs=array(n,"children");for(int i=0;i<cs.length();i++){JSONObject c=cs.optJSONObject(i);if(c!=null&&containsType(c,kind,depth+1))return true;}return false;}
    private static void collectText(JSONObject n,StringBuilder b,int depth){if(depth>20||b.length()>300000)return;for(String k:new String[]{"title","text"}){String s=n.optString(k);if(!s.equals("null"))b.append(' ').append(s);}JSONArray ls=array(n,"lines");for(int i=0;i<ls.length();i++)b.append(' ').append(ls.optString(i));JSONArray cs=array(n,"children");for(int i=0;i<cs.length();i++){JSONObject c=cs.optJSONObject(i);if(c!=null)collectText(c,b,depth+1);}}
    private static String kind(JSONObject n){
        String all=n.toString();
        if(all.contains("p=promo_click")||all.contains("p=promotion"))return "promotion";
        if(all.contains("p=job&")||all.contains("native=jobs")||all.contains("view=jobs"))return "jobs";
        if(all.contains("p=housing"))return "housing";
        if(all.contains("p=challenges"))return "challenge";
        if(all.contains("p=feed"))return "feed";
        if(all.contains("p=chat"))return "chat";
        return "other";
    }
    private void split(JSONArray nodes){
        List<JSONObject> parts=new ArrayList<>();
        for(int k=0;k<nodes.length();k++){
            JSONObject n=nodes.optJSONObject(k);if(n==null)continue;
            if(k==0&&n.optString("type").equals("card")){
                JSONArray cs=array(n,"children");boolean intro=true;
                for(int i=0;i<cs.length();i++){JSONObject c=cs.optJSONObject(i);if(c==null)continue;String type=c.optString("type");
                    if(intro&&type.equals("link")){shortcuts.add(c);continue;}
                    if(intro&&(type.equals("heading")||type.equals("text"))){TextView v=text(c.optString("text"),type.equals("heading")?25:15,type.equals("heading"));if(type.equals("text"))v.setTextColor(theme.muted);add(root,v,0,8);continue;}
                    intro=false;parts.add(c);
                }
            }else parts.add(n);
        }
        Map<String,Integer> counts=new HashMap<>();
        for(JSONObject node:parts){String k=kind(node);int n=counts.containsKey(k)?counts.get(k)+1:1;counts.put(k,n);String key=k+"_"+n;
            String title=heading(node);if(title.isEmpty())title=t("Інформація","Informace","Information");StringBuilder s=new StringBuilder();collectText(node,s,0);
            boolean locked=k.equals("promotion")||containsType(node,"form",0)||k.equals("other");
            server.add(new HomeRules249.Section(key,title,s.toString(),locked));sources.put(key,node);
        }
    }
    private void buildHeader(){
        quick=new NativeSiteUi.Flow(activity,8);quick.setTag("home249-shortcuts");renderShortcuts();add(root,quick,4,8);
        TextView pinHint=text(t("Утримуйте ярлик, щоб закріпити його першим.","Podržením připnete zkratku na začátek.","Hold a shortcut to pin it first."),12,false);pinHint.setTextColor(theme.muted);add(root,pinHint,0,8);
        NativeSiteUi.Flow controls=new NativeSiteUi.Flow(activity,8);
        controls.addView(button(t("Налаштувати головну","Upravit hlavní stránku","Customize home"),this::customize));
        controls.addView(button(t("До розділу","Přejít do sekce","Jump to section"),this::jumpMenu));
        controls.addView(button(t("Оновити дані","Obnovit data","Refresh data"),this::refresh));add(root,controls,4,10);
        LinearLayout searchBar=new LinearLayout(activity);searchBar.setGravity(Gravity.CENTER_VERTICAL);
        query=new EditText(activity);query.setSingleLine(true);query.setTextColor(theme.text);query.setHintTextColor(theme.muted);query.setHint(t("Пошук у блоках цієї головної","Hledat v blocích této stránky","Search blocks on this home"));query.setTextSize(15);query.setMinHeight(dp(48));query.setSelectAllOnFocus(false);query.setTag("home249-search");query.setContentDescription(t("Пошук у завантажених блоках головної","Hledat v načtených blocích domovské stránky","Search loaded home blocks"));
        searchBar.addView(query,new LinearLayout.LayoutParams(0,-2,1));Button clear=button("×",()->{query.setText("");hideIme();root.post(()->{if(attached&&parentScroll!=null)parentScroll.scrollTo(0,beforeSearchY);});});clear.setContentDescription(t("Очистити пошук","Vymazat hledání","Clear search"));searchBar.addView(clear,new LinearLayout.LayoutParams(dp(48),dp(48)));add(root,searchBar,0,3);
        scope=text("",12,false);scope.setTextColor(theme.muted);scope.setAccessibilityLiveRegion(View.ACCESSIBILITY_LIVE_REGION_POLITE);add(root,scope,0,6);
        query.addTextChangedListener(new TextWatcher(){public void beforeTextChanged(CharSequence s,int st,int c,int af){if(s.length()==0){beforeSearchY=parentScroll==null?0:parentScroll.getScrollY();}}public void onTextChanged(CharSequence s,int st,int b,int c){renderVisibility();}public void afterTextChanged(Editable e){}});
        resume=button(t("Продовжити читання","Pokračovat ve čtení","Continue reading"),()->jump(resumeId,resumeOffset,true));
        resume.setVisibility(HomeRules249.canResume(resumeId,resumeTime,System.currentTimeMillis(),server,hidden)?View.VISIBLE:View.GONE);add(root,resume,3,4);
    }
    private static String shortcutKey(JSONObject n){try{byte[] d=MessageDigest.getInstance("SHA-256").digest(HomeRules249.jobRoute(n.optString("route")).getBytes("UTF-8"));StringBuilder b=new StringBuilder();for(int i=0;i<12;i++)b.append(String.format(Locale.ROOT,"%02x",d[i]));return b.toString();}catch(Exception e){return Integer.toHexString(n.optString("route").hashCode());}}
    private void renderShortcuts(){
        quick.removeAllViews();List<JSONObject> sorted=new ArrayList<>(shortcuts);Collections.sort(sorted,(a,b)->Boolean.compare(pins.contains(shortcutKey(b)),pins.contains(shortcutKey(a))));
        for(JSONObject n:sorted){String title=n.optString("title",n.optString("text")),id=shortcutKey(n);Button btn=button((pins.contains(id)?"★ ":"")+title,()->navigate(n.optString("route")));btn.setOnLongClickListener(v->{if(prefs==null||!host.alive())return false;if(!pins.remove(id))pins.add(id);persist();renderShortcuts();return true;});quick.addView(btn);}
    }
    private void buildSections(){
        for(HomeRules249.Section s:server){
            LinearLayout wrap=column();wrap.setTag("home249-section:"+s.id);wrappers.put(s.id,wrap);
            if(s.locked){View body=owner.batch20Nodes(new JSONArray().put(sources.get(s.id)));bodies.put(s.id,body);add(wrap,body,0,0);continue;}
            Button head=button(s.title,()->{if(!collapsed.remove(s.id))collapsed.add(s.id);persist();renderVisibility();});head.setGravity(Gravity.START|Gravity.CENTER_VERTICAL);head.setTypeface(Typeface.DEFAULT,Typeface.BOLD);head.setTextSize(18);headers.put(s.id,head);add(wrap,head,0,7);
            View body=buildBody(s);bodies.put(s.id,body);add(wrap,body,0,0);
        }
    }
    private View buildBody(HomeRules249.Section s){
        JSONObject node=sources.get(s.id);JSONArray cs=array(node,"children");
        if(node.optString("type").equals("details"))return owner.batch20Nodes(cs);
        if(!(s.id.startsWith("jobs_")||s.id.startsWith("housing_"))){JSONArray body=new JSONArray();for(int i=0;i<cs.length();i++){JSONObject c=cs.optJSONObject(i);if(c!=null&&!c.optString("type").equals("heading"))body.put(c);}return owner.batch20Nodes(body.length()>0?body:new JSONArray().put(node));}
        LinearLayout output=column();List<JSONObject> cards=new ArrayList<>();
        for(int i=0;i<cs.length();i++){JSONObject c=cs.optJSONObject(i);if(c==null||c.optString("type").equals("heading"))continue;String route=c.optString("route");boolean item=c.optString("type").equals("link")&&(route.contains("p=job&")||route.contains("p=housing&"));if(item)cards.add(c);else add(output,owner.batch20Nodes(new JSONArray().put(c)),0,6);}
        if(cards.isEmpty())return output;
        int count=HomeRules249.twoColumns(activity.getResources().getDisplayMetrics().widthPixels/activity.getResources().getDisplayMetrics().density-32,activity.getResources().getConfiguration().fontScale,grid)?2:1;
        for(int i=0;i<cards.size();i+=count){LinearLayout row=new LinearLayout(activity);row.setBaselineAligned(false);int end=Math.min(cards.size(),i+count);
            for(int k=i;k<end;k++){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(0,-2,1);if(k>i)p.setMarginStart(dp(10));row.addView(card(cards.get(k)),p);}
            if(end-i<count)row.addView(new View(activity),new LinearLayout.LayoutParams(0,1,1));add(output,row,0,10);
        }return output;
    }
    private View card(JSONObject node){
        LinearLayout card=column();card.setBackground(shape(theme.surface,14));card.setClipToOutline(true);String image=node.optString("image","");
        if(!image.isEmpty()&&!image.equals("null")){
            FrameLayout frame=new FrameLayout(activity);frame.setBackgroundColor(theme.border);
            View v=host.image(image);if(v!=null){if(v instanceof ImageView){((ImageView)v).setScaleType(ImageView.ScaleType.CENTER_CROP);v.setContentDescription(node.optString("title"));}frame.addView(v,new FrameLayout.LayoutParams(-1,-1));}
            card.addView(frame,new LinearLayout.LayoutParams(-1,dp(grid?120:170)));
        }
        LinearLayout copy=column();copy.setPadding(dp(12),dp(12),dp(12),dp(12));String title=node.optString("title",node.optString("text",""));add(copy,text(title,16,true),0,7);
        JSONArray lines=array(node,"lines");for(int i=0;i<lines.length();i++){String line=lines.optString(i);if(!line.trim().isEmpty()){TextView v=text(line,14,false);v.setTextColor(theme.muted);add(copy,v,0,5);}}
        card.addView(copy);card.setMinimumHeight(dp(48));card.setFocusable(true);card.setContentDescription(title);card.setOnClickListener(v->{if(host.alive())navigate(node.optString("route"));});return card;
    }
    private void renderVisibility(){
        if(query==null)return;String q=query.getText().toString();int visible=0,total=0,index=0;
        for(HomeRules249.Section s:HomeRules249.ordered(server,order)){
            LinearLayout wrap=wrappers.get(s.id);if(wrap==null)continue;if(!s.locked)total++;
            boolean shown=HomeRules249.visible(s,hidden,q);wrap.setVisibility(shown?View.VISIBLE:View.GONE);
            if(shown&&!s.locked)visible++;
            if(!s.locked){boolean folded=collapsed.contains(s.id)&&q.trim().isEmpty();bodies.get(s.id).setVisibility(folded?View.GONE:View.VISIBLE);headers.get(s.id).setText((folded?"▸ ":"▾ ")+s.title);headers.get(s.id).setContentDescription(s.title+" — "+(folded?t("розгорнути","rozbalit","expand"):t("згорнути","sbalit","collapse")));}
            if(sections.getChildAt(index)!=wrap){if(wrap.getParent() instanceof ViewGroup)((ViewGroup)wrap.getParent()).removeView(wrap);LinearLayout.LayoutParams params=new LinearLayout.LayoutParams(-1,-2);params.bottomMargin=dp(16);sections.addView(wrap,index,params);}index++;
        }
        scope.setText(t("Показано блоків: ","Zobrazené bloky: ","Blocks shown: ")+visible+" / "+total+". "+t("Лише дані цього екрана, не весь сайт.","Pouze data této stránky, nikoli celý web.","Only this screen's data, not the whole site."));
        if(emptyState!=null)emptyState.setVisibility(visible==0?View.VISIBLE:View.GONE);
    }
    private void customize(){
        if(prefs==null){dialog().setMessage(t("Увійдіть, щоб зберігати власну головну.","Pro uložení nastavení se přihlaste.","Sign in to save your home settings.")).setPositiveButton("OK",null).show();return;}
        LinearLayout box=column();box.setPadding(dp(16),dp(12),dp(16),dp(12));ScrollView sc=new ScrollView(activity);sc.addView(box);
        Switch layout=new Switch(activity);layout.setText(t("Дві картки в ряд","Dvě karty na řádek","Two cards per row"));layout.setTextColor(theme.text);layout.setMinHeight(dp(48));layout.setChecked(grid);layout.setOnCheckedChangeListener((b,on)->{grid=on;persist();for(HomeRules249.Section s:server)if(!s.locked&&(s.id.startsWith("jobs_")||s.id.startsWith("housing_"))){View old=bodies.get(s.id);LinearLayout p=wrappers.get(s.id);p.removeView(old);View next=buildBody(s);bodies.put(s.id,next);add(p,next,0,0);}renderVisibility();});add(box,layout,0,12);
        LinearLayout rows=column();add(box,rows,0,8);Runnable[] refreshRows=new Runnable[1];refreshRows[0]=()->{rows.removeAllViews();for(HomeRules249.Section s:HomeRules249.ordered(server,order)){
            if(s.locked)continue;LinearLayout row=new LinearLayout(activity);row.setGravity(Gravity.CENTER_VERTICAL);CheckBox show=new CheckBox(activity);show.setText(s.title);show.setTextColor(theme.text);show.setMinHeight(dp(48));show.setChecked(!hidden.contains(s.id));show.setOnCheckedChangeListener((b,on)->{if(on)hidden.remove(s.id);else hidden.add(s.id);persist();renderVisibility();});row.addView(show,new LinearLayout.LayoutParams(0,-2,1));
            for(int d:new int[]{-1,1}){Button move=button(d<0?"↑":"↓",()->{order=HomeRules249.move(server,order,s.id,d);persist();renderVisibility();refreshRows[0].run();});move.setContentDescription(s.title+" "+(d<0?t("вище","výše","up"):t("нижче","níže","down")));row.addView(move,new LinearLayout.LayoutParams(dp(48),dp(48)));}add(rows,row,0,6);
        }};refreshRows[0].run();
        TextView note=text(t("Змінюється лише вигляд на цьому пристрої. Реклама та серверні форми залишаються на місці.","Mění se pouze vzhled na tomto zařízení. Reklama a serverové formuláře zůstávají na místě.","Only presentation on this device changes. Ads and server forms remain in place."),13,false);note.setTextColor(theme.muted);add(box,note,6,6);
        AlertDialog d=dialog().setTitle(t("Моя головна","Moje hlavní stránka","My home")).setView(sc).setPositiveButton(t("Готово","Hotovo","Done"),null).setNeutralButton(t("Скинути вигляд","Obnovit rozložení","Reset layout"),null).create();
        d.setOnShowListener(x->d.getButton(AlertDialog.BUTTON_NEUTRAL).setOnClickListener(v->dialog().setMessage(t("Повернути порядок і видимість блоків? Дані акаунта не зміняться.","Obnovit pořadí a viditelnost bloků? Účet se nezmění.","Reset block order and visibility? Account data will not change.")).setNegativeButton(t("Скасувати","Zrušit","Cancel"),null).setPositiveButton(t("Скинути","Obnovit","Reset"),(a,b)->{hidden.clear();collapsed.clear();pins.clear();order.clear();persist();renderShortcuts();renderVisibility();refreshRows[0].run();}).show()));d.show();styleDialog(d);
    }
    private AlertDialog.Builder dialog(){int color=theme.surface;double light=0.2126*((color>>16)&255)+0.7152*((color>>8)&255)+0.0722*(color&255);return new AlertDialog.Builder(new ContextThemeWrapper(activity,light<128?android.R.style.Theme_Material_Dialog_Alert:android.R.style.Theme_Material_Light_Dialog_Alert));}
    private void styleDialog(AlertDialog d){if(d.getWindow()!=null){d.getWindow().setBackgroundDrawable(shape(theme.surface,20));d.getWindow().setLayout(Math.min(activity.getResources().getDisplayMetrics().widthPixels-dp(24),dp(560)),WindowManager.LayoutParams.WRAP_CONTENT);}}
    private void jumpMenu(){List<String> labels=new ArrayList<>(),ids=new ArrayList<>();for(HomeRules249.Section s:HomeRules249.ordered(server,order))if(HomeRules249.visible(s,hidden,query.getText().toString())){labels.add(s.title);ids.add(s.id);}dialog().setTitle(t("Розділи головної","Sekce hlavní stránky","Home sections")).setItems(labels.toArray(new String[0]),(d,i)->jump(ids.get(i),0,true)).setNegativeButton(t("Скасувати","Zrušit","Cancel"),null).show();}
    private void persist(){if(prefs!=null)prefs.edit().putStringSet("hidden",new HashSet<>(hidden)).putStringSet("collapsed",new HashSet<>(collapsed)).putStringSet("pins",new HashSet<>(pins)).putString("order",HomeRules249.encodeOrder(order)).putBoolean("grid",grid).apply();}
    private void navigate(String route){persistPosition();hideIme();host.navigate(HomeRules249.jobRoute(route));}
    private void refresh(){long now=SystemClock.uptimeMillis();if(now-lastRefresh<1500)return;lastRefresh=now;persistPosition();hideIme();host.navigate(model.optString("route","/?p=home"));}
    private void hideIme(){View f=activity.getCurrentFocus();if(f!=null){android.view.inputmethod.InputMethodManager ime=(android.view.inputmethod.InputMethodManager)activity.getSystemService(Context.INPUT_METHOD_SERVICE);if(ime!=null)ime.hideSoftInputFromWindow(f.getWindowToken(),0);f.clearFocus();}}
    private int topOf(View v){if(parentScroll==null)return 0;Rect r=new Rect(0,0,v.getWidth(),v.getHeight());parentScroll.offsetDescendantRectToMyCoords(v,r);return r.top;}
    private void rememberPosition(){if(!attached||parentScroll==null||query==null||query.length()>0)return;int y=parentScroll.getScrollY();String found="";int offset=0;for(HomeRules249.Section s:HomeRules249.ordered(server,order)){View v=wrappers.get(s.id);if(v==null||v.getVisibility()!=View.VISIBLE)continue;int top=topOf(v);if(top<=y+dp(40)){found=s.id;offset=Math.max(0,y-top);}}if(!found.isEmpty()){resumeId=found;resumeOffset=offset;resumeTime=System.currentTimeMillis();}}
    private void persistPosition(){rememberPosition();if(prefs!=null&&!resumeId.isEmpty())prefs.edit().putString("resume-id",resumeId).putInt("resume-offset",resumeOffset).putLong("resume-time",resumeTime).apply();}
    private void jump(String id,int offset,boolean unfold){if(!host.alive()||id==null||parentScroll==null)return;View v=wrappers.get(id);if(v==null||v.getVisibility()!=View.VISIBLE)return;hideIme();if(unfold&&collapsed.remove(id)){persist();renderVisibility();}root.post(()->{if(attached&&parentScroll!=null)parentScroll.smoothScrollTo(0,Math.max(0,topOf(v)+offset));});}
}
