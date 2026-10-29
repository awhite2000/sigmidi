// Run the real embedded editor with a small DOM substitute; no network or browser dependency.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
class Element {
  constructor(tag) { this.tagName = tag; this.children = []; this.textContent = ''; }
  append(child) { this.children.push(child); }
  replaceChildren() { this.children = []; }
  addEventListener() {}
  querySelectorAll(selector) {
    return walk(this).filter(n => n.tagName === 'details' &&
      (selector !== 'details:not(.messageEditor)' || n.className !== 'messageEditor'));
  }
}
function walk(node) { return node.children.flatMap(child => [child, ...walk(child)]); }
const ids = new Map();
const context = vm.createContext({
  document: {getElementById(id) { if (!ids.has(id)) ids.set(id, new Element('div')); return ids.get(id); },
             createElement(tag) { return new Element(tag); }},
  sessionStorage: {getItem() { return ''; }}, setInterval() {}, window: {addEventListener() {}},
});
const script = fs.readFileSync('web/index.html', 'utf8').split('<script>')[1].split('</script>')[0];
vm.runInContext(script, context);
const sample = {version:4, ladderLayout:0, switchCount:10, debounceMs:10, pcOffset:0, windowMv:20, enclosureVariant:0,
  leds:{enabled:false,brightness:64,colorOrder:0,protocol:0},
  ladder:[2200,287,508,683,825,943,1042,1127,1200,1264,1320], pedals:[],
  switches:Array.from({length:10}, (_, i)=>({name:`Switch ${i+1}`,press:[],release:[],led:i+1}))};
