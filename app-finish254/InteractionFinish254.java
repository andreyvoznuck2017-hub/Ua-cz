package eu.svoyi.nativeapp;

import android.app.*;
import android.content.*;
import android.graphics.Rect;
import android.view.*;
import android.view.inputmethod.EditorInfo;
import android.view.inputmethod.InputMethodManager;
import android.widget.*;
import org.json.JSONObject;
import java.util.*;

/** Final interaction pass: restores list position per account/page and hardens mobile focus/touch behavior
 * without replacing existing server handlers, transport, permissions or data models. */
public final class InteractionFinish254 {
    private InteractionFinish254(){}
    private static final Set<String> PAGES=new HashSet<>(Arrays.asList(
        "dating","nearby","housing","groups","group","feed","events","event","notifications","mail","messages","chat"
    ));
    private static final WeakHashMap<ScrollView,ViewTreeObserver.OnScrollChangedListener> listeners=new WeakHashMap<>();

    public static void apply(Activity a,JSONObject model){
        if(a==null||model==null)return;
        final String page=model.optString("page","");
        if(!PAGES.contains(page))return;
        final long account=account(model);
        View decor=a.findViewById(android.R.id.content);if(decor==null)return;
        decor.post(()->{
            restoreScroll(a,decor,page,account);
            tuneClicks(a,decor);
            if("mail".equals(page)||"messages".equals(page)||"chat".equals(page))tuneMail(a,decor);
            if("notifications".equals(page))tuneNotifications(a,decor);
            if("dating".equals(page)||"nearby".equals(page))tuneDating(a,decor);
            if("groups".equals(page)||"group".equals(page)||"feed".equals(page))tuneCommunity(a,decor);
            if("housing".equals(page))tuneHousing(a,decor);
        });
    }

    private static long account(JSONObject model){
        JSONObject state=model.optJSONObject("state"),user=state==null?null:state.optJSONObject("user");
        return user==null?0:user.optLong("id",0);
    }

    private static void restoreScroll(Activity a,View root,String page,long account){
        ScrollView sc=findLargestScroll(root);if(sc==null)return;
        String key="scroll:"+account+":"+page;
        SharedPreferences p=a.getSharedPreferences("svoyi_finish254_ui",Context.MODE_PRIVATE);
        int saved=p.getInt(key,0);
        if(saved>0&&sc.getScrollY()<8)sc.postDelayed(()->{
            if(sc.isAttachedToWindow())sc.scrollTo(0,Math.min(saved,Math.max(0,sc.getChildAt(0)==null?0:sc.getChildAt(0).getHeight()-sc.getHeight())));
        },120);
        if(listeners.containsKey(sc))return;
        final long[] last={0};
        ViewTreeObserver.OnScrollChangedListener l=()->{
            long now=android.os.SystemClock.uptimeMillis();if(now-last[0]<220)return;last[0]=now;
            if(sc.isAttachedToWindow())p.edit().putInt(key,Math.max(0,sc.getScrollY())).apply();
        };
        if(sc.getViewTreeObserver().isAlive()){sc.getViewTreeObserver().addOnScrollChangedListener(l);listeners.put(sc,l);}
        sc.addOnAttachStateChangeListener(new View.OnAttachStateChangeListener(){
            public void onViewAttachedToWindow(View v){}
            public void onViewDetachedFromWindow(View v){
                p.edit().putInt(key,Math.max(0,sc.getScrollY())).apply();
                ViewTreeObserver o=sc.getViewTreeObserver();ViewTreeObserver.OnScrollChangedListener x=listeners.remove(sc);
                if(x!=null&&o.isAlive())o.removeOnScrollChangedListener(x);
                sc.removeOnAttachStateChangeListener(this);
            }
        });
    }

    private static ScrollView findLargestScroll(View v){
        final ScrollView[] best={null};final int[] area={-1};
        walk(v,x->{if(x instanceof ScrollView){int a=Math.max(1,x.getWidth())*Math.max(1,x.getHeight());if(a>area[0]){area[0]=a;best[0]=(ScrollView)x;}}});
        return best[0];
    }

    private static void tuneClicks(Activity a,View root){
        int min=dp(a,48);
        walk(root,v->{
            if(v.isClickable()&&v.getMinimumHeight()<min)v.setMinimumHeight(min);
            if(v instanceof Button)((Button)v).setAllCaps(false);
            if(v instanceof HorizontalScrollView)((HorizontalScrollView)v).setHorizontalScrollBarEnabled(false);
        });
    }

