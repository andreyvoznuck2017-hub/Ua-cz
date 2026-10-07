package eu.svoyi.nativeapp;

import android.app.*;
import android.content.*;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.view.*;
import android.widget.*;
import org.json.*;
import java.util.*;

/** Responsive home, preserving every server section and its native actions. */
public final class HomeScreen257 {
    private static final int SITE=0, PLUS=1;
    private final Activity activity;
    private final MainActivity owner;
    private final NativeJobsScreen.Host host;
    private final JSONObject model;
    private final LinearLayout root;
    private final int variant;
    private final List<JSONObject> stats=new ArrayList<>(), sections=new ArrayList<>();
    private JSONObject avatar;
    private String heroTitle="", heroLead="", heroSeason="";
    private final int bg,card,text,muted,border,link,accent,heroText,heroMuted;
    private final String language;
    private final boolean dark;

    public static View buildSite(NativeWelcome w,JSONObject model){return new HomeScreen257(w,model,SITE).root;}
    public static View buildPlus(NativeWelcome w,JSONObject model){return new HomeScreen257(w,model,PLUS).root;}

    private HomeScreen257(NativeWelcome w,JSONObject value,int which){
        activity=w.activity;owner=(MainActivity)w.activity;host=w.host;model=value==null?new JSONObject():value;variant=which;
        language=locale(model);
        ThemePalette p=w.colors;dark=p!=null&&p.dark;
        bg=p==null?Color.rgb(248,242,233):p.background;card=p==null?Color.rgb(255,252,247):p.surface;text=p==null?Color.rgb(52,42,36):p.text;muted=p==null?Color.rgb(124,106,92):p.muted;
        border=p==null?Color.rgb(230,213,191):p.border;link=p==null?Color.rgb(36,91,155):p.accent;accent=p==null?Color.rgb(183,104,43):p.accent;heroText=Color.rgb(255,246,236);heroMuted=Color.rgb(255,209,138);
        root=column();root.setBackgroundColor(bg);root.setTag("home257-site");
        JSONArray nodes=array(model,"nodes");
        if(nodes.length()==0){TextView empty=text(t("Головна не завантажилася","Domovská stránka se nenačetla","Home did not load"),18,true,text);add(root,empty,14,14);return;}
        parse(nodes);
        // Keep the current server order; new sections must never disappear behind a fixed list.
        add(root,hero(),0,variant==SITE?12:10);
        add(root,variant==SITE?siteStats():plusStats(),0,8);
        boolean nearby=false;for(JSONObject n:sections)if(n.toString().contains("p=nearby")){nearby=true;break;}
        if(!nearby)add(root,nearbyQuick(),0,12);
        for(JSONObject n:sections){View v=section(n);if(v!=null)add(root,v,0,12);}
        TextView footer=text(t("Свої у Європі","Svoji v Evropě","Svoyi in Europe"),12,true,muted);footer.setGravity(Gravity.CENTER);add(root,footer,8,20);
    }

    private void parse(JSONArray nodes){
        JSONObject top=nodes.optJSONObject(0);
        if(top!=null&&"card".equals(top.optString("type"))){
            JSONArray c=array(top,"children");boolean body=false;int statCount=0;
            for(int i=0;i<c.length();i++){
                JSONObject n=c.optJSONObject(i);if(n==null)continue;String type=n.optString("type");
                if(!body&&type.equals("image")&&avatar==null){avatar=n;continue;}
                if(!body&&type.equals("heading")&&heroTitle.isEmpty()){heroTitle=n.optString("text");continue;}
                if(!body&&type.equals("text")&&heroLead.isEmpty()){heroLead=n.optString("text");continue;}
                if(!body&&type.equals("text")&&heroSeason.isEmpty()){heroSeason=n.optString("text");continue;}
                if(!body&&type.equals("link")&&statCount<4){stats.add(n);statCount++;continue;}
                body=true;appendSection(n,0);
            }
            for(int k=1;k<nodes.length();k++)appendSection(nodes.optJSONObject(k),0);
        }else for(int k=0;k<nodes.length();k++)appendSection(nodes.optJSONObject(k),0);
    }

    private void appendSection(JSONObject n,int depth){
        if(n==null||depth>8)return;JSONArray c=array(n,"children");
        boolean wrapper="card".equals(n.optString("type"))&&n.optString("id").isEmpty()&&c.length()>0;
        if(wrapper)for(int i=0;i<c.length();i++){JSONObject x=c.optJSONObject(i);if(x==null||!"card".equals(x.optString("type"))){wrapper=false;break;}}
        if(wrapper){for(int i=0;i<c.length();i++)appendSection(c.optJSONObject(i),depth+1);}else sections.add(n);
    }

