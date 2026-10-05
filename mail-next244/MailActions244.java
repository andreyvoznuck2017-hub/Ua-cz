package eu.svoyi.nativeapp;
import android.app.AlertDialog;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.res.ColorStateList;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.ColorDrawable;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.RippleDrawable;
import android.text.TextUtils;
import android.view.Gravity;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.view.inputmethod.InputMethodManager;
import android.widget.*;
import org.json.*;
import java.util.HashSet;
/** Native UI only. Uses the existing mail transport, nonces, server permissions and confirmations. */
public final class MailActions244 {
 private MailActions244(){}
 private interface Action {void run(JSONObject m)throws Exception;}
 private static int dp(NativeMailScreen s,int x){return Math.round(s.activity.getResources().getDisplayMetrics().density*x);}
 private static GradientDrawable shape(NativeMailScreen s,int color,int radius){GradientDrawable d=new GradientDrawable();d.setColor(color);d.setCornerRadius(dp(s,radius));return d;}
 private static TextView text(NativeMailScreen s,String value,int size,int color){TextView t=new TextView(s.activity);t.setText(value);t.setTextSize(size);t.setTextColor(color);return t;}
 private static JSONObject fresh(NativeMailScreen s,int id){return s.alive()?s.model.messages.get(id):null;}
 private static String mine(JSONObject m){JSONArray rs=m.optJSONArray("reactions");if(rs!=null)for(int i=0;i<rs.length();i++){JSONObject r=rs.optJSONObject(i);if(r!=null&&r.optBoolean("mine"))return r.optString("emoji","");}return "";}
 private static void invoke(NativeMailScreen s,AlertDialog dialog,int id,Action action){
  dialog.dismiss();JSONObject m=fresh(s,id);if(m==null||s.actionBusy)return;
  try{action.run(m);}catch(Exception e){MailDiagnostics.record(e,false);s.status("Не вдалося виконати дію. Спробуйте ще раз.",true);}
 }
 private static void row(NativeMailScreen s,LinearLayout parent,AlertDialog dialog,int id,String label,String glyph,boolean danger,Action action){
  LinearLayout r=new LinearLayout(s.activity);r.setOrientation(0);r.setGravity(Gravity.CENTER_VERTICAL);r.setPadding(dp(s,14),dp(s,11),dp(s,14),dp(s,11));r.setMinimumHeight(dp(s,52));r.setContentDescription(label);r.setFocusable(true);
  r.setBackground(new RippleDrawable(ColorStateList.valueOf(s.theme.border),shape(s,s.theme.surface,14),null));
  TextView icon=text(s,glyph,22,danger?s.theme.error:s.theme.accent);icon.setGravity(Gravity.CENTER);icon.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);r.addView(icon,new LinearLayout.LayoutParams(dp(s,32),dp(s,32)));
  TextView name=text(s,label,16,danger?s.theme.error:s.theme.text);name.setPadding(dp(s,12),0,0,0);r.addView(name,new LinearLayout.LayoutParams(0,-2,1));
  r.setOnClickListener(v->invoke(s,dialog,id,action));parent.addView(r,new LinearLayout.LayoutParams(-1,-2));
 }
 public static void open(NativeMailScreen s,JSONObject original){
  if(!s.alive()||s.actionBusy||original==null)return;final int id=original.optInt("id");JSONObject m=fresh(s,id);if(m==null)return;
  final boolean removed=NativeMailPolicy.deleted(m),own=NativeMailPolicy.sender(m)==s.account;
  LinearLayout box=new LinearLayout(s.activity);box.setOrientation(1);box.setPadding(dp(s,14),dp(s,10),dp(s,14),dp(s,14));box.setBackground(shape(s,s.theme.surface,24));
  View grip=new View(s.activity);grip.setBackground(shape(s,s.theme.border,3));LinearLayout.LayoutParams gp=new LinearLayout.LayoutParams(dp(s,36),dp(s,4));gp.gravity=Gravity.CENTER_HORIZONTAL;gp.bottomMargin=dp(s,14);box.addView(grip,gp);
  TextView title=text(s,own?"Ваше повідомлення":"Повідомлення",17,s.theme.text);title.setTypeface(Typeface.DEFAULT,Typeface.BOLD);title.setPadding(dp(s,12),0,0,dp(s,8));box.addView(title);
  String preview=removed?"Користувач видалив повідомлення":RichMessage.parse(m.optString("body","")).text;
  if(preview.trim().isEmpty())preview="Вкладення";
  TextView summary=text(s,preview,14,s.theme.muted);summary.setMaxLines(3);summary.setEllipsize(TextUtils.TruncateAt.END);summary.setPadding(dp(s,12),0,dp(s,12),dp(s,12));box.addView(summary);
  ScrollView scroll=new ScrollView(s.activity);scroll.setFillViewport(false);scroll.addView(box);
  final AlertDialog dialog=s.dialogBuilder().setView(scroll).create();
  if(!removed&&s.canReact(m)){
   HorizontalScrollView horizontal=new HorizontalScrollView(s.activity);horizontal.setHorizontalScrollBarEnabled(false);LinearLayout emojis=new LinearLayout(s.activity);emojis.setPadding(0,dp(s,4),0,dp(s,10));HashSet<String> seen=new HashSet<>();String selected=mine(m);
   for(int i=0;i<s.reactionChoices.length();i++){
    final String emoji=s.reactionChoices.optString(i);if(!NativeMailScreen.supportedReaction(emoji)||!seen.add(emoji))continue;
    TextView b=text(s,emoji,27,s.theme.text);b.setGravity(Gravity.CENTER);b.setContentDescription("Реакція "+emoji);b.setSelected(emoji.equals(selected));b.setFocusable(true);
    b.setBackground(new RippleDrawable(ColorStateList.valueOf(s.theme.border),shape(s,emoji.equals(selected)?s.theme.field:s.theme.surface,24),null));
    b.setOnClickListener(v->invoke(s,dialog,id,current->{if(s.canReact(current))s.react(current,emoji.equals(mine(current))?"":emoji);}));
    LinearLayout.LayoutParams ep=new LinearLayout.LayoutParams(dp(s,50),dp(s,50));ep.setMarginEnd(dp(s,2));emojis.addView(b,ep);
   }
   horizontal.addView(emojis);box.addView(horizontal);
   if(!selected.isEmpty())row(s,box,dialog,id,"Прибрати свою реакцію","−",false,current->{if(s.canReact(current))s.react(current,"");});
  }
  if(!removed){
   if(s.canSend)row(s,box,dialog,id,"Відповісти","↩",false,current->{
    if(NativeMailPolicy.deleted(current)||!s.canSend)return;s.replyTo(current);
    s.input.post(()->{if(!s.alive())return;s.input.requestFocus();InputMethodManager ime=(InputMethodManager)s.activity.getSystemService(Context.INPUT_METHOD_SERVICE);if(ime!=null)ime.showSoftInput(s.input,InputMethodManager.SHOW_IMPLICIT);});
   });
   row(s,box,dialog,id,"Копіювати","⧉",false,current->{if(NativeMailPolicy.deleted(current))return;ClipboardManager c=(ClipboardManager)s.activity.getSystemService(Context.CLIPBOARD_SERVICE);if(c!=null){c.setPrimaryClip(ClipData.newPlainText("Повідомлення",RichMessage.parse(current.optString("body","")).text));s.status("Скопійовано",false);}});
   row(s,box,dialog,id,"Виділити текст","Ｔ",false,current->{if(!NativeMailPolicy.deleted(current))s.selectMessageText(current);});
  }
  if(own){
   if(s.mayEdit(m))row(s,box,dialog,id,"Редагувати","✎",false,current->{if(s.mayEdit(current))s.edit(current);else s.status("Час редагування повідомлення минув.",true);});
   if(!removed&&m.optBoolean("canDelete",true))row(s,box,dialog,id,"Видалити для обох","⌫",true,current->{if(NativeMailPolicy.sender(current)==s.account&&!NativeMailPolicy.deleted(current)&&current.optBoolean("canDelete",true))s.delete(current,false);});
   if(m.optBoolean("canErase",true))row(s,box,dialog,id,"Видалити без сліду","⋯",true,current->{if(NativeMailPolicy.sender(current)==s.account&&current.optBoolean("canErase",true))s.delete(current,true);});
  }
  row(s,box,dialog,id,"Скасувати","×",false,current->{});
  s.show(dialog);Window window=dialog.getWindow();if(window!=null){window.setBackgroundDrawable(new ColorDrawable(Color.TRANSPARENT));window.setGravity(Gravity.BOTTOM);window.setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_NOTHING|WindowManager.LayoutParams.SOFT_INPUT_STATE_ALWAYS_HIDDEN);int width=Math.min(s.activity.getResources().getDisplayMetrics().widthPixels-dp(s,16),dp(s,540));window.setLayout(width,-2);scroll.post(()->{int limit=(int)(s.activity.getResources().getDisplayMetrics().heightPixels*0.78);if(scroll.getHeight()>limit)window.setLayout(width,limit);});}
 }
}
