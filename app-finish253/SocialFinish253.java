package eu.svoyi.nativeapp;

import android.app.*;
import android.content.*;
import android.graphics.*;
import android.graphics.drawable.GradientDrawable;
import android.text.TextUtils;
import android.view.*;
import android.view.inputmethod.EditorInfo;
import android.widget.*;
import org.json.JSONObject;
import java.util.*;

/** UI-only second finish pass for social, dating, housing, notifications and mail.
 * Reuses the existing server data, routes and click handlers. */
public final class SocialFinish253 {
    private SocialFinish253(){}
    private static final Set<String> SOCIAL=new HashSet<>(Arrays.asList(
        "dating","nearby","housing","groups","group","feed","events","event","notifications","mail","messages","chat"
    ));

    public static void apply(Activity a,JSONObject model){
        if(a==null||model==null)return;
        final String page=model.optString("page","");
        if(!SOCIAL.contains(page))return;
        View decor=a.findViewById(android.R.id.content);if(decor==null)return;
        decor.post(()->{
            tuneTree(decor,a,page);
            if("mail".equals(page)||"messages".equals(page)||"chat".equals(page))tuneMail(decor,a);
            if("dating".equals(page)||"nearby".equals(page))tuneDating(decor,a);
            if("housing".equals(page))tuneHousing(decor,a);
            if("groups".equals(page)||"group".equals(page)||"feed".equals(page))tuneCommunity(decor,a);
            if("notifications".equals(page))tuneNotifications(decor,a);
        });
    }

    private static void tuneTree(View v,Activity a,String page){
        int d=dp(a,1);
        if(v instanceof Button){
            Button b=(Button)v;b.setAllCaps(false);b.setMinHeight(48*d);
            b.setPadding(Math.max(b.getPaddingLeft(),12*d),Math.max(b.getPaddingTop(),8*d),Math.max(b.getPaddingRight(),12*d),Math.max(b.getPaddingBottom(),8*d));
        }else if(v instanceof EditText){
            EditText e=(EditText)v;e.setMinHeight(48*d);e.setTextSize(Math.max(15,e.getTextSize()/a.getResources().getDisplayMetrics().scaledDensity));
            e.setPadding(Math.max(e.getPaddingLeft(),12*d),Math.max(e.getPaddingTop(),9*d),Math.max(e.getPaddingRight(),12*d),Math.max(e.getPaddingBottom(),9*d));
            e.setImeOptions(e.getImeOptions()|EditorInfo.IME_FLAG_NO_EXTRACT_UI);
        }else if(v instanceof TextView){
            TextView t=(TextView)v;t.setLineSpacing(dp(a,2),1.02f);
        }else if(v instanceof ImageView){
            ImageView im=(ImageView)v;im.setAdjustViewBounds(true);
        }
        if(v instanceof HorizontalScrollView)((HorizontalScrollView)v).setHorizontalScrollBarEnabled(false);
        if(v instanceof ViewGroup){
            ViewGroup g=(ViewGroup)v;
            if(v.isClickable()&&v.getMinimumHeight()<48*d)v.setMinimumHeight(48*d);
            for(int i=0;i<g.getChildCount();i++)tuneTree(g.getChildAt(i),a,page);
        }
    }

    private static void tuneMail(View root,Activity a){
        final EditText composer=findComposer(root);
        if(composer!=null){
            composer.setMinHeight(dp(a,54));composer.setMaxLines(5);composer.setSingleLine(false);composer.setHorizontallyScrolling(false);
            composer.setGravity(Gravity.TOP|Gravity.START);composer.setContentDescription("Поле нового повідомлення");
            composer.setOnFocusChangeListener((v,focused)->{
                ViewGroup parent=(ViewGroup)composer.getParent();
                if(parent!=null)parent.setMinimumHeight(focused?dp(a,64):0);
            });
        }
        walk(root,v->{
            CharSequence d=v.getContentDescription();
            String s=d==null?"":d.toString().toLowerCase(Locale.ROOT);
            if(s.contains("повідомлен")||s.contains("message")){
                if(v.isClickable())v.setMinimumHeight(Math.max(v.getMinimumHeight(),dp(a,52)));
            }
        });
    }