    private View hero(){
        FrameLayout hero=new FrameLayout(activity);hero.setTag("home257-hero");hero.setMinimumHeight(dp(156));hero.setBackground(round(Color.rgb(39,31,25),18,border));hero.setClipToOutline(true);hero.setElevation(dp(variant==SITE?1:2));
        View backdrop=host.image("https://test.jkunis.eu/assets/themes/prague-night-clean.png");
        if(backdrop instanceof ImageView)((ImageView)backdrop).setScaleType(ImageView.ScaleType.CENTER_CROP);
        if(backdrop!=null)hero.addView(backdrop,new FrameLayout.LayoutParams(-1,-1));
        GradientDrawable overlay=new GradientDrawable(GradientDrawable.Orientation.LEFT_RIGHT,new int[]{Color.argb(246,23,32,36),Color.argb(194,16,39,56),Color.argb(85,16,39,56)});
        hero.addView(view(overlay),new FrameLayout.LayoutParams(-1,-1));
        LinearLayout row=new LinearLayout(activity);row.setGravity(Gravity.CENTER_VERTICAL);row.setPadding(dp(14),dp(14),dp(14),dp(14));
        View av=avatarView();LinearLayout.LayoutParams ap=new LinearLayout.LayoutParams(dp(variant==SITE?52:58),dp(variant==SITE?52:58));ap.setMarginEnd(dp(12));row.addView(av,ap);
        LinearLayout copy=column();TextView title=text(heroTitle.isEmpty()?"Свої у Європі":heroTitle,variant==SITE?20:21,true,heroText);add(copy,title,0,5);
        if(!heroLead.isEmpty()){TextView lead=text(heroLead,13,false,Color.rgb(244,225,207));lead.setMaxLines(2);add(copy,lead,0,3);}
        if(!heroSeason.isEmpty()){TextView season=text(heroSeason,13,false,heroMuted);season.setMaxLines(1);add(copy,season,0,0);}
        row.addView(copy,new LinearLayout.LayoutParams(0,-2,1));hero.addView(row,new FrameLayout.LayoutParams(-1,-2,Gravity.CENTER_VERTICAL));
        TextView leaves=text(variant==SITE?"🍁\n🍂":"🍁",variant==SITE?28:24,false,heroMuted);leaves.setAlpha(.9f);FrameLayout.LayoutParams lp=new FrameLayout.LayoutParams(-2,-2,Gravity.TOP|Gravity.END);lp.setMargins(0,dp(4),dp(6),0);hero.addView(leaves,lp);
        return hero;
    }

    private View avatarView(){
        FrameLayout frame=new FrameLayout(activity);frame.setBackground(round(Color.argb(235,255,252,247),80,Color.argb(210,255,255,255)));frame.setClipToOutline(true);
        String url=avatar==null?"":avatar.optString("url",avatar.optString("src",avatar.optString("image","")));
        View image=url.isEmpty()?null:host.image(url);if(image instanceof ImageView)((ImageView)image).setScaleType(ImageView.ScaleType.CENTER_CROP);
        if(image!=null)frame.addView(image,new FrameLayout.LayoutParams(-1,-1));else{TextView t=text("👤",26,false,muted);t.setGravity(Gravity.CENTER);frame.addView(t,new FrameLayout.LayoutParams(-1,-1));}
        return frame;
    }

    private View nearbyQuick(){
        LinearLayout row=new LinearLayout(activity);row.setGravity(Gravity.CENTER_VERTICAL);
        row.setPadding(dp(13),dp(11),dp(13),dp(11));row.setBackground(round(card,14,border));row.setElevation(dp(1));
        TextView icon=text("👥",22,false,text);LinearLayout.LayoutParams ip=new LinearLayout.LayoutParams(dp(38),dp(44));row.addView(icon,ip);
        LinearLayout copy=column();TextView title=text(t("Люди поруч","Lidé poblíž","People nearby"),15,true,text);add(copy,title,0,2);
        TextView sub=text(t("Знайти своїх у вашому місті","Najděte své lidi ve vašem městě","Find people in your city"),12,false,muted);sub.setMaxLines(1);add(copy,sub,0,0);
        row.addView(copy,new LinearLayout.LayoutParams(0,-2,1));
        TextView action=text(t("Показати всіх →","Zobrazit všechny →","Show all →"),13,true,link);action.setGravity(Gravity.END|Gravity.CENTER_VERTICAL);row.addView(action,new LinearLayout.LayoutParams(-2,dp(44)));
        row.setFocusable(true);row.setContentDescription(t("Люди поруч. Показати всіх","Lidé poblíž. Zobrazit všechny","People nearby. Show all"));
        row.setOnClickListener(v->{if(host.alive())host.navigate(AppFinish252.route("/?p=nearby"));});
        return row;
    }

