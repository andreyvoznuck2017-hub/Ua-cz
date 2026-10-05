#!/usr/bin/env python3
"""Deterministic refinements to the native layout source before compilation."""
from pathlib import Path
p=Path('repair/NativeSiteUi.java');s=p.read_text()
def replace(old,new):
    global s
    assert old in s,old[:100]
    s=s.replace(old,new)
replace('v.setImageDrawable(NativeIcons.get(c,key,t.accent));','v.setImageDrawable(SiteGlyph.supports(key)?new SiteGlyph(key,t.accent):NativeIcons.get(c,key,t.accent));')
replace('FrameLayout hero=new FrameLayout(a);','FrameLayout hero=new CopyFrame(a,dp(a,180));')
replace('FrameLayout f=new FrameLayout(a);f.setMinimumHeight(dp(a,270));','FrameLayout f=new CopyFrame(a,dp(a,270));f.setMinimumHeight(dp(a,270));')
replace('filters.setContentDescription("Фільтри діалогів");','filters.setContentDescription("Фільтри діалогів");filters.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_YES);')
replace('edit.setContentDescription("Змінити фото й обкладинку");','edit.setContentDescription("Змінити фото й обкладинку");edit.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_YES);')
replace('String type=c.optString("type"),tx=plain(c.optString("text"));','String type=c.optString("type"),tx=plain(c.optString("text"));if(tx.contains("Завантажуємо ваш прогрес"))tx="Перегляньте свій прогрес і доступні бонуси у розділі досягнень.";')
helper=r'''
    /** Background images never decide height inside a vertically unbounded ScrollView. */
    static final class CopyFrame extends FrameLayout {
        final int minimum;
        CopyFrame(Context c,int min){super(c);minimum=min;}
        @Override protected void onMeasure(int ws,int hs){
            int w=MeasureSpec.getSize(ws);int last=getChildCount()-1;
            if(last<0){setMeasuredDimension(w,minimum);return;}
            View copy=getChildAt(last);copy.measure(MeasureSpec.makeMeasureSpec(w,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(0,MeasureSpec.UNSPECIFIED));
            int h=Math.max(minimum,copy.getMeasuredHeight());
            for(int i=0;i<last;i++)getChildAt(i).measure(MeasureSpec.makeMeasureSpec(w,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(h,MeasureSpec.EXACTLY));
            setMeasuredDimension(w,h);
        }
        @Override protected void onLayout(boolean changed,int l,int t,int r,int b){
            for(int i=0;i<getChildCount();i++){View v=getChildAt(i);int h=v.getMeasuredHeight();v.layout(0,i==getChildCount()-1?b-t-h:0,r-l,i==getChildCount()-1?b-t:h);}
        }
    }
    /** Draw at 24 logical units: no font-dependent symbols or unsupported icon names. */
    static final class SiteGlyph extends Drawable {
        final String key;final Paint pen=new Paint(3);
        SiteGlyph(String k,int color){key=k;pen.setColor(color);pen.setStyle(Paint.Style.STROKE);pen.setStrokeWidth(1.65f);pen.setStrokeCap(Paint.Cap.ROUND);pen.setStrokeJoin(Paint.Join.ROUND);}
        static boolean supports(String s){return s.equals("camera")||s.equals("smile")||s.equals("microphone")||s.equals("video")||s.equals("attachment")||s.equals("text");}
        void line(Canvas c,float x,float y,float a,float b){c.drawLine(x,y,a,b,pen);}
        public void draw(Canvas c){
            android.graphics.Rect r=getBounds();float scale=Math.min(r.width(),r.height())/24f;int state=c.save();c.translate(r.left+(r.width()-24*scale)/2,r.top+(r.height()-24*scale)/2);c.scale(scale,scale);
            if(key.equals("camera")){android.graphics.Path p=new android.graphics.Path();p.moveTo(3,7);p.lineTo(7,7);p.lineTo(9,4);p.lineTo(15,4);p.lineTo(17,7);p.lineTo(21,7);p.lineTo(21,20);p.lineTo(3,20);p.close();c.drawPath(p,pen);c.drawCircle(12,13,4,pen);}
            else if(key.equals("smile")){c.drawCircle(12,12,9,pen);c.drawPoint(9,9,pen);c.drawPoint(15,9,pen);c.drawArc(7,8,17,17,25,130,false,pen);}
            else if(key.equals("microphone")){c.drawRoundRect(9,3,15,15,3,3,pen);c.drawArc(6,8,18,18,0,180,false,pen);line(c,6,9,6,12);line(c,18,9,18,12);line(c,12,18,12,21);line(c,9,21,15,21);}
            else if(key.equals("video")){c.drawRoundRect(3,6,16,18,2,2,pen);android.graphics.Path p=new android.graphics.Path();p.moveTo(16,10);p.lineTo(21,7);p.lineTo(21,17);p.lineTo(16,14);c.drawPath(p,pen);}
            else if(key.equals("attachment")){android.graphics.Path p=new android.graphics.Path();p.moveTo(9,8);p.lineTo(9,17);p.cubicTo(9,21,16,21,16,17);p.lineTo(16,6);p.cubicTo(16,1,6,1,6,6);p.lineTo(6,17);p.cubicTo(6,25,20,25,20,17);p.lineTo(20,8);c.drawPath(p,pen);}
            else {line(c,3,19,8,5);line(c,8,5,13,19);line(c,5,14,11,14);c.drawOval(15,12,21,19,pen);line(c,21,12,21,19);}
            c.restoreToCount(state);
        }
        public void setAlpha(int a){pen.setAlpha(a);}public void setColorFilter(android.graphics.ColorFilter f){pen.setColorFilter(f);}public int getOpacity(){return android.graphics.PixelFormat.TRANSLUCENT;}
        @Override public int getIntrinsicWidth(){return 24;}@Override public int getIntrinsicHeight(){return 24;}
    }
'''
assert s.endswith('}\n');s=s[:-2]+helper+'}\n';p.write_text(s)
print('Native layout refinements applied')