sample.switches[9].press.push({type:1,number:24,channel:2,value:0,delayMs:5});
vm.runInContext(`config=${JSON.stringify(sample)}`, context);
for (let count=6;count<=10;++count) {
  vm.runInContext(`config.switchCount=${count};tab='Switches';render()`, context);
  assert.equal(ids.get('content').children.length, count);
  assert.equal(ids.get('content').children[count-1].children[0].textContent, `${count} · Switch ${count}`);
  vm.runInContext("tab='Calibration';render()", context);
  const labels=walk(ids.get('content')).filter(n=>n.tagName==='label' && /^(Switch \d+|Idle) \(mV\)$/.test(n.textContent));
  assert.equal(labels.length,count+1);
  assert.equal(labels.at(-1).textContent,`Switch ${count} (mV)`);
}
vm.runInContext("tab='Settings';render()",context);
let countField=walk(ids.get('content')).find(n=>n.tagName==='select');
assert.deepEqual(countField.children.map(n=>Number(n.value)),[4,5,6,7,8,9,10]);
countField.value='6';countField.onchange();
assert.equal(vm.runInContext('config.switchCount',context),6);
assert.equal(vm.runInContext('config.switches[9].press[0].number',context),24);
assert.equal(vm.runInContext('config.ladder[10]',context),1320);
countField=walk(ids.get('content')).find(n=>n.tagName==='select');
countField.value='10';countField.onchange();
vm.runInContext("tab='Switches';render()",context);
assert.equal(ids.get('content').children.length,10);
assert.ok(walk(ids.get('content')).some(n=>n.tagName==='summary' && n.textContent==='PC24/2'));
let labels=walk(ids.get('content')).filter(n=>n.tagName==='label' && n.textContent==='LED assignment');
assert.equal(labels.length,10);
assert.deepEqual(labels[0].children[0].children.map(n=>Number(n.value)),Array.from({length:11},(_,i)=>i));
labels[0].children[0].value='6';labels[0].children[0].onchange();
assert.equal(vm.runInContext('config.switches[0].led',context),6);
vm.runInContext("tab='Settings';render()",context);
function fieldInput(name) { return walk(ids.get('content')).find(n=>n.tagName==='label' && n.textContent===name).children[0]; }
let orientation=fieldInput('Enclosure variant');
assert.deepEqual(orientation.children.map(n=>Number(n.value)),[0,1]);
orientation.value='1';orientation.onchange();
assert.equal(vm.runInContext('config.enclosureVariant',context),1);
assert.equal(vm.runInContext('JSON.parse(JSON.stringify(config)).enclosureVariant',context),1);
assert.equal(vm.runInContext('dirty',context),true);
assert.equal(vm.runInContext('config.switches[9].press[0].number',context),24);
orientation.value='0';orientation.onchange();
assert.equal(vm.runInContext('config.enclosureVariant',context),0);
let input=fieldInput('Enable LED chain');input.checked=true;input.onchange();
assert.equal(vm.runInContext('config.leds.enabled',context),true);
input=fieldInput('Brightness (0–255)');input.value='96';input.onchange();
assert.equal(vm.runInContext('config.leds.brightness',context),96);
input=fieldInput('Color order');assert.equal(input.children.length,6);input.value='4';input.onchange();
assert.equal(vm.runInContext('config.leds.colorOrder',context),4);
input=fieldInput('WS2811 timing');assert.equal(input.children.length,3);input.value='2';input.onchange();
assert.equal(vm.runInContext('config.leds.protocol',context),2);
assert.equal(vm.runInContext('config.switches[9].led',context),10);
console.log('Editor tests passed: legacy counts 6–10 and options 4–10, preserved mappings, LED assignments and chain settings');
// Modular views use logical row order while every edit targets permanent tap storage.
const tapLabels=['B','A','2','1','C','3','D','4','E','5'];
const expectedOrders={4:[1,2,3,4],6:[5,1,2,6,3,4],8:[7,5,1,2,8,6,3,4],10:[9,7,5,1,2,10,8,6,3,4]};
sample.ladderLayout=1;
sample.switches.forEach((s,i)=>s.name=`Tap ${i+1}`);
sample.switches[4].press=[{type:0,number:17,channel:1,value:5,delayMs:5}];
vm.runInContext(`config=${JSON.stringify(sample)}`,context);
for(const [count,order] of Object.entries(expectedOrders)){
 vm.runInContext(`config.switchCount=${count};tab='Switches';render()`,context);
 assert.deepEqual(ids.get('content').children.map(d=>d.children[0].textContent),order.map(tap=>`${tapLabels[tap-1]} · Tap ${tap}`));
 vm.runInContext("tab='Calibration';render()",context);
 const fields=walk(ids.get('content')).filter(n=>n.tagName==='label'&&/^(Switch [A-E1-5]|Idle) \(mV\)$/.test(n.textContent));
 assert.deepEqual(fields.map(n=>n.textContent),['Idle (mV)',...order.map(t=>`Switch ${tapLabels[t-1]} (mV)`)]);
 assert.deepEqual(fields.map(n=>Number(n.children[0].value)),[sample.ladder[0],...order.map(t=>sample.ladder[t])]);
}
vm.runInContext("config.switchCount=6;tab='Switches';render()",context);
let nameInput=walk(ids.get('content').children[0]).find(n=>n.tagName==='label'&&n.textContent==='Switch name').children[0];
nameInput.value='Extension upper';nameInput.onchange();
assert.equal(vm.runInContext('config.switches[4].name',context),'Extension upper');
assert.equal(vm.runInContext('config.switches[0].name',context),'Tap 1');
vm.runInContext("tab='Calibration';render()",context);
const firstCalibration=walk(ids.get('content')).find(n=>n.tagName==='label'&&n.textContent==='Switch C (mV)').children[0];
firstCalibration.value='949';firstCalibration.onchange();
assert.equal(vm.runInContext('config.ladder[5]',context),949);
assert.equal(vm.runInContext('config.ladder[1]',context),287);
vm.runInContext("tab='Settings';render()",context);
assert.deepEqual(fieldInput('Number of footswitches').children.map(n=>Number(n.value)),[4,6,8,10]);
fieldInput('Number of footswitches').value='4';fieldInput('Number of footswitches').onchange();
assert.equal(vm.runInContext('config.switches[4].name',context),'Extension upper');
assert.equal(vm.runInContext('config.ladder[5]',context),949);
fieldInput('Number of footswitches').value='6';fieldInput('Number of footswitches').onchange();
vm.runInContext("tab='Switches';render();requests=[];api=async(path,data)=>{requests.push({path,data});return {revision:2}}",context);
const testButton=walk(ids.get('content').children[0]).find(n=>n.tagName==='button'&&n.textContent==='Test press');
(async()=>{
 await testButton.onclick();
 assert.equal(vm.runInContext('requests[1].data.switch',context),4);
 assert.equal(vm.runInContext('requests[1].data.edge',context),'press');
 console.log('Modular editor tests passed: 4/6/8/10 row order, physical message/LED/calibration storage, inactive data retention and mapped MIDI Test');
 const mirroredOrders={4:[2,1,4,3],6:[2,1,5,4,3,6],8:[2,1,5,7,4,3,6,8],10:[2,1,5,7,9,4,3,6,8,10]};
 vm.runInContext("config.switches.forEach((s,i)=>s.led=10-i)",context);
 for(const [count,order] of Object.entries(mirroredOrders)){
  const before=vm.runInContext('JSON.stringify([config.switches,config.ladder,config.pedals,config.leds])',context);
  vm.runInContext(`config.switchCount=${count};tab='Settings';render()`,context);
  const selector=fieldInput('Enclosure variant');selector.value='1';selector.onchange();
  assert.equal(vm.runInContext('config.enclosureVariant',context),1);
  assert.ok(!walk(ids.get('content')).some(n=>n.tagName==='label' && ['Display orientation','Mirrored switch layout'].includes(n.textContent)));
  vm.runInContext("tab='Switches';render()",context);
  assert.deepEqual(ids.get('content').children.map(d=>d.children[0].textContent),order.map(tap=>`${tapLabels[tap-1]} · ${vm.runInContext(`config.switches[${tap-1}].name`,context)}`));
  vm.runInContext("tab='Calibration';render()",context);
  const fields=walk(ids.get('content')).filter(n=>n.tagName==='label'&&/^(Switch [A-E1-5]|Idle) \(mV\)$/.test(n.textContent));
  assert.deepEqual(fields.map(n=>n.textContent),['Idle (mV)',...order.map(t=>`Switch ${tapLabels[t-1]} (mV)`)]);
  assert.deepEqual(fields.map(n=>Number(n.children[0].value)),[0,...order].map(t=>vm.runInContext(`config.ladder[${t}]`,context)));
  vm.runInContext("tab='Settings';render()",context);
  fieldInput('Enclosure variant').value='0';fieldInput('Enclosure variant').onchange();
  assert.equal(vm.runInContext('JSON.stringify([config.switches,config.ladder,config.pedals,config.leds])',context),before);
  vm.runInContext("tab='Switches';render()",context);
  assert.deepEqual(ids.get('content').children.map(d=>d.children[0].textContent),expectedOrders[count].map(tap=>`${tapLabels[tap-1]} · ${vm.runInContext(`config.switches[${tap-1}].name`,context)}`));
 }
 // In the Left enclosure the first card is A/T2, including both MIDI Test actions.
 vm.runInContext("config.enclosureVariant=1;config.switchCount=6;config.switches[1].press=[{type:0,channel:2,number:22,value:127,delayMs:5}];tab='Switches';render()",context);
 const card=ids.get('content').children[0];
 const cardInput=name=>walk(card).find(n=>n.tagName==='label'&&n.textContent===name).children[0];
 cardInput('Switch name').value='Left A';cardInput('Switch name').onchange();
 cardInput('LED assignment').value='3';cardInput('LED assignment').onchange();
 cardInput('Controller').value='29';cardInput('Controller').onchange();
 assert.equal(vm.runInContext('config.switches[1].name',context),'Left A');
 assert.equal(vm.runInContext('config.switches[1].led',context),3);
 assert.equal(vm.runInContext('config.switches[1].press[0].number',context),29);
 assert.equal(vm.runInContext('config.switches[0].name',context),'Tap 1');
 for(const edge of ['press','release']){
  vm.runInContext('requests=[]',context);
  await walk(card).find(n=>n.tagName==='button'&&n.textContent===`Test ${edge}`).onclick();
  assert.equal(vm.runInContext('requests[1].data.switch',context),1);
  assert.equal(vm.runInContext('requests[1].data.edge',context),edge);
 }
 vm.runInContext("tab='Calibration';render()",context);
 const calibration=fieldInput('Switch A (mV)');calibration.value='511';calibration.onchange();
 assert.equal(vm.runInContext('config.ladder[2]',context),511);
 assert.equal(vm.runInContext('config.ladder[1]',context),287);
 console.log('Left/Right editor tests passed: unified selector, both row orders for 4/6/8/10, fixed labels and inactive data, mapped name/message/LED/calibration edits and press/release MIDI Test');
 // Rounding is presentation-only until an explicit edit, including new captures.
 const measured=[2200.25,286.95654,507.69232,682.75861,825.125,942.85712,1042.10535,1126.82922,1200.375,1263.82971,1320.125];
 vm.runInContext(`config.ladder=${JSON.stringify(measured)};config.windowMv=20.4;config.pedals=[{enabled:true,resistor:true,invert:false,logarithmic:false,maxOhms:9999.5,heel:123.4,toe:3000.6,curve:9.3,channel:1,cc:11,outMin:0,outMax:127}]`,context);
 for(const variant of [0,1]){
  vm.runInContext(`config.enclosureVariant=${variant};dirty=false`,context);
  const precise=vm.runInContext('JSON.stringify(config)',context);
  vm.runInContext("tab='Calibration';render()",context);
  const order=variant?mirroredOrders[6]:expectedOrders[6];
  const values=walk(ids.get('content')).filter(n=>n.tagName==='label'&&/^(Switch [A-E1-5]|Idle) \(mV\)$/.test(n.textContent));
  assert.deepEqual(values.map(n=>Number(n.children[0].value)),[0,...order].map(t=>Math.round(measured[t])));
  assert.ok(values.every(n=>Number(n.children[0].step)===1));
  assert.equal(Number(fieldInput('Acceptance half-width (mV)').value),20);
  assert.equal(Number(fieldInput('Acceptance half-width (mV)').step),1);
  vm.runInContext("tab='Pedals';render()",context);
  assert.equal(Number(fieldInput('Heel signal (mV)').value),123);
  assert.equal(Number(fieldInput('Toe signal (mV)').value),3001);
  assert.equal(Number(fieldInput('Maximum resistance (Ω)').value),9999.5);
  assert.equal(Number(fieldInput('Log curve strength').value),9.3);
  assert.equal(vm.runInContext('JSON.stringify(config)',context),precise);
  assert.equal(vm.runInContext('dirty',context),false);
 }
 fieldInput('Heel signal (mV)').value='124.6';fieldInput('Heel signal (mV)').onchange();
 assert.equal(vm.runInContext('config.pedals[0].heel',context),125);
 assert.equal(Number(fieldInput('Heel signal (mV)').value),125);
 vm.runInContext("tab='Calibration';render()",context);
 fieldInput('Switch A (mV)').value='508.6';fieldInput('Switch A (mV)').onchange();
 assert.equal(vm.runInContext('config.ladder[2]',context),509);
 assert.equal(vm.runInContext('config.ladder[1]',context),measured[1]);
 const captureRow=ids.get('content').children.find(n=>walk(n).some(child=>child.tagName==='label'&&child.textContent==='Switch A (mV)'));
 vm.runInContext('api=async()=>({adcCalibrated:true,mv:[507.69232,100.25,200.75]})',context);
 await walk(captureRow).find(n=>n.tagName==='button'&&n.textContent==='Capture').onclick();
 assert.equal(vm.runInContext('config.ladder[2]',context),507.69232);
 assert.equal(Number(fieldInput('Switch A (mV)').value),508);
 assert.equal(vm.runInContext('config.ladder[1]',context),measured[1]);
 const storedBeforeSave=vm.runInContext('JSON.stringify(config)',context);
 vm.runInContext('api=async(path,data)=>{requests.push({path,data});return {revision:3}};requests=[]',context);
 await vm.runInContext("write('save')",context);
 assert.equal(vm.runInContext('JSON.stringify(requests[0].data.config)',context),storedBeforeSave);
 console.log('Calibration display tests passed: whole mV in both variants, integer editing, exact untouched/captured/saved values and unrounded non-voltage parameters');


 // Per-message PC counters keep identities when the list is edited.
 vm.runInContext(`config=${JSON.stringify(sample)};config.switchCount=4;config.enclosureVariant=0;config.switches[0].press=[{type:1,pcMode:0,channel:2,number:24,value:0,delayMs:5,counterId:0},{type:1,pcMode:0,channel:2,number:9,value:0,delayMs:5,counterId:0}];tab='Switches';render()`,context);
 function messageBox(i){return walk(ids.get('content').children[0]).filter(n=>n.tagName==='details'&&n.className==='messageEditor')[i]}
 function messageField(i,name){return walk(messageBox(i)).find(n=>n.tagName==='label'&&n.textContent===name)?.children[0]}
 assert.deepEqual(messageField(0,'PC mode').children.map(n=>n.textContent),['STATIC','INCR','DECR']);
 messageField(0,'PC mode').value='1';messageField(0,'PC mode').onchange();
 const id1=vm.runInContext('config.switches[0].press[0].counterId',context);
 assert.ok(id1>0); assert.equal(messageField(0,'Program'),undefined); assert.equal(messageField(0,'Value'),undefined);
 assert.ok(walk(messageBox(0)).some(n=>n.tagName==='summary'&&n.textContent==='PC+/2'));
 messageField(1,'PC mode').value='2';messageField(1,'PC mode').onchange();
 const id2=vm.runInContext('config.switches[0].press[1].counterId',context);
 assert.ok(id2>id1);
 walk(messageBox(1)).find(n=>n.tagName==='button'&&n.textContent==='↑').onclick();
 assert.equal(vm.runInContext('config.switches[0].press[1].counterId',context),id1);
 assert.equal(vm.runInContext('config.switches[0].press[0].counterId',context),id2);
 assert.ok(walk(messageBox(0)).some(n=>n.tagName==='summary'&&n.textContent==='PC-/2'));
 messageField(1,'PC mode').value='0';messageField(1,'PC mode').onchange();
 assert.equal(Number(messageField(1,'Program').value),24);
 assert.equal(vm.runInContext('config.switches[0].press[1].counterId',context),id1);
 walk(messageBox(0)).find(n=>n.tagName==='button'&&n.textContent==='Insert before').onclick();
 assert.equal(vm.runInContext('config.switches[0].press[1].counterId',context),id2);
 assert.equal(messageField(0,'PC mode'),undefined); // CC retains Controller/Value form.
 assert.ok(messageField(0,'Controller')&&messageField(0,'Value'));
 console.log('PC editor modes passed: STATIC/INCR/DECR, compact summaries, hidden static number/value, independent stable identities during reorder/insert');


})().catch(e=>{console.error(e);process.exitCode=1});

