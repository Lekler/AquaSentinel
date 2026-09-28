"""Mapa com ciclo de montagem seguro nas atualizações do Streamlit."""
from pathlib import Path
import streamlit as st
from mapa_base import TILES, ATRIBUICAO
ASSETS=Path(__file__).parent/'assets'
VENDOR=ASSETS/'vendor'/'leaflet'
_GPS=st.components.v2.component('aquasentinela_gps',
 html='<div class="location-map"></div><button type="button">◎ Usar minha localização</button><p role="status" aria-live="polite"></p>',
 css=(VENDOR/'leaflet.css').read_text(encoding='utf-8')+"\n.location-map{height:300px;border-radius:15px;isolation:isolate;overflow:hidden}button{width:100%;padding:14px;margin-top:12px;border:1px solid #0062ed;border-radius:30px;color:#0056d9;background:white;font:bold 16px sans-serif;cursor:pointer}button:disabled{opacity:.5}p{font:13px/1.5 sans-serif;color:#344b60}.leaflet-control-attribution{font-size:10px;line-height:1.3;white-space:normal;max-width:100%}.aqua-marker{transition:transform .18s linear}.aqua-marker span{display:block;width:30px;height:30px;border-radius:50% 50% 50% 0;background:linear-gradient(135deg,#00cdc4,#007db6);transform:rotate(-45deg);box-shadow:0 3px 8px #00394c55}.aqua-marker span:after{content:'';position:absolute;width:11px;height:11px;background:white;border-radius:50%;top:9px;left:9px}\n",
 js=(VENDOR/'leaflet.js').read_text(encoding='utf-8')+'\n'+(ASSETS/'location.js').read_text(encoding='utf-8'))
def aplicar_posicao(posicao):
 import math
 if not posicao or st.session_state.get('foto_salva_id'):
  return False
 lat,lon=float(posicao['latitude']),float(posicao['longitude'])
 if not math.isfinite(lat) or not math.isfinite(lon) or not (-90<=lat<=90 and -180<=lon<=180):
  raise ValueError('Localização inválida.')
 gps=posicao if posicao.get('source')=='gps' else None
 mudou=(st.session_state.get('foto_lat')!=lat or st.session_state.get('foto_lon')!=lon or st.session_state.get('foto_gps')!=gps)
 if mudou:
  st.session_state.foto_lat=lat;st.session_state.foto_lon=lon;st.session_state.foto_gps=gps
  st.session_state.foto_confirmacao=False
 return mudou

def _posicao_alterada():
 try:
  aplicar_posicao((st.session_state.get('gps_foto') or {}).get('position'))
 except (ValueError,TypeError,KeyError):
  pass  # Invalid events are also rejected by the page; never store their coordinates.

def obter_localizacao():
 from i18n import em_ingles
 lat,lon=st.session_state.get('foto_lat'),st.session_state.get('foto_lon')
 if st.session_state.get('foto_salva_id') and st.session_state.get('foto_posicao_salva'):
  lat=st.session_state.foto_posicao_salva['latitude'];lon=st.session_state.foto_posicao_salva['longitude']
 gps=st.session_state.get('foto_gps') or {}
 accuracy=gps.get('accuracy') if gps.get('latitude')==lat and gps.get('longitude')==lon else None
 return _GPS(data={'tiles':TILES,'attribution':ATRIBUICAO,'latitude':lat,'longitude':lon,'accuracy':accuracy,'saved':bool(st.session_state.get('foto_salva_id')), 'language':'en' if em_ingles() else 'pt'},key='gps_foto',on_position_change=_posicao_alterada).position
