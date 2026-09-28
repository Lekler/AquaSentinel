export default function({parentElement, data, setTriggerValue}) {
  const root=parentElement.querySelector('.location-map');
  const button=parentElement.querySelector('button'), status=parentElement.querySelector('[role=status]');
  // Retain the Leaflet instance, viewport and tiles across Python updates.
  let state=root.aquaLocation;
  if (!state) {
    const canvas=document.createElement('div');canvas.style.height='100%';root.replaceChildren(canvas);
    const map=window.L.map(canvas).setView([-22.91,-43.17],11);
    window.L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',{
      maxZoom:19,attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
    }).addTo(map);
    state={map, marker:null, circle:null, active:true, generation:0, initialized:false};
    root.aquaLocation=state;
    state.text=(pt,en)=>state.data.language==='en'?en:pt;
    state.place=point=>{
      if(state.marker)state.marker.setLatLng(point);
      else {
        const icon=window.L.divIcon({className:'aqua-marker',html:'<span></span>',iconSize:[30,40],iconAnchor:[15,40]});
        state.marker=window.L.marker(point,{draggable:!state.data.saved,icon}).addTo(map);
        state.marker.on('dragend',()=>state.emit(state.marker.getLatLng()));
      }
      if(state.data.saved)state.marker.dragging?.disable();else state.marker.dragging?.enable();
    };
    state.precision=(point,accuracy)=>{
      if(state.circle){map.removeLayer(state.circle);state.circle=null;}
      if(!state.data.saved && Number.isFinite(accuracy) && accuracy>0){
        state.circle=window.L.circle(point,{radius:accuracy,color:'#008fa7',weight:1,fillColor:'#00aabb',fillOpacity:.15,interactive:false}).addTo(map);
        state.status.textContent=state.text(`Precisão aproximada do GPS: ${Math.round(accuracy)} m. O círculo não representa a extensão da ocorrência.`,`Approximate GPS accuracy: ${Math.round(accuracy)} m. The circle does not show the extent of the report.`);
      }
    };
    state.emit=point=>{
      if(state.data.saved)return;
      state.place(point);state.precision(point,null);state.initialized=true;
      state.status.textContent=state.text('Ponto ajustado. Confira a localização antes de enviar.','Point adjusted. Check the location before submitting.');
      state.send('position',{latitude:point.lat,longitude:point.lng,source:'map'});
    };
    map.on('click',e=>state.emit(e.latlng));
    state.locate=()=>{
      if(state.data.saved)return;
      if(!window.isSecureContext||!navigator.geolocation){state.status.textContent=state.text('GPS indisponível. Marque o ponto no mapa.','GPS unavailable. Mark the point on the map.');return;}
      state.button.disabled=true;state.status.textContent=state.text('Aguardando localização…','Waiting for location…');
      navigator.geolocation.getCurrentPosition(pos=>{
        if(!state.active || state.data.saved)return;
        state.button.disabled=false;
        const point=[pos.coords.latitude,pos.coords.longitude];
        state.place(point);state.precision(point,pos.coords.accuracy);
        map.panTo(point,{animate:true});state.initialized=true;
        state.send('position',{latitude:point[0],longitude:point[1],accuracy:pos.coords.accuracy,timestamp:pos.timestamp,source:'gps'});
      },err=>{
        if(!state.active)return;state.button.disabled=!!state.data.saved;
        state.status.textContent=err.code===1?state.text('Permissão negada. Marque o ponto no mapa.','Permission denied. Mark the point on the map.'):state.text('GPS indisponível. Tente novamente ou marque o ponto no mapa.','GPS unavailable. Try again or mark the point on the map.');
      },{enableHighAccuracy:true,timeout:15000,maximumAge:0});
    };
    state.resize=new ResizeObserver(()=>map.invalidateSize({pan:false}));state.resize.observe(root);
    state.dispose=()=>{
      if(!state.active)return;state.active=false;state.resize.disconnect();state.detach.disconnect();
      if(state.button.onclick===state.locate)state.button.onclick=null;
      map.remove();delete root.aquaLocation;
    };
    // Cleanup can precede a data rerender: only dispose on actual DOM removal.
    state.detach=new MutationObserver(()=>{if(!root.isConnected)state.dispose();});
    state.detach.observe(document.documentElement,{childList:true,subtree:true});
    state.detach.observe(parentElement,{childList:true,subtree:true});
  }
  state.data=data;state.send=setTriggerValue;state.button=button;state.status=status;
  const generation=++state.generation;
  button.textContent=state.text('◎ Usar minha localização','◎ Use my location');
  button.disabled=!!data.saved;button.hidden=!!data.saved;button.onclick=state.locate;
  status.textContent=state.text('Clique no mapa ou arraste o marcador para ajustar.','Click the map or drag the marker to adjust.');
  if(Number.isFinite(data.latitude)&&Number.isFinite(data.longitude)){
    const point=[data.latitude,data.longitude];
    state.place(point);state.precision(point,data.accuracy);
    if(!state.initialized){state.map.setView(point,16);state.initialized=true;}
    else if(!state.map.getBounds().contains(point))state.map.panTo(point,{animate:true});
  }
  if(data.saved)status.textContent=state.text('Localização salva.','Location saved.');
  return ()=>{if(generation===state.generation&&!root.isConnected)state.dispose();};
}
