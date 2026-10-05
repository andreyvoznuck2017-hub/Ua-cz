from .qa import *

def received_media(b,a,kind,before):return [m for m in messages(b,a) if m.get('kind')==kind and m.get('id',0)>before]
def inspect_media(b,a,kind,before):
 must(kind+'-peer-receipt',wait(lambda:bool(received_media(b,a,kind,before)),35));m=received_media(b,a,kind,before)[-1];att=m.get('attachment');url=att.get('url','') if isinstance(att,dict) else str(att or '');url=urljoin(ORIGIN,url);must(kind+'-same-origin',urlsplit(url).netloc==urlsplit(ORIGIN).netloc);r=b['s'].get(url,timeout=30);must(kind+'-downloaded',r.ok and len(r.content)>100);p=OUT/(kind+'-captured-media.bin');p.write_bytes(r.content)
 proc=subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)],capture_output=True,text=True,timeout=20);must(kind+'-decodable-container',proc.returncode==0,proc.stderr[:300]);meta=json.loads(proc.stdout);save(kind+'-media-metadata.json',meta);duration=float(meta.get('format',{}).get('duration',0));must(kind+'-duration-real',duration>0.5 and duration<(310 if kind=='voice' else 70));must(kind+'-stream-kind',any(s.get('codec_type')==('audio' if kind=='voice' else 'video') for s in meta.get('streams',[])));return m

def run():
 a,b=start();thread(a,b)
 def voice():
  type_into('',clear=True);hide_keyboard();must('voice-toolbar-action',click('Голосове повідомлення','content-desc'));must('voice-recorder-visible',wait(lambda:has('Записати')));capture('voice-before-recording');must('voice-record',click('Записати'));time.sleep(3);must('voice-stop',click('Зупинити'));must('voice-preview-enabled',wait(lambda:has('Прослухати')));must('voice-duration-control',has('Позиція голосового запису','content-desc'));capture('voice-recorded')
  must('voice-preview',click('Прослухати'));time.sleep(1);capture('voice-preview-playing');must('voice-cancel-recording',click('Скасувати'));must('voice-cancel-returned',wait(lambda:has('Надіслати','content-desc',True)));must('cancelled-voice-not-sent',not any(m.get('kind')=='voice' for m in messages(b,a)))
  before=max((m['id'] for m in messages(b,a)),default=0);must('voice-reopen',click('Голосове повідомлення','content-desc'));must('voice-record-again-ready',wait(lambda:has('Записати')));click('Записати');time.sleep(3);click('Зупинити');must('voice-attach-enabled',wait(lambda:has('Додати до повідомлення')));click('Додати до повідомлення');must('voice-back-in-thread',wait(lambda:has('Надіслати','content-desc',True)));time.sleep(2);capture('voice-staged');must('voice-send',click('Надіслати','content-desc',True));m=inspect_media(b,a,'voice',before);capture('voice-received-and-sent')
 case(7,'voice-record-cancel-preview-send',voice)
 def video():
  thread(a,b);type_into('',clear=True);hide_keyboard();before=max((m['id'] for m in messages(b,a)),default=0);must('round-video-action',click('Кругле відео','content-desc'))
  def external_controls():return [n for n in nodes() if n.get('package','').startswith(('com.android.camera','com.google.android.GoogleCamera'))]
  must('system-camera-opened',wait(lambda:bool(external_controls()),25));capture('video-camera-open')
  switch=[n for n in external_controls() if re.search('switch|front|rear',n.get('content-desc',''),re.I) and n.get('clickable')=='true'];must('camera-switch-control',bool(switch));tap_node(switch[0]);time.sleep(1);capture('video-camera-switched')
  actions=[n for n in external_controls() if re.search('start|record|capture|shutter',n.get('content-desc',''),re.I) and n.get('clickable')=='true'];must('video-record-control',bool(actions));tap_node(actions[0]);time.sleep(4);capture('video-recording')
  stop=[n for n in external_controls() if re.search('stop|shutter',n.get('content-desc',''),re.I) and n.get('clickable')=='true'];must('video-stop-control',bool(stop));tap_node(stop[0]);time.sleep(1)
  done=[n for n in external_controls() if re.search('done|accept|review_done|use video',n.get('content-desc','')+' '+n.get('text','')+' '+n.get('resource-id',''),re.I) and n.get('clickable')=='true'];must('video-confirm-control',bool(done));tap_node(done[0]);must('video-returned-to-thread',wait(lambda:has('Надіслати','content-desc',True),25));time.sleep(2);capture('round-video-staged');must('round-video-send',click('Надіслати','content-desc',True));inspect_media(b,a,'round_video',before);capture('round-video-sent')
 case(8,'round-video-camera-switch-send',video)
 save('media-test-limits.json',{'recordedByActualAndroidComponents':True,'camera':'emulated scene','microphone':'emulator audio input','physicalMicrophoneQualityTested':False,'physicalFrontRearCamerasTested':False})
try:run()
except Exception as e:check('media-suite-startup',False,str(e));save('startup-error.txt',traceback.format_exc());capture('startup-failure')
finally:finish()
raise SystemExit(0 if TASKS and all(t['status']=='passed' for t in TASKS) and all(c['passed'] for c in core['CHECKS']) else 1)
