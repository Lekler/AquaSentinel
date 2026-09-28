"""Helpers for the Portuguese and English interface."""
import streamlit as st


def em_ingles():
    idioma = st.query_params.get('lang')
    if idioma is not None:
        st.session_state['idioma'] = 'en' if idioma.lower() in {'en', 'en-us', 'english'} else 'pt'
    return st.session_state.get('idioma', 'pt') == 'en'


def texto(portugues, ingles):
    return ingles if em_ingles() else portugues


def idioma_query():
    return '?lang=en' if em_ingles() else '?lang=pt'


def alternador_html(base=''):
    from urllib.parse import urlencode
    atual = 'EN' if em_ingles() else 'PT'
    destino = 'pt' if em_ingles() else 'en'
    parametros = {k:v for k,v in st.query_params.items() if k != 'lang'}
    parametros['lang'] = destino
    return (f'<span class="language-switch"><span class="language-current">{atual}</span>'
            f'<a href="{base}?{urlencode(parametros)}" target="_self">{destino.upper()}</a></span>')
