package eu.svoyi.nativeapp;

import android.app.Activity;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.text.TextUtils;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.inputmethod.EditorInfo;
import android.widget.*;
import org.json.JSONObject;
import java.util.*;

/** Presentation only: transport, drafts, receipts, media and lifecycle remain owned by NativeMailScreen. */
public final class MailScreen257 {
    private MailScreen257(){}
    private static final WeakHashMap<Activity,String> languages=new WeakHashMap<>();
    static String language(JSONObject model){
        if(model==null)return "uk";JSONObject state=model.optJSONObject("state");
        String value=state==null?model.optString("language"):state.optString("language",model.optString("language"));
        if(value.isEmpty())try{value=android.net.Uri.parse(model.optString("route")).getQueryParameter("lang");}catch(RuntimeException ignored){}
        if(value!=null&&!value.isEmpty())return value.startsWith("cs")?"cs":value.startsWith("en")?"en":"uk";
        org.json.JSONArray menu=model.optJSONArray("menu");if(menu!=null)for(int i=0;i<menu.length();i++){JSONObject item=menu.optJSONObject(i);if(item!=null&&"home".equals(item.optString("key"))){String label=item.optString("text").toLowerCase(Locale.ROOT);if(label.equals("home"))return "en";if(label.contains("domů")||label.contains("hlavní")||label.contains("domov"))return "cs";}}
        return "uk";
    }
    public static void remember(Activity a,JSONObject model){
        if(a==null||model==null)return;languages.put(a,language(model));
    }
    private static String t(NativeMailScreen s,String uk,String cs,String en){String l=languages.get(s.activity);return "cs".equals(l)?cs:"en".equals(l)?en:uk;}
    private static int dp(NativeMailScreen s,float n){return Math.round(n*s.activity.getResources().getDisplayMetrics().density);}
    private static GradientDrawable shape(NativeMailScreen s,int color,int radius,int border){GradientDrawable d=new GradientDrawable();d.setColor(color);d.setCornerRadius(dp(s,radius));if(border!=0)d.setStroke(dp(s,1),border);return d;}
    private static TextView text(NativeMailScreen s,String value,int size,boolean bold){TextView v=new TextView(s.activity);v.setText(value);v.setTextSize(size);v.setTextColor(s.theme.text);v.setIncludeFontPadding(false);v.setTypeface(Typeface.create(bold?"sans-serif-medium":"sans-serif",bold?Typeface.BOLD:Typeface.NORMAL));return v;}
    private static void pad(NativeMailScreen s,View v,int x,int y){v.setPadding(dp(s,x),dp(s,y),dp(s,x),dp(s,y));}

