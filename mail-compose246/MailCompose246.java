package eu.svoyi.nativeapp;

import android.content.Context;
import android.net.Uri;
import android.os.Build;
import android.view.View;
import android.view.ViewTreeObserver;
import android.view.Window;
import android.view.WindowInsets;
import android.view.WindowInsetsController;
import android.view.WindowManager;
import android.view.inputmethod.InputMethodManager;
import android.widget.EditText;
import java.util.WeakHashMap;

/** Main-thread lifecycle handoff. Does not change transport, permissions, or image loading. */
public final class MailCompose246 {
    private MailCompose246() {}
    private static final WeakHashMap<NativeMailScreen, Pending> pending = new WeakHashMap<>();
    private static final WeakHashMap<NativeMailScreen, Focus> focus = new WeakHashMap<>();
    private static final class Pending {
        final Uri uri; final String kind; final long duration;
        Pending(Uri u, String k, long d) { uri=u; kind=k; duration=d; }
    }

    /** onActivityResult runs before onResume. Do not start a cancellable copy while paused. */
    public static boolean defer(NativeMailScreen s, Uri uri, String kind, long duration) {
        if (!s.paused || uri == null) return false;
        if (!s.alive() || !s.canSend || s.sending || s.staging) return false;
        Pending old=pending.get(s);
        if (old != null) {
            if (!old.uri.equals(uri)) NativeMailCapture.delete(s.activity, uri);
            s.status("Попередній файл ще очікує повернення до переписки.", false);
            return true;
        }
        pending.put(s,new Pending(uri,kind,duration));
        return true;
    }

    /** Called after the existing resume() has restored paused=false and account state. */
    public static void resumed(NativeMailScreen s) {
        Pending p=pending.remove(s);
        if (p == null) return;
        if (!s.alive() || s.paused || !s.canSend || s.sending || s.staging) {
            NativeMailCapture.delete(s.activity,p.uri);
            return;
        }
        // Re-enter original staging path exactly once; all size/MIME/nonce checks are retained.
        s.stage(p.uri,p.kind,p.duration);
    }

    public static void closing(NativeMailScreen s) {
        Pending p=pending.remove(s);
        if (p != null) NativeMailCapture.delete(s.activity,p.uri);
        Focus f=focus.remove(s);
        if (f != null) f.cancel();
    }

    /** A reply action intentionally focuses input, but must wait for the dialog window to leave. */
    public static void replyFocused(NativeMailScreen s) {
        if (!s.alive() || s.paused || !s.canSend || s.input == null || s.replyPrefix.isEmpty()) return;
        Focus old=focus.remove(s);
        if (old != null) old.cancel();
        Focus task=new Focus(s);
        focus.put(s,task);
        task.start();
    }

    private static final class Focus implements Runnable, ViewTreeObserver.OnWindowFocusChangeListener, View.OnAttachStateChangeListener {
        final NativeMailScreen owner;
        final EditText editor;
        boolean done;
        Focus(NativeMailScreen s) { owner=s; editor=s.input; }
        final Runnable timeout=new Runnable(){ public void run(){ cancel(); } };
        void start() {
            editor.requestFocus();
            editor.addOnAttachStateChangeListener(this);
            editor.getViewTreeObserver().addOnWindowFocusChangeListener(this);
            editor.post(this);
            editor.postDelayed(timeout,2500);
        }
        public void onWindowFocusChanged(boolean hasFocus) { if (hasFocus && !done) editor.post(this); }
        public void onViewAttachedToWindow(View v) { if (!done) editor.post(this); }
        public void onViewDetachedFromWindow(View v) { cancel(); }
        public void run() {
            if (done) return;
            if (!owner.alive() || owner.paused || !owner.canSend || owner.input != editor || owner.replyPrefix.isEmpty()) { cancel(); return; }
            if (!editor.isAttachedToWindow() || !editor.hasWindowFocus()) return;
            editor.requestFocus();
            if (!editor.hasFocus()) return;
            Window w=owner.activity.getWindow();
            int mode=w.getAttributes().softInputMode;
            // Remove only the hidden-state request; retain existing resize/inset behavior.
            w.setSoftInputMode((mode & ~WindowManager.LayoutParams.SOFT_INPUT_MASK_STATE) | WindowManager.LayoutParams.SOFT_INPUT_STATE_UNCHANGED);
            InputMethodManager ime=(InputMethodManager)owner.activity.getSystemService(Context.INPUT_METHOD_SERVICE);
            if (ime != null) ime.showSoftInput(editor,InputMethodManager.SHOW_IMPLICIT);
            if (Build.VERSION.SDK_INT >= 30) Api30.show(editor);
            // One intentional request per reply. Do not reopen IME after the user dismisses it.
            cancel();
        }
        void cancel() {
            if (done) return;
            done=true;
            editor.removeCallbacks(this);editor.removeCallbacks(timeout);
            editor.removeOnAttachStateChangeListener(this);
            if (editor.getViewTreeObserver().isAlive()) editor.getViewTreeObserver().removeOnWindowFocusChangeListener(this);
            if (focus.get(owner)==this) focus.remove(owner);
        }
    }
    private static final class Api30 {
        static void show(View v) { WindowInsetsController c=v.getWindowInsetsController(); if(c!=null)c.show(WindowInsets.Type.ime()); }
    }
}