    private View siteStats(){
        LinearLayout box=column();
        for(int i=0;i<stats.size();i+=2){LinearLayout row=new LinearLayout(activity);row.setBaselineAligned(false);for(int j=0;j<2;j++){int k=i+j;if(k>=stats.size()){row.addView(new View(activity),new LinearLayout.LayoutParams(0,1,1));continue;}View c=statCard(stats.get(k),false);LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(0,-2,1);if(j>0)p.setMarginStart(dp(8));row.addView(c,p);}add(box,row,0,8);}
        return box;
    }

    private View plusStats(){
        HorizontalScrollView sc=new HorizontalScrollView(activity);sc.setHorizontalScrollBarEnabled(false);LinearLayout row=new LinearLayout(activity);row.setGravity(Gravity.CENTER_VERTICAL);row.setPadding(0,0,dp(2),0);
        for(JSONObject n:stats){View c=statCard(n,true);LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(dp(variant==PLUS?172:160),dp(62));p.setMarginEnd(dp(8));row.addView(c,p);}sc.addView(row,new HorizontalScrollView.LayoutParams(-2,-2));return sc;
    }

    private View statCard(JSONObject n,boolean compact){
        LinearLayout c=column();c.setGravity(Gravity.CENTER_VERTICAL);c.setPadding(dp(compact?12:13),dp(compact?9:10),dp(compact?12:13),dp(compact?9:10));c.setBackground(round(card,14,border));c.setElevation(dp(1));c.setMinimumHeight(dp(compact?58:64));
        JSONArray lines=array(n,"lines");String title=n.optString("title",n.optString("text","")),icon=lines.optString(0),label=lines.length()>1?lines.optString(1):"";
        if(title.matches("[0-9 .,+]+")){TextView value=text((icon.isEmpty()?"":icon+" ")+title,compact?16:17,true,text);add(c,value,0,1);if(!label.isEmpty()){TextView l=text(label,12,false,muted);l.setMaxLines(1);add(c,l,0,0);}}
        else{TextView value=text((icon.isEmpty()?"":icon+" ")+title,compact?14:15,true,text);value.setMaxLines(1);add(c,value,0,1);if(!label.isEmpty()&&!label.equals(title)){TextView l=text(label,11,false,muted);l.setMaxLines(1);add(c,l,0,0);}}
        String route=n.optString("route");c.setContentDescription(n.optString("text",title));c.setFocusable(true);c.setOnClickListener(v->{if(host.alive())host.navigate(AppFinish252.route(route));});return c;
    }

    private View section(JSONObject n){
        String type=n.optString("type"),title=sectionTitle(n),kind=kind(n,title);JSONArray children=array(n,"children");
        if(type.equals("details"))return challenge(n,title);
        LinearLayout shell=column();shell.setPadding(dp(variant==SITE?13:12),dp(variant==SITE?13:12),dp(variant==SITE?13:12),dp(variant==SITE?13:12));shell.setBackground(round(card,variant==SITE?16:18,border));shell.setElevation(dp(variant==SITE?1:2));shell.setTag("home257-section:"+kind);
        HeaderParts hp=headerParts(children,title);
        if(!hp.title.isEmpty())add(shell,sectionHeader(hp.title,hp.action),0,variant==SITE?8:10);
        JSONArray body=hp.body;
        View content;
        if(kind.equals("feed"))content=feedList(body);
        else if(kind.equals("topics"))content=topicList(body);
        else if(kind.equals("chat"))content=chatList(body);
        else if(variant==PLUS&&(kind.equals("jobs")||kind.equals("housing")))content=plusCards(body,kind);
        else if(kind.equals("jobs")||kind.equals("housing"))content=siteListings(body,kind);
        else{content=renderNodes(body.length()>0?body:new JSONArray().put(n),0);}
        add(shell,content,0,0);return shell;
    }

    private View challenge(JSONObject n,String title){
        LinearLayout shell=column();shell.setPadding(dp(12),dp(10),dp(12),dp(10));shell.setBackground(round(card,variant==SITE?14:18,border));shell.setElevation(dp(1));Button head=plainButton((variant==SITE?"▸ ":"▾ ")+(title.isEmpty()?t("📷 Фоточелендж тижня","📷 Foto výzva týdne","📷 Photo challenge of the week"):title));head.setGravity(Gravity.START|Gravity.CENTER_VERTICAL);head.setTextColor(text);head.setTypeface(Typeface.DEFAULT,Typeface.BOLD);shell.addView(head,new LinearLayout.LayoutParams(-1,dp(48)));
        View body=owner.batch20Nodes(array(n,"children"));siteify(body,variant==PLUS);body.setVisibility(variant==SITE?View.GONE:View.VISIBLE);add(shell,body,2,0);
        head.setOnClickListener(v->{boolean show=body.getVisibility()!=View.VISIBLE;body.setVisibility(show?View.VISIBLE:View.GONE);head.setText((show?"▾ ":"▸ ")+(title.isEmpty()?t("📷 Фоточелендж тижня","📷 Foto výzva týdne","📷 Photo challenge of the week"):title));});return shell;
    }