    public static void inbox(NativeMailScreen s){
        if(s.root==null||s.peer>0||s.activity.isFinishing())return;
        s.root.setBackgroundColor(s.theme.surface);
        // The app bar already says Messages. This line describes the list instead of repeating it.
        if(s.root.getChildCount()>0&&s.root.getChildAt(0) instanceof ViewGroup){ViewGroup top=(ViewGroup)s.root.getChildAt(0);pad(s,top,16,8);if(top.getChildCount()>0){View title=top.getChildAt(0);if(title instanceof ViewGroup){ViewGroup group=(ViewGroup)title;for(int i=0;i<group.getChildCount();i++){View child=group.getChildAt(i);if(i==0&&child instanceof TextView){TextView label=(TextView)child;label.setText(t(s,"Ваші діалоги","Vaše konverzace","Your conversations"));label.setTextSize(18);label.setIncludeFontPadding(false);}else child.setVisibility(View.GONE);}}else if(title instanceof TextView){((TextView)title).setText(t(s,"Ваші діалоги","Vaše konverzace","Your conversations"));((TextView)title).setTextSize(18);}}}
        if(s.search!=null){
            s.search.setHint(t(s,"Пошук у діалогах","Hledat v konverzacích","Search conversations"));s.search.setContentDescription(s.search.getHint());s.search.setTextSize(15);s.search.setTextColor(s.theme.text);s.search.setHintTextColor(s.theme.muted);s.search.setMinHeight(dp(s,48));pad(s,s.search,14,10);s.search.setBackground(shape(s,s.theme.field,24,s.theme.border));s.search.setImeOptions(EditorInfo.IME_ACTION_SEARCH|EditorInfo.IME_FLAG_NO_EXTRACT_UI);
        }
        int unread=0;for(JSONObject row:s.conversations.values())if(row.optInt("unread")>0)unread++;
        chip(s,s.allInbox,t(s,"Усі","Vše","All")+" · "+s.conversations.size(),!s.unreadOnly);
        chip(s,s.unreadInbox,t(s,"Непрочитані","Nepřečtené","Unread")+" · "+unread,s.unreadOnly);
        if(s.allInbox!=null&&s.allInbox.getParent() instanceof View)((View)s.allInbox.getParent()).setVisibility(View.VISIBLE);
        if(s.inboxScope!=null){
            String query=s.search==null?"":s.search.getText().toString().trim();
            s.inboxScope.setText(s.moreConversations?t(s,"Пошук у завантажених діалогах. Нижче можна завантажити решту.","Hledání v načtených konverzacích. Další načtete níže.","Searching loaded conversations. Load more below."):t(s,"Пошук у всіх діалогах","Hledání ve všech konverzacích","Searching all conversations"));
            s.inboxScope.setVisibility(s.moreConversations||!query.isEmpty()?View.VISIBLE:View.GONE);s.inboxScope.setTextSize(12);s.inboxScope.setTextColor(s.theme.muted);
        }
        if(s.inboxList!=null){
            for(int i=0;i<s.inboxList.getChildCount();i++){View row=s.inboxList.getChildAt(i);if(row instanceof NativeMailInboxRow){
                pad(s,row,10,12);row.setMinimumHeight(dp(s,78));row.setElevation(0);row.setBackground(shape(s,s.theme.surface,0,0));
                ViewGroup.LayoutParams lp=row.getLayoutParams();if(lp instanceof ViewGroup.MarginLayoutParams){ViewGroup.MarginLayoutParams m=(ViewGroup.MarginLayoutParams)lp;m.setMargins(0,0,0,dp(s,1));row.setLayoutParams(m);}styleRow(s,row);
            }}
            String q=s.search==null?"":s.search.getText().toString().trim();
            boolean empty=s.conversations.isEmpty()&&q.isEmpty()&&!s.unreadOnly;
            if(empty&&s.inboxList.getChildCount()>0&&!(s.inboxList.getChildAt(0) instanceof NativeMailInboxRow)){
                View old=s.inboxList.getChildAt(0);if(!"mail257-empty".equals(old.getTag())){
                    LinearLayout box=new LinearLayout(s.activity);box.setOrientation(1);box.setGravity(Gravity.CENTER);box.setTag("mail257-empty");pad(s,box,20,32);
                    TextView icon=text(s,"💬",42,false);icon.setGravity(Gravity.CENTER);box.addView(icon,new LinearLayout.LayoutParams(-2,-2));TextView title=text(s,t(s,"Ваші повідомлення","Vaše zprávy","Your messages"),21,true);LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-2,-2);p.topMargin=dp(s,16);box.addView(title,p);
                    TextView note=text(s,t(s,"Знайдіть людину та натисніть «Написати» в її анкеті.","Najděte člověka a v jeho profilu zvolte Napsat.","Find someone and choose Message on their profile."),14,false);note.setTextColor(s.theme.muted);note.setGravity(Gravity.CENTER);note.setLineSpacing(dp(s,3),1);p=new LinearLayout.LayoutParams(-1,-2);p.topMargin=dp(s,10);p.bottomMargin=dp(s,18);box.addView(note,p);
                    Button create=new Button(s.activity);create.setAllCaps(false);create.setText(t(s,"＋ Нове повідомлення","＋ Nová zpráva","＋ New message"));create.setTextSize(15);create.setTextColor(s.theme.primaryText);create.setBackground(shape(s,s.theme.accent,14,0));create.setMinHeight(dp(s,48));pad(s,create,18,10);create.setOnClickListener(v->{if(s.alive())s.host.navigate("/?p=people");});box.addView(create,new LinearLayout.LayoutParams(-2,-2));
                    s.inboxList.removeViewAt(0);s.inboxList.addView(box,0,new LinearLayout.LayoutParams(-1,-2));
                }
            }
        }
    }
    private static void chip(NativeMailScreen s,Button b,String title,boolean active){
        if(b==null)return;b.setText(title);b.setTextSize(13);b.setAllCaps(false);b.setTextColor(active?s.theme.primaryText:s.theme.muted);b.setBackground(shape(s,active?s.theme.accent:s.theme.field,22,active?0:s.theme.border));b.setMinHeight(dp(s,44));b.setMinimumHeight(dp(s,44));pad(s,b,12,8);
        ViewGroup.LayoutParams lp=b.getLayoutParams();if(lp instanceof ViewGroup.MarginLayoutParams){ViewGroup.MarginLayoutParams m=(ViewGroup.MarginLayoutParams)lp;m.setMargins(0,dp(s,6),dp(s,6),dp(s,8));b.setLayoutParams(m);}
    }
    private static void styleRow(NativeMailScreen s,View v){
        if(v instanceof TextView){TextView tv=(TextView)v;tv.setIncludeFontPadding(false);float size=tv.getTextSize()/s.activity.getResources().getDisplayMetrics().scaledDensity;if(size>=15){tv.setTextSize(15);tv.setMaxLines(1);tv.setEllipsize(TextUtils.TruncateAt.END);}else if(size>=12){tv.setTextSize(13);tv.setMaxLines(1);tv.setEllipsize(TextUtils.TruncateAt.END);}}
        if(v instanceof ViewGroup){ViewGroup g=(ViewGroup)v;for(int i=0;i<g.getChildCount();i++)styleRow(s,g.getChildAt(i));}
    }
    public static void thread(NativeMailScreen s){
        if(s.root==null||s.peer<=0)return;
        s.root.setBackgroundColor(s.theme.surface);
        if(s.header!=null){s.header.setBackgroundColor(s.theme.surface);s.header.setMinimumHeight(dp(s,64));pad(s,s.header,10,8);}
        if(s.presence!=null){s.presence.setTextSize(12);s.presence.setIncludeFontPadding(false);}
        if(s.historySearch!=null){s.historySearch.setTextSize(15);s.historySearch.setMinHeight(dp(s,46));pad(s,s.historySearch,12,8);s.historySearch.setBackground(shape(s,s.theme.field,22,s.theme.border));s.historySearch.setHint(t(s,"Пошук у переписці","Hledat ve zprávách","Search this conversation"));}
        if(s.composer!=null){pad(s,s.composer,10,8);s.composer.setBackground(shape(s,s.theme.surface,0,0));}
        if(s.input!=null){
            s.input.setHint(t(s,"Повідомлення…","Zpráva…","Message…"));s.input.setContentDescription(s.input.getHint());s.input.setTextSize(16);s.input.setTextColor(s.theme.text);s.input.setHintTextColor(s.theme.muted);s.input.setBackground(shape(s,s.theme.field,22,s.theme.border));pad(s,s.input,14,11);s.input.setMinHeight(dp(s,48));s.input.setMinLines(1);s.input.setMaxLines(5);s.input.setGravity(Gravity.TOP|Gravity.START);s.input.setHorizontallyScrolling(false);s.input.setImeOptions(EditorInfo.IME_FLAG_NO_EXTRACT_UI|EditorInfo.IME_ACTION_NONE);
        }
        if(s.send!=null){s.send.setContentDescription(t(s,"Надіслати","Odeslat","Send"));s.send.setBackground(shape(s,s.theme.accent,24,0));s.send.setMinimumHeight(dp(s,48));s.send.setMinimumWidth(dp(s,48));}
        View tools=s.root.findViewWithTag("site-match-mail-toolbar");
        if(tools instanceof HorizontalScrollView){View child=((HorizontalScrollView)tools).getChildAt(0);if(child instanceof LinearLayout){LinearLayout bar=(LinearLayout)child;if(!"mail257-tools".equals(bar.getTag())){
            bar.setTag("mail257-tools");ArrayList<View> buttons=new ArrayList<>();for(int i=0;i<bar.getChildCount();i++)buttons.add(bar.getChildAt(i));bar.removeAllViews();
            String[] uk={"","Фото","Голос","Кружечок","Файл","Aa",""},cs={"","Foto","Hlas","Video","Soubor","Aa",""},en={"","Photo","Voice","Video","File","Aa",""};
            for(int i=0;i<buttons.size();i++){final View button=buttons.get(i);LinearLayout item=new LinearLayout(s.activity);item.setGravity(Gravity.CENTER_VERTICAL);pad(s,item,6,2);item.setBackground(shape(s,s.theme.field,10,0));item.addView(button,new LinearLayout.LayoutParams(dp(s,34),dp(s,40)));String name=i<uk.length?t(s,uk[i],cs[i],en[i]):"";if(!name.isEmpty()){TextView label=text(s,name,12,true);item.addView(label,new LinearLayout.LayoutParams(-2,-2));item.setContentDescription(button.getContentDescription());item.setOnClickListener(v->button.performClick());}LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-2,dp(s,44));lp.setMarginEnd(dp(s,5));bar.addView(item,lp);}
        }}}
        composer(s);
    }
    public static void composer(NativeMailScreen s){
        if(s.characterCount!=null){s.characterCount.setTextSize(11);s.characterCount.setIncludeFontPadding(false);}
        if(s.sendState!=null){s.sendState.setTextSize(12);s.sendState.setIncludeFontPadding(false);}
        if(s.retrySend!=null){s.retrySend.setAllCaps(false);s.retrySend.setTextSize(14);}
    }
}
