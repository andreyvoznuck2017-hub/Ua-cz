package eu.svoyi.nativeapp;

import android.app.Activity;
import android.content.Context;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.*;
import org.json.*;
import java.util.*;

/** Native projection adapter. It never manufactures server actions, user records or permissions. */
public final class Batch20Ui {
 private Batch20Ui(){}
 private static final Map<Activity,JSONObject> home=new WeakHashMap<>();
 static int dp(Context c,float n){return Math.round(c.getResources().getDisplayMetrics().density*n);}
 static LinearLayout column(Context c){LinearLayout v=new LinearLayout(c);v.setOrientation(LinearLayout.VERTICAL);return v;}
 static GradientDrawable shape(Context c,int color,int radius,int border){GradientDrawable d=new GradientDrawable();d.setColor(color);d.setCornerRadius(dp(c,radius));if(border!=0)d.setStroke(dp(c,1),border);return d;}
 static TextView text(Context c,ThemePalette t,String value,float size,boolean bold){TextView v=new TextView(c);v.setText(value);v.setTextColor(t.text);v.setTextSize(size);v.setTypeface(Typeface.create("sans-serif",bold?Typeface.BOLD:Typeface.NORMAL));v.setLineSpacing(dp(c,2),1);return v;}
 static void add(LinearLayout p,View v,int top,int bottom){if(v==null)return;if(v.getParent() instanceof ViewGroup)((ViewGroup)v.getParent()).removeView(v);LinearLayout.LayoutParams q=new LinearLayout.LayoutParams(-1,-2);q.setMargins(0,dp(p.getContext(),top),0,dp(p.getContext(),bottom));p.addView(v,q);}
 static JSONArray array(JSONObject o,String key){JSONArray a=o==null?null:o.optJSONArray(key);return a==null?new JSONArray():a;}
 static String label(JSONObject o){String s=o.optString("title");return s.isEmpty()||s.equals("Відкрити")?o.optString("text",s):s;}
 static boolean local(Uri u){String host=u.getHost();return host==null||host.equalsIgnoreCase("test.jkunis.eu");}
 public static String route(String original){
  if(original==null)return "";
  try{Uri u=Uri.parse(original);if(!local(u))return original;String p=u.getQueryParameter("p");if((p==null||p.equals("home"))&&("jobs".equals(u.getQueryParameter("view"))||"job-search".equals(u.getFragment()))){Uri.Builder b=u.buildUpon();b.clearQuery();Set<String> keys=u.getQueryParameterNames();for(String k:keys)if(!k.equals("view")&&!k.equals("native"))for(String v:u.getQueryParameters(k))b.appendQueryParameter(k,v);if(p==null)b.appendQueryParameter("p","home");b.appendQueryParameter("native","jobs");b.fragment(null);return b.build().toString();}}catch(RuntimeException ignored){}
  return original;
 }
 public static JSONObject prepare(JSONObject result){
  if(result==null)return null;
  try{JSONObject copy=new JSONObject(result.toString());normalize(array(copy,"nodes"),0);return copy;}catch(JSONException e){return result;}
 }
 private static void normalize(JSONArray list,int depth)throws JSONException{
  if(depth>30)return;
  for(int i=0;i<list.length();i++){
   JSONObject n=list.optJSONObject(i);if(n==null)continue;
   String type=n.optString("type");
   if(type.equals("link"))n.put("route",route(n.optString("route")));
   if(type.equals("details")&&n.optBoolean("profileSection")){
    // Lazy profile panes must register descendant anchors before their contents are built.
    LinkedHashSet<String> ids=new LinkedHashSet<>();JSONArray old=array(n,"anchors");for(int j=0;j<old.length();j++)if(!old.optString(j).isEmpty())ids.add(old.optString(j));anchors(array(n,"children"),ids,0);n.put("anchors",new JSONArray(ids));
   }
   if(type.equals("form")){
    String action="";JSONArray fields=array(n,"fields");for(int j=0;j<fields.length();j++){JSONObject f=fields.optJSONObject(j);if(f!=null&&f.optString("name").equals("action"))action=f.optString("value");}
    if(action.equals("block_peer")){JSONArray buttons=array(n,"buttons");for(int j=0;j<buttons.length();j++){JSONObject b=buttons.optJSONObject(j);if(b!=null&&b.optString("confirm").isEmpty())b.put("confirm","Додати користувача до чорного списку?");}}
   }
   normalize(array(n,"children"),depth+1);
   normalize(array(n,"actions"),depth+1);
   normalize(array(n,"identityChildren"),depth+1);
   normalize(array(n,"profileChildren"),depth+1);
  }
 }
 private static void anchors(JSONArray nodes,Set<String> ids,int depth){if(depth>20)return;for(int i=0;i<nodes.length();i++){JSONObject n=nodes.optJSONObject(i);if(n==null)continue;String id=n.optString("id");if(!id.isEmpty())ids.add(id);anchors(array(n,"children"),ids,depth+1);}}
 public static void remember(Activity a,JSONObject result){home.remove(a);if(result!=null&&result.optString("page").equals("home"))home.put(a,result);}
 public static View home(NativeWelcome welcome,String name,View jobs,View housing,View posts){
  Activity a=welcome.activity;ThemePalette t=welcome.colors;NativeJobsScreen.Host host=welcome.host;LinearLayout page=column(a);page.setTag("batch20-home");
  JSONObject model=home.remove(a);JSONArray nodes=array(model,"nodes");
  if(!(a instanceof MainActivity)||nodes.length()==0){add(page,text(a,t,"Головна поки недоступна. Оновіть сторінку після відновлення зв’язку.",16,false),12,12);return page;}
  MainActivity owner=(MainActivity)a;
  for(int k=0;k<nodes.length();k++){
   JSONObject node=nodes.optJSONObject(k);if(node==null)continue;
   if(k==0&&node.optString("type").equals("card")){
    JSONArray cs=array(node,"children");NativeSiteUi.Flow shortcuts=new NativeSiteUi.Flow(a,8);boolean flushed=false;
    for(int i=0;i<cs.length();i++){
     JSONObject n=cs.optJSONObject(i);if(n==null)continue;String kind=n.optString("type");
     if(!flushed&&(kind.equals("heading")||kind.equals("text"))){TextView v=text(a,t,n.optString("text"),kind.equals("heading")?24:14,kind.equals("heading"));if(!kind.equals("heading"))v.setTextColor(t.muted);add(page,v,0,8);}
     else if(!flushed&&kind.equals("link")){String title=label(n);TextView b=text(a,t,title,13,true);b.setPadding(dp(a,12),dp(a,9),dp(a,12),dp(a,9));b.setMinHeight(dp(a,44));b.setGravity(Gravity.CENTER);b.setBackground(shape(a,t.surface,15,t.border));b.setContentDescription(title);b.setFocusable(true);b.setOnClickListener(v->{if(host.alive())host.navigate(route(n.optString("route")));});shortcuts.addView(b);}
     else{if(!flushed){add(page,shortcuts,4,18);flushed=true;}add(page,section(owner,t,host,n),0,16);}
    }
    if(!flushed&&shortcuts.getChildCount()>0)add(page,shortcuts,4,16);
   }else add(page,section(owner,t,host,node),0,16);
  }
  return page;
 }
 private static View section(MainActivity a,ThemePalette t,NativeJobsScreen.Host host,JSONObject n){
  // Preserve the server's native forms and expandable challenge contents instead of dropping them.
  if(!n.optString("type").equals("card"))return a.batch20Nodes(new JSONArray().put(n));
  JSONArray cs=array(n,"children");List<JSONObject> items=new ArrayList<>();JSONArray head=new JSONArray();
  boolean collection=false;
  for(int i=0;i<cs.length();i++){JSONObject c=cs.optJSONObject(i);if(c==null)continue;String r=c.optString("route");boolean entity=c.optString("type").equals("link")&&(r.contains("p=job&")||r.contains("p=housing&"));if(entity){items.add(c);collection=true;}else head.put(c);}
  if(!collection)return a.batch20Nodes(new JSONArray().put(n));
  LinearLayout section=column(a);add(section,a.batch20Nodes(head),0,7);
  boolean one=a.getResources().getConfiguration().fontScale>1.2f||a.getResources().getDisplayMetrics().widthPixels/a.getResources().getDisplayMetrics().density<360;
  for(int i=0;i<items.size();i+=one?1:2){LinearLayout row=new LinearLayout(a);row.setBaselineAligned(false);int end=Math.min(items.size(),i+(one?1:2));for(int j=i;j<end;j++){
   View item=entity(a,t,host,items.get(j));LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(0,-1,1);if(j>i)lp.setMarginStart(dp(a,10));row.addView(item,lp);
  }if(!one&&end-i==1)row.addView(new View(a),new LinearLayout.LayoutParams(0,1,1));add(section,row,0,10);}
  return section;
 }
 private static View entity(MainActivity a,ThemePalette t,NativeJobsScreen.Host host,JSONObject n){
  LinearLayout card=column(a);card.setBackground(shape(a,t.surface,15,t.border));card.setClipToOutline(true);card.setMinimumHeight(dp(a,70));
  String image=n.optString("image");if(!image.isEmpty()){View v=host.image(image);if(v instanceof ImageView)((ImageView)v).setScaleType(ImageView.ScaleType.CENTER_CROP);card.addView(v,new LinearLayout.LayoutParams(-1,dp(a,125)));}
  LinearLayout copy=column(a);copy.setPadding(dp(a,12),dp(a,12),dp(a,12),dp(a,12));add(copy,text(a,t,label(n),15,true),0,7);JSONArray lines=array(n,"lines");for(int i=0;i<lines.length();i++){String line=lines.optString(i);if(line.isEmpty())continue;TextView v=text(a,t,line,13,false);v.setTextColor(t.muted);add(copy,v,0,5);}card.addView(copy);
  card.setFocusable(true);card.setContentDescription(label(n));card.setOnClickListener(v->{if(host.alive())host.navigate(route(n.optString("route")));});return card;
 }
 /** Labels stay attached to original controls and original server-validated submit handlers. */
 public static View form(JSONObject model,View view){
  if(model==null||view==null)return view;ArrayList<EditText> edits=new ArrayList<>();collectEditors(view,edits);int at=0;JSONArray fs=array(model,"fields");
  for(int i=0;i<fs.length();i++){JSONObject f=fs.optJSONObject(i);if(f==null)continue;String kind=f.optString("type");if(kind.equals("hidden")||kind.equals("file")||kind.equals("select")||kind.equals("checkbox")||kind.equals("radio"))continue;
   if(at>=edits.size())break;EditText e=edits.get(at++);String label=f.optString("label",f.optString("name"));e.setContentDescription("Поле "+f.optString("name")+": "+label);if(f.optBoolean("readOnly"))e.setFocusable(false);
  }return view;
 }
 private static void collectEditors(View v,List<EditText> out){if(v instanceof EditText)out.add((EditText)v);else if(v instanceof ViewGroup){ViewGroup g=(ViewGroup)v;for(int i=0;i<g.getChildCount();i++)collectEditors(g.getChildAt(i),out);}}
 public static View profilePanes(NativeProfileScreen s,View result){
  if(!(result instanceof LinearLayout)||s.strip==null||s.panes.size()<3)return result;LinearLayout box=(LinearLayout)result;ViewGroup parent=(ViewGroup)s.strip.getParent();if(parent==null)return result;int index=parent.indexOfChild(s.strip);parent.removeView(s.strip);LinearLayout bar=new LinearLayout(s.activity);bar.setGravity(Gravity.CENTER_VERTICAL);
  Button prev=new Button(s.activity),next=new Button(s.activity);prev.setText("‹");next.setText("›");for(Button b:new Button[]{prev,next}){b.setMinWidth(0);b.setMinimumWidth(0);b.setPadding(0,0,0,0);b.setTextSize(23);b.setTextColor(s.colors.accent);b.setBackgroundColor(0);}
  prev.setContentDescription("Попередні розділи анкети");next.setContentDescription("Наступні розділи анкети");prev.setOnClickListener(v->s.strip.smoothScrollBy(-s.strip.getWidth()*3/4,0));next.setOnClickListener(v->s.strip.smoothScrollBy(s.strip.getWidth()*3/4,0));bar.addView(prev,new LinearLayout.LayoutParams(dp(s.activity,34),dp(s.activity,48)));bar.addView(s.strip,new LinearLayout.LayoutParams(0,-2,1));bar.addView(next,new LinearLayout.LayoutParams(dp(s.activity,34),dp(s.activity,48)));box.addView(bar,index,new LinearLayout.LayoutParams(-1,-2));return result;
 }
}