    private View sectionHeader(String title,JSONObject action){
        LinearLayout row=new LinearLayout(activity);row.setGravity(Gravity.CENTER_VERTICAL);TextView h=text(title,variant==SITE?16:18,true,text);row.addView(h,new LinearLayout.LayoutParams(0,-2,1));
        if(action!=null){TextView a=text(action.optString("title",action.optString("text","")),13,true,link);a.setGravity(Gravity.END|Gravity.CENTER_VERTICAL);a.setPadding(dp(8),dp(7),0,dp(7));a.setFocusable(true);a.setOnClickListener(v->{if(host.alive())host.navigate(AppFinish252.route(action.optString("route")));});row.addView(a,new LinearLayout.LayoutParams(-2,-2));}
        return row;
    }


    private View feedList(JSONArray body){
        LinearLayout out=column();
        for(int i=0;i<body.length();i++){
            JSONObject post=body.optJSONObject(i);if(post==null)continue;
            if(!"card".equals(post.optString("type"))){View v=owner.batch20Nodes(new JSONArray().put(post));siteify(v,variant==PLUS);add(out,v,0,8);continue;}
            add(out,feedPost(post),0,12);if(i<body.length()-1){View line=new View(activity);line.setBackgroundColor(border);out.addView(line,new LinearLayout.LayoutParams(-1,dp(1)));add(out,new Space(activity),0,12);}
        }
        return out;
    }

    private View feedPost(JSONObject post){
        JSONArray c=array(post,"children"),extraActions=new JSONArray();JSONObject avatarNode=null,nameNode=null,menuNode=null,mediaNode=null,likeForm=null,commentsNode=null;String meta="",body="";
        for(int i=0;i<c.length();i++){JSONObject x=c.optJSONObject(i);if(x==null)continue;String type=x.optString("type");
            if(type.equals("link")&&x.optBoolean("avatar")&&avatarNode==null){avatarNode=x;continue;}
            if(type.equals("link")&&avatarNode!=null&&nameNode==null&&!x.optString("text").equals("⋯")){nameNode=x;continue;}
            if(type.equals("text")&&meta.isEmpty()){meta=x.optString("text");continue;}
            if(type.equals("link")&&x.optString("text").equals("⋯")){menuNode=x;continue;}
            if(type.equals("text")){body+=(body.isEmpty()?"":"\n")+x.optString("text");continue;}
            if(type.equals("link")&&"cover".equals(x.optString("layout"))){mediaNode=x;continue;}
            if(type.equals("form")){likeForm=x;continue;}
            if(type.equals("action")){extraActions.put(x);continue;}
            if(type.equals("link")&&(x.optString("route").contains("comments=")||x.optString("text").toLowerCase(Locale.ROOT).matches(".*(коментар|comment|koment).*$")))commentsNode=x;
        }
        LinearLayout box=column();if(variant==PLUS){box.setPadding(dp(11),dp(10),dp(11),dp(10));box.setBackground(round(blend(card,bg,.45f),14,border));box.setElevation(dp(1));}
        LinearLayout author=new LinearLayout(activity);author.setGravity(Gravity.CENTER_VERTICAL);
        final JSONObject avNode=avatarNode,nmNode=nameNode,mnNode=menuNode,medNode=mediaNode,comNode=commentsNode,lfNode=likeForm;
        if(avNode!=null){FrameLayout av=new FrameLayout(activity);av.setBackground(round(blend(card,bg,.45f),40,border));av.setClipToOutline(true);View img=host.image(avNode.optString("image"));if(img instanceof ImageView)((ImageView)img).setScaleType(ImageView.ScaleType.CENTER_CROP);if(img!=null)av.addView(img,new FrameLayout.LayoutParams(-1,-1));av.setOnClickListener(v->{if(host.alive())host.navigate(AppFinish252.route(avNode.optString("route")));});LinearLayout.LayoutParams ap=new LinearLayout.LayoutParams(dp(42),dp(42));ap.setMarginEnd(dp(10));author.addView(av,ap);}
        LinearLayout who=column();if(nmNode!=null){TextView name=text(nmNode.optString("title",nmNode.optString("text")),14,true,text);name.setOnClickListener(v->{if(host.alive())host.navigate(AppFinish252.route(nmNode.optString("route")));});add(who,name,0,1);}if(!meta.isEmpty()){TextView m=text(meta,11,false,muted);m.setMaxLines(1);add(who,m,0,0);}author.addView(who,new LinearLayout.LayoutParams(0,-2,1));
        if(mnNode!=null){TextView dots=text("⋯",22,true,muted);dots.setGravity(Gravity.CENTER);dots.setOnClickListener(v->{if(host.alive())host.navigate(AppFinish252.route(mnNode.optString("route")));});author.addView(dots,new LinearLayout.LayoutParams(dp(42),dp(42)));}
        add(box,author,0,7);
        if(!body.isEmpty()){TextView b=text(body,variant==SITE?14:15,false,text);b.setLineSpacing(dp(2),1.05f);add(box,b,0,9);}
        if(medNode!=null&&!medNode.optString("image").isEmpty()){FrameLayout media=new FrameLayout(activity);media.setClipToOutline(true);media.setBackground(round(blend(card,bg,.45f),12,border));View image=host.image(medNode.optString("image"));if(image instanceof ImageView)((ImageView)image).setScaleType(ImageView.ScaleType.CENTER_CROP);if(image!=null)media.addView(image,new FrameLayout.LayoutParams(-1,-1));media.setOnClickListener(v->{if(host.alive())host.navigate(AppFinish252.route(medNode.optString("route")));});box.addView(media,new LinearLayout.LayoutParams(-1,dp(Math.min(230,activity.getResources().getDisplayMetrics().widthPixels/activity.getResources().getDisplayMetrics().density*.57f))));add(box,new Space(activity),0,6);}
        LinearLayout reactions=new LinearLayout(activity);reactions.setGravity(Gravity.CENTER_VERTICAL);
        if(lfNode!=null){View like=owner.batch20Nodes(new JSONArray().put(lfNode));siteify(like,false);compactAction(like);reactions.addView(like,new LinearLayout.LayoutParams(0,-2,1));}
        if(comNode!=null){TextView cm=text(comNode.optString("text"),13,false,muted);cm.setGravity(Gravity.END|Gravity.CENTER_VERTICAL);cm.setPadding(dp(8),dp(8),0,dp(8));cm.setOnClickListener(v->{if(host.alive())host.navigate(AppFinish252.route(comNode.optString("route")));});reactions.addView(cm,new LinearLayout.LayoutParams(-2,-2));}
        if(reactions.getChildCount()>0)add(box,reactions,2,0);
        if(extraActions.length()>0){View actions=owner.batch20Nodes(extraActions);siteify(actions,false);compactAction(actions);add(box,actions,0,0);}
        return box;
    }

