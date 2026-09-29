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
    from html import escape
    label = texto('Idioma atual: português. Mudar para inglês.', 'Current language: English. Switch to Portuguese.')
    return (f'<a class="language-switch language-{atual.lower()}" href="{escape(base + "?" + urlencode(parametros), quote=True)}" '
            f'target="_self" aria-label="{label}" title="{label}">'
            f'<span class="language-en">EN</span><span class="language-track" aria-hidden="true"><span></span></span>'
            f'<span class="language-pt">PT</span></a>')
