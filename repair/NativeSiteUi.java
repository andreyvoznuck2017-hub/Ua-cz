package eu.svoyi.nativeapp;

import android.app.Activity;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Typeface;
import android.graphics.drawable.Drawable;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.*;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.*;

/** Native views using the current server projection, not a WebView or screenshot. */
public final class NativeSiteUi {
    private NativeSiteUi() {}
    private static final Map<Activity,JSONObject> homeModels = new WeakHashMap<>();
    public static void remember(Activity activity, JSONObject result) {
        homeModels.remove(activity);
        if (result != null && "home".equals(result.optString("page"))) homeModels.put(activity,result);
    }
    static int dp(Context c,float n){return Math.round(c.getResources().getDisplayMetrics().density*n);}
    static GradientDrawable shape(Context c,int fill,int radius,int stroke){
        GradientDrawable d=new GradientDrawable();d.setColor(fill);d.setCornerRadius(dp(c,radius));
        if(stroke!=0)d.setStroke(dp(c,1),stroke);return d;
    }
    static TextView text(Context c,ThemePalette t,String value,int size,boolean bold){
        TextView v=new TextView(c);v.setText(value);v.setTextColor(t.text);v.setTextSize(size);
        v.setTypeface(Typeface.create(bold?"sans-serif-medium":"sans-serif",bold?Typeface.BOLD:Typeface.NORMAL));
        v.setIncludeFontPadding(false);v.setLineSpacing(dp(c,2),1);return v;
    }
    static LinearLayout col(Context c){LinearLayout l=new LinearLayout(c);l.setOrientation(1);return l;}
    static void add(LinearLayout p,View v,int top,int bottom){
        if(v==null)return;detach(v);LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);
        lp.setMargins(0,dp(p.getContext(),top),0,dp(p.getContext(),bottom));p.addView(v,lp);
    }
    static void detach(View v){if(v.getParent() instanceof ViewGroup)((ViewGroup)v.getParent()).removeView(v);}
    static JSONArray array(JSONObject n,String key){JSONArray a=n==null?null:n.optJSONArray(key);return a==null?new JSONArray():a;}
    static String plain(String value){return value==null?"":value.replaceAll("<[^>]*>","").replace("&nbsp;"," ").replace("&amp;","&").trim();}
    static void navigate(NativeJobsScreen.Host h,String route){
        if(!h.alive()||route==null||route.isEmpty())return;
        if(route.contains("#job-search"))route="/?p=home&native=jobs";
        h.navigate(route);
    }
    static String label(JSONObject n){return plain(n.optString("title",n.optString("text")));}
    static LinearLayout panel(Context c,ThemePalette t,int pad){
        LinearLayout p=col(c);p.setBackground(shape(c,t.surface,16,t.border));
        p.setPadding(dp(c,pad),dp(c,pad),dp(c,pad),dp(c,pad));return p;
    }
    static ImageView icon(Context c,ThemePalette t,String key,int size){
        ImageView v=new ImageView(c);v.setImageDrawable(NativeIcons.get(c,key,t.accent));
        v.setScaleType(ImageView.ScaleType.CENTER_INSIDE);v.setPadding(dp(c,5),dp(c,5),dp(c,5),dp(c,5));
        v.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);return v;
    }
    static View photo(NativeJobsScreen.Host h,String url){View v=h.image(url);if(v instanceof ImageView)((ImageView)v).setScaleType(ImageView.ScaleType.CENTER_CROP);v.setClipToOutline(false);return v;}
    static TextView link(Context c,ThemePalette t,JSONObject n,NativeJobsScreen.Host h,boolean filled){
        TextView b=text(c,t,label(n),14,true);b.setPadding(dp(c,12),dp(c,12),dp(c,12),dp(c,12));
        b.setMinHeight(dp(c,44));b.setGravity(Gravity.CENTER_VERTICAL);
        b.setTextColor(filled?t.primaryText:t.accent);if(filled)b.setBackground(shape(c,t.accent,12,0));
        b.setContentDescription(label(n));b.setFocusable(true);b.setOnClickListener(v->navigate(h,n.optString("route")));return b;
    }
    public static View home(NativeWelcome w,String user,View jobs,View housing,View publications){
        Activity a=w.activity;ThemePalette t=w.colors;NativeJobsScreen.Host h=w.host;
        JSONObject model=homeModels.remove(a);JSONArray nodes=array(model,"nodes");
        LinearLayout page=col(a);page.setTag("site-match-home");
        if(nodes.length()==0){add(page,text(a,t,"Не вдалося отримати головну. Оновіть сторінку.",16,false),8,12);return page;}
        JSONObject first=nodes.optJSONObject(0);JSONArray children=array(first,"children");
        FrameLayout hero=new FrameLayout(a);hero.setBackground(shape(a,t.field,16,t.border));hero.setClipToOutline(true);
        View cover=photo(h,"https://test.jkunis.eu/assets/themes/prague-night-clean.png");hero.addView(cover,new FrameLayout.LayoutParams(-1,-1));
        View fade=new View(a);int solid=t.dark?t.surface:0xfff3f6fa;int end=t.dark?0x30202534:0x0affffff;
        fade.setBackground(new GradientDrawable(GradientDrawable.Orientation.LEFT_RIGHT,new int[]{solid,solid,end}));hero.addView(fade,new FrameLayout.LayoutParams(-1,-1));
        LinearLayout copy=col(a);copy.setPadding(dp(a,16),dp(a,26),dp(a,16),dp(a,24));int seen=0;
        for(int i=0;i<children.length()&&seen<3;i++){
            JSONObject n=children.optJSONObject(i);if(n==null)continue;String kind=n.optString("type");if(!kind.equals("text")&&!kind.equals("heading"))continue;
            boolean head=kind.equals("heading");TextView txt=text(a,t,plain(n.optString("text")),head?25:seen==0?10:13,head||seen==0);
            if(seen==0){txt.setTextColor(t.accent);txt.setLetterSpacing(.12f);}else if(!head)txt.setTextColor(t.muted);
            add(copy,txt,seen==0?0:7,0);seen++;
        }
        hero.addView(copy,new FrameLayout.LayoutParams(-1,-2));add(page,hero,0,12);
        Flow pills=new Flow(a,8);for(int i=0;i<children.length();i++){
            JSONObject n=children.optJSONObject(i);if(n==null||!n.optString("type").equals("link"))continue;
            LinearLayout chip=new LinearLayout(a);chip.setGravity(Gravity.CENTER_VERTICAL);chip.setPadding(dp(a,9),dp(a,6),dp(a,11),dp(a,6));chip.setBackground(shape(a,t.surface,23,t.border));chip.setMinimumHeight(dp(a,44));
            chip.addView(icon(a,t,n.optString("icon"),24),new LinearLayout.LayoutParams(dp(a,27),dp(a,27)));
            TextView title=text(a,t,label(n),12,true);LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-2,-2);lp.setMarginStart(dp(a,5));chip.addView(title,lp);
            chip.setContentDescription(label(n));chip.setFocusable(true);chip.setOnClickListener(v->navigate(h,n.optString("route")));pills.addView(chip);
        }
        add(page,pills,0,12);
        for(int i=0;i<children.length();i++){
            JSONObject n=children.optJSONObject(i);if(n==null||!n.optString("type").equals("card"))continue;
            JSONArray nested=array(n,"children");boolean covers=false;for(int k=0;k<nested.length();k++){JSONObject z=nested.optJSONObject(k);if(z!=null&&"cover".equals(z.optString("layout")))covers=true;}
            if(!covers){add(page,renderCard(a,t,h,n,0),4,14);continue;}
            List<JSONObject> tiles=new ArrayList<>();boolean grid=false;
            for(int j=0;j<nested.length();j++){
                JSONObject item=nested.optJSONObject(j);if(item==null)continue;
                if(item.optString("type").equals("heading")){grid=true;add(page,text(a,t,plain(item.optString("text")),18,true),8,10);}
                else if(item.optString("layout").equals("cover")){
                    if(grid)tiles.add(item);else if(item.optString("route").contains("p=feed"))add(page,feature(a,t,h,item,true),0,10);else add(page,feature(a,t,h,item,false),0,8);
                }else if(item.optString("type").equals("link"))add(page,link(a,t,item,h,false),0,4);
            }
            for(int j=0;j<tiles.size();j+=2){LinearLayout row=new LinearLayout(a);
                for(int k=j;k<Math.min(j+2,tiles.size());k++){View tile=tile(a,t,h,tiles.get(k));LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(0,dp(a,132),1);lp.setMargins(0,0,k==j?dp(a,8):0,0);row.addView(tile,lp);}
                if(j+1>=tiles.size())row.addView(new View(a),new LinearLayout.LayoutParams(0,1,1));add(page,row,0,8);
            }
        }
        // Server projection also includes desktop-only duplicates. Actual dynamic cards remain.
        for(int i=1;i<nodes.length();i++){
            JSONObject n=nodes.optJSONObject(i);if(n==null)continue;String raw=n.toString();
            if(raw.contains("Усе потрібне — серед своїх")||raw.contains("РЕКЛАМА ТА ПРОСУВВАННЯ"))continue;
            JSONArray cs=array(n,"children");boolean allLinks=cs.length()>5;for(int k=0;k<cs.length();k++){JSONObject c=cs.optJSONObject(k);if(c==null||!"link".equals(c.optString("type")))allLinks=false;}
            if(allLinks)continue;
            if("job-search".equals(n.optString("id"))){
                if(jobs!=null)add(page,jobs,12,12);JSONObject route=new JSONObject();try{route.put("title","Усі вакансії та пошук роботи →");route.put("route","/?p=home&native=jobs");}catch(Exception ignored){}
                add(page,link(a,t,route,h,true),0,12);continue;
            }
            add(page,renderCard(a,t,h,n,0),8,12);
        }
        if(housing!=null)add(page,housing,4,12);if(publications!=null)add(page,publications,4,12);return page;
    }
    static View renderCard(Activity a,ThemePalette t,NativeJobsScreen.Host h,JSONObject n,int depth){
        LinearLayout box=panel(a,t,16);if(depth>8)return box;JSONArray arr=array(n,"children");for(int i=0;i<arr.length();i++){
            JSONObject c=arr.optJSONObject(i);if(c==null)continue;String type=c.optString("type"),tx=plain(c.optString("text"));
            if(type.equals("heading")){add(box,text(a,t,tx,c.optInt("level",2)<=2?21:18,true),7,10);}
            else if(type.equals("text")){TextView v=text(a,t,tx,13,false);v.setTextColor(t.muted);add(box,v,4,8);}
            else if(type.equals("link")){add(box,link(a,t,c,h,tx.contains("Додати своє")||tx.contains("Отримати")),4,6);}
            else if(type.equals("image")&&!c.optString("src").isEmpty()){View p=photo(h,c.optString("src"));box.addView(p,new LinearLayout.LayoutParams(-1,dp(a,180)));}
            else if(type.equals("form")){add(box,h.form(c),5,6);}
            else if(type.equals("card")){add(box,renderCard(a,t,h,c,depth+1),8,4);}
        }return box;
    }
    static View tile(Activity a,ThemePalette t,NativeJobsScreen.Host h,JSONObject n){
        FrameLayout f=new FrameLayout(a);f.setBackground(shape(a,t.surface,12,t.border));f.setClipToOutline(true);f.addView(photo(h,n.optString("image")),new FrameLayout.LayoutParams(-1,-1));View shade=new View(a);shade.setBackground(new GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM,new int[]{0,0xb0001020}));f.addView(shade,new FrameLayout.LayoutParams(-1,-1));
        LinearLayout copy=col(a);copy.setPadding(dp(a,12),dp(a,10),dp(a,12),dp(a,12));TextView title=text(a,t,label(n),16,true);title.setTextColor(Color.WHITE);copy.addView(title);TextView go=text(a,t,"Перейти →",11,false);go.setTextColor(Color.WHITE);add(copy,go,4,0);f.addView(copy,new FrameLayout.LayoutParams(-1,-2,Gravity.BOTTOM));f.setContentDescription(label(n));f.setOnClickListener(v->navigate(h,n.optString("route")));return f;
    }
    static View feature(Activity a,ThemePalette t,NativeJobsScreen.Host h,JSONObject n,boolean main){
        String title=label(n),description=plain(n.optString("text"));int at=description.indexOf(title);if(at>=0)description=description.substring(at+title.length()).trim();
        if(!main){LinearLayout row=new LinearLayout(a);row.setGravity(Gravity.CENTER_VERTICAL);row.setBackground(shape(a,t.surface,14,t.border));row.setClipToOutline(true);
            LinearLayout copy=col(a);copy.setPadding(dp(a,14),dp(a,14),dp(a,8),dp(a,14));copy.addView(text(a,t,title,13,true));TextView sub=text(a,t,description,11,false);sub.setTextColor(t.muted);add(copy,sub,4,0);row.addView(copy,new LinearLayout.LayoutParams(0,-2,1));row.addView(photo(h,n.optString("image")),new LinearLayout.LayoutParams(dp(a,108),dp(a,84)));row.setOnClickListener(v->navigate(h,n.optString("route")));return row;}
        FrameLayout f=new FrameLayout(a);f.setMinimumHeight(dp(a,270));f.setBackground(shape(a,t.surface,14,0));f.setClipToOutline(true);f.addView(photo(h,n.optString("image")),new FrameLayout.LayoutParams(-1,-1));View shade=new View(a);shade.setBackground(new GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM,new int[]{0x05051927,0xe5101b30}));f.addView(shade,new FrameLayout.LayoutParams(-1,-1));
        LinearLayout copy=col(a);copy.setPadding(dp(a,18),dp(a,75),dp(a,18),dp(a,18));TextView over=text(a,t,"СВОЇ У ЄВРОПІ",10,true);over.setTextColor(Color.WHITE);over.setLetterSpacing(.12f);copy.addView(over);TextView header=text(a,t,title,24,true);header.setTextColor(Color.WHITE);add(copy,header,8,6);description=description.replace("Відкрити спільноту →","").trim();TextView sub=text(a,t,description,13,false);sub.setTextColor(Color.WHITE);add(copy,sub,0,12);TextView button=text(a,t,"Відкрити спільноту →",13,true);button.setTextColor(Color.WHITE);button.setBackground(shape(a,0xff2858a1,10,0));button.setPadding(dp(a,14),dp(a,12),dp(a,14),dp(a,12));copy.addView(button);f.addView(copy,new FrameLayout.LayoutParams(-1,-2,Gravity.BOTTOM));f.setContentDescription(title);f.setOnClickListener(v->navigate(h,n.optString("route")));return f;
    }
    /** Separate measuring of avatar and identity prevents overlap on small screens. */
    public static View profile(NativeProfileContent pc,JSONObject n,boolean cabinet){
        Activity a=pc.activity;ThemePalette t=pc.colors;NativeProfileContent.Host h=pc.host;
        LinearLayout card=panel(a,t,0);card.setTag(cabinet?"site-match-cabinet":"site-match-profile");card.setClipToOutline(true);
        JSONArray identity=n.optJSONArray("identityChildren");if(identity==null)identity=n.optJSONArray("profileChildren");if(identity==null)identity=array(n,"children");
        JSONArray clean=new JSONArray();for(int i=0;i<identity.length();i++){JSONObject c=identity.optJSONObject(i);if(c==null)continue;String type=c.optString("type"),tx=c.optString("text");if(tx.equals("ОСОБИСТИЙ КАБІНЕТ")||tx.equals("ПРОФІЛЬ"))continue;
            if(type.equals("cover")||type.equals("link")&&c.optString("image").equals(n.optString("avatar")))continue;if(cabinet&&type.equals("link"))continue;clean.put(c);
        }
        View cover;String url=n.optString("cover");if(url.isEmpty()){cover=new View(a);Drawable d=h.cover(n.optJSONObject("coverStyle"));cover.setBackground(d!=null?d:new GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM,new int[]{t.field,t.dark?0xff424d5b:0xffaab5ba}));}
        else{cover=h.image(url,false,n.optJSONObject("coverStyle"));if(cover instanceof ImageView)((ImageView)cover).setScaleType(ImageView.ScaleType.CENTER_CROP);cover.setOnClickListener(v->{if(h.alive())h.photo(url,n);});}
        FrameLayout avatar=new FrameLayout(a);avatar.setPadding(dp(a,4),dp(a,4),dp(a,4),dp(a,4));avatar.setBackground(shape(a,t.surface,100,0));avatar.setElevation(dp(a,4));View image=h.image(n.optString("avatar"),true,n.optJSONObject("avatarStyle"));detach(image);avatar.addView(image,new FrameLayout.LayoutParams(-1,-1));
        avatar.setContentDescription("Відкрити фото профілю");avatar.setOnClickListener(v->{if(!h.alive())return;String r=n.optString("avatarRoute");if(!r.isEmpty())h.navigate(r);else if(!n.optString("avatar").isEmpty())h.photo(n.optString("avatar"),n);});
        LinearLayout copy=col(a);pc.identity(copy,clean,0);copy.setPadding(0,0,0,0);ProfileHeader mast=new ProfileHeader(a,cover,avatar,copy,cabinet);card.addView(mast,new LinearLayout.LayoutParams(-1,-2));
        if(cabinet&&!n.optString("editRoute").isEmpty()){ImageView edit=icon(a,t,"camera",30);edit.setBackground(shape(a,t.surface,12,t.border));edit.setContentDescription("Змінити фото й обкладинку");edit.setOnClickListener(v->{if(h.alive())h.navigate(n.optString("editRoute"));});mast.addCamera(edit);}
        LinearLayout actions=col(a);actions.setPadding(dp(a,15),dp(a,8),dp(a,15),dp(a,16));pc.actions(actions,array(n,"actions"));card.addView(actions);return card;
    }
    static final class ProfileHeader extends ViewGroup {
        final View cover,avatar,copy;final boolean cabinet;View camera;int coverH,avatarS,over,pad,gap,copyTop,copyLeft;
        ProfileHeader(Context c,View co,View av,View cp,boolean cab){super(c);cover=co;avatar=av;copy=cp;cabinet=cab;setClipChildren(false);addView(co);addView(av);addView(cp);}
        void addCamera(View v){camera=v;addView(v);}
        @Override protected void onMeasure(int ws,int hs){int w=MeasureSpec.getSize(ws);coverH=dp(getContext(),cabinet?180:156);avatarS=dp(getContext(),cabinet?108:66);over=dp(getContext(),cabinet?40:25);pad=dp(getContext(),16);gap=dp(getContext(),12);
            boolean stack=w<dp(getContext(),340)&&getResources().getConfiguration().fontScale>1.2f;copyLeft=stack?pad:pad+avatarS+gap;copyTop=stack?coverH-over+avatarS+gap:coverH+dp(getContext(),12);
            cover.measure(MeasureSpec.makeMeasureSpec(w,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(coverH,MeasureSpec.EXACTLY));avatar.measure(MeasureSpec.makeMeasureSpec(avatarS,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(avatarS,MeasureSpec.EXACTLY));copy.measure(MeasureSpec.makeMeasureSpec(Math.max(1,w-copyLeft-pad),MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(0,MeasureSpec.UNSPECIFIED));
            if(camera!=null)camera.measure(MeasureSpec.makeMeasureSpec(dp(getContext(),40),MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(dp(getContext(),40),MeasureSpec.EXACTLY));setMeasuredDimension(w,Math.max(coverH-over+avatarS,copyTop+copy.getMeasuredHeight())+dp(getContext(),10));}
        @Override protected void onLayout(boolean changed,int l,int t,int r,int b){cover.layout(0,0,r-l,coverH);avatar.layout(pad,coverH-over,pad+avatarS,coverH-over+avatarS);copy.layout(copyLeft,copyTop,r-l-pad,copyTop+copy.getMeasuredHeight());if(camera!=null)camera.layout(r-l-pad-camera.getMeasuredWidth(),coverH-dp(getContext(),48),r-l-pad,coverH-dp(getContext(),8));}
    }
    static final class Flow extends ViewGroup {
        final int gap;Flow(Context c,int g){super(c);gap=dp(c,g);}
        @Override protected void onMeasure(int ws,int hs){int w=MeasureSpec.getSize(ws),x=0,y=0,line=0;for(int i=0;i<getChildCount();i++){View v=getChildAt(i);v.measure(MeasureSpec.makeMeasureSpec(w,MeasureSpec.AT_MOST),MeasureSpec.makeMeasureSpec(0,MeasureSpec.UNSPECIFIED));int cw=v.getMeasuredWidth(),ch=v.getMeasuredHeight();if(x>0&&x+cw>w){x=0;y+=line+gap;line=0;}x+=cw+gap;line=Math.max(line,ch);}setMeasuredDimension(w,y+line);}
        @Override protected void onLayout(boolean changed,int l,int t,int r,int b){int w=r-l,x=0,y=0,line=0;for(int i=0;i<getChildCount();i++){View v=getChildAt(i);int cw=v.getMeasuredWidth(),ch=v.getMeasuredHeight();if(x>0&&x+cw>w){x=0;y+=line+gap;line=0;}v.layout(x,y,x+cw,y+ch);x+=cw+gap;line=Math.max(line,ch);}}
    }
    public static void inbox(NativeMailScreen s){
        Activity a=s.activity;ThemePalette t=s.theme;s.root.setBackgroundColor(t.surface);
        if(s.root.getChildCount()>0&&s.root.getChildAt(0) instanceof LinearLayout){LinearLayout top=(LinearLayout)s.root.getChildAt(0);if(top.getChildCount()>0)top.removeViewAt(0);LinearLayout titles=col(a);titles.addView(text(a,t,"Повідомлення",21,true));TextView sub=text(a,t,"Ваші діалоги",13,false);sub.setTextColor(t.muted);add(titles,sub,6,0);top.addView(titles,0,new LinearLayout.LayoutParams(0,-2,1));ImageView filters=icon(a,t,"more",30);filters.setContentDescription("Фільтри діалогів");top.addView(filters,new LinearLayout.LayoutParams(dp(a,42),dp(a,44)));
            filters.setOnClickListener(v->{PopupMenu p=new PopupMenu(a,v);p.getMenu().add("Усі діалоги").setOnMenuItemClickListener(m->{s.allInbox.performClick();return true;});p.getMenu().add("Непрочитані").setOnMenuItemClickListener(m->{s.unreadInbox.performClick();return true;});p.getMenu().add("Очистити пошук").setOnMenuItemClickListener(m->{s.search.setText("");return true;});p.show();});}
        if(s.allInbox!=null&&s.allInbox.getParent() instanceof View)((View)s.allInbox.getParent()).setVisibility(View.GONE);if(s.inboxScope!=null)s.inboxScope.setVisibility(View.GONE);
        if(s.search!=null){s.search.setHint("Пошук у діалогах");s.search.setTextSize(16);s.search.setBackground(shape(a,t.field,23,0));s.search.setPadding(dp(a,15),dp(a,11),dp(a,15),dp(a,11));s.search.setMinimumHeight(dp(a,46));}
        if(s.scroll!=null)s.scroll.setBackgroundColor(t.surface);if(s.inboxList!=null)s.inboxList.setPadding(0,dp(a,6),0,0);
    }
    public static void inboxRow(LinearLayout row,JSONObject data){
        Context a=row.getContext();row.setBackgroundColor(Color.TRANSPARENT);row.setPadding(0,dp(a,9),0,dp(a,9));row.setMinimumHeight(dp(a,72));
        if(row.getChildCount()<2||!(row.getChildAt(1) instanceof LinearLayout))return;LinearLayout labels=(LinearLayout)row.getChildAt(1);if(labels.getChildCount()>1&&labels.getChildAt(1) instanceof TextView){TextView p=(TextView)labels.getChildAt(1);p.setMaxLines(1);p.setTextSize(14);}if(labels.getChildCount()>2)labels.getChildAt(2).setVisibility(View.GONE);
        JSONObject presence=data==null?null:data.optJSONObject("presence");final boolean online=presence!=null&&presence.optBoolean("online")&&!presence.optBoolean("hidden");
        row.getOverlay().clear();if(online){Paint paint=new Paint(3);paint.setColor(0xff1daf75);Drawable dot=new Drawable(){public void draw(Canvas c){c.drawCircle(dp(a,46),dp(a,52),dp(a,5),paint);}public void setAlpha(int v){paint.setAlpha(v);}public void setColorFilter(android.graphics.ColorFilter f){paint.setColorFilter(f);}public int getOpacity(){return -3;}};dot.setBounds(0,0,dp(a,60),dp(a,72));row.getOverlay().add(dot);}
    }
    public static void thread(NativeMailScreen s){
        Activity a=s.activity;ThemePalette t=s.theme;View actions=s.root.findViewWithTag("mail-thread-actions");
        if(actions instanceof LinearLayout&&s.header!=null){LinearLayout old=(LinearLayout)actions;List<View> buttons=new ArrayList<>();for(int i=0;i<old.getChildCount();i++)buttons.add(old.getChildAt(i));old.removeAllViews();s.root.removeView(old);s.header.setPadding(dp(a,2),dp(a,6),dp(a,3),dp(a,6));
            if(s.header.getChildCount()>1){View av=s.header.getChildAt(1);LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(dp(a,34),dp(a,34));lp.setMargins(0,0,dp(a,6),0);av.setLayoutParams(lp);}
            for(View v:buttons){String cd=String.valueOf(v.getContentDescription());if(cd.contains("Пошук"))continue;s.header.addView(v,new LinearLayout.LayoutParams(dp(a,36),dp(a,42)));}
            View more=null;for(View v:buttons)if(String.valueOf(v.getContentDescription()).contains("Дії"))more=v;if(more!=null)more.setOnClickListener(v->{PopupMenu p=new PopupMenu(a,v);p.getMenu().add("Пошук у діалозі").setOnMenuItemClickListener(m->{s.toggleHistorySearch();return true;});p.getMenu().add("Усі дії діалогу").setOnMenuItemClickListener(m->{s.threadTools();return true;});p.show();});
        }
        if(s.scroll!=null)s.scroll.setBackgroundColor(t.background);
        if(s.composer!=null&&s.tools!=null){detach(s.tools);HorizontalScrollView wrap=new HorizontalScrollView(a);wrap.setHorizontalScrollBarEnabled(false);wrap.setBackgroundColor(t.surface);LinearLayout toolbar=new LinearLayout(a);toolbar.setPadding(dp(a,8),dp(a,4),dp(a,8),dp(a,4));wrap.addView(toolbar);wrap.setTag("site-match-mail-toolbar");
            Runnable[] handlers={()->s.emoji(),()->s.host.chooseAttachment("photo",s::acceptAttachment),()->s.record("voice"),()->s.record("round_video"),()->s.host.chooseAttachment("file",s::acceptAttachment),()->s.format(),()->s.composeTools()};String[] keys={"smile","camera","microphone","video","attachment","text","more"};String[] names={"Смайли","Зробити фото","Голосове повідомлення","Кругле відео","Фото та файли","Форматування","Інші інструменти"};
            for(int i=0;i<keys.length;i++){final Runnable fn=handlers[i];ImageView b=icon(a,t,keys[i],30);b.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_YES);b.setContentDescription(names[i]);b.setBackground(shape(a,t.field,9,0));b.setOnClickListener(v->{if(s.alive()&&s.canSend&&!s.sending&&!s.staging)fn.run();});LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(dp(a,34),dp(a,34));p.setMarginEnd(dp(a,5));toolbar.addView(b,p);}
            int index=s.root.indexOfChild(s.composer);s.root.addView(wrap,index,new LinearLayout.LayoutParams(-1,-2));s.composer.setPadding(dp(a,10),dp(a,6),dp(a,10),dp(a,10));s.input.setBackground(shape(a,t.surface,13,t.border));s.input.setTextSize(16);s.input.setPadding(dp(a,12),dp(a,11),dp(a,12),dp(a,11));s.input.setMinHeight(dp(a,44));s.input.setMinimumHeight(dp(a,44));
        }
    }
}
