package eu.svoyi.nativeapp;

import android.app.*;
import android.content.*;
import android.graphics.*;
import android.graphics.drawable.*;
import android.view.*;
import android.widget.*;
import org.json.*;
import java.util.*;

/** Restyles the already-rendered personal cabinet while reusing original action Views and listeners. */
public final class AccountScreen251 {
    public static final int SITE=0, PLUS=1;
    private static final int BG=Color.rgb(244,247,252), CARD=Color.WHITE, TEXT=Color.rgb(24,38,61), MUTED=Color.rgb(83,104,136), BLUE=Color.rgb(42,96,227), BORDER=Color.rgb(216,225,238), SOFT=Color.rgb(239,244,252);
    private AccountScreen251(){}

    public static void apply(Activity activity,JSONObject model,int variant){
        if(activity==null||model==null)return;
        View decor=activity.findViewById(android.R.id.content);
        if(decor==null)return;
        decor.post(()->restyle(activity,decor,model,variant));
    }

    private static void restyle(Activity a,View decor,JSONObject model,int variant){
        String lang=language(model);
        TextView marker=findAnyText(decor,new String[]{"Особистий кабінет","Osobní kabinet","Personal cabinet","Особистий профіль","Osobní profil","Personal profile"});
        if(marker==null)return;
        ScrollView scroll=findScroll(marker);
        if(scroll==null||scroll.getChildCount()==0)return;
        View old=scroll.getChildAt(0);
        if(old.getTag()!=null&&String.valueOf(old.getTag()).startsWith("account251-"))return;

        JSONObject state=model.optJSONObject("state"),user=state==null?null:state.optJSONObject("user");
        String name=user==null?"":user.optString("name","");
        if(name.isEmpty()){TextView n=findLikelyName(old);name=n==null?tr(lang,"Користувач","Uživatel","User"):n.getText().toString();}
        String status=textOf(findAnyContains(old,new String[]{"Онлайн","Online"})),emailTitle=textOf(findAnyText(old,new String[]{"Email не підтверджено","E-mail není potvrzen","Email not verified"})),emailBody="";
        TextView email=findContains(old,"@");if(email!=null)emailBody=email.getText().toString();

        View cover=findCover(old,a),
            avatar=findByDescAny(old,new String[]{"Відкрити фото профілю","Otevřít profilovou fotku","Open profile photo"},false),
            viewProfile=findClickableTextAny(old,new String[]{"Переглянути профіль","Zobrazit profil","View profile"}),
            edit=findClickableTextAny(old,new String[]{"Редагувати","Upravit","Edit"}),
            resend=findClickableTextAny(old,new String[]{"Надіслати лист повторно","Odeslat e-mail znovu","Resend email"});
        View completion=findByDescAny(old,new String[]{"Заповнення анкети:","Vyplnění profilu:","Profile completion:"},true);

        LinkedHashMap<String,View> actions=new LinkedHashMap<>();
        String[][] actionSpecs={
            {"views","Хто дивився","Kdo si mě prohlížel","Who viewed me"},
            {"achievements","Досягнення та бонуси","Úspěchy a bonusy","Achievements and bonuses"},
            {"badges","Мої значки","Moje odznaky","My badges"},
            {"mail_settings","Налаштування пошти","Nastavení zpráv","Message settings"},
            {"security","Безпека та входи","Zabezpečení a přihlášení","Security and logins"},
            {"account","Акаунт","Účet","Account"},
            {"services","Додаткові послуги","Doplňkové služby","Extra services"},
            {"basic","Основні дані","Základní údaje","Basic information"},
            {"work_profile","Робоча анкета","Pracovní profil","Work profile"},
            {"dating","Знайомства","Seznamka","Dating"},
            {"housing","Житло","Bydlení","Housing"},
            {"blacklist","Чорний список","Černá listina","Blacklist"},
            {"notifications","Сповіщення","Oznámení","Notifications"},
            {"privacy","Приватність","Soukromí","Privacy"},
            {"themes","Теми","Motivy","Themes"},
            {"site_panel","Панель сайту","Panel webu","Site panel"},
            {"app","Застосунок","Aplikace","App"}
        };
        for(String[] s:actionSpecs){View v=findByDescAny(old,new String[]{s[1]+".",s[2]+".",s[3]+"."},true);if(v!=null)actions.put(s[0],v);}
        LinkedHashMap<String,View> quick=new LinkedHashMap<>();
        String[][] quickSpecs={
            {"cv","Моє CV","Moje CV","My CV"},{"saved_jobs","Обрані вакансії","Uložené nabídky","Saved jobs"},
            {"reviews","Відгуки","Recenze","Reviews"},{"for_me","Для мене","Pro mě","For me"},
            {"messages","Повідомлення","Zprávy","Messages"},{"stats","Статистика","Statistiky","Statistics"}
        };
        for(String[] s:quickSpecs){View v=findByDescAny(old,new String[]{s[1]+".",s[2]+".",s[3]+"."},true);if(v!=null)quick.put(s[0],v);}

        LinearLayout page=column(a);page.setTag(variant==SITE?"account251-site":"account251-plus");page.setPadding(dp(a,variant==SITE?12:10),dp(a,12),dp(a,variant==SITE?12:10),dp(a,24));page.setBackgroundColor(BG);
        page.addView(hero(a,cover,avatar,name,status,viewProfile,edit,variant),lp(-1,-2,0,0,0,12,a));
        if(!emailTitle.isEmpty())page.addView(emailCard(a,emailTitle,emailBody,resend,variant),lp(-1,-2,0,0,0,12,a));
        if(variant==SITE)buildSite(a,page,completion,actions,quick,lang);else buildPlus(a,page,completion,actions,quick,lang);

        scroll.removeAllViews();scroll.setFillViewport(false);scroll.setBackgroundColor(BG);scroll.addView(page,new ScrollView.LayoutParams(-1,-2));
    }

