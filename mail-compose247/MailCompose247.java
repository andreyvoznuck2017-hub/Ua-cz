package eu.svoyi.nativeapp;

import android.app.AlertDialog;
import android.content.Context;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.SystemClock;
import android.text.Editable;
import android.text.InputFilter;
import android.text.SpannableStringBuilder;
import android.text.Spanned;
import android.view.Gravity;
import android.view.View;
import android.view.ViewTreeObserver;
import android.view.Window;
import android.view.WindowManager;
import android.view.inputmethod.InputMethodManager;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import org.json.JSONObject;
import java.lang.ref.WeakReference;
import java.util.ArrayList;

/** Keeps the quote in existing reply state, never inside the user-editable composer.
 * Serialized drafts and transport retain the unchanged server BBCode representation. */
public final class MailCompose247 {
 private MailCompose247() {}
 private static final int LIMIT=3000;
 private static int dp(NativeMailScreen s,int n){return Math.round(n*s.activity.getResources().getDisplayMetrics().density);}
 private static String prefix(NativeMailScreen s){return s.replyPrefix==null?"":s.replyPrefix;}
 public static String raw(NativeMailScreen s){return prefix(s)+(s.input==null?"":s.input.getText().toString());}
 public static Editable wire(NativeMailScreen s){return new SpannableStringBuilder(raw(s));}

