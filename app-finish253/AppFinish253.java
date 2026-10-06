package eu.svoyi.nativeapp;

import android.app.Activity;
import android.net.Uri;
import org.json.JSONObject;
import java.util.Locale;

/** Route and post-render integration for the 2.5.3 social-core batch. */
public final class AppFinish253 {
    private AppFinish253(){}
    public static void remember(Activity a,JSONObject model){SocialUi253.apply(a,model);}
    public static String route(String original){
        if(original==null||original.trim().isEmpty())return "/?p=home";
        // DatingScreenPolicy validates profile links against the canonical site host.
        // Preserve absolute server profile links whose numeric view is the user id.
        try{
            Uri raw=Uri.parse(original.trim());
            String rawP=raw.getQueryParameter("p"),rawView=raw.getQueryParameter("view"),rawHost=raw.getHost();
            if("dating".equals(rawP)&&rawView!=null&&rawView.matches("[1-9][0-9]*")&&rawHost!=null&&rawHost.endsWith("jkunis.eu"))
                return original.trim();
        }catch(RuntimeException ignored){}
        String base=AppFinish252.route(original);
        if(base==null||base.isEmpty())return "/?p=home";
        try{
            Uri u=Uri.parse(base);String p=u.getQueryParameter("p"),view=u.getQueryParameter("view");
            if("people".equals(p)||"users".equals(p))return "/?p=nearby";
            if("dating".equals(p)&&view!=null&&u.getQueryParameter("tab")==null){
                String v=view.toLowerCase(Locale.ROOT);
                if("discover".equals(v)||"likes".equals(v)||"matches".equals(v))return "/?p=dating&tab="+v;
            }
            if("housing".equals(p)&&"favorites".equals(view)&&u.getQueryParameter("favorites")==null)return "/?p=housing&favorites=1";
            if("groups".equals(p)&&"mine".equals(view)&&u.getQueryParameter("mine")==null)return "/?p=groups&mine=1";
            return base;
        }catch(RuntimeException e){return base;}
    }
}
