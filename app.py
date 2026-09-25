"""Entrada única do AquaSentinela: participação por foto e painel ambiental."""
import streamlit as st
from pathlib import Path
from i18n import texto

st.set_page_config(page_title='AquaSentinela', page_icon=str(Path(__file__).parent / 'assets' / 'home' / 'Logo.png'), layout='wide')
st.session_state.setdefault('foto_epoch', 0)

pagina = st.navigation([
    st.Page('app_pages/inicio.py', title=texto('Início', 'Home'), icon=':material/home:', default=True),
    st.Page('app_pages/registrar.py', title=texto('Registrar ocorrência', 'Report an occurrence'), icon=':material/photo_camera:', url_path='registrar'),
    st.Page('app_pages/mapa.py', title=texto('Mapa e registros', 'Map and reports'), icon=':material/map:', url_path='mapa'),
    st.Page('painel_ari.py', title=texto('Chuva e ARI · experimental', 'Rain and ARI · experimental'), icon=':material/monitoring:', url_path='avaliacao'),
], position='top')
pagina.run()
