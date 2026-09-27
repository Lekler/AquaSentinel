"""Entrada única do AquaSentinela: participação por foto e painel ambiental."""
import streamlit as st
from pathlib import Path
from i18n import texto

st.set_page_config(page_title='AquaSentinela', page_icon=str(Path(__file__).parent / 'assets' / 'home' / 'Logo.png'), layout='wide')
st.session_state.setdefault('foto_epoch', 0)

# O estilo compartilhado chega antes das páginas e permanece nas transições.
# Streamlit marca os elementos do render anterior com data-stale enquanto
# recebe o novo conteúdo; preserve o espaço sem exibir a página antiga.
assets = Path(__file__).parent / 'assets'
st.html('<style>' + (assets / 'home.css').read_text(encoding='utf-8')
        + (assets / 'registro.css').read_text(encoding='utf-8')
        + '\n[data-testid="stElementContainer"][data-stale="true"] '
          '{visibility:hidden;pointer-events:none;}\n</style>')

pagina = st.navigation([
    st.Page('app_pages/inicio.py', title=texto('Início', 'Home'), icon=':material/home:', default=True),
    st.Page('app_pages/registrar.py', title=texto('Registrar ocorrência', 'Report an occurrence'), icon=':material/photo_camera:', url_path='registrar'),
    st.Page('app_pages/mapa.py', title=texto('Mapa e registros', 'Map and reports'), icon=':material/map:', url_path='mapa'),
    st.Page('app_pages/local.py', title=texto('Histórico do local', 'Location history'), icon=':material/history:', url_path='local'),
    st.Page('painel_ari.py', title=texto('Chuva e ARI · experimental', 'Rain and ARI · experimental'), icon=':material/monitoring:', url_path='avaliacao'),
    st.Page('app_pages/sobre.py', title=texto('Sobre', 'About'), icon=':material/info:', url_path='sobre'),
    st.Page('app_pages/duvidas.py', title=texto('Dúvidas', 'Questions'), icon=':material/help:', url_path='duvidas'),
], position='hidden')
with st.container(key=f'pagina-{pagina.url_path or "inicio"}'):
    pagina.run()