    private View topicList(JSONArray body){
        LinearLayout out=column();for(int i=0;i<body.length();i++){JSONObject n=body.optJSONObject(i);if(n==null)continue;if(!"link".equals(n.optString("type"))){View v=owner.batch20Nodes(new JSONArray().put(n));siteify(v,false);add(out,v,0,4);continue;}LinearLayout row=column();row.setPadding(dp(2),dp(10),dp(2),dp(10));String title=n.optString("title",n.optString("text"));TextView t=text(title,14,true,text);t.setMaxLines(2);add(row,t,0,3);JSONArray ls=array(n,"lines");for(int k=0;k<ls.length();k++){String line=ls.optString(k);if(line.isEmpty()||line.equals("◌"))continue;TextView l=text(line,k==0?11:12,false,k==0?muted:text);l.setMaxLines(k==0?1:3);add(row,l,0,2);}row.setOnClickListener(v->{if(host.alive())host.navigate(AppFinish252.route(n.optString("route")));});out.addView(row,new LinearLayout.LayoutParams(-1,-2));if(i<body.length()-1){View div=new View(activity);div.setBackgroundColor(border);out.addView(div,new LinearLayout.LayoutParams(-1,dp(1)));}}return out;
    }

    private View chatList(JSONArray body){
        LinearLayout out=column();for(int i=0;i<body.length();i++){JSONObject n=body.optJSONObject(i);if(n==null)continue;if(!"link".equals(n.optString("type"))){View v=owner.batch20Nodes(new JSONArray().put(n));siteify(v,false);add(out,v,0,6);continue;}LinearLayout bubble=column();bubble.setPadding(dp(11),dp(9),dp(11),dp(9));bubble.setBackground(round(blend(card,bg,.45f),12,border));TextView t=text(n.optString("title"),13,true,text);add(bubble,t,0,2);JSONArray ls=array(n,"lines");for(int k=0;k<ls.length();k++){String line=ls.optString(k);if(line.isEmpty()||line.startsWith(n.optString("title")+" ·"))continue;TextView l=text(line,12,false,k==0?muted:text);l.setMaxLines(4);add(bubble,l,0,2);}bubble.setOnClickListener(v->{if(host.alive())host.navigate(AppFinish252.route(n.optString("route")));});add(out,bubble,0,8);}return out;
    }