    private static View hero(Activity a,View cover,View avatar,String name,String status,View viewProfile,View edit,int variant){
        FrameLayout card=new FrameLayout(a);card.setBackground(round(a,CARD,18,BORDER));card.setClipToOutline(true);card.setElevation(dp(a,2));
        boolean narrow=a.getResources().getConfiguration().screenWidthDp<360;
        int h=variant==SITE?(narrow?285:265):(narrow?225:205);card.setMinimumHeight(dp(a,h));
        View backdrop=cover;
        if(backdrop!=null){detach(backdrop);backdrop.setAlpha(variant==SITE?0.94f:0.88f);FrameLayout.LayoutParams p=new FrameLayout.LayoutParams(-1,dp(a,variant==SITE?140:92));card.addView(backdrop,p);}
        else{View v=new View(a);v.setBackground(new GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM,new int[]{Color.rgb(232,241,255),Color.rgb(249,251,255)}));card.addView(v,new FrameLayout.LayoutParams(-1,dp(a,variant==SITE?140:92)));}

        if(avatar!=null){detach(avatar);avatar.setBackground(round(a,Color.WHITE,60,Color.WHITE));avatar.setElevation(dp(a,4));int size=dp(a,narrow?(variant==SITE?70:64):(variant==SITE?76:68));FrameLayout.LayoutParams ap=new FrameLayout.LayoutParams(size,size);ap.leftMargin=dp(a,variant==SITE?22:18);ap.topMargin=dp(a,variant==SITE?103:58);card.addView(avatar,ap);}

        LinearLayout info=column(a);TextView title=text(a,name,variant==SITE?21:20,true,TEXT);info.addView(title);
        if(!status.isEmpty()){TextView st=text(a,status,12,false,MUTED);info.addView(st,lp(-1,-2,0,4,0,0,a));}
        FrameLayout.LayoutParams ip=new FrameLayout.LayoutParams(-1,-2);ip.leftMargin=dp(a,narrow?(variant==SITE?104:94):(variant==SITE?116:102));ip.rightMargin=dp(a,16);ip.topMargin=dp(a,variant==SITE?151:100);card.addView(info,ip);

