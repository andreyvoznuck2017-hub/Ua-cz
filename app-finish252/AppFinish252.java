package eu.svoyi.nativeapp;

import android.app.Activity;
import android.net.Uri;
import android.view.View;
import android.view.ViewGroup;
import android.widget.*;
import org.json.JSONObject;
import java.util.*;

/** Final integration layer: keeps server actions, fixes local routes and applies site-matched native screens. */
public final class AppFinish252 {
    private static final Map<Activity,JSONObject> home = new WeakHashMap<>();
    private static final Set<String> POLISH = new HashSet<>(Arrays.asList(
        "dating","nearby","people","online","events","event","housing","feed","chat","rides",
        "business","groups","courses","guides","entertainment","finance","plans","promotion",
        "analytics","notifications","search","shop","saved","applications","recommended","cv"
    ));
    private AppFinish252(){}

    public static void remember(Activity a,JSONObject model){
        if(a==null||model==null)return;
        String page=model.optString("page","");
        if("home".equals(page)){
            try{home.put(a,new JSONObject(model.toString()));}catch(Exception e){home.put(a,model);}
        }
        if("profile".equals(page))AccountScreen252.apply(a,model,AccountScreen252.SITE);
        if(POLISH.contains(page))polish(a,model);
    }

    public static View home(NativeWelcome welcome,String name,View jobs,View housing,View posts){
        JSONObject model=home.remove(welcome.activity);
        return HomeScreen252.buildSite(welcome,model==null?new JSONObject():model);
    }

    /** Converts every local website URL to one canonical in-app relative route without losing filters/back params. */
    public static String route(String original){
        if(original==null||original.trim().isEmpty())return "/?p=home";
        try{
            Uri u=Uri.parse(original.trim());
            String scheme=u.getScheme(),host=u.getHost();
            boolean local=host==null||host.isEmpty()||host.equalsIgnoreCase("test.jkunis.eu")||host.endsWith(".jkunis.eu");
            if(!local)return original;
            if(scheme!=null&&!scheme.isEmpty()&&!"http".equalsIgnoreCase(scheme)&&!"https".equalsIgnoreCase(scheme))return original;
            String p=u.getQueryParameter("p");
            Uri fixed=u;
            if((p==null||"home".equals(p))&&("jobs".equals(u.getQueryParameter("view"))||"job-search".equals(u.getFragment()))){
                Uri.Builder b=u.buildUpon();
                if(p==null)b.appendQueryParameter("p","home");
                if(u.getQueryParameter("native")==null)b.appendQueryParameter("native","jobs");
                fixed=b.build();
            }
            String path=fixed.getEncodedPath();
            if(path==null||path.isEmpty())path="/";
            StringBuilder out=new StringBuilder(path);
            String q=fixed.getEncodedQuery();if(q!=null&&!q.isEmpty())out.append('?').append(q);
            String f=fixed.getEncodedFragment();if(f!=null&&!f.isEmpty())out.append('#').append(f);
            return out.toString();
        }catch(RuntimeException e){return original;}
    }

    /** Light-touch styling for the remaining server-rendered native screens; handlers and data stay untouched. */
    private static void polish(Activity a,JSONObject model){
        View decor=a.findViewById(android.R.id.content);
        if(decor==null)return;
        decor.post(()->walk(decor,a));
    }
    private static void walk(View v,Activity a){
        int d=Math.max(1,Math.round(a.getResources().getDisplayMetrics().density));
        if(v instanceof Button){
            Button b=(Button)v;b.setAllCaps(false);b.setMinHeight(48*d);
            if(b.getPaddingLeft()<10*d)b.setPadding(12*d,8*d,12*d,8*d);
        }else if(v instanceof EditText){
            EditText e=(EditText)v;e.setMinHeight(48*d);
            if(e.getPaddingLeft()<10*d)e.setPadding(12*d,8*d,12*d,8*d);
        }else if(v instanceof TextView){
            TextView t=(TextView)v;t.setLineSpacing(2*d,1.02f);
        }else if(v instanceof ImageView){
            ((ImageView)v).setAdjustViewBounds(true);
        }
        if(v instanceof HorizontalScrollView)((HorizontalScrollView)v).setHorizontalScrollBarEnabled(false);
        if(v instanceof ViewGroup){
            ViewGroup g=(ViewGroup)v;
            if(v.isClickable()&&v.getMinimumHeight()<48*d)v.setMinimumHeight(48*d);
            for(int i=0;i<g.getChildCount();i++)walk(g.getChildAt(i),a);
        }
    }
}