    private View siteListings(JSONArray body,String kind){
        LinearLayout out=column();for(int i=0;i<body.length();i++){JSONObject n=body.optJSONObject(i);if(n==null)continue;if(!"link".equals(n.optString("type"))){View v=owner.batch20Nodes(new JSONArray().put(n));siteify(v,false);add(out,v,0,6);continue;}LinearLayout item=column();item.setPadding(dp(11),dp(10),dp(11),dp(10));item.setBackground(round(blend(card,bg,.45f),12,border));TextView t=text(n.optString("title"),14,true,text);t.setMaxLines(3);add(item,t,0,4);JSONArray ls=array(n,"lines");for(int k=0;k<ls.length();k++){String line=ls.optString(k);if(line.isEmpty())continue;int color=(kind.equals("housing")&&k==ls.length()-1)?(dark?0xff8fd2a4:0xff276f46):muted;TextView l=text(line,12,false,color);l.setMaxLines(2);add(item,l,0,2);}item.setOnClickListener(v->{if(host.alive())host.navigate(AppFinish252.route(n.optString("route")));});add(out,item,0,8);}return out;
    }

    private View plusCards(JSONArray body,String kind){
        List<JSONObject> items=new ArrayList<>();JSONArray extras=new JSONArray();
        for(int i=0;i<body.length();i++){JSONObject x=body.optJSONObject(i);if(x==null)continue;String route=x.optString("route");if("link".equals(x.optString("type"))&&(route.contains("p=job&id=")||route.contains("p=housing&id=")))items.add(x);else extras.put(x);}
        LinearLayout out=column();if(extras.length()>0)add(out,owner.batch20Nodes(extras),0,8);
        HorizontalScrollView sc=new HorizontalScrollView(activity);sc.setHorizontalScrollBarEnabled(false);LinearLayout row=new LinearLayout(activity);for(JSONObject x:items){View card=plusEntity(x,kind);LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(dp(258),-2);p.setMarginEnd(dp(10));row.addView(card,p);}sc.addView(row,new HorizontalScrollView.LayoutParams(-2,-2));add(out,sc,0,0);return out;
    }

    private View plusEntity(JSONObject n,String kind){
        LinearLayout c=column();c.setBackground(round(blend(card,bg,.45f),16,border));c.setClipToOutline(true);c.setMinimumHeight(dp(110));
        String image=n.optString("image","");if(!image.isEmpty()){View v=host.image(image);if(v instanceof ImageView)((ImageView)v).setScaleType(ImageView.ScaleType.CENTER_CROP);if(v!=null)c.addView(v,new LinearLayout.LayoutParams(-1,dp(118)));}
        LinearLayout copy=column();copy.setPadding(dp(12),dp(11),dp(12),dp(12));TextView t=text(n.optString("title",n.optString("text","")),15,true,text);t.setMaxLines(3);add(copy,t,0,6);JSONArray ls=array(n,"lines");for(int i=0;i<ls.length();i++){String s=ls.optString(i);if(s.isEmpty())continue;TextView l=text(s,12,false,i==ls.length()-1&&kind.equals("housing")?(dark?0xff8fd2a4:0xff276f46):muted);l.setMaxLines(2);add(copy,l,0,3);}c.addView(copy);c.setFocusable(true);c.setContentDescription(n.optString("title"));c.setOnClickListener(v->{if(host.alive())host.navigate(AppFinish252.route(n.optString("route")));});return c;
    }

    private void siteify(View v,boolean plus){
        if(v instanceof TextView){TextView t=(TextView)v;if(v instanceof Button){t.setTextColor(link);t.setAllCaps(false);v.setBackgroundColor(Color.TRANSPARENT);}else t.setTextColor(text);}
        if(v instanceof ViewGroup){ViewGroup g=(ViewGroup)v;for(int i=0;i<g.getChildCount();i++)siteify(g.getChildAt(i),plus);}
        if(v instanceof LinearLayout&&v.isClickable()){v.setBackground(round(plus?blend(card,bg,.45f):card,plus?14:10,border));v.setElevation(dp(plus?1:0));}
    }

