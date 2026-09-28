"""Mapa com ciclo de montagem seguro nas atualizações do Streamlit."""
from pathlib import Path
import streamlit as st
ASSETS=Path(__file__).parent/'assets'
VENDOR=ASSETS/'vendor'/'leaflet'
_GPS=st.components.v2.component('aquasentinela_gps',
 html='<div class="location-map"></div><button type="button">◎ Usar minha localização</button><p role="status" aria-live="polite"></p>',
 css=(VENDOR/'leaflet.css').read_text(encoding='utf-8')+"\n.location-map{height:250px;border-radius:15px;isolation:isolate}button{width:100%;padding:14px;margin-top:12px;border:1px solid #0062ed;border-radius:30px;color:#0056d9;background:white;font:bold 16px sans-serif;cursor:pointer}button:disabled{opacity:.5}p{font:13px/1.5 sans-serif;color:#5c769b}.aqua-marker span{display:block;width:30px;height:30px;border-radius:50% 50% 50% 0;background:linear-gradient(135deg,#00cdc4,#007db6);transform:rotate(-45deg);box-shadow:0 3px 8px #00394c55}.aqua-marker span:after{content:'';position:absolute;width:11px;height:11px;background:white;border-radius:50%;top:9px;left:9px}\n",
 js=(VENDOR/'leaflet.js').read_text(encoding='utf-8')+'\n'+(ASSETS/'location.js').read_text(encoding='utf-8'))
def obter_localizacao():
 from i18n import em_ingles
 lat,lon=st.session_state.get('foto_lat'),st.session_state.get('foto_lon')
 if st.session_state.get('foto_salva_id') and st.session_state.get('foto_posicao_salva'):
  lat=st.session_state.foto_posicao_salva['latitude'];lon=st.session_state.foto_posicao_salva['longitude']
 gps=st.session_state.get('foto_gps') or {}
 accuracy=gps.get('accuracy') if gps.get('latitude')==lat and gps.get('longitude')==lon else None
 return _GPS(data={'latitude':lat,'longitude':lon,'accuracy':accuracy,'saved':bool(st.session_state.get('foto_salva_id')), 'language':'en' if em_ingles() else 'pt'},key='gps_foto',on_position_change=lambda:None).position
