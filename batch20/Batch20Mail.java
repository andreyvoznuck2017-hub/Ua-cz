package eu.svoyi.nativeapp;

import android.content.Context;
import android.net.ConnectivityManager;
import android.net.NetworkCapabilities;
import android.os.SystemClock;
import android.view.*;
import android.widget.*;
import org.json.JSONObject;
import java.util.*;

/** UI-scoped mail work; existing transport, nonces, permissions and encrypted draft storage stay authoritative. */
public final class Batch20Mail {
 private Batch20Mail(){}
 private static final Map<NativeMailScreen,State> states=new WeakHashMap<>();
 private static final class State {
  Button earlier,stop;ProgressBar progress;TextView hint;
  boolean scanning;String query="";int remaining,first,count;long since,lastTouch;
 }
 private static State state(NativeMailScreen s){State v=states.get(s);if(v==null){v=new State();states.put(s,v);}return v;}
 private static int dp(NativeMailScreen s,int n){return Math.round(s.activity.getResources().getDisplayMetrics().density*n);}
 public static void attached(NativeMailScreen s){
  if(!s.alive()||s.root==null||s.peer<=0)return;State st=state(s);
  if(s.historySearchRow!=null&&s.historySearchRow.findViewWithTag("batch20-older-search")==null){
   LinearLayout controls=new LinearLayout(s.activity);controls.setGravity(Gravity.CENTER_VERTICAL);controls.setTag("batch20-older-search");st.earlier=new Button(s.activity);st.earlier.setText("Шукати в давніших повідомленнях");st.earlier.setTextSize(13);st.earlier.setAllCaps(false);st.earlier.setContentDescription("Шукати в давніших повідомленнях");st.earlier.setOnClickListener(v->startSearch(s));controls.addView(st.earlier,new LinearLayout.LayoutParams(0,-2,1));
   st.stop=new Button(s.activity);st.stop.setText("Зупинити");st.stop.setAllCaps(false);st.stop.setTextSize(13);st.stop.setOnClickListener(v->{st.scanning=false;searchUpdated(s);});controls.addView(st.stop,new LinearLayout.LayoutParams(-2,-2));s.historySearchRow.addView(controls);
   st.hint=new TextView(s.activity);st.hint.setTextColor(s.theme.muted);st.hint.setTextSize(12);st.hint.setPadding(dp(s,8),0,dp(s,8),dp(s,4));st.hint.setAccessibilityLiveRegion(View.ACCESSIBILITY_LIVE_REGION_POLITE);s.historySearchRow.addView(st.hint);
  }
  if(s.newMessages!=null)s.newMessages.setContentDescription("Перейти до нових повідомлень");
  if(s.scroll!=null){s.scroll.setContentDescription("Історія повідомлень");s.scroll.setOnTouchListener((v,event)->{if(event.getActionMasked()==MotionEvent.ACTION_DOWN||event.getActionMasked()==MotionEvent.ACTION_MOVE)st.lastTouch=SystemClock.uptimeMillis();return false;});}
  if(s.composer!=null&&s.root.findViewWithTag("batch20-send-progress")==null){st.progress=new ProgressBar(s.activity,null,android.R.attr.progressBarStyleHorizontal);st.progress.setIndeterminate(true);st.progress.setTag("batch20-send-progress");st.progress.setContentDescription("Триває обробка повідомлення або вкладення");st.progress.setVisibility(View.GONE);int at=s.root.indexOfChild(s.composer);s.root.addView(st.progress,Math.max(0,at),new LinearLayout.LayoutParams(-1,dp(s,3)));}
  searchUpdated(s);composerUpdated(s);
 }
 public static View message(NativeMailScreen s,JSONObject m,View row){
  if(row==null||m==null||m.optInt("id")<=0)return row;int id=m.optInt("id");row.setContentDescription("Дії повідомлення "+id);row.setLongClickable(true);row.setOnLongClickListener(v->{if(!s.alive())return false;JSONObject current=s.model.messages.get(id);if(current==null)return false;s.messageTools(current);return true;});return row;
 }
 private static String query(NativeMailScreen s){return s.historySearch==null?"":s.historySearch.getText().toString().trim();}
 private static void startSearch(NativeMailScreen s){
  if(!s.alive()||s.paused||s.historyBusy||!s.hasOlder||query(s).isEmpty())return;State st=state(s);st.scanning=true;st.query=query(s);st.remaining=5;st.count=s.historyMatches.size();st.since=SystemClock.uptimeMillis();loadNext(s,st);
 }
 private static void loadNext(NativeMailScreen s,State st){
  if(!s.alive()||s.paused||!st.scanning||s.historySearchRow==null||s.historySearchRow.getVisibility()!=View.VISIBLE||!st.query.equals(query(s))){st.scanning=false;searchUpdated(s);return;}
  if(s.historyBusy)return;
  if(!s.hasOlder||st.remaining<=0||SystemClock.uptimeMillis()-st.since>30000){st.scanning=false;searchUpdated(s);return;}
  st.first=s.model.first();st.remaining--;s.loadOlder();searchUpdated(s);
 }
 public static void applied(NativeMailScreen s){
  State st=states.get(s);if(st==null)return;
  if(st.scanning&&!s.historyBusy){
   if(!st.query.equals(query(s))||s.model.first()>=st.first){st.scanning=false;}
   else if(s.historyMatches.size()>st.count){st.scanning=false;for(Integer id:s.historyMatches)if(id<st.first){s.jumpMessage(id);break;}}
   else s.ui.postDelayed(()->loadNext(s,st),160);
  }
  searchUpdated(s);composerUpdated(s);
 }
 public static void searchUpdated(NativeMailScreen s){
  State st=states.get(s);if(st==null||st.earlier==null)return;
  if(!st.query.equals(query(s)))st.scanning=false;
  st.earlier.setEnabled(s.alive()&&!s.paused&&!s.historyBusy&&!st.scanning&&s.hasOlder&&!query(s).isEmpty());st.stop.setVisibility(st.scanning?View.VISIBLE:View.GONE);
  String summary=s.historyBusy&&st.scanning?"Перевіряю давніші повідомлення…":s.hasOlder?"Пошук охоплює завантажену історію. Продовжуйте, щоб перевірити давніші повідомлення.":"Перевірено всю доступну історію цієї переписки.";
  st.hint.setText(summary);st.earlier.setVisibility(s.hasOlder?View.VISIBLE:View.GONE);
 }
 public static void searchFailed(NativeMailScreen s){State st=states.get(s);if(st!=null)st.scanning=false;searchUpdated(s);}
 public static void composerUpdated(NativeMailScreen s){State st=states.get(s);if(st!=null&&st.progress!=null)st.progress.setVisibility(s.sending||s.staging?View.VISIBLE:View.GONE);if(s.retrySend!=null)s.retrySend.setContentDescription("Повторити невдале надсилання без дублювання");}
 public static boolean beforeSend(NativeMailScreen s){
  if(!s.alive()||s.paused||s.sending)return false;
  try{ConnectivityManager c=(ConnectivityManager)s.activity.getSystemService(Context.CONNECTIVITY_SERVICE);if(c!=null&&c.getActiveNetwork()==null){s.saveDraft();s.status("Немає мережі. Чернетку збережено — надішліть після відновлення зв’язку.",true);return false;}}catch(SecurityException ignored){}
  // A present network is not evidence of internet reachability; the transport still decides success.
  return true;
 }
 public static void viewportBottom(NativeMailScreen s){
  State st=states.get(s);if(!s.alive()||s.scroll==null||s.list==null)return;
  // Do not let an already-queued keyboard layout callback override a more recent reading gesture.
  if(st!=null&&SystemClock.uptimeMillis()-st.lastTouch<900&&!s.atBottom())return;
  if(s.input!=null&&s.input.hasFocus()||s.atBottom())s.scroll.scrollTo(0,s.list.getHeight());
 }
 public static void inbox(NativeMailScreen s){
  if(s.inboxScope!=null){s.inboxScope.setVisibility(View.VISIBLE);s.inboxScope.setTextSize(12);s.inboxScope.setTextColor(s.theme.muted);}
  if(s.search!=null)s.search.setHint("Знайти серед завантажених діалогів…");
  if(s.allInbox!=null&&s.allInbox.getParent() instanceof View)((View)s.allInbox.getParent()).setVisibility(View.VISIBLE);
 }
 public static void close(NativeMailScreen s){State st=states.remove(s);if(st!=null)st.scanning=false;}
}