    private HeaderParts headerParts(JSONArray children,String fallback){
        String title=fallback;JSONObject action=null;JSONArray body=new JSONArray();boolean headingConsumed=false;
        for(int i=0;i<children.length();i++){JSONObject x=children.optJSONObject(i);if(x==null)continue;String type=x.optString("type");
            if(!headingConsumed&&type.equals("heading")){title=x.optString("text",title);headingConsumed=true;continue;}
            if(action==null&&body.length()==0&&type.equals("link")&&isHeaderAction(x)){action=x;continue;}
            body.put(x);
        }
        return new HeaderParts(title,action,body);
    }

    private static boolean isHeaderAction(JSONObject n){String t=n.optString("title",n.optString("text",""));return t.contains("Усі")||t.contains("Спільнота")||t.contains("Приєднатися")||t.contains("All")||t.contains("Vše")||t.contains("→")||t.contains("↗");}
    private static String sectionTitle(JSONObject n){if("details".equals(n.optString("type")))return n.optString("text","");String own=n.optString("title",n.optString("text",""));JSONArray c=array(n,"children");for(int i=0;i<c.length();i++){JSONObject x=c.optJSONObject(i);if(x!=null&&"heading".equals(x.optString("type")))return x.optString("text",own);}return own;}
    private static String kind(JSONObject n,String title){title=title.toLowerCase(Locale.ROOT);String all=(title+" "+n.toString()).toLowerCase(Locale.ROOT);if(all.contains("promo_click")||all.contains("promotion")||all.contains("реклама"))return "promotion";if(all.contains("p=job&id=")||title.contains("ваканс")||title.contains("pracovní")||title.contains("jobs"))return "jobs";if(all.contains("p=housing&id=")||title.contains("житло")||title.contains("bydlení")||title.contains("housing"))return "housing";if("details".equals(n.optString("type"))||title.contains("фоточелендж")||title.contains("photo challenge"))return "challenge";if(title.contains("розмова в чаті")||title.contains("chat conversation")||title.contains("rozhovory v chatu"))return "chat";if(title.contains("дописи")||title.contains("posts")||title.contains("příspěv"))return "feed";if(title.contains("обговор")||title.contains("discuss"))return "topics";return "other";}
    private static int sectionOrder(JSONObject n){String k=kind(n,sectionTitle(n));if(k.equals("feed"))return 10;if(k.equals("topics"))return 20;if(k.equals("chat"))return 30;if(k.equals("jobs"))return 40;if(k.equals("housing"))return 50;if(k.equals("challenge"))return 60;if(k.equals("promotion"))return 90;return 80;}



    private int blend(int a,int b,float f){return Color.rgb(Math.round(Color.red(a)*(1-f)+Color.red(b)*f),Math.round(Color.green(a)*(1-f)+Color.green(b)*f),Math.round(Color.blue(a)*(1-f)+Color.blue(b)*f));}

    /** Collapse only a single-action form. Its original submit listener retains CSRF and values. */
    private void compactAction(View v){
        if(v==null)return;
        if(v instanceof ViewGroup){v.setMinimumHeight(0);v.setPadding(0,0,0,0);ViewGroup g=(ViewGroup)v;for(int i=0;i<g.getChildCount();i++){View c=g.getChildAt(i);ViewGroup.LayoutParams lp=c.getLayoutParams();if(lp!=null&&!(c instanceof ImageView)){lp.height=-2;if(lp instanceof ViewGroup.MarginLayoutParams)((ViewGroup.MarginLayoutParams)lp).setMargins(0,0,0,0);c.setLayoutParams(lp);}compactAction(c);}}
        if(v instanceof Button){Button b=(Button)v;b.setMinHeight(dp(44));b.setMinimumHeight(dp(44));b.setTextSize(13);b.setTextColor(muted);b.setPadding(dp(8),dp(4),dp(8),dp(4));}
    }

