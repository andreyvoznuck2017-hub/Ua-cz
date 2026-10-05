from .qa import *

def walk(value):
 if isinstance(value,dict):
  yield value
  for k,v in value.items():
   if k!='state':yield from walk(v)
 elif isinstance(value,list):
  for v in value:yield from walk(v)

def run():
 a,b=start()
 def full_home():
  goto_home();must('current-greeting',has('Вітаємо,',contains=True));expected=['Свіжі вакансії','Нове житло','Про що говорять свої','Зараз у загальному чаті','Фоточелендж тижня']
  for i,title in enumerate(expected):must('home-section-'+str(i),seek(title,contains=True));capture('home-section-'+str(i))
  must('open-home-challenge',click('Фоточелендж тижня',contains=True));must('challenge-content-not-dropped',wait(lambda:has('Усі фото',contains=True) or has('Додати своє фото',contains=True)));capture('home-challenge-expanded')
 case(9,'complete-current-home-sections',full_home)
 def destinations():
  for caption,expected in [('Знайти роботу','Вакансії'),('🏠 Житло','Житло'),('💬 Спільнота','Спільнота'),('☕ Чат','чат'),('📅 Події','Події')]:
   goto_home();must('home-chip-'+caption,click(caption,contains=True));must('destination-'+caption,wait(lambda:not has('Вітаємо,',contains=True) and has(expected,contains=True),18));capture('destination-'+str(len(core['CHECKS'])))
  goto_home();must('show-all-jobs',seek('Усі вакансії',contains=True));click('Усі вакансії',contains=True);must('show-all-opens-jobs-not-home',wait(lambda:not has('Вітаємо,',contains=True) and has('Вакансії',contains=True)));capture('show-all-jobs')
 case(10,'home-cards-and-show-all-routes',destinations)
 def data_matches():
  model=api(a['s'],{'op':'screen','route':'/?p=home'});save('home-reference.json',model);links=[n for n in walk(model.get('nodes',[])) if n.get('type')=='link'];job=next(n for n in links if 'p=job&id=' in n.get('route',''));house=next(n for n in links if 'p=housing&id=' in n.get('route',''))
  for label,n in [('job',job),('housing',house)]:
   goto_home();title=n['title'];must(label+'-matches-server-card',seek(title,contains=True));capture('home-server-data-'+label);must(label+'-detail-click',click(title,contains=True));must(label+'-detail-content',wait(lambda:has(title,contains=True)));capture('home-detail-'+label)
 case(11,'home-collections-server-data-and-details',data_matches)
 def nearby():
  goto_home();must('drawer',click('Відкрити меню','content-desc'));must('people-menu',click('Усі користувачі'));must('people-screen',wait(lambda:has('Свої поруч',contains=True)));click('Свої поруч',contains=True);must('nearby-native-screen',wait(lambda:has('Поле radius:','content-desc',True)));radius=next(n for n in editors() if n.get('content-desc','').startswith('Поле radius:'));must('default-radius-ten',radius.get('text')=='10');must('no-location-explained',seek('Увімкніть геолокацію',contains=True));capture('nearby-without-location')
  # Searching by city must render real people or an explicit empty result, not a missing JS list.
  type_into('Praha',name='city');hide_keyboard();must('submit-nearby-filter',seek('Показати'));click('Показати');time.sleep(3);capture('nearby-city-result');must('nearby-city-result-rendered',has('людей не',contains=True) or has('Нікого',contains=True) or has('Написати',contains=True) or has('профіль',contains=True))
 case(12,'nearby-filters-and-no-location-state',nearby)
 def activities_bonus():
  goto_home();click('Відкрити меню','content-desc');must('people-menu-for-activities',click('Усі користувачі'));must('activities-entry',wait(lambda:has('Активності',contains=True)));click('Активності',contains=True);time.sleep(2);capture('activities-native');must('activity-creation-control',seek('Створити активність',contains=True))
  # Deliberately not fabricate an API mutation when the app has no control.
  must('activity-create-open',click('Створити активність',contains=True));must('activity-title-input',wait(lambda:has('Поле title:','content-desc',True)))
 case(13,'activities-create-and-home-engagement',activities_bonus)
 def restoration():
  goto_home();must('housing-anchor',seek('Нове житло',contains=True));labels=[(n.get('text',''),rect(n)[1]) for n in nodes() if '[ДЕМО]' in n.get('text','') and rect(n)[1]>350]
  must('home-reading-anchor',bool(labels));caption,y=labels[0];click(caption);time.sleep(2);adb('shell','input','keyevent','KEYCODE_BACK');must('returned-home-position',wait(lambda:has(caption)));after=find(caption)[0];must('home-anchor-offset',abs(rect(after)[1]-y)<80,str((y,rect(after)[1])));capture('home-return-position')
  adb('shell','svc','wifi','disable');adb('shell','svc','data','disable');time.sleep(1)
  try:
   must('home-keeps-rendered-data-offline',has(caption));capture('home-offline-visible')
  finally:adb('shell','svc','wifi','enable');adb('shell','svc','data','enable')
 case(14,'home-return-position-and-offline-content',restoration)

try:run()
except Exception as e:check('home-suite-startup',False,str(e));save('startup-error.txt',traceback.format_exc());capture('startup-failure')
finally:
 try:adb('shell','svc','wifi','enable');adb('shell','svc','data','enable')
 except Exception:pass
 finish()
raise SystemExit(0 if TASKS and all(t['status']=='passed' for t in TASKS) and all(c['passed'] for c in core['CHECKS']) else 1)
