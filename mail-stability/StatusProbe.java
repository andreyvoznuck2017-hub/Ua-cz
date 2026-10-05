package eu.svoyi.qa;
import org.json.JSONObject;
import java.lang.reflect.Method;
/** Runs on Android ART against the packaged application, not mocked JSONObject. */
public final class StatusProbe {
 static int tests;
 static void check(String name,boolean ok){tests++;System.out.println("CHECK "+name+" "+ok);if(!ok)throw new AssertionError(name);}
 static boolean policy(String name,JSONObject j)throws Exception {Class<?> c=Class.forName("eu.svoyi.nativeapp.NativeMailPolicy");Method m=c.getDeclaredMethod(name,JSONObject.class);m.setAccessible(true);return (Boolean)m.invoke(null,j);}
 public static void main(String[]args)throws Exception {
  boolean baseline=args.length>0&&args[0].equals("baseline");
  for(String key:new String[]{"deleted","delivered"}){
   check(key+"-absent",!policy(key,new JSONObject()));
   boolean actual=policy(key,new JSONObject().put(key+"_at",JSONObject.NULL));
   if(baseline)System.out.println("BASELINE_NULL_TIMESTAMP "+key+" "+actual);else check(key+"-json-null",!actual);
   check(key+"-explicit-false",!policy(key,new JSONObject().put(key,false).put(key+"_at","2026-10-05 11:00:00")));
   check(key+"-explicit-true",policy(key,new JSONObject().put(key,true)));
   check(key+"-timestamp",policy(key,new JSONObject().put(key+"_at","2026-10-05 11:00:00")));
  }
  if(!baseline){
   Class<?> n=Class.forName("eu.svoyi.nativeapp.MailNulls");Method edit=n.getMethod("edited",JSONObject.class);
   check("edited-null",!(Boolean)edit.invoke(null,new JSONObject().put("editedAt",JSONObject.NULL)));
   check("edited-literal-null",!(Boolean)edit.invoke(null,new JSONObject().put("editedAt","null")));
   check("edited-valid",(Boolean)edit.invoke(null,new JSONObject().put("edited_at","2026-10-05 11:00:00")));
   check("edited-explicit-false",!(Boolean)edit.invoke(null,new JSONObject().put("edited",false).put("editedAt","2026-10-05 11:00:00")));
   Class<?> d=Class.forName("eu.svoyi.nativeapp.MailDiagnostics");Method sanitizer=d.getMethod("sanitized",Throwable.class);
   Throwable error=new IllegalStateException("PRIVATE_PASSWORD_TOKEN",new IllegalArgumentException("PRIVATE_CHAT_CONTENT"));
   String safe=(String)sanitizer.invoke(null,error);check("report-no-secret-messages",!safe.contains("PRIVATE_")&&safe.contains("IllegalStateException")&&safe.contains("IllegalArgumentException"));check("report-bounded",safe.length()<12000);
  }
  System.out.println("ART_CHECKS_PASSED "+tests);
 }
}