// Per-physical-switch toggle option survives variant changes and edits no MIDI/LED data.
vm.runInContext("tab='Switches';render()",context);
let toggleField=walk(ids.get('content').children[0]).find(n=>n.tagName==='label'&&n.textContent==='Toggle mode').children[0];
const toggleTap=vm.runInContext('switchOrder()[0]',context);
const oldActions=vm.runInContext(`JSON.stringify(config.switches[${toggleTap}].press)`,context);
toggleField.checked=true;toggleField.onchange();
assert.equal(vm.runInContext(`config.switches[${toggleTap}].toggle`,context),true);
assert.equal(vm.runInContext(`JSON.stringify(config.switches[${toggleTap}].press)`,context),oldActions);
assert.ok(walk(ids.get('content').children[0]).some(n=>n.tagName==='h2'&&n.textContent==='Toggle ON · first press'));
assert.ok(walk(ids.get('content').children[0]).some(n=>n.tagName==='h2'&&n.textContent==='Toggle OFF · next press'));
vm.runInContext('config.enclosureVariant=1-config.enclosureVariant;render()',context);
assert.equal(vm.runInContext(`config.switches[${toggleTap}].toggle`,context),true);
console.log('Toggle editor passed: per-switch setting, physical identity, action headings and unchanged MIDI lists');
