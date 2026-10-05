package eu.svoyi.qa;
import android.app.*;
import android.content.*;
import android.graphics.Bitmap;
import android.os.Bundle;
import android.view.*;
import org.json.JSONObject;
import java.io.File;
import java.io.FileOutputStream;
import java.lang.reflect.Method;
/** Separate test-only APK; injects a malformed model into the exact release mail entrypoint. */
public final class RecoveryProbe extends Instrumentation {
 volatile Throwable failure;
 public void onCreate(Bundle b){super.onCreate(b);start();}
 public void onStart(){
  Bundle result=new Bundle();
  try{
   Intent i=new Intent().setComponent(new ComponentName("eu.svoyi.nativeapp","eu.svoyi.nativeapp.MainActivity")).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
   Activity a=startActivitySync(i);Thread.sleep(5000);
   runOnMainSync(()->{try{
    Method m=a.getClass().getDeclaredMethod("renderChat",JSONObject.class);m.setAccessible(true);m.invoke(a,(Object)null);
    View panel=a.getWindow().getDecorView().findViewWithTag("mail-recovery-panel");if(panel==null)throw new AssertionError("Recovery panel absent");
    Class<?> d=Class.forName("eu.svoyi.nativeapp.MailDiagnostics",true,a.getClassLoader());
    String text=(String)d.getMethod("report",Activity.class).invoke(null,a);
    if(!text.contains("NullPointerException")||text.contains("Unable to"))throw new AssertionError("Expected scrubbed captured exception");
    result.putBoolean("caught-malformed-model",true);result.putBoolean("recovery-panel-visible",true);result.putBoolean("local-sanitized-report",true);
   }catch(Throwable t){failure=t;}});
   if(failure!=null)throw new RuntimeException(failure);
   waitForIdleSync();Thread.sleep(800);
   File dest=new File(a.getExternalFilesDir(null),"qa-recovery.png");try(FileOutputStream out=new FileOutputStream(dest)){Bitmap b=getUiAutomation().takeScreenshot();if(b==null)throw new AssertionError("No recovery screenshot");b.compress(Bitmap.CompressFormat.PNG,100,out);b.recycle();}
   result.putString("screenshot",dest.getAbsolutePath());
   runOnMainSync(()->{try{a.getClass().getMethod("mailStabilityHome").invoke(a);}catch(Throwable t){failure=t;}});
   if(failure!=null)throw new RuntimeException(failure);
   result.putBoolean("home-action-dispatched",true);finish(Activity.RESULT_OK,result);
  }catch(Throwable t){result.putString("error",t.getClass().getName());result.putString("detail",String.valueOf(t));finish(Activity.RESULT_CANCELED,result);}
 }
}
