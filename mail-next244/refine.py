#!/usr/bin/env python3
from pathlib import Path
p=Path('mail-next244/MailActions244.java');s=p.read_text()
old='s.input.post(()->{if(!s.alive())return;s.input.requestFocus();InputMethodManager ime=(InputMethodManager)s.activity.getSystemService(Context.INPUT_METHOD_SERVICE);if(ime!=null)ime.showSoftInput(s.input,InputMethodManager.SHOW_IMPLICIT);});'
new='''s.input.postDelayed(new Runnable(){int attempts=8;public void run(){
     if(!s.alive()||!s.input.isAttachedToWindow())return;
     if(!s.input.hasWindowFocus()){if(attempts-->0)s.input.postDelayed(this,80);return;}
     s.input.requestFocus();InputMethodManager ime=(InputMethodManager)s.activity.getSystemService(Context.INPUT_METHOD_SERVICE);
     if(ime!=null)ime.showSoftInput(s.input,InputMethodManager.SHOW_IMPLICIT);
    }},160);'''
assert s.count(old)==1,'Reply implementation changed; inspect before rewriting'
s=s.replace(old,new)
old='window.setGravity(Gravity.BOTTOM);window.setSoftInputMode'
new='window.setGravity(Gravity.BOTTOM);window.setNavigationBarColor(s.theme.surface);int luminance=Color.red(s.theme.surface)+Color.green(s.theme.surface)+Color.blue(s.theme.surface);window.getDecorView().setSystemUiVisibility(luminance>384?View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR:0);window.setSoftInputMode'
assert s.count(old)==1;s=s.replace(old,new)
p.write_text(s)
