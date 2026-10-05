package eu.svoyi.nativeapp;
import android.app.Activity;
import android.graphics.Rect;
import android.os.Build;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowInsets;
import android.view.ViewTreeObserver;
import android.widget.*;
import org.json.JSONObject;
/** Recover a failed mail screen without modifying conversations on the server. */
public final class MailSafety {
 private MailSafety(){}
 static int dp(Activity a,int n){return Math.round(a.getResources().getDisplayMetrics().density*n);}
 static Button button(Activity a,String text,Runnable action){Button b=new Button(a);b.setAllCaps(false);b.setText(text);b.setMinHeight(dp(a,48));b.setOnClickListener(v->action.run());return b;}
 public static void before(JSONObject chat){MailDiagnostics.mail(chat!=null&&chat.optInt("peerId")>0);}
 public static void failed(MainActivity a,LinearLayout body,ThemePalette theme,NativeMailScreen screen,Throwable cause){
  MailDiagnostics.record(cause,false);
  if(screen!=null){try{screen.close();}catch(RuntimeException ignored){}finally{screen.closed=true;}}
  if(body==null||a.isFinishing()||a.isDestroyed())return;
  body.removeAllViews();
  LinearLayout box=new LinearLayout(a);box.setOrientation(1);box.setPadding(dp(a,20),dp(a,24),dp(a,20),dp(a,20));box.setBackgroundColor(theme.background);box.setTag("mail-recovery-panel");
  TextView title=new TextView(a);title.setText("Не вдалося відкрити повідомлення");title.setTextSize(22);title.setTextColor(theme.text);box.addView(title);
  TextView detail=new TextView(a);detail.setText("Листування на сервері не видалено. Можна повторити відкриття або переглянути технічний звіт про збій.");detail.setTextSize(15);detail.setTextColor(theme.muted);detail.setPadding(0,dp(a,12),0,dp(a,18));box.addView(detail);
  box.addView(button(a,"Спробувати ще раз",a::mailStabilityRetry));box.addView(button(a,"Технічний звіт",()->MailDiagnostics.show(a)));box.addView(button(a,"На головну",a::mailStabilityHome));body.addView(box,new LinearLayout.LayoutParams(-1,-2));
 }
 public static void settings(Activity a,LinearLayout content){if(content==null||content.findViewWithTag("mail-diagnostics-button")!=null)return;Button b=button(a,"Діагностика застосунку",()->MailDiagnostics.show(a));b.setTag("mail-diagnostics-button");content.addView(b,new LinearLayout.LayoutParams(-1,-2));}
 public static void inbox(NativeMailScreen s){
  if(s.root==null||s.root.getChildCount()==0)return;View v=s.root.getChildAt(0);if(!(v instanceof ViewGroup))return;
  ViewGroup head=(ViewGroup)v;View menu=head.getChildCount()>1?head.getChildAt(head.getChildCount()-1):null;if(menu==null)return;
  menu.setOnClickListener(anchor->{PopupMenu popup=new PopupMenu(s.activity,anchor);
   popup.getMenu().add("Усі діалоги").setOnMenuItemClickListener(item->{s.allInbox.performClick();return true;});
   popup.getMenu().add("Непрочитані").setOnMenuItemClickListener(item->{s.unreadInbox.performClick();return true;});
   popup.getMenu().add("Очистити пошук").setOnMenuItemClickListener(item->{s.search.setText("");return true;});
   popup.getMenu().add("Діагностика застосунку").setOnMenuItemClickListener(item->{MailDiagnostics.show(s.activity);return true;});popup.show();
  });
 }
 public static void thread(NativeMailScreen s){
  if(s.root==null||s.composer==null)return;final View toolbar=s.root.findViewWithTag("site-match-mail-toolbar");if(toolbar==null)return;
  // 2.4.2 detached this button; keep attachments reachable while the large toolbar is hidden by IME.
  if(s.tools!=null&&s.tools.getParent()==null)s.composer.addView(s.tools,0,new LinearLayout.LayoutParams(dp(s.activity,44),dp(s.activity,46)));
  final ViewTreeObserver.OnGlobalLayoutListener listener=()->{
   boolean keyboard;if(Build.VERSION.SDK_INT>=30)keyboard=Api30.ime(s.root);else{Rect r=new Rect();s.root.getWindowVisibleDisplayFrame(r);keyboard=s.activity.getWindow().getDecorView().getHeight()-r.bottom>dp(s.activity,120);}
   int visibility=s.canSend&&!keyboard?View.VISIBLE:View.GONE;if(toolbar.getVisibility()!=visibility)toolbar.setVisibility(visibility);
  };
  s.root.getViewTreeObserver().addOnGlobalLayoutListener(listener);
  s.root.addOnAttachStateChangeListener(new View.OnAttachStateChangeListener(){public void onViewAttachedToWindow(View v){}public void onViewDetachedFromWindow(View v){if(v.getViewTreeObserver().isAlive())v.getViewTreeObserver().removeOnGlobalLayoutListener(listener);}});
 }
 public static void presence(NativeMailScreen s){
  if(s.presence==null)return;JSONObject p=s.partner==null?null:s.partner.optJSONObject("presence");boolean show=p!=null&&!p.optBoolean("hidden")&&(!p.has("visible")||p.optBoolean("visible"));String label=show?p.optString("label",""):"";
  s.presence.setText(label);s.presence.setTextColor(show&&p.optBoolean("online")?s.theme.accent:s.theme.muted);s.presence.setVisibility(label.isEmpty()?View.GONE:View.VISIBLE);
 }
 private static final class Api30{static boolean ime(View v){WindowInsets i=v.getRootWindowInsets();return i!=null&&i.isVisible(WindowInsets.Type.ime());}}
}
