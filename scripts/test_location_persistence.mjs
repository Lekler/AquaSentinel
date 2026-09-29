import fs from 'node:fs';
import assert from 'node:assert/strict';
const source=fs.readFileSync(new URL('../assets/location.js',import.meta.url),'utf8');
const mount=(await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'))).default;
let created=0,destroyed=0,tiles=0,gpsCalls=0,zoom=11,pans=0;
const circles=[],events=[],handlers={};
const button={},status={},root={isConnected:true,replaceChildren(child){this.child=child}};
globalThis.document={documentElement:{},createElement:()=>({style:{}})};
globalThis.ResizeObserver=class{observe(){}disconnect(){}};
globalThis.MutationObserver=class{observe(){}disconnect(){}};
const map={setView(p,z){zoom=z;return this},panTo(){pans++},getBounds(){return {contains:()=>true}},
  on(n,f){handlers[n]=f},invalidateSize(){},removeLayer(){},remove(){destroyed++}};
globalThis.window={isSecureContext:true,L:{map(){created++;return map},tileLayer:(url)=>{assert.ok(url.includes('World_Street_Map'));return {addTo(){tiles++}}},divIcon:x=>x,
  circle:(point,options)=>({addTo(){circles.push(options);return this}}),
  marker:point=>({addTo(){return this},on(){},setLatLng(){},getLatLng:()=>point,dragging:{enable(){},disable(){}}})}};
Object.defineProperty(globalThis,'navigator',{value:{geolocation:{getCurrentPosition(ok){gpsCalls++;ok({coords:{latitude:-22.9,longitude:-43.1,accuracy:8},timestamp:123})}}},configurable:true});
const args={parentElement:{querySelector:s=>s==='.location-map'?root:s==='button'?button:status},
  data:{latitude:null,longitude:null,tiles:'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}'},setTriggerValue:(key,value)=>events.push({key,value})};
const first=mount(args);
assert.equal(gpsCalls,0);
handlers.click({latlng:{lat:-22,lng:-43}});
assert.equal(events[0].value.source,'map');assert.equal(circles.length,0,'No made-up precision circle');
first(); // cleanup before next render must retain the connected map
const second=mount({...args,data:{latitude:-22,longitude:-43}});
assert.equal(created,1);assert.equal(destroyed,0);assert.equal(tiles,1);assert.equal(zoom,11);
first();assert.equal(destroyed,0,'Delayed old cleanup must not destroy updated map');
button.onclick();assert.equal(gpsCalls,1);assert.equal(circles.at(-1).radius,8);assert.equal(pans,1);
const third=mount({...args,data:{latitude:-22.9,longitude:-43.1,accuracy:8}});
assert.equal(created,1);assert.equal(zoom,11);
const before=circles.length;
const saved=mount({...args,data:{latitude:-22.9,longitude:-43.1,accuracy:8,saved:true}});
assert.equal(circles.length,before);assert.equal(root.aquaLocation.circle,null);assert.equal(button.hidden,true);
const count=events.length;handlers.click({latlng:{lat:0,lng:0}});assert.equal(events.length,count);
mount({...args,data:{latitude:-22.9,longitude:-43.1,language:'en'}});
assert.ok(button.textContent.includes('Use my location'));
root.isConnected=false;root.aquaLocation.dispose();saved();second();third();
assert.equal(destroyed,1);assert.equal(button.onclick,null);
console.log('OK: one map instance and tile layer; viewport retained; GPS circle only with accuracy; saved marker locked; cleanup and English.');