    private static void tuneMail(Activity a,View root){
        Window w=a.getWindow();if(w!=null)w.setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE|WindowManager.LayoutParams.SOFT_INPUT_STATE_UNCHANGED);
        EditText composer=findComposer(root);if(composer==null)return;
        composer.setSingleLine(false);composer.setMaxLines(6);composer.setMinHeight(dp(a,54));composer.setGravity(Gravity.TOP|Gravity.START);
        composer.setImeOptions(composer.getImeOptions()|EditorInfo.IME_FLAG_NO_EXTRACT_UI);
        composer.setContentDescription("Поле нового повідомлення");
        composer.setOnFocusChangeListener((v,focused)->{
            if(!focused)return;
            composer.postDelayed(()->{
                Rect r=new Rect(0,0,composer.getWidth(),composer.getHeight());
                composer.requestRectangleOnScreen(r,true);
                InputMethodManager ime=(InputMethodManager)a.getSystemService(Context.INPUT_METHOD_SERVICE);
                if(ime!=null&&composer.hasWindowFocus())ime.showSoftInput(composer,InputMethodManager.SHOW_IMPLICIT);
            },160);
        });
    }

    private static EditText findComposer(View root){
        final EditText[] best={null};final int[] score={-999};
        walk(root,v->{if(!(v instanceof EditText))return;EditText e=(EditText)v;
            String h=String.valueOf(e.getHint()).toLowerCase(Locale.ROOT),d=String.valueOf(e.getContentDescription()).toLowerCase(Locale.ROOT);
            int s=0;if(h.contains("повідом")||h.contains("message")||h.contains("zpráv"))s+=10;
            if(d.contains("повідом")||d.contains("message"))s+=5;if(!e.isSingleLine())s+=2;
            int[] loc=new int[2];e.getLocationOnScreen(loc);s+=Math.min(4,loc[1]/500);
            if(s>score[0]){score[0]=s;best[0]=e;}
        });return score[0]>=4?best[0]:null;
    }

    private static void tuneNotifications(Activity a,View root){
        walk(root,v->{if(v instanceof ViewGroup&&v.isClickable()){
            v.setMinimumHeight(Math.max(v.getMinimumHeight(),dp(a,64)));
            if(v.getContentDescription()==null)v.setContentDescription("Відкрити сповіщення");
        }});
    }

    private static void tuneDating(Activity a,View root){
        walk(root,v->{
            if(v instanceof ImageView&&v.getParent() instanceof View&&((View)v.getParent()).isClickable()){
                ((ImageView)v).setScaleType(ImageView.ScaleType.CENTER_CROP);v.setMinimumHeight(Math.max(v.getMinimumHeight(),dp(a,170)));
            }
            if(v instanceof TextView){
                TextView t=(TextView)v;String s=t.getText().toString().trim().toLowerCase(Locale.ROOT);
                if(s.equals("подобається")||s.equals("like")||s.equals("líbí se")||s.contains("super like")||s.equals("написати")||s.equals("message")||s.equals("napsat")){
                    t.setMinHeight(dp(a,48));t.setGravity((t.getGravity()&~Gravity.VERTICAL_GRAVITY_MASK)|Gravity.CENTER_VERTICAL);
                }
            }
        });
    }

    private static void tuneCommunity(Activity a,View root){
        walk(root,v->{if(v instanceof TextView){
            TextView t=(TextView)v;String s=t.getText().toString().trim().toLowerCase(Locale.ROOT);
            if(s.equals("відповісти")||s.equals("reply")||s.equals("odpovědět")||s.equals("редагувати")||s.equals("edit")||s.equals("upravit")||s.equals("видалити")||s.equals("delete")||s.equals("smazat")){
                t.setMinHeight(dp(a,44));t.setPadding(Math.max(t.getPaddingLeft(),dp(a,8)),t.getPaddingTop(),Math.max(t.getPaddingRight(),dp(a,8)),t.getPaddingBottom());
                t.setGravity((t.getGravity()&~Gravity.VERTICAL_GRAVITY_MASK)|Gravity.CENTER_VERTICAL);
            }
        }});
    }

    private static void tuneHousing(Activity a,View root){
        walk(root,v->{
            if(v instanceof ImageView&&v.getParent() instanceof View&&((View)v.getParent()).isClickable()){
                ((ImageView)v).setScaleType(ImageView.ScaleType.CENTER_CROP);v.setMinimumHeight(Math.max(v.getMinimumHeight(),dp(a,120)));
            }
            if(v instanceof ViewGroup&&v.isClickable())v.setMinimumHeight(Math.max(v.getMinimumHeight(),dp(a,72)));
        });
    }

    private interface Visitor{void visit(View v);}
    private static void walk(View v,Visitor x){x.visit(v);if(v instanceof ViewGroup){ViewGroup g=(ViewGroup)v;for(int i=0;i<g.getChildCount();i++)walk(g.getChildAt(i),x);}}
    private static int dp(Context c,int n){return Math.round(c.getResources().getDisplayMetrics().density*n);}
}
