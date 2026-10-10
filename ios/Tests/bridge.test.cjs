const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../Svoyi/Resources/HostBridge.js'), 'utf8');
function make({origin='https://test.jkunis.eu', frame=false, active=true, nativeShare, complete=true} = {}) {
  const calls=[], timers=[], attributes=[];
  const window={webkit:{messageHandlers:{svoyiHost:{postMessage:async data=>{calls.push(data);return {completed:complete};}}}},
    addEventListener(){},matchMedia(){return {addEventListener(){}};}};
  window.top=frame?{}:window;
  const navigator={userActivation:{isActive:active}};
  if (nativeShare) navigator.share=nativeShare;
  const document={readyState:'complete',body:{},documentElement:{},addEventListener(){}};
  class MutationObserver { constructor(cb){this.cb=cb;} observe(element, options){attributes.push(options);} }
  const ctx=vm.createContext({window,navigator,document,location:{origin},MutationObserver,DOMException,
    getComputedStyle:()=>({backgroundColor:'rgb(22, 25, 31)'}),setTimeout:fn=>{timers.push(fn);return timers.length;}});
  vm.runInContext(source,ctx);
  return {window,navigator,document,calls,timers,attributes,ctx};
}
test('does not expose the host bridge on a foreign origin',()=>{const x=make({origin:'https://evil.test'});assert.equal(x.navigator.share,undefined);assert.equal(x.calls.length,0);});
test('does not expose the bridge inside an iframe',()=>{assert.equal(make({frame:true}).navigator.share,undefined);});
test('preserves an existing native Web Share function',()=>{const share=()=>{};assert.equal(make({nativeShare:share}).navigator.share,share);});
test('theme synchronization is attribute-only, does not replace site panels',async()=>{const x=make();x.timers.forEach(f=>f());await Promise.resolve();assert.equal(x.calls.length,1);assert.equal(x.calls[0].type,'theme');assert.deepEqual(Array.from(x.calls[0].rgb),[22,25,31]);assert.ok(x.attributes.every(o=>!o.childList));});
test('successful text/URL share returns only after native completion',async()=>{const x=make();await x.navigator.share({text:'Привіт',url:'https://test.jkunis.eu/'});assert.equal(x.calls[0].text,'Привіт');});
test('cancelled share rejects with AbortError',async()=>{const x=make({complete:false});await assert.rejects(x.navigator.share({text:'hello'}),e=>e.name==='AbortError');});
test('requires user activation',async()=>{const x=make({active:false});await assert.rejects(x.navigator.share({text:'hello'}),e=>e.name==='NotAllowedError');assert.equal(x.calls.length,0);});
test('file share is explicitly unsupported rather than falsely reported successful',async()=>{const x=make();assert.equal(x.navigator.canShare({files:[{}]}),false);await assert.rejects(x.navigator.share({files:[{}],text:'x'}),e=>e.name==='TypeError');});
test('caps bridge text size',async()=>{const x=make();await x.navigator.share({title:'a'.repeat(300),text:'b'.repeat(20000)});assert.equal(x.calls[0].title.length,200);assert.equal(x.calls[0].text.length,10000);});
test('idempotent bridge injection',()=>{const x=make();vm.runInContext(source,x.ctx);assert.equal(x.attributes.length,2);});
