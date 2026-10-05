package eu.svoyi.nativeapp;
import org.json.JSONObject;
/** Server null timestamps are absence, not the literal string "null". */
public final class MailNulls {
    private MailNulls() {}
    public static boolean present(JSONObject data,String key) {
        if(data==null || data.isNull(key))return false;
        Object value=data.opt(key);
        if(!(value instanceof String))return false;
        String s=((String)value).trim();
        return !s.isEmpty() && !"null".equalsIgnoreCase(s);
    }
    private static boolean flag(JSONObject data,String key,boolean fallback) {
        if(data==null||data.isNull(key))return fallback;
        Object value=data.opt(key);
        if(value instanceof Boolean)return (Boolean)value;
        if("true".equalsIgnoreCase(String.valueOf(value)))return true;
        if("false".equalsIgnoreCase(String.valueOf(value)))return false;
        return fallback;
    }
    public static boolean deleted(JSONObject data){return flag(data,"deleted",present(data,"deleted_at"));}
    public static boolean delivered(JSONObject data){return flag(data,"delivered",present(data,"delivered_at"));}
    public static boolean edited(JSONObject data){return flag(data,"edited",present(data,"editedAt")||present(data,"edited_at"));}
}