        LinearLayout buttons=new LinearLayout(a);buttons.setGravity(Gravity.CENTER_VERTICAL);
        if(viewProfile!=null){prepareHeroButton(a,viewProfile,true);buttons.addView(viewProfile,new LinearLayout.LayoutParams(0,dp(a,48),1));}
        if(edit!=null){prepareHeroButton(a,edit,false);LinearLayout.LayoutParams ep=new LinearLayout.LayoutParams(0,dp(a,48),1);ep.setMarginStart(dp(a,8));buttons.addView(edit,ep);}
        FrameLayout.LayoutParams bp=new FrameLayout.LayoutParams(-1,dp(a,48));bp.leftMargin=dp(a,variant==SITE?16:14);bp.rightMargin=dp(a,variant==SITE?16:14);bp.bottomMargin=dp(a,14);bp.gravity=Gravity.BOTTOM;card.addView(buttons,bp);
        return card;
    }

    private static View emailCard(Activity a,String title,String body,View action,int variant){
        LinearLayout c=column(a);c.setPadding(dp(a,14),dp(a,12),dp(a,14),dp(a,12));c.setBackground(round(a,Color.rgb(252,253,255),16,BORDER));
        TextView t=text(a,"✉  "+title,15,true,TEXT);c.addView(t);if(!body.isEmpty()){TextView b=text(a,body,12,false,MUTED);c.addView(b,lp(-1,-2,0,6,0,8,a));}
        if(action!=null){detach(action);stylePlainAction(a,action);c.addView(action,new LinearLayout.LayoutParams(-1,dp(a,46)));}
        return c;
    }

    private static void buildSite(Activity a,LinearLayout page,View completion,LinkedHashMap<String,View> actions,LinkedHashMap<String,View> quick,String lang){
        page.addView(sectionTitle(a,tr(lang,"Особистий кабінет","Osobní kabinet","Personal cabinet")));
        if(completion!=null){detach(completion);styleCompletion(a,completion);page.addView(completion,lp(-1,-2,0,0,0,10,a));}
        LinearLayout list=column(a);list.setPadding(dp(a,6),dp(a,2),dp(a,6),dp(a,2));list.setBackground(round(a,CARD,16,BORDER));
        String[] order={"views","achievements","badges","mail_settings","security","account","services","basic","work_profile","dating","housing","blacklist","notifications","privacy","themes","site_panel","app"};
        int added=0;for(String key:order){View v=actions.get(key);if(v==null)continue;detach(v);styleRow(a,v,false);list.addView(v,new LinearLayout.LayoutParams(-1,dp(a,72)));added++;if(added<actions.size())list.addView(divider(a),lp(-1,1,66,0,12,0,a));}
        page.addView(list,lp(-1,-2,0,0,0,16,a));
        page.addView(sectionTitle(a,tr(lang,"Швидкий доступ","Rychlý přístup","Quick access")));
        page.addView(quickGrid(a,quick,false),lp(-1,-2,0,0,0,8,a));
    }

    private static void buildPlus(Activity a,LinearLayout page,View completion,LinkedHashMap<String,View> actions,LinkedHashMap<String,View> quick,String lang){
        LinearLayout summary=new LinearLayout(a);summary.setGravity(Gravity.CENTER_VERTICAL);summary.setPadding(dp(a,12),dp(a,10),dp(a,12),dp(a,10));summary.setBackground(round(a,CARD,16,BORDER));
        TextView cap=text(a,tr(lang,"Заповнення профілю","Vyplnění profilu","Profile completion"),13,true,TEXT);summary.addView(cap,new LinearLayout.LayoutParams(0,-2,1));
        if(completion!=null){detach(completion);styleCompletion(a,completion);summary.addView(completion,new LinearLayout.LayoutParams(dp(a,150),dp(a,62)));}
        page.addView(summary,lp(-1,-2,0,0,0,12,a));

        addGroup(a,page,tr(lang,"Профіль і анкета","Profil a dotazník","Profile and questionnaire"),actions,new String[]{"basic","work_profile","dating","housing"});
        addGroup(a,page,tr(lang,"Безпека й керування","Zabezpečení a správa","Security and management"),actions,new String[]{"security","account","privacy","blacklist","notifications","mail_settings","themes"});
        addGroup(a,page,tr(lang,"Можливості","Možnosti","Features"),actions,new String[]{"views","achievements","badges","services","site_panel","app"});
        page.addView(sectionTitle(a,tr(lang,"Швидкий доступ","Rychlý přístup","Quick access")));
        page.addView(quickGrid(a,quick,true),lp(-1,-2,0,0,0,8,a));
    }

    private static void addGroup(Activity a,LinearLayout page,String title,Map<String,View> actions,String[] keys){
        TextView h=sectionTitle(a,title);page.addView(h);
        LinearLayout group=column(a);group.setPadding(dp(a,6),dp(a,4),dp(a,6),dp(a,4));group.setBackground(round(a,CARD,16,BORDER));
        int count=0;for(String key:keys)if(actions.get(key)!=null)count++;int at=0;for(String key:keys){View v=actions.get(key);if(v==null)continue;detach(v);styleRow(a,v,true);group.addView(v,new LinearLayout.LayoutParams(-1,dp(a,66)));at++;if(at<count)group.addView(divider(a),lp(-1,1,62,0,10,0,a));}
        page.addView(group,lp(-1,-2,0,0,0,12,a));
    }

    private static View quickGrid(Activity a,LinkedHashMap<String,View> quick,boolean plus){
        LinearLayout grid=column(a);List<View> vals=new ArrayList<>(quick.values());
        boolean oneColumn=a.getResources().getConfiguration().screenWidthDp<360;
        int cols=oneColumn?1:2;
        for(int i=0;i<vals.size();i+=cols){LinearLayout row=new LinearLayout(a);row.setBaselineAligned(false);for(int j=0;j<cols;j++){if(i+j>=vals.size()){if(cols>1)row.addView(new View(a),new LinearLayout.LayoutParams(0,1,1));continue;}View v=vals.get(i+j);detach(v);styleQuick(a,v,plus);LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(0,dp(a,plus?116:126),1);if(j>0)p.setMarginStart(dp(a,8));row.addView(v,p);}grid.addView(row,lp(-1,-2,0,0,0,8,a));}
        return grid;
    }

    private static void prepareHeroButton(Activity a,View v,boolean primary){detach(v);v.setBackground(round(a,primary?BLUE:Color.rgb(247,249,253),14,primary?BLUE:BORDER));v.setPadding(dp(a,10),0,dp(a,10),0);recolor(v,primary?Color.WHITE:TEXT,MUTED);if(v instanceof TextView)((TextView)v).setAllCaps(false);}
    private static void stylePlainAction(Activity a,View v){v.setBackground(round(a,Color.rgb(248,250,253),13,BORDER));v.setPadding(dp(a,12),0,dp(a,12),0);recolor(v,TEXT,MUTED);if(v instanceof TextView)((TextView)v).setAllCaps(false);}
    private static void styleCompletion(Activity a,View v){v.setBackground(round(a,CARD,14,BORDER));v.setPadding(dp(a,12),dp(a,8),dp(a,12),dp(a,8));recolor(v,TEXT,MUTED);}
    private static void styleRow(Activity a,View v,boolean compact){v.setBackgroundColor(Color.TRANSPARENT);v.setPadding(dp(a,10),0,dp(a,10),0);v.setMinimumHeight(dp(a,compact?66:72));recolor(v,TEXT,MUTED);if(v instanceof TextView)((TextView)v).setAllCaps(false);}
    private static void styleQuick(Activity a,View v,boolean plus){v.setBackground(round(a,CARD,16,BORDER));v.setPadding(dp(a,12),dp(a,12),dp(a,12),dp(a,12));v.setElevation(dp(a,plus?1:0));recolor(v,TEXT,MUTED);if(v instanceof TextView)((TextView)v).setAllCaps(false);}
    private static void recolor(View v,int primary,int secondary){if(v instanceof TextView){TextView t=(TextView)v;t.setTextColor(primary);}if(v instanceof ViewGroup){ViewGroup g=(ViewGroup)v;for(int i=0;i<g.getChildCount();i++){View c=g.getChildAt(i);if(c instanceof TextView){TextView t=(TextView)c;t.setTextColor(i==0?primary:secondary);}recolor(c,primary,secondary);}}}

    private static TextView sectionTitle(Activity a,String s){TextView v=text(a,s,18,true,TEXT);v.setPadding(dp(a,2),dp(a,8),0,dp(a,9));return v;}
    private static View divider(Activity a){View v=new View(a);v.setBackgroundColor(BORDER);return v;}
    private static LinearLayout column(Context c){LinearLayout v=new LinearLayout(c);v.setOrientation(LinearLayout.VERTICAL);return v;}
    private static TextView text(Context c,String s,float size,boolean bold,int color){TextView v=new TextView(c);v.setText(s);v.setTextSize(size);v.setTextColor(color);v.setTypeface(Typeface.create("sans-serif",bold?Typeface.BOLD:Typeface.NORMAL));v.setLineSpacing(dp(c,2),1);return v;}
    private static GradientDrawable round(Context c,int color,float radius,int stroke){GradientDrawable d=new GradientDrawable();d.setColor(color);d.setCornerRadius(dp(c,radius));d.setStroke(dp(c,1),stroke);return d;}
    private static int dp(Context c,float v){return Math.round(c.getResources().getDisplayMetrics().density*v);}
    private static LinearLayout.LayoutParams lp(int w,int h,int left,int top,int right,int bottom,Context c){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(w,h<0?h:dp(c,h));p.setMargins(dp(c,left),dp(c,top),dp(c,right),dp(c,bottom));return p;}

    private static String language(JSONObject model){
        JSONObject state=model.optJSONObject("state");String s=state==null?"":state.optString("language","");
        if(s.isEmpty())s=model.optString("language","");s=s.toLowerCase(Locale.ROOT);
        return s.startsWith("cs")||s.startsWith("cz")?"cs":s.startsWith("en")?"en":"uk";
    }
    private static String tr(String lang,String uk,String cs,String en){return "cs".equals(lang)?cs:"en".equals(lang)?en:uk;}
    private static TextView findAnyText(View v,String[] values){for(String s:values){TextView t=findText(v,s,false);if(t!=null)return t;}return null;}
    private static TextView findAnyContains(View v,String[] values){for(String s:values){TextView t=findContains(v,s);if(t!=null)return t;}return null;}
    private static View findClickableTextAny(View v,String[] values){for(String s:values){View x=findClickableText(v,s);if(x!=null)return x;}return null;}
    private static View findByDescAny(View v,String[] values,boolean prefix){for(String s:values){View x=findByDesc(v,s,prefix);if(x!=null)return x;}return null;}

    private static ScrollView findScroll(View v){ViewParent p=v.getParent();while(p!=null){if(p instanceof ScrollView)return (ScrollView)p;p=p.getParent();}return null;}
    private static void detach(View v){if(v!=null&&v.getParent() instanceof ViewGroup)((ViewGroup)v.getParent()).removeView(v);}
    private static TextView findText(View v,String value,boolean contains){if(v instanceof TextView){String t=((TextView)v).getText().toString();if(contains?t.contains(value):t.equals(value))return (TextView)v;}if(v instanceof ViewGroup){ViewGroup g=(ViewGroup)v;for(int i=0;i<g.getChildCount();i++){TextView x=findText(g.getChildAt(i),value,contains);if(x!=null)return x;}}return null;}
    private static TextView findContains(View v,String value){return findText(v,value,true);}
    private static View findClickableText(View v,String value){if(v.isClickable()&&v instanceof TextView&&((TextView)v).getText().toString().equals(value))return v;if(v instanceof ViewGroup){ViewGroup g=(ViewGroup)v;for(int i=0;i<g.getChildCount();i++){View x=findClickableText(g.getChildAt(i),value);if(x!=null)return x;}}return null;}
    private static View findByDesc(View v,String value,boolean prefix){CharSequence d=v.getContentDescription();if(v.isClickable()&&d!=null&&(prefix?d.toString().startsWith(value):d.toString().equals(value)))return v;if(v instanceof ViewGroup){ViewGroup g=(ViewGroup)v;for(int i=0;i<g.getChildCount();i++){View x=findByDesc(g.getChildAt(i),value,prefix);if(x!=null)return x;}}return null;}
    private static View findCover(View v,Context c){View[] best=new View[1];int[] area={0};walk(v,x->{if(x instanceof ImageView&&x.getWidth()>dp(c,240)&&x.getHeight()>dp(c,80)){int a=x.getWidth()*x.getHeight();if(a>area[0]){area[0]=a;best[0]=x;}}});return best[0];}
    private static TextView findLikelyName(View v){final TextView[] out={null};walk(v,x->{if(out[0]!=null)return;if(x instanceof TextView){String s=((TextView)x).getText().toString();if(!s.isEmpty()&&s.length()<60&&!s.contains("кабінет")&&!s.contains("Email")&&!s.contains("Переглянути")&&!s.contains("Редагувати")&&s.matches(".*[A-Za-zА-Яа-яІіЇїЄє].*")&&((TextView)x).getTextSize()>18)out[0]=(TextView)x;}});return out[0];}
    private static String textOf(TextView v){return v==null?"":v.getText().toString();}
    private interface Visitor{void visit(View v);}
    private static void walk(View v,Visitor x){x.visit(v);if(v instanceof ViewGroup){ViewGroup g=(ViewGroup)v;for(int i=0;i<g.getChildCount();i++)walk(g.getChildAt(i),x);}}
}