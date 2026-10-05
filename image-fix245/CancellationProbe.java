package eu.svoyi.qa;
import android.graphics.Bitmap;
import android.graphics.drawable.BitmapDrawable;
import android.graphics.drawable.Drawable;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.*;
import java.lang.reflect.*;
import java.net.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;
import java.util.function.BooleanSupplier;
/** Test-only app_process harness loading NativeImageLoad from the APK under test.
 * Includes a deterministic ownership double AND real Android HTTP reads over loopback.
 * This class and its exception collector never enter the delivered APK.
 */
public final class CancellationProbe {
 static final List<Throwable> UNCAUGHT=Collections.synchronizedList(new ArrayList<Throwable>());
 static final JSONArray RESULTS=new JSONArray();
 static Class<?> type;
 static Object make()throws Exception{Constructor<?> c=type.getDeclaredConstructor(BooleanSupplier.class);c.setAccessible(true);return c.newInstance((BooleanSupplier)()->true);}
 static Object call(Object target,String name,Class<?>[] sig,Object...args)throws Exception{
  Method m=type.getDeclaredMethod(name,sig);m.setAccessible(true);
  try{return m.invoke(target,args);}catch(InvocationTargetException e){Throwable t=e.getCause();if(t instanceof Exception)throw (Exception)t;throw e;}
 }
 static void cancel(Object o)throws Exception{call(o,"cancel",new Class<?>[0]);}
 static void stream(Object o,InputStream s)throws Exception{call(o,"stream",new Class<?>[]{InputStream.class},s);}
 static void conn(Object o,HttpURLConnection c)throws Exception{call(o,"connection",new Class<?>[]{HttpURLConnection.class},c);}
 static void check(Object o)throws Exception{call(o,"check",new Class<?>[0]);}
 static void await(CountDownLatch l)throws Exception{if(!l.await(5,TimeUnit.SECONDS))throw new AssertionError("Timed out waiting for test synchronization");}
 static final class ControlledStream extends InputStream {
  final CountDownLatch reading=new CountDownLatch(1),release=new CountDownLatch(1),externalClose=new CountDownLatch(1);
  final AtomicInteger owners=new AtomicInteger(),foreign=new AtomicInteger();volatile Thread owner;volatile boolean active;
  public int read(){active=true;reading.countDown();boolean interrupted=false;for(;;){try{release.await();break;}catch(InterruptedException e){interrupted=true;}}active=false;if(interrupted)Thread.currentThread().interrupt();return -1;}
  public void close(){if(Thread.currentThread()!=owner){foreign.incrementAndGet();externalClose.countDown();if(active)throw new IllegalStateException("controlled concurrent read-close");}else owners.incrementAndGet();}
 }
 static final class ControlledConnection extends HttpURLConnection {
  final AtomicInteger foreign=new AtomicInteger(),owners=new AtomicInteger();volatile Thread owner;
  ControlledConnection()throws Exception{super(new URL("http://127.0.0.1/owned-only"));}
  public void connect(){}public boolean usingProxy(){return false;}
  public void disconnect(){if(Thread.currentThread()==owner)owners.incrementAndGet();else foreign.incrementAndGet();}
 }
 static JSONObject deterministic(int i)throws Exception{
  Object load=make();ControlledStream input=new ControlledStream();ControlledConnection http=new ControlledConnection();AtomicReference<Throwable> error=new AtomicReference<>();
  Thread worker=new Thread(()->{input.owner=Thread.currentThread();http.owner=Thread.currentThread();try{conn(load,http);stream(load,input);input.read();check(load);}catch(InterruptedIOException expected){}catch(Throwable e){error.set(e);}finally{input.close();http.disconnect();}},"qa-image-owner-"+i);
  int before=UNCAUGHT.size();worker.start();await(input.reading);long start=System.nanoTime();cancel(load);long millis=TimeUnit.NANOSECONDS.toMillis(System.nanoTime()-start);cancel(load);
  input.externalClose.await(100,TimeUnit.MILLISECONDS);input.release.countDown();worker.join(5000);Thread.sleep(10);
  JSONObject r=new JSONObject().put("case","blocked-read-cancel-"+i).put("foreignStreamCloses",input.foreign.get()).put("foreignDisconnects",http.foreign.get()).put("ownerCloses",input.owners.get()).put("workerFinished",!worker.isAlive()).put("cancellationCallMs",millis).put("uncaughtCleanupExceptions",UNCAUGHT.size()-before);
  r.put("passed",input.foreign.get()==0&&http.foreign.get()==0&&input.owners.get()==1&&!worker.isAlive()&&error.get()==null&&millis<500);RESULTS.put(r);return r;
 }
 static void rejectedRegistration()throws Exception{
  Object load=make();cancel(load);ControlledStream s=new ControlledStream();s.owner=Thread.currentThread();ControlledConnection c=new ControlledConnection();c.owner=Thread.currentThread();boolean inputRejected=false,connRejected=false;
  try{stream(load,s);}catch(InterruptedIOException expected){inputRejected=true;}finally{s.close();}
  try{conn(load,c);}catch(InterruptedIOException expected){connRejected=true;}finally{c.disconnect();}
  Thread.sleep(200);
  RESULTS.put(new JSONObject().put("case","cancelled-before-registration").put("streamRejected",inputRejected).put("connectionRejected",connRejected).put("foreignStreamCloses",s.foreign.get()).put("foreignDisconnects",c.foreign.get()).put("passed",inputRejected&&connRejected&&s.foreign.get()==0&&c.foreign.get()==0&&s.owners.get()==1&&c.owners.get()==1));
 }
 static void drawableOwnership()throws Exception{
  Bitmap claimed=Bitmap.createBitmap(2,2,Bitmap.Config.ARGB_8888);Object a=make();Drawable d=new BitmapDrawable(null,claimed);
  boolean decoded=(Boolean)call(a,"decoded",new Class<?>[]{Drawable.class},d);boolean claim=(Boolean)call(a,"claim",new Class<?>[]{Drawable.class},d);cancel(a);Thread.sleep(50);
  boolean kept=!claimed.isRecycled();claimed.recycle();
  Bitmap abandoned=Bitmap.createBitmap(2,2,Bitmap.Config.ARGB_8888);Object b=make();call(b,"decoded",new Class<?>[]{Drawable.class},new BitmapDrawable(null,abandoned));cancel(b);
  for(int i=0;i<30&&!abandoned.isRecycled();i++)Thread.sleep(10);
  RESULTS.put(new JSONObject().put("case","drawable-ownership").put("publishedDrawableKept",kept).put("abandonedDrawableDisposed",abandoned.isRecycled()).put("passed",decoded&&claim&&kept&&abandoned.isRecycled()));
 }
 static final class CountedHttpStream extends FilterInputStream {
  final Thread owner;final AtomicInteger foreign=new AtomicInteger(),owned=new AtomicInteger();
  CountedHttpStream(InputStream in){super(in);owner=Thread.currentThread();}
  public void close()throws IOException{if(Thread.currentThread()!=owner)foreign.incrementAndGet();else owned.incrementAndGet();super.close();}
 }
 static void realHttp(int i)throws Exception{
  ServerSocket server=new ServerSocket(0,1,InetAddress.getByName("127.0.0.1"));CountDownLatch blocked=new CountDownLatch(1);Object load=make();AtomicReference<CountedHttpStream> input=new AtomicReference<>();AtomicReference<String> failure=new AtomicReference<>();AtomicReference<String> platform=new AtomicReference<>();
  Thread producer=new Thread(()->{try(Socket socket=server.accept()){
   BufferedReader r=new BufferedReader(new InputStreamReader(socket.getInputStream()));String line;while((line=r.readLine())!=null&&!line.isEmpty()){}
   OutputStream out=socket.getOutputStream();out.write("HTTP/1.1 200 OK\r\nContent-Length: 4096\r\nConnection: close\r\n\r\nA".getBytes("US-ASCII"));out.flush();Thread.sleep(250);out.write(new byte[4095]);out.flush();
  }catch(Exception ignored){}finally{try{server.close();}catch(IOException ignored){}}},"qa-slow-http");producer.setDaemon(true);producer.start();
  Thread reader=new Thread(()->{HttpURLConnection http=null;CountedHttpStream s=null;try{
   http=(HttpURLConnection)new URL("http://127.0.0.1:"+server.getLocalPort()+"/image").openConnection();http.setConnectTimeout(2000);http.setReadTimeout(1000);conn(load,http);
   InputStream raw=http.getInputStream();platform.set(raw.getClass().getName());s=new CountedHttpStream(raw);input.set(s);stream(load,s);if(s.read()!=65)throw new IOException("Invalid fixture response");blocked.countDown();s.read(new byte[1024]);check(load);
  }catch(InterruptedIOException expected){}catch(IOException expectedAfterCancel){}catch(Throwable e){failure.set(e.getClass().getName());}finally{if(s!=null)try{s.close();}catch(Exception ignored){}if(http!=null)try{http.disconnect();}catch(RuntimeException ignored){}}},"qa-android-http-reader");
  int before=UNCAUGHT.size();reader.start();await(blocked);Thread.sleep(40);cancel(load);reader.join(5000);producer.join(2000);Thread.sleep(50);CountedHttpStream s=input.get();
  RESULTS.put(new JSONObject().put("case","android-http-slow-cancel-"+i).put("platformStream",platform.get()).put("foreignStreamCloses",s==null?-1:s.foreign.get()).put("ownerCloses",s==null?-1:s.owned.get()).put("uncaughtCleanupExceptions",UNCAUGHT.size()-before).put("workerFinished",!reader.isAlive()).put("passed",s!=null&&s.foreign.get()==0&&s.owned.get()==1&&!reader.isAlive()&&failure.get()==null));
 }
 public static void main(String[]args)throws Exception{
  boolean baseline=args.length>0&&args[0].equals("baseline");Thread.setDefaultUncaughtExceptionHandler((t,e)->UNCAUGHT.add(e));type=Class.forName("eu.svoyi.nativeapp.NativeImageLoad");
  try{
   for(int i=0;i<20;i++)deterministic(i);
   rejectedRegistration();drawableOwnership();for(int i=0;i<10;i++)realHttp(i);
   int failed=0;for(int i=0;i<RESULTS.length();i++)if(!RESULTS.getJSONObject(i).getBoolean("passed"))failed++;
   JSONArray errors=new JSONArray();for(Throwable t:UNCAUGHT){JSONObject e=new JSONObject().put("class",t.getClass().getName());JSONArray frames=new JSONArray();for(StackTraceElement f:t.getStackTrace())frames.put(f.getClassName()+"."+f.getMethodName());e.put("frames",frames);errors.put(e);}
   boolean expected=baseline?failed>0&&UNCAUGHT.size()>0:failed==0&&UNCAUGHT.isEmpty();
   System.out.println(new JSONObject().put("mode",baseline?"baseline-reproduction":"candidate-regression").put("androidApi",android.os.Build.VERSION.SDK_INT).put("testCount",RESULTS.length()).put("invariantFailures",failed).put("expectationMet",expected).put("tests",RESULTS).put("uncaught",errors).toString(2));
   System.exit(expected?0:2);
  }catch(Throwable e){e.printStackTrace();System.exit(3);}
 }
}
