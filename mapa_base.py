"""Shared street basemap; no CARTO credential-dependent endpoints."""
TILES = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}'
ATRIBUICAO = ('Tiles &copy; <a href="https://www.esri.com/">Esri</a> — Sources: Esri, HERE, Garmin, USGS, '
             'Intermap, INCREMENT P, NRCan, Esri Japan, METI, Esri China (Hong Kong), Esri Korea, '
             'Esri (Thailand), NGCC, &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>, GIS User Community')
ESTILO = {
    'version': 8,
    'sources': {'ruas': {'type': 'raster', 'tiles': [TILES], 'tileSize': 256,
                          'maxzoom': 19, 'attribution': ATRIBUICAO}},
    'layers': [{'id': 'ruas', 'type': 'raster', 'source': 'ruas'}],
}


def estilo_url():
    import streamlit as st
    base = st.get_option('server.baseUrlPath').strip('/')
    return ('/' + base if base else '') + '/app/static/mapa-ruas.json'
