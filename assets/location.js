
export default function({parentElement, data, setTriggerValue}) {
  const root=parentElement.querySelector('.location-map'), button=parentElement.querySelector('button'), status=parentElement.querySelector('[role=status]');
  // CCv2 can render again on the same DOM before calling the previous cleanup.
  // Dispose explicitly and give Leaflet its own fresh container on every mount.
  root.aquaDispose?.();
  const canvas=document.createElement('div');
  canvas.style.height='100%';
  root.replaceChildren(canvas);
  let active=true, marker, accuracyCircle;
  const saved=data.saved===true;
  const valid=Number.isFinite(data.latitude)&&Number.isFinite(data.longitude);
  const map=window.L.map(canvas).setView(valid?[data.latitude,data.longitude]:[-22.91,-43.17],valid?16:11);
  window.L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'}).addTo(map);
  const icon=window.L.divIcon({className:'aqua-marker',html:'<span></span>',iconSize:[30,40],iconAnchor:[15,40]});
  function place(point) {
    if(marker) marker.setLatLng(point);
    else {marker=window.L.marker(point,{draggable:!saved,icon}).addTo(map);if(!saved)marker.on('dragend',()=>emit(marker.getLatLng()));}
  }
  function circle(point,accuracy) {
    if(accuracyCircle){map.removeLayer(accuracyCircle);accuracyCircle=null;}
    if(saved)return;
    const measured=Number.isFinite(accuracy)&&accuracy>0;
    accuracyCircle=window.L.circle(point,{radius:measured?accuracy:25,color:'#008fa7',weight:1,fillColor:'#00aabb',fillOpacity:.15,interactive:false}).addTo(map);
    status.textContent=measured?`Precisão estimada do GPS: ${Math.round(accuracy)} m. Confira o ponto.`:'Círculo de referência de 25 m; não representa precisão de GPS.';
  }
  function emit(point) {if(saved)return;place(point);circle(point,null);setTriggerValue('position',{latitude:point.lat,longitude:point.lng,source:'map'});}
  if(valid) place([data.latitude,data.longitude]);
  if(!saved)map.on('click',e=>emit(e.latlng));
  status.textContent=valid?'Confira o ponto. Clique no mapa ou arraste o marcador para ajustar.':'Use sua localização ou clique no mapa para marcar o local da foto.';
  if(valid&&!saved)circle([data.latitude,data.longitude],data.accuracy);
  button.disabled=saved;button.hidden=saved;
  if(saved)status.textContent='Localização salva. Apenas o marcador é exibido.';
  const locate=()=>{
    if(saved)return;
    if(!window.isSecureContext||!navigator.geolocation){status.textContent='O GPS precisa de HTTPS ou localhost. Você também pode marcar o ponto no mapa.';return;}
    button.disabled=true;status.textContent='Aguardando permissão e localização…';
    navigator.geolocation.getCurrentPosition(pos=>{
      if(!active)return;button.disabled=false;
      place([pos.coords.latitude,pos.coords.longitude]);circle([pos.coords.latitude,pos.coords.longitude],pos.coords.accuracy);
      setTriggerValue('position',{latitude:pos.coords.latitude,longitude:pos.coords.longitude,accuracy:pos.coords.accuracy,timestamp:pos.timestamp,source:'gps'});
    },err=>{if(!active)return;button.disabled=false;status.textContent=err.code===1?'Permissão negada. Marque o ponto no mapa.':'GPS indisponível. Tente novamente ou marque o ponto no mapa.';},
    {enableHighAccuracy:true,timeout:15000,maximumAge:0});
  };
  button.onclick=locate;
  const observer=new ResizeObserver(()=>map.invalidateSize());observer.observe(root);
  const dispose=()=>{
    if(!active)return;
    active=false;observer.disconnect();
    if(button.onclick===locate)button.onclick=null;
    map.remove();
    if(root.aquaDispose===dispose)delete root.aquaDispose;
  };
  root.aquaDispose=dispose;
  return dispose;
}
