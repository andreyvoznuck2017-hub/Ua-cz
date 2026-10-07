package eu.svoyi.nativeapp;
import android.app.*;import android.content.*;import android.view.*;import android.widget.*;import org.json.*;import java.util.*;
class ThemePalette {int background,surface,text,muted,accent,border,field,primaryText,ownBubble,ownText;boolean dark;String key;}
class MainActivity extends Activity {public View batch20Nodes(JSONArray n){return null;}}
class NativeWelcome {Activity activity;ThemePalette colors;NativeJobsScreen.Host host;}
class NativeJobsScreen {interface Host {boolean alive();void navigate(String r);View image(String u);}}
class NativeSiteUi {static final class Flow extends ViewGroup {Flow(Context c,int n){super(c);}protected void onLayout(boolean c,int l,int t,int r,int b){}}}
class AppFinish252 {public static String route(String s){return s;}}
class NativeMailInboxRow extends LinearLayout {NativeMailInboxRow(Context c){super(c);}}
class NativeMailScreen {
 Activity activity;ThemePalette theme;Host host;int peer;boolean unreadOnly,moreConversations;
 LinearLayout root,inboxList,header,composer;EditText search,input,historySearch;
 TextView inboxScope,presence,characterCount,sendState;Button allInbox,unreadInbox,retrySend;View send;
 LinkedHashMap<Integer,JSONObject> conversations;
 boolean alive(){return true;}
 interface Host {void navigate(String route);}
}
