package eu.svoyi.nativeapp;

import android.app.*;
import android.content.*;
import android.graphics.*;
import android.graphics.drawable.*;
import android.os.*;
import android.text.TextUtils;
import android.view.*;
import android.view.inputmethod.EditorInfo;
import android.widget.*;
import org.json.JSONObject;
import java.util.*;

/**
 * 2.5.3 social-core UI pass.
 * Restyles only already-rendered native views and never replaces their click handlers,
 * form callbacks, server permissions or transport.
 */
public final class SocialUi253 {
    private SocialUi253(){}
    private static final Set<String> PAGES=new HashSet<>(Arrays.asList(
        "dating","nearby","housing","groups","feed","messages","notifications","events"
    ));
    public static void apply(Activity a,JSONObject model){
        if(a==null||model==null)return;
        String page=page(model);if(!PAGES.contains(page))return;
        View decor=a.findViewById(android.R.id.content);if(decor==null)return;
        Runnable work=()->restyle(a,decor,page,model);
        decor.post(work);decor.postDelayed(work,260);
    }
    private static String page(JSONObject m){
        String p=m.optString("page","");
        if(!p.isEmpty())return p;
        String r=m.optString("route","");
        try{String q=android.net.Uri.parse(r).getQueryParameter("p");return q==null?"":q;}catch(RuntimeException e){return "";}
    }
    private static void restyle(Activity a,View decor,String page,JSONObject model){
        a.getWindow().setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE|WindowManager.LayoutParams.SOFT_INPUT_STATE_UNCHANGED);
        walk(a,decor,page);
        if("dating".equals(page)||"nearby".equals(page))dating(a,decor);
        else if("housing".equals(page))housing(a,decor);
        else if("groups".equals(page)||"feed".equals(page))social(a,decor);
        else if("messages".equals(page))mail(a,decor);
        else if("notifications".equals(page))notifications(a,decor);
    }
    private static void walk(Activity a,View v,String page){
        int d=dp(a,1);
        if(v instanceof Button){
            Button b=(Button)v;b.setAllCaps(false);b.setMinHeight(48*d);b.setMinWidth(48*d);
            if(b.getPaddingLeft()<10*d)b.setPadding(12*d,8*d,12*d,8*d);
        }else if(v instanceof EditText){
            EditText e=(EditText)v;e.setMinHeight(50*d);e.setTextSize(Math.max(16,e.getTextSize()/a.getResources().getDisplayMetrics().scaledDensity));
            e.setImeOptions(e.getImeOptions()|EditorInfo.IME_FLAG_NO_EXTRACT_UI);
            if(e.getPaddingLeft()<10*d)e.setPadding(12*d,9*d,12*d,9*d);
        }else if(v instanceof TextView){
            TextView t=(TextView)v;t.setLineSpacing(dp(a,2),1.03f);
            String s=t.getText()==null?"":t.getText().toString();
            if(actionText(s)){t.setMinHeight(dp(a,44));t.setGravity((t.getGravity()&Gravity.HORIZONTAL_GRAVITY_MASK)|Gravity.CENTER_VERTICAL);if(t.getPaddingLeft()<dp(a,8))t.setPadding(dp(a,8),dp(a,6),dp(a,8),dp(a,6));}
        }else if(v instanceof ImageView){
            ImageView i=(ImageView)v;i.setAdjustViewBounds(true);
            if(i.getWidth()>=dp(a,180)||i.getHeight()>=dp(a,160))i.setScaleType(ImageView.ScaleType.CENTER_CROP);
        }
        if(v instanceof HorizontalScrollView)((HorizontalScrollView)v).setHorizontalScrollBarEnabled(false);
        if(v instanceof ViewGroup){
            ViewGroup g=(ViewGroup)v;if(v.isClickable()&&v.getMinimumHeight()<dp(a,48))v.setMinimumHeight(dp(a,48));
            for(int i=0;i<g.getChildCount();i++)walk(a,g.getChildAt(i),page);
        }
    }
    private static boolean actionText(String s){
        String x=s.toLowerCase(Locale.ROOT);
        return x.contains("відпові")||x.contains("редаг")||x.contains("видал")||x.contains("вподоб")||x.contains("лайк")||
               x.contains("reply")||x.contains("edit")||x.contains("delete")||x.contains("like")||
               x.contains("odpově")||x.contains("upravit")||x.contains("smazat")||x.contains("líb");
    }
    private static void dating(Activity a,View root){
        styleTabs(a,root,new String[]{"Поруч","Лайки","Вподобали","Взаємні","Моя анкета","Discover","Nearby","Likes","Matches","Poblíž","Líbí"});
        for(View v:findClickable(root)){
            CharSequence d=v.getContentDescription();String s=d==null?textOf(v):d.toString();
            String low=s.toLowerCase(Locale.ROOT);
            if(low.contains("super")||low.contains("супер"))v.setContentDescription("Super Like — потрібне підтвердження перед дією");
            if(low.contains("подоба")||low.contains("like"))v.setMinimumHeight(dp(a,52));
        }
    }
    private static void housing(Activity a,View root){
        styleTabs(a,root,new String[]{"Усі","Обране","Додати","Favorites","All","Create","Vše","Oblíbené","Přidat"});
        for(ImageView i:findImages(root))if(i.getWidth()>=dp(a,150)||i.getHeight()>=dp(a,110)){i.setScaleType(ImageView.ScaleType.CENTER_CROP);i.setClipToOutline(true);}
    }
    private static void social(Activity a,View root){
        styleTabs(a,root,new String[]{"Усі","Мої","Створити","All","Mine","Create","Vše","Moje","Vytvořit"});
        for(TextView t:findTexts(root)){
            String s=t.getText()==null?"":t.getText().toString().toLowerCase(Locale.ROOT);
            if(s.contains("коментар")||s.contains("comment")||s.contains("odpově")){t.setMinHeight(dp(a,44));t.setGravity(Gravity.CENTER_VERTICAL);}
        }
    }
    private static void notifications(Activity a,View root){
        for(View v:findClickable(root)){if(v.getMinimumHeight()<dp(a,58))v.setMinimumHeight(dp(a,58));}
        styleTabs(a,root,new String[]{"Усі","Непрочитані","All","Unread","Vše","Nepřečtené"});
    }
    private static void mail(Activity a,View root){
        EditText input=bottomEdit(root);
        if(input!=null){
            input.setTag("finish253-mail-input");input.setMinHeight(dp(a,50));input.setTextSize(16);input.setSingleLine(false);input.setMaxLines(5);
            input.setHorizontallyScrolling(false);input.setPadding(dp(a,12),dp(a,9),dp(a,12),dp(a,9));
        }
        final View toolbar=root.findViewWithTag("site-match-mail-toolbar");
        final View nav=findBottomNav(root);
        if(root.getViewTreeObserver().isAlive()&&root.getTag(0x7f0f0253)==null){
            ViewTreeObserver.OnGlobalFocusChangeListener l=(oldF,newF)->{
                boolean writing=newF instanceof EditText && (newF==input || ancestorTagged(newF,"finish253-mail-input"));
                if(toolbar!=null)toolbar.setVisibility(writing?View.GONE:View.VISIBLE);
                if(nav!=null)nav.setVisibility(writing?View.GONE:View.VISIBLE);
                if(writing&&newF!=null)newF.post(()->newF.requestFocus());
            };
            root.getViewTreeObserver().addOnGlobalFocusChangeListener(l);
            root.setTag(0x7f0f0253,l);
        }
    }
    private static boolean ancestorTagged(View v,String tag){
        View x=v;while(x!=null){if(tag.equals(x.getTag()))return true;ViewParent p=x.getParent();x=p instanceof View?(View)p:null;}return false;
    }
    private static View findBottomNav(View root){
        ArrayList<TextView> labels=findTexts(root);TextView seed=null;
        for(TextView t:labels){String s=t.getText()==null?"":t.getText().toString();if("Головна".equals(s)||"Повідомлення".equals(s)||"Сповіщення".equals(s)||"Профіль".equals(s)){seed=t;break;}}
        if(seed==null)return null;View x=seed;
        while(x.getParent() instanceof ViewGroup){ViewGroup g=(ViewGroup)x.getParent();int hits=0;for(int i=0;i<g.getChildCount();i++)hits+=navHits(g.getChildAt(i));if(hits>=3)return g;x=g;}
        return null;
    }
    private static int navHits(View v){int n=0;if(v instanceof TextView){String s=((TextView)v).getText().toString();if("Головна".equals(s)||"Повідомлення".equals(s)||s.startsWith("Сповіщення")||"Профіль".equals(s))n++;}if(v instanceof ViewGroup){ViewGroup g=(ViewGroup)v;for(int i=0;i<g.getChildCount();i++)n+=navHits(g.getChildAt(i));}return n;}
    private static void styleTabs(Activity a,View root,String[] labels){
        Set<String> set=new HashSet<>(Arrays.asList(labels));
        for(TextView t:findTexts(root)){
            String s=t.getText()==null?"":t.getText().toString().trim();boolean hit=false;
            for(String q:set)if(!q.isEmpty()&&s.toLowerCase(Locale.ROOT).contains(q.toLowerCase(Locale.ROOT))&&s.length()<=40){hit=true;break;}
            if(!hit)continue;
            t.setMinHeight(dp(a,44));t.setGravity(Gravity.CENTER);t.setPadding(dp(a,12),dp(a,7),dp(a,12),dp(a,7));t.setMaxLines(1);t.setEllipsize(TextUtils.TruncateAt.END);
        }
    }
    private static EditText bottomEdit(View root){
        EditText best=null;int y=-1;for(EditText e:findEdits(root)){int[] p=new int[2];try{e.getLocationOnScreen(p);}catch(RuntimeException ex){continue;}if(p[1]>y){y=p[1];best=e;}}return best;
    }
    private static String textOf(View v){if(v instanceof TextView)return ((TextView)v).getText().toString();return "";}
    private static ArrayList<View> findClickable(View root){ArrayList<View> out=new ArrayList<>();walkViews(root,v->{if(v.isClickable())out.add(v);});return out;}
    private static ArrayList<TextView> findTexts(View root){ArrayList<TextView> out=new ArrayList<>();walkViews(root,v->{if(v instanceof TextView)out.add((TextView)v);});return out;}
    private static ArrayList<EditText> findEdits(View root){ArrayList<EditText> out=new ArrayList<>();walkViews(root,v->{if(v instanceof EditText)out.add((EditText)v);});return out;}
    private static ArrayList<ImageView> findImages(View root){ArrayList<ImageView> out=new ArrayList<>();walkViews(root,v->{if(v instanceof ImageView)out.add((ImageView)v);});return out;}
    private interface Visit{void on(View v);}
    private static void walkViews(View v,Visit x){x.on(v);if(v instanceof ViewGroup){ViewGroup g=(ViewGroup)v;for(int i=0;i<g.getChildCount();i++)walkViews(g.getChildAt(i),x);}}
    private static int dp(Context c,float v){return Math.round(c.getResources().getDisplayMetrics().density*v);}
}