    private static void tuneDating(View root,Activity a){
        walk(root,v->{
            if(v instanceof ImageView){
                ImageView im=(ImageView)v;
                ViewParent p=im.getParent();
                if(p instanceof View&&((View)p).isClickable()){
                    im.setScaleType(ImageView.ScaleType.CENTER_CROP);
                    if(im.getMinimumHeight()<dp(a,160))im.setMinimumHeight(dp(a,160));
                }
            }
            if(v instanceof TextView){
                TextView t=(TextView)v;String s=t.getText().toString();
                if(isOneOf(s,"Подобається","Лайк","Like","Líbí se","Super like","Super Like","Написати","Napsat","Message")){
                    t.setMinHeight(dp(a,48));t.setGravity((t.getGravity()&~Gravity.VERTICAL_GRAVITY_MASK)|Gravity.CENTER_VERTICAL);
                }
            }
        });
    }

    private static void tuneHousing(View root,Activity a){
        walk(root,v->{
            if(v instanceof ImageView&&v.getParent() instanceof View&&((View)v.getParent()).isClickable()){
                ((ImageView)v).setScaleType(ImageView.ScaleType.CENTER_CROP);v.setMinimumHeight(Math.max(v.getMinimumHeight(),dp(a,110)));
            }
            if(v instanceof ViewGroup&&v.isClickable())v.setMinimumHeight(Math.max(v.getMinimumHeight(),dp(a,72)));
        });
    }

    private static void tuneCommunity(View root,Activity a){
        walk(root,v->{
            if(v instanceof TextView){
                TextView t=(TextView)v;String s=t.getText().toString();
                if(isOneOf(s,"Відповісти","Reply","Odpovědět","Редагувати","Edit","Upravit","Видалити","Delete","Smazat")){
                    t.setMinHeight(dp(a,44));t.setGravity((t.getGravity()&~Gravity.VERTICAL_GRAVITY_MASK)|Gravity.CENTER_VERTICAL);
                    t.setPadding(Math.max(t.getPaddingLeft(),8*dp(a,1)),t.getPaddingTop(),Math.max(t.getPaddingRight(),8*dp(a,1)),t.getPaddingBottom());
                }
            }
        });
    }

    private static void tuneNotifications(View root,Activity a){
        walk(root,v->{if(v instanceof ViewGroup&&v.isClickable())v.setMinimumHeight(Math.max(v.getMinimumHeight(),dp(a,64)));});
    }

    private static EditText findComposer(View root){
        final EditText[] best={null};final int[] score={Integer.MIN_VALUE};
        walk(root,v->{
            if(!(v instanceof EditText))return;EditText e=(EditText)v;String hint=String.valueOf(e.getHint()).toLowerCase(Locale.ROOT);
            String desc=String.valueOf(e.getContentDescription()).toLowerCase(Locale.ROOT);
            int s=0;if(hint.contains("повідом")||hint.contains("message")||hint.contains("zpráv"))s+=10;
            if(desc.contains("повідом")||desc.contains("message"))s+=6;
            if(!e.isSingleLine())s+=2;
            int[] loc=new int[2];e.getLocationOnScreen(loc);s+=Math.min(5,loc[1]/400);
            if(s>score[0]){score[0]=s;best[0]=e;}
        });return score[0]>=4?best[0]:null;
    }

    private static boolean isOneOf(String s,String... values){for(String v:values)if(s.equalsIgnoreCase(v))return true;return false;}
    private interface Visitor{void visit(View v);}
    private static void walk(View v,Visitor x){x.visit(v);if(v instanceof ViewGroup){ViewGroup g=(ViewGroup)v;for(int i=0;i<g.getChildCount();i++)walk(g.getChildAt(i),x);}}
    private static int dp(Context c,int n){return Math.round(c.getResources().getDisplayMetrics().density*n);}
}
