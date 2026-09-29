"""Mapa com ciclo de montagem seguro nas atualizações do Streamlit."""
from pathlib import Path
import streamlit as st
from mapa_base import TILES, ATRIBUICAO
ASSETS=Path(__file__).parent/'assets'
VENDOR=ASSETS/'vendor'/'leaflet'
def _componente(contexto='foto'):
 compacto=contexto=='foto'
 html=('<div class="location-toolbar"><div class="location-heading"><b>2</b><h2 class="location-title">Localização</h2></div><button type="button">◎ Usar minha localização</button></div><div class="location-map"></div><p role="status" aria-live="polite"></p>'
       if compacto else '<div class="location-map"></div><button type="button">◎ Usar minha localização</button><p role="status" aria-live="polite"></p>')
 return st.components.v2.component('aquasentinela_gps' if compacto else 'aquasentinela_gps_trecho',
  html=html,
  css=(VENDOR/'leaflet.css').read_text(encoding='utf-8')+"\n.location-map{height:300px;border-radius:15px;isolation:isolate;overflow:hidden}button{width:100%;padding:14px;margin-top:12px;border:1px solid #0062ed;border-radius:30px;color:#0056d9;background:white;font:bold 16px sans-serif;cursor:pointer}button:disabled{opacity:.5}p{font:13px/1.5 sans-serif;color:#344b60}.leaflet-control-attribution{font-size:10px;line-height:1.3;white-space:normal;max-width:100%}.aqua-marker{transition:transform .18s linear}.aqua-marker span{display:block;width:30px;height:30px;border-radius:50% 50% 50% 0;background:linear-gradient(135deg,#00cdc4,#007db6);transform:rotate(-45deg);box-shadow:0 3px 8px #00394c55}.aqua-marker span:after{content:'';position:absolute;width:11px;height:11px;background:white;border-radius:50%;top:9px;left:9px}\n" + ((ASSETS/'location-compact.css').read_text(encoding='utf-8') if compacto else ''),
  js=(VENDOR/'leaflet.js').read_text(encoding='utf-8')+'\n'+(ASSETS/'location.js').read_text(encoding='utf-8'))

def chaves(contexto):
 return ('foto_lat','foto_lon','foto_gps') if contexto=='foto' else (f'{contexto}-lat',f'{contexto}-lon',f'{contexto}-gps')

def aplicar_posicao(posicao, contexto='foto'):
 import math
 if not posicao or (contexto=='foto' and st.session_state.get('foto_salva_id')):
  return False
 lat,lon=float(posicao['latitude']),float(posicao['longitude'])
 if not math.isfinite(lat) or not math.isfinite(lon) or not (-90<=lat<=90 and -180<=lon<=180):
  raise ValueError('Localização inválida.')
 gps=posicao if posicao.get('source')=='gps' else None
 lat_key,lon_key,gps_key=chaves(contexto)
 mudou=(st.session_state.get(lat_key)!=lat or st.session_state.get(lon_key)!=lon or st.session_state.get(gps_key)!=gps)
 if mudou:
  st.session_state[lat_key]=lat;st.session_state[lon_key]=lon;st.session_state[gps_key]=gps
  if contexto=='foto':st.session_state.foto_confirmacao=False
 return mudou

def _posicao_alterada(contexto='foto'):
 try:
  aplicar_posicao((st.session_state.get(f'gps_{contexto}') or {}).get('position'), contexto)
 except (ValueError,TypeError,KeyError):
  pass  # Invalid events are also rejected by the page; never store their coordinates.

def obter_localizacao(contexto='foto'):
 from i18n import em_ingles
 lat_key,lon_key,gps_key=chaves(contexto)
 lat,lon=st.session_state.get(lat_key),st.session_state.get(lon_key)
 salvo=contexto=='foto' and bool(st.session_state.get('foto_salva_id'))
 if salvo and st.session_state.get('foto_posicao_salva'):
  lat=st.session_state.foto_posicao_salva['latitude'];lon=st.session_state.foto_posicao_salva['longitude']
 gps=st.session_state.get(gps_key) or {}
 accuracy=gps.get('accuracy') if gps.get('latitude')==lat and gps.get('longitude')==lon else None
 return _componente(contexto)(data={'tiles':TILES,'attribution':ATRIBUICAO,'latitude':lat,'longitude':lon,'accuracy':accuracy,'saved':salvo, 'language':'en' if em_ingles() else 'pt'},key=f'gps_{contexto}',on_position_change=lambda:_posicao_alterada(contexto)).position
