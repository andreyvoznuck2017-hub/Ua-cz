from .qa import *

def walk(value):
 if isinstance(value,dict):
  yield value
  for k,v in value.items():
   if k!='state':yield from walk(v)
 elif isinstance(value,list):
  for v in value:yield from walk(v)

def own_model(a):return api(a['s'],{'op':'screen','route':'/?p=user&id='+str(a['id'])})

def choose_photo(filename,label='Обрати файл'):
 must('photo-file-control',seek(label,contains=True));must('open-image-picker',click(label,contains=True));time.sleep(2)
 if not has(filename,app=False):click('Show roots','content-desc',app=False);time.sleep(.6);click('Downloads',app=False);time.sleep(.7)
 must('fixture-in-system-picker',wait(lambda:has(filename,app=False)));click(filename,app=False);must('picker-photo-staged',wait(lambda:has(filename,contains=True),18))

def run():
 a,b=start()
 def profile_layout():
  goto_profile(True);must('profile-identity',has(a['name']));must('profile-edit-visible',has('Редагувати профіль',contains=True));capture('profile-header-larger-avatar')
  # Counter links must select lazy panes, not remain on a blank anchor.
  must('friends-counter',click('друзів',contains=True));must('friends-panel-loaded',wait(lambda:has('Пошук друзів',contains=True) or has('Поле friends_q:','content-desc',True)));capture('friends-counter-opens-lazy-pane')
  goto_profile(True);must('gifts-counter',click('подарунків',contains=True));must('gifts-panel-selected',wait(lambda:has('Подарунки',contains=True)));capture('gifts-counter-opens-lazy-pane')
  must('profile-tab-arrows',has('Наступні розділи анкети','content-desc'));click('Наступні розділи анкети','content-desc');capture('profile-lower-section-navigation')
 case(15,'profile-layout-and-lazy-section-anchors',profile_layout)
 def edit_main():
  goto_profile(True);must('edit-profile',click('Редагувати профіль',contains=True));must('edit-profile-name',wait(lambda:has('Поле name:','content-desc',True)));type_into('Batch20 bio saved from Android',name='bio');hide_keyboard();must('save-profile-control',seek('Зберегти основні дані'));click('Зберегти основні дані');must('bio-visible-on-peer-server',wait(lambda:'Batch20 bio saved from Android' in json.dumps(api(b['s'],{'op':'screen','route':'/?p=user&id='+str(a['id'])}),ensure_ascii=False),20));capture('profile-edit-saved')
  goto_profile(True);must('about-tab',seek('Про мене',contains=True));click('Про мене',contains=True);must('bio-in-native-profile',wait(lambda:has('Batch20 bio saved from Android',contains=True)));capture('profile-bio-after-save')
 case(16,'edit-profile-data-roundtrip',edit_main)
 def gallery():
  f=Path('/tmp/batch20-profile.png');im=Image.new('RGB',(480,320),(224,239,251));ImageDraw.Draw(im).text((85,140),'BATCH20 OWN PROFILE TEST',fill=(15,40,60));im.save(f);adb('push',str(f),'/sdcard/Download/'+f.name)
  goto_profile(True);must('photos-tab',seek('Фото',contains=True));click('Фото',contains=True);must('gallery-add-form',wait(lambda:has('Додати фото')));choose_photo(f.name);type_into('Batch20 gallery photo',name='caption');hide_keyboard();must('gallery-submit',seek('Додати фото'));click('Додати фото');must('gallery-photo-server',wait(lambda:'Batch20 gallery photo' in json.dumps(own_model(a),ensure_ascii=False),22));capture('gallery-photo-added');must('gallery-photo-open',seek('Batch20 gallery photo',contains=True));click('Batch20 gallery photo',contains=True);time.sleep(2);capture('gallery-photo-viewer')
 case(17,'gallery-file-selection-save-and-view',gallery)
 def wall_post():
  goto_profile(True);must('posts-tab',seek('Публікації',contains=True));click('Публікації',contains=True);must('publish-form',wait(lambda:has('Опублікувати')));type_into('Batch20 wall post from native app',name='body');hide_keyboard();must('publish-post',seek('Опублікувати'));click('Опублікувати');must('peer-sees-wall-post',wait(lambda:'Batch20 wall post from native app' in json.dumps(api(b['s'],{'op':'screen','route':'/?p=user&id='+str(a['id'])}),ensure_ascii=False),20));must('post-in-native-ui',seek('Batch20 wall post from native app',contains=True));capture('wall-publication-created')
  # Posting alone is not acceptance of comments, editing, deletion and likes.
  must('post-comment-controls',has('Коментувати',contains=True) or has('Коментарі',contains=True));capture('wall-comment-entry')
 case(18,'profile-wall-publish-and-comment-controls',wall_post)
 def friends_gifts():
  goto_profile(True);must('friends-counter-link',click('друзів',contains=True));must('friends-search-loaded',wait(lambda:has('Поле friends_q:','content-desc',True)));type_into('Nobody QA Batch20',name='friends_q');hide_keyboard();must('friends-search-submit',seek('Знайти'));click('Знайти');time.sleep(2);must('friends-search-preserves-owner',a['name'] in json.dumps(own_model(a),ensure_ascii=False));capture('friends-search')
  goto_profile(True);must('gifts-counter-link',click('подарунків',contains=True));must('gifts-not-services-store',wait(lambda:has('Подарунки',contains=True)));capture('gifts-owned-list')
  goto_profile();must('rewards-entry',seek('Досягнення',contains=True));click('Досягнення',contains=True);time.sleep(2);capture('rewards-projection');must('rewards-not-js-placeholder',not has('Завантаж',contains=True) and (has('Бонус',contains=True) or has('Рівень',contains=True)))
 case(19,'friends-gifts-and-achievements',friends_gifts)
 def privacy():
  goto_home();thread(a,b);must('peer-profile-link',click('Відкрити профіль','content-desc',True));must('peer-profile-rendered',wait(lambda:has(b['name'])));must('peer-not-own-editor',not has('Редагувати профіль',contains=True));capture('peer-profile-permissions')
  # Never submit a block silently: verify and cancel the actual native confirmation.
  must('block-action-visible',seek('Заблокувати',contains=True));click('Заблокувати',contains=True);must('block-confirmation-visible',wait(lambda:has('Додати користувача до чорного списку?',contains=True)));capture('block-confirmation');must('cancel-block',click('Скасувати'));must('cancel-keeps-mail-sendable',api(a['s'],{'op':'screen','route':'/?p=messages&with='+str(b['id'])}).get('chat',{}).get('canSend') is True)
  goto_profile();must('privacy-settings',seek('Приватність',contains=True));click('Приватність',contains=True);must('privacy-form',wait(lambda:has('Закритий профіль')));capture('privacy-settings-before');must('private-profile-toggle',click('Закритий профіль'));hide_keyboard();must('privacy-submit',seek('Зберегти'));click('Зберегти');time.sleep(2);peer=api(b['s'],{'op':'screen','route':'/?p=user&id='+str(a['id'])});save('private-profile-peer-result.json',peer);must('private-bio-hidden-from-peer','Batch20 bio saved from Android' not in json.dumps(peer,ensure_ascii=False));capture('privacy-saved')
 case(20,'own-peer-privacy-and-blacklist-confirmation',privacy)

try:run()
except Exception as e:check('profile-suite-startup',False,str(e));save('startup-error.txt',traceback.format_exc());capture('startup-failure')
finally:finish()
raise SystemExit(0 if TASKS and all(t['status']=='passed' for t in TASKS) and all(c['passed'] for c in core['CHECKS']) else 1)