    /** Render the current projection without adding empty generic card containers around each item. */
    private View renderNodes(JSONArray nodes,int depth){
        LinearLayout out=column();if(depth>8)return out;
        for(int i=0;i<nodes.length();i++){
            JSONObject n=nodes.optJSONObject(i);if(n==null)continue;String type=n.optString("type");View v=null;
            if(type.equals("link"))v=preview(n);
            else if(type.equals("card")){v=renderNodes(array(n,"children"),depth+1);if(depth>0){v.setPadding(dp(10),dp(10),dp(10),dp(10));v.setBackground(round(blend(card,bg,.4f),12,border));}}
            else if(type.equals("text")||type.equals("heading")){String value=n.optString("text");if(!value.isEmpty())v=text(value,type.equals("heading")?16:13,type.equals("heading"),type.equals("heading")?text:muted);}
            else if(type.equals("image")){String url=n.optString("src",n.optString("url",n.optString("image")));if(!url.isEmpty()){FrameLayout frame=new FrameLayout(activity);frame.setBackground(round(bg,12,border));frame.setClipToOutline(true);View im=host.image(url);if(im instanceof ImageView)((ImageView)im).setScaleType(ImageView.ScaleType.CENTER_CROP);if(im!=null)frame.addView(im,new FrameLayout.LayoutParams(-1,dp(180)));v=frame;}}
            else{v=owner.batch20Nodes(new JSONArray().put(n));siteify(v,false);}
            if(v!=null)add(out,v,0,i==nodes.length()-1?0:8);
        }return out;
    }
    private View preview(JSONObject n){
        boolean avatar=n.optBoolean("avatar");String image=n.optString("image",n.optString("src",""));
        String title=n.optString("title",n.optString("text",""));JSONArray lines=array(n,"lines");
        LinearLayout row=new LinearLayout(activity);row.setGravity(Gravity.CENTER_VERTICAL);row.setPadding(dp(6),dp(7),dp(6),dp(7));row.setMinimumHeight(dp(48));
        if(!image.isEmpty()){
            FrameLayout frame=new FrameLayout(activity);frame.setBackground(round(bg,avatar?40:10,border));frame.setClipToOutline(true);View im=host.image(image);if(im instanceof ImageView)((ImageView)im).setScaleType(ImageView.ScaleType.CENTER_CROP);if(im!=null)frame.addView(im,new FrameLayout.LayoutParams(-1,-1));
            LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(dp(avatar?44:82),dp(avatar?44:72));p.setMarginEnd(dp(10));row.addView(frame,p);
        }
        LinearLayout copy=column();TextView name=text(title,14,true,text);name.setMaxLines(3);name.setEllipsize(android.text.TextUtils.TruncateAt.END);add(copy,name,0,lines.length()>0?4:0);
        for(int j=0;j<lines.length();j++){String line=lines.optString(j);if(line.isEmpty()||line.equals(title)||line.matches("[👥◌›]+"))continue;TextView detail=text(line,12,false,muted);detail.setMaxLines(3);detail.setEllipsize(android.text.TextUtils.TruncateAt.END);add(copy,detail,0,2);}
        row.addView(copy,new LinearLayout.LayoutParams(0,-2,1));String route=n.optString("route");if(!route.isEmpty()){row.setFocusable(true);row.setContentDescription(title);row.setOnClickListener(v->{if(host.alive())host.navigate(AppFinish252.route(route));});}
        return row;
    }

    private static String locale(JSONObject model){
        JSONObject state=model==null?null:model.optJSONObject("state");
        String x=state==null?"":state.optString("language","");
        if(x.isEmpty())x=model==null?"":model.optString("language","");
        x=x==null?"":x.toLowerCase(Locale.ROOT);
        return x.startsWith("cs")?"cs":x.startsWith("en")?"en":"uk";
    }
    private String t(String uk,String cs,String en){return language.equals("cs")?cs:language.equals("en")?en:uk;}

    private int dp(float v){return Math.round(activity.getResources().getDisplayMetrics().density*v);}
    private LinearLayout column(){LinearLayout v=new LinearLayout(activity);v.setOrientation(LinearLayout.VERTICAL);return v;}
    private TextView text(String s,float size,boolean bold,int color){TextView v=new TextView(activity);v.setText(s);v.setTextSize(size);v.setTextColor(color);v.setTypeface(Typeface.create("sans-serif",bold?Typeface.BOLD:Typeface.NORMAL));v.setLineSpacing(dp(2),1f);v.setIncludeFontPadding(false);return v;}
    private Button plainButton(String s){Button b=new Button(activity);b.setText(s);b.setAllCaps(false);b.setTextSize(15);b.setMinHeight(dp(48));b.setBackgroundColor(Color.TRANSPARENT);return b;}
    private GradientDrawable round(int color,float radius,int stroke){GradientDrawable g=new GradientDrawable();g.setColor(color);g.setCornerRadius(dp(radius));g.setStroke(dp(1),stroke);return g;}
    private View view(GradientDrawable d){View v=new View(activity);v.setBackground(d);return v;}
    private void add(LinearLayout p,View v,float top,float bottom){if(v==null)return;if(v.getParent() instanceof ViewGroup)((ViewGroup)v.getParent()).removeView(v);LinearLayout.LayoutParams q=new LinearLayout.LayoutParams(-1,"home257-hero".equals(v.getTag())?dp(156):-2);q.setMargins(0,dp(top),0,dp(bottom));p.addView(v,q);}
    private static JSONArray array(JSONObject j,String k){JSONArray a=j==null?null:j.optJSONArray(k);return a==null?new JSONArray():a;}
    private static final class HeaderParts{final String title;final JSONObject action;final JSONArray body;HeaderParts(String t,JSONObject a,JSONArray b){title=t;action=a;body=b;}}
}
