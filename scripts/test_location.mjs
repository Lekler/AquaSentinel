// Teste do contrato de eventos do mapa, sem navegador ou GPS físico.
import fs from 'node:fs';
import assert from 'node:assert/strict';
const source=fs.readFileSync(new URL('../assets/location.js',import.meta.url),'utf8');
const mount=(await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'))).default;
let gpsCalls=0, removed=false;
const circles=[];
const events=[], handlers={};
const button={},status={},root={replaceChildren(child){this.child=child}};
globalThis.document={createElement:()=>({style:{}})};
const map={setView(){return this},on(name,fn){handlers[name]=fn},invalidateSize(){},removeLayer(){},remove(){removed=true}};
globalThis.window={isSecureContext:true,L:{map:()=>map,tileLayer:()=>({addTo(){}}),divIcon:x=>x,
circle:(point,options)=>({addTo(){circles.push(options);return this}}),
marker:point=>({addTo(){return this},on(){},setLatLng(){},getLatLng:()=>point})}};
Object.defineProperty(globalThis,'navigator',{value:{geolocation:{getCurrentPosition(ok){gpsCalls++;ok({coords:{latitude:-22.9,longitude:-43.1,accuracy:8},timestamp:123})}}},configurable:true});
globalThis.ResizeObserver=class{observe(){}disconnect(){}};
const clean=mount({parentElement:{querySelector:s=>s==='.location-map'?root:s==='button'?button:status},
data:{latitude:null,longitude:null},setTriggerValue:(key,value)=>events.push({key,value})});
assert.equal(gpsCalls,0,'GPS deve exigir clique');
handlers.click({latlng:{lat:-22,lng:-43}});
assert.equal(events[0].value.source,'map');
assert.equal(circles.at(-1).radius,25);
button.onclick();
assert.equal(gpsCalls,1);
assert.equal(events[1].value.accuracy,8);
assert.equal(events[1].value.source,'gps');
assert.equal(circles.at(-1).radius,8);
assert.equal(circles.at(-1).fillOpacity,.15);
clean();assert.equal(removed,true);assert.equal(button.onclick,null);
console.log('OK: seleção no mapa, GPS somente após clique, precisão e limpeza dos eventos.');

// Reproduce CCv2 rendering twice before disposing the first render.
let created=0, destroyed=0;
const containers=new Set();
window.L.map=container=>{
  assert.ok(!containers.has(container),'Map container is already initialized');
  containers.add(container);created++;
  return {...map,remove(){containers.delete(container);destroyed++}};
};
const args={parentElement:{querySelector:s=>s==='.location-map'?root:s==='button'?button:status},
  data:{latitude:-22.9,longitude:-43.1},setTriggerValue:(key,value)=>events.push({key,value})};
const first=mount(args);
const second=mount({...args,data:{latitude:-22.8,longitude:-43.2}});
assert.equal(created,2);assert.equal(destroyed,1);
first(); // A delayed cleanup must not remove the new map or its GPS handler.
assert.equal(destroyed,1);assert.equal(typeof button.onclick,'function');
second();second();
assert.equal(destroyed,2);assert.equal(containers.size,0);
console.log('OK: remontagem no mesmo DOM, descarte atrasado e limpeza idempotente.');
const before=circles.length;
const saved=mount({...args,data:{latitude:-22.8,longitude:-43.2,accuracy:20,saved:true}});
assert.equal(circles.length,before,'Registro salvo não deve desenhar círculo');
assert.equal(button.hidden,true);assert.equal(button.disabled,true);
saved();
const selected=mount({...args,data:{latitude:-22.8,longitude:-43.2,accuracy:42,saved:false}});
assert.equal(circles.at(-1).radius,42);assert.equal(button.hidden,false);
selected();
console.log('OK: círculo de precisão na seleção e apenas marcador depois de salvar.');
