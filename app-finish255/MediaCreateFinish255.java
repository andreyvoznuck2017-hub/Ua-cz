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

/** 2.5.5 media/form polish.
 * Keeps the existing transport, server rules and original click listeners.
 * This pass only hardens mobile ergonomics, attachment/media previews and creation forms. */
public final class MediaCreateFinish255 {
    private MediaCreateFinish255(){}

    private static final Set<String> PAGES=new HashSet<>(Arrays.asList(
        "mail","messages","chat","groups","group","feed","housing","events","event","dating","nearby","notifications"
    ));

    public static void apply(Activity a,JSONObject model){
        if(a==null||model==null)return;
        final String page=model.optString("page","");
        if(!PAGES.contains(page))return;
        View root=a.findViewById(android.R.id.content);if(root==null)return;
        root.post(()->{
            tuneBase(a,root);
            tuneMedia(a,root);
            tuneForms(a,root,page);
            if("mail".equals(page)||"messages".equals(page)||"chat".equals(page))tuneMail(a,root);
            if("groups".equals(page)||"group".equals(page)||"feed".equals(page))tuneComments(a,root);
            if("dating".equals(page)||"nearby".equals(page))tuneDating(a,root);
            if("housing".equals(page)||"events".equals(page)||"event".equals(page))tuneCreationPages(a,root);
        });
    }

    private static void tuneBase(Activity a,View root){
        int touch=dp(a,48);
        walk(root,v->{
            if(v.isClickable()&&v.getMinimumHeight()<touch)v.setMinimumHeight(touch);
            if(v instanceof Button)((Button)v).setAllCaps(false);
            if(v instanceof HorizontalScrollView)((HorizontalScrollView)v).setHorizontalScrollBarEnabled(false);
        });
    }

    private static void tuneMedia(Activity a,View root){
        walk(root,v->{
            if(v instanceof ImageView){
                ImageView im=(ImageView)v;im.setAdjustViewBounds(true);
                ViewParent p=im.getParent();
                if((v.isClickable()||(p instanceof View&&((View)p).isClickable()))&&im.getMinimumHeight()<dp(a,96)){
                    im.setMinimumHeight(dp(a,96));im.setScaleType(ImageView.ScaleType.CENTER_CROP);
                }
                if(im.getContentDescription()==null&&(v.isClickable()||(p instanceof View&&((View)p).isClickable())))
                    im.setContentDescription("Відкрити медіа");
            }else if(v instanceof VideoView){
                v.setMinimumHeight(Math.max(v.getMinimumHeight(),dp(a,180)));
                if(v.getContentDescription()==null)v.setContentDescription("Відео");
            }else if(v instanceof SeekBar){
                v.setMinimumHeight(Math.max(v.getMinimumHeight(),dp(a,48)));
            }
        });
    }

    private static void tuneForms(Activity a,View root,String page){
        walk(root,v->{
            if(v instanceof EditText){
                EditText e=(EditText)v;
                e.setMinHeight(Math.max(e.getMinHeight(),dp(a,52)));
                e.setImeOptions(e.getImeOptions()|EditorInfo.IME_FLAG_NO_EXTRACT_UI);
                String hint=String.valueOf(e.getHint()).toLowerCase(Locale.ROOT);
                String desc=String.valueOf(e.getContentDescription()).toLowerCase(Locale.ROOT);
                if(e.getContentDescription()==null&&e.getHint()!=null)e.setContentDescription(e.getHint());
                if(hint.contains("опис")||hint.contains("description")||hint.contains("popis")||
                   desc.contains("опис")||desc.contains("description")||desc.contains("popis")){
                    e.setSingleLine(false);e.setMaxLines(8);e.setGravity(Gravity.TOP|Gravity.START);
                }
                e.setOnFocusChangeListener((x,focused)->{
                    if(!focused)return;
                    e.postDelayed(()->{
                        Rect r=new Rect(0,0,e.getWidth(),Math.max(e.getHeight(),dp(a,52)));
                        e.requestRectangleOnScreen(r,true);
                    },120);
                });
            }else if(v instanceof Spinner){
                v.setMinimumHeight(Math.max(v.getMinimumHeight(),dp(a,52)));
            }else if(v instanceof CheckBox||v instanceof Switch){
                v.setMinimumHeight(Math.max(v.getMinimumHeight(),dp(a,48)));
            }
        });
    }

