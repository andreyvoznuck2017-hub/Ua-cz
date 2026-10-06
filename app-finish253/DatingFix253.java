package eu.svoyi.nativeapp;

import android.net.Uri;
import org.json.JSONObject;

/** Resolves a dating profile id from server data even when node.id is empty. */
public final class DatingFix253 {
    private DatingFix253(){}
    public static int profileId(JSONObject item){
        if(item==null)return 0;
        String[] keys={"id","userId","profileId","user_id","profile_id"};
        for(String k:keys){
            int n=item.optInt(k,0);
            if(n>0)return n;
            String s=item.optString(k,"");
            if(!s.isEmpty())try{n=Integer.parseInt(s);if(n>0)return n;}catch(NumberFormatException ignored){}
        }
        String route=item.optString("route","");
        if(route.isEmpty())route=item.optString("url","");
        try{
            String v=Uri.parse(route).getQueryParameter("view");
            if(v!=null&&!v.isEmpty()){
                int n=Integer.parseInt(v);
                if(n>0)return n;
            }
        }catch(RuntimeException ignored){}
        return 0;
    }
}
