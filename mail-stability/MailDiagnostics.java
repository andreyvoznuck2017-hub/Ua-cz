package eu.svoyi.nativeapp;
import android.app.Activity;
import android.app.ActivityManager;
import android.app.AlertDialog;
import android.app.Application;
import android.app.ApplicationExitInfo;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageInfo;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.widget.Toast;
import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Set;
/** Local, bounded diagnostics. No exception messages, account data or network payloads. */
public final class MailDiagnostics {
 private static volatile boolean installed;
 private static volatile String screen="startup";
 private static Context app;
 private static final String STORE="svoyi-local-diagnostics-v1";
 private MailDiagnostics(){}
 public static synchronized void install(Activity activity){
  if(installed)return;
  app=activity.getApplicationContext();installed=true;
  final Thread.UncaughtExceptionHandler previous=Thread.getDefaultUncaughtExceptionHandler();
  Thread.setDefaultUncaughtExceptionHandler((thread,error)->{
   try{record(error,true);}finally{
    if(previous!=null)previous.uncaughtException(thread,error);
    else{android.os.Process.killProcess(android.os.Process.myPid());System.exit(10);}
   }
  });
  activity.getApplication().registerActivityLifecycleCallbacks(new Application.ActivityLifecycleCallbacks(){
   boolean offered;
   public void onActivityCreated(Activity a,Bundle b){}
   public void onActivityStarted(Activity a){}
   public void onActivityResumed(Activity a){
    if(offered||!a.getClass().getName().equals("eu.svoyi.nativeapp.MainActivity"))return;
    offered=true;
    SharedPreferences p=app.getSharedPreferences(STORE,Context.MODE_PRIVATE);
    if(!p.getBoolean("pendingCrash",false))return;
    new Handler(Looper.getMainLooper()).postDelayed(()->{
     if(a.isFinishing()||a.isDestroyed())return;
     p.edit().putBoolean("pendingCrash",false).apply();
     new AlertDialog.Builder(a).setTitle("Попередній запуск завершився зі збоєм")
      .setMessage("На телефоні збережено технічний звіт без текстів повідомлень, паролів і токенів. Він нікуди не надсилається автоматично.")
      .setPositiveButton("Переглянути звіт",(d,w)->show(a)).setNegativeButton("Пізніше",null).show();
    },1000);
   }
   public void onActivityPaused(Activity a){}
   public void onActivityStopped(Activity a){}
   public void onActivitySaveInstanceState(Activity a,Bundle b){}
   public void onActivityDestroyed(Activity a){}
  });
 }
 public static void mail(boolean thread){screen=thread?"mail-thread":"mail-inbox";}
 public static void clearScreen(){screen="other-screen";}
 static String safe(String value){if(value==null)return "";String s=value.replaceAll("[^a-zA-Z0-9._$ /-]","_");return s.substring(0,Math.min(140,s.length()));}
 public static String sanitized(Throwable error){
  StringBuilder b=new StringBuilder();Set<Throwable> seen=Collections.newSetFromMap(new IdentityHashMap<Throwable,Boolean>());
  for(int n=0;error!=null&&n<5&&seen.add(error);n++,error=error.getCause()){
   b.append(n==0?"error=":"cause=").append(safe(error.getClass().getName())).append('\n');
   StackTraceElement[] trace=error.getStackTrace();
   for(int i=0;i<Math.min(12,trace.length);i++){StackTraceElement e=trace[i];b.append("  ").append(safe(e.getClassName())).append('.').append(safe(e.getMethodName())).append(':').append(e.getLineNumber()).append('\n');}
  }
  return b.toString();
 }
 public static void record(Throwable error,boolean fatal){
  if(app==null)return;
  try{
   SharedPreferences p=app.getSharedPreferences(STORE,Context.MODE_PRIVATE);
   String item="time="+System.currentTimeMillis()+"\nlastMailPhase="+screen+"\nfatal="+fatal+"\n"+sanitized(error);
   String report=item+"\n"+p.getString("report","");if(report.length()>16000)report=report.substring(0,16000);
   p.edit().putString("report",report).putBoolean("pendingCrash",fatal||p.getBoolean("pendingCrash",false)).commit();
  }catch(RuntimeException ignored){}
 }
 static String header(Activity a){
  String version="unknown";
  try{PackageInfo p=a.getPackageManager().getPackageInfo(a.getPackageName(),0);version=p.versionName+" ("+p.versionCode+")";}catch(Exception ignored){}
  String text="SVOYI LOCAL DIAGNOSTIC\nversion="+version+"\npackage="+a.getPackageName()+"\nandroid="+Build.VERSION.RELEASE+" / API "+Build.VERSION.SDK_INT+"\ndevice="+safe(Build.MANUFACTURER)+" "+safe(Build.MODEL)+"\nlastMailPhase="+screen+"\n";
  if(Build.VERSION.SDK_INT>=30)text+=Api30.exits(a);return text;
 }
 public static String report(Activity a){String saved=a.getSharedPreferences(STORE,Context.MODE_PRIVATE).getString("report","");return header(a)+"\n"+(saved.isEmpty()?"No captured application exception.\n":saved)+"\nNo conversation text, login, password, cookie or token is collected.";}
 public static void show(Activity a){
  if(a.isFinishing()||a.isDestroyed())return;
  final String report=report(a);
  new AlertDialog.Builder(a).setTitle("Діагностика застосунку").setMessage(report)
   .setPositiveButton("Поділитися",(d,w)->{
    Intent i=new Intent(Intent.ACTION_SEND).setType("text/plain").putExtra(Intent.EXTRA_TEXT,report).putExtra(Intent.EXTRA_SUBJECT,"Svoyi — технічний звіт");
    try{a.startActivity(Intent.createChooser(i,"Надіслати технічний звіт"));}catch(RuntimeException e){Toast.makeText(a,"Не знайдено застосунку для надсилання. Скористайтеся копіюванням.",Toast.LENGTH_LONG).show();}
   }).setNeutralButton("Скопіювати",(d,w)->{
    ClipboardManager c=(ClipboardManager)a.getSystemService(Context.CLIPBOARD_SERVICE);if(c!=null)c.setPrimaryClip(ClipData.newPlainText("Svoyi diagnostic",report));Toast.makeText(a,"Технічний звіт скопійовано",Toast.LENGTH_SHORT).show();
   }).setNegativeButton("Закрити",null).show();
 }
 private static final class Api30{
  static String exits(Context c){
   try{ActivityManager am=(ActivityManager)c.getSystemService(Context.ACTIVITY_SERVICE);List<ApplicationExitInfo> items=am.getHistoricalProcessExitReasons(c.getPackageName(),0,3);StringBuilder b=new StringBuilder();for(ApplicationExitInfo e:items)b.append("exitReason=").append(e.getReason()).append(" status=").append(e.getStatus()).append(" time=").append(e.getTimestamp()).append('\n');return b.toString();}
   catch(RuntimeException e){return "exitHistory=unavailable\n";}
  }
 }
}