    private static void tuneMail(Activity a,View root){
        Window w=a.getWindow();if(w!=null)w.setSoftInputMode(
            WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE|WindowManager.LayoutParams.SOFT_INPUT_STATE_UNCHANGED);
        final EditText composer=findComposer(root);
        if(composer!=null){
            composer.setSingleLine(false);composer.setMaxLines(6);composer.setMinHeight(dp(a,54));
            composer.setGravity(Gravity.TOP|Gravity.START);
            composer.setImeOptions(composer.getImeOptions()|EditorInfo.IME_FLAG_NO_EXTRACT_UI);
            composer.setContentDescription("Поле нового повідомлення");
            composer.setOnFocusChangeListener((v,focused)->{
                if(!focused)return;
                composer.postDelayed(()->{
                    composer.requestRectangleOnScreen(new Rect(0,0,composer.getWidth(),composer.getHeight()),true);
                    InputMethodManager ime=(InputMethodManager)a.getSystemService(Context.INPUT_METHOD_SERVICE);
                    if(ime!=null&&composer.hasWindowFocus())ime.showSoftInput(composer,InputMethodManager.SHOW_IMPLICIT);
                },140);
            });
        }
        walk(root,v->{
            String text=v instanceof TextView?((TextView)v).getText().toString().trim():"";
            String desc=String.valueOf(v.getContentDescription());
            if(matchesAny(text,desc,"Зробити фото","Голосове повідомлення","Кругле відео","Фото та файли","Форматування","Інші інструменти",
                    "Take photo","Voice message","Round video","Photos and files","Formatting","More tools",
                    "Vyfotit","Hlasová zpráva","Kulaté video","Fotky a soubory")){
                v.setMinimumHeight(Math.max(v.getMinimumHeight(),dp(a,48)));
                if(v.getContentDescription()==null&&!text.isEmpty())v.setContentDescription(text);
            }
            if(v.isLongClickable()&&v.getContentDescription()==null)v.setContentDescription("Дії повідомлення");
        });
    }

    private static void tuneComments(Activity a,View root){
        walk(root,v->{
            if(!(v instanceof TextView))return;
            TextView t=(TextView)v;String s=t.getText().toString().trim().toLowerCase(Locale.ROOT);
            if(s.equals("відповісти")||s.equals("reply")||s.equals("odpovědět")||
               s.equals("редагувати")||s.equals("edit")||s.equals("upravit")||
               s.equals("видалити")||s.equals("delete")||s.equals("smazat")||
               s.equals("лайк")||s.equals("like")||s.equals("líbí se")){
                t.setMinHeight(dp(a,44));t.setGravity((t.getGravity()&~Gravity.VERTICAL_GRAVITY_MASK)|Gravity.CENTER_VERTICAL);
                t.setPadding(Math.max(t.getPaddingLeft(),dp(a,8)),t.getPaddingTop(),Math.max(t.getPaddingRight(),dp(a,8)),t.getPaddingBottom());
            }
        });
    }

    private static void tuneDating(Activity a,View root){
        walk(root,v->{
            if(v instanceof TextView){
                TextView t=(TextView)v;String s=t.getText().toString().trim().toLowerCase(Locale.ROOT);
                if(s.contains("подоба")||s.equals("like")||s.contains("super like")||s.equals("написати")||
                   s.equals("message")||s.equals("napsat")||s.contains("líbí")){
                    t.setMinHeight(dp(a,52));t.setGravity((t.getGravity()&~Gravity.VERTICAL_GRAVITY_MASK)|Gravity.CENTER_VERTICAL);
                }
            }
        });
    }

    private static void tuneCreationPages(Activity a,View root){
        walk(root,v->{
            if(v instanceof Button){
                Button b=(Button)v;b.setMinHeight(Math.max(b.getMinHeight(),dp(a,52)));
            }
            if(v instanceof ImageView&&v.isClickable()){
                v.setMinimumHeight(Math.max(v.getMinimumHeight(),dp(a,110)));
                if(v.getContentDescription()==null)v.setContentDescription("Додати або відкрити фото");
            }
        });
    }

    private static EditText findComposer(View root){
        final EditText[] best={null};final int[] score={Integer.MIN_VALUE};
        walk(root,v->{if(!(v instanceof EditText))return;EditText e=(EditText)v;
            String h=String.valueOf(e.getHint()).toLowerCase(Locale.ROOT),d=String.valueOf(e.getContentDescription()).toLowerCase(Locale.ROOT);
            int s=0;if(h.contains("повідом")||h.contains("message")||h.contains("zpráv"))s+=10;
            if(d.contains("повідом")||d.contains("message"))s+=6;if(!e.isSingleLine())s+=2;
            int[] loc=new int[2];e.getLocationOnScreen(loc);s+=Math.min(4,loc[1]/500);
            if(s>score[0]){score[0]=s;best[0]=e;}
        });return score[0]>=4?best[0]:null;
    }

    private static boolean matchesAny(String text,String desc,String... values){
        for(String v:values)if(v.equalsIgnoreCase(text)||desc.equalsIgnoreCase(v)||desc.toLowerCase(Locale.ROOT).contains(v.toLowerCase(Locale.ROOT)))return true;
        return false;
    }
    private interface Visitor{void visit(View v);}
    private static void walk(View v,Visitor x){x.visit(v);if(v instanceof ViewGroup){ViewGroup g=(ViewGroup)v;for(int i=0;i<g.getChildCount();i++)walk(g.getChildAt(i),x);}}
    private static int dp(Context c,int n){return Math.round(c.getResources().getDisplayMetrics().density*n);}
}