 public static void reply(NativeMailScreen s,JSONObject message,String selected){
  JSONObject current=s.currentMessage(message);
  if(current==null||!s.canSend||s.sending||s.staging||s.input==null||selected==null||selected.trim().isEmpty())return;
  String quote=NativeMailPresentation.quote(selected),typed=s.input.getText().toString();
  if(NativeMailTextFilter.count(quote+typed)>LIMIT){s.status("Цитата й текст разом мають містити не більше 3000 символів.",true);return;}
  s.replyPrefix=quote;
  s.replySender=NativeMailPolicy.sender(current)==s.account?"Ви":s.partner==null?"Співрозмовник":s.partner.optString("name","Співрозмовник");
  s.draftRevision++;s.failedSend=false;s.paintReply();s.updateComposer();s.saveDraft();s.input.requestFocus();
  // The existing 2.4.6 wrapper owns the one-shot keyboard focus handoff.
 }
 public static void cancel(NativeMailScreen s){
  if(!s.alive()||s.sending||s.staging)return;
  s.replyPrefix="";s.replySender="";s.draftRevision++;s.failedSend=false;
  s.paintReply();s.updateComposer();s.saveDraft();
 }
 /** Only called immediately after a legacy serialized-draft restoration. */
 public static void restored(NativeMailScreen s){
  if(s.input==null)return;
  String quote=prefix(s),text=s.input.getText().toString();
  if(!quote.isEmpty()&&text.startsWith(quote)){
   boolean loading=s.loadingDraft;s.loadingDraft=true;
   int at=Math.max(0,s.input.getSelectionStart()-quote.length());
   try{s.input.setText(text.substring(quote.length()));s.input.setSelection(Math.min(at,s.input.length()));}
   finally{s.loadingDraft=loading;}
  }
  s.paintReply();s.updateComposer();
 }
 public static void attached(NativeMailScreen s){
  restored(s);
  ArrayList<InputFilter> filters=new ArrayList<>();
  for(InputFilter f:s.input.getFilters())if(!(f instanceof QuoteLimit))filters.add(f);
  filters.add(new QuoteLimit(s));s.input.setFilters(filters.toArray(new InputFilter[0]));
 }
 public static void changed(NativeMailScreen s,CharSequence value){
  if(s.loadingDraft)return;
  s.draftRevision++;s.failedSend=false;s.updateComposer();
  s.ui.removeCallbacks(s.draftSaver);s.ui.postDelayed(s.draftSaver,450);
  s.ui.removeCallbacks(s.typingStop);s.ui.postDelayed(s.typingStop,1800);
  if(SystemClock.elapsedRealtime()-s.lastTyping>1500)s.typing(value.length()>0);
 }
 private static final class QuoteLimit implements InputFilter {
  final WeakReference<NativeMailScreen> owner;
  QuoteLimit(NativeMailScreen s){owner=new WeakReference<>(s);}
  public CharSequence filter(CharSequence source,int start,int end,Spanned dest,int dstart,int dend){
   NativeMailScreen s=owner.get();if(s==null||s.loadingDraft)return null;
   int limit=Math.max(0,LIMIT-NativeMailTextFilter.count(prefix(s)));
   return new NativeMailTextFilter(limit,()->s.status("Цитата й текст разом мають містити не більше 3000 символів.",true)).filter(source,start,end,dest,dstart,dend);
  }
 }
 public static void paint(NativeMailScreen s){
  if(s.replyRow==null)return;
  s.replyRow.removeAllViews();String quote=prefix(s);
  s.replyRow.setVisibility(quote.isEmpty()||!s.canSend?View.GONE:View.VISIBLE);
  if(quote.isEmpty())return;
  LinearLayout row=new LinearLayout(s.activity);row.setGravity(Gravity.CENTER_VERTICAL);row.setPadding(dp(s,10),dp(s,7),dp(s,4),dp(s,7));
  GradientDrawable bg=new GradientDrawable();bg.setColor(s.theme.field);bg.setCornerRadius(dp(s,12));row.setBackground(bg);
  View bar=new View(s.activity);bar.setBackgroundColor(s.theme.accent);LinearLayout.LayoutParams bp=new LinearLayout.LayoutParams(dp(s,3),dp(s,40));bp.setMarginEnd(dp(s,10));row.addView(bar,bp);
  LinearLayout labels=new LinearLayout(s.activity);labels.setOrientation(LinearLayout.VERTICAL);
  TextView title=new TextView(s.activity);title.setText("Відповідь · "+(s.replySender==null||s.replySender.isEmpty()?"Цитата":s.replySender));title.setTextSize(12);title.setTypeface(Typeface.DEFAULT,Typeface.BOLD);title.setTextColor(s.theme.accent);labels.addView(title);
  TextView body=new TextView(s.activity);body.setText(RichMessage.parse(quote).text);body.setTextColor(s.theme.muted);body.setTextSize(13);body.setMaxLines(2);body.setEllipsize(android.text.TextUtils.TruncateAt.END);body.setTag("mail-reply-context");labels.addView(body);
  row.addView(labels,new LinearLayout.LayoutParams(0,-2,1));row.addView(s.icon("close","Скасувати відповідь цитатою",()->cancel(s)),new LinearLayout.LayoutParams(dp(s,44),dp(s,44)));
  s.replyRow.addView(row,new LinearLayout.LayoutParams(-1,-2));
 }
 /** Style the existing edit dialog; preserve all permission/conflict/save callbacks. */
 public static void dialog(NativeMailScreen s,AlertDialog dialog){
  Window w=dialog.getWindow();if(w==null)return;
  View found=w.getDecorView().findViewWithTag("mail-edit-input");if(!(found instanceof EditText))return;
  EditText edit=(EditText)found;
  edit.setSingleLine(false);edit.setMinLines(2);edit.setMaxLines(6);edit.setMinHeight(dp(s,78));edit.setMinimumHeight(dp(s,78));edit.setMaxHeight(dp(s,184));edit.setGravity(Gravity.TOP|Gravity.START);edit.setTextSize(16);edit.setPadding(dp(s,12),dp(s,10),dp(s,12),dp(s,10));edit.setVerticalScrollBarEnabled(true);edit.setHorizontallyScrolling(false);edit.setImeOptions(android.view.inputmethod.EditorInfo.IME_FLAG_NO_EXTRACT_UI);
  edit.setLayoutParams(new LinearLayout.LayoutParams(-1,-2));
  View state=w.getDecorView().findViewWithTag("mail-edit-state");if(state instanceof TextView){((TextView)state).setTextSize(12);state.setMinimumHeight(0);}
  for(int button:new int[]{AlertDialog.BUTTON_POSITIVE,AlertDialog.BUTTON_NEGATIVE})if(dialog.getButton(button)!=null){dialog.getButton(button).setAllCaps(false);dialog.getButton(button).setTextSize(15);dialog.getButton(button).setMinHeight(dp(s,48));}
  w.setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE|WindowManager.LayoutParams.SOFT_INPUT_STATE_UNCHANGED);w.setGravity(Gravity.CENTER);w.setLayout(Math.min(s.activity.getResources().getDisplayMetrics().widthPixels-dp(s,24),dp(s,520)),-2);
  edit.requestFocus();new DialogFocus(s,dialog,edit).start();
 }
 private static final class DialogFocus implements Runnable,ViewTreeObserver.OnWindowFocusChangeListener{
  final NativeMailScreen s;final AlertDialog d;final EditText e;boolean done;
  final Runnable timeout=()->stop();
  DialogFocus(NativeMailScreen s,AlertDialog d,EditText e){this.s=s;this.d=d;this.e=e;}
  void start(){e.getViewTreeObserver().addOnWindowFocusChangeListener(this);e.post(this);e.postDelayed(timeout,2000);}
  public void onWindowFocusChanged(boolean yes){if(yes&&!done)e.post(this);}
  public void run(){if(done)return;if(!s.alive()||!d.isShowing()){stop();return;}if(!e.hasWindowFocus()||!e.isAttachedToWindow())return;e.requestFocus();InputMethodManager ime=(InputMethodManager)s.activity.getSystemService(Context.INPUT_METHOD_SERVICE);if(ime!=null)ime.showSoftInput(e,InputMethodManager.SHOW_IMPLICIT);stop();}
  void stop(){if(done)return;done=true;e.removeCallbacks(this);e.removeCallbacks(timeout);if(e.getViewTreeObserver().isAlive())e.getViewTreeObserver().removeOnWindowFocusChangeListener(this);}
 }
}
