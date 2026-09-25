"""Helpers for the Portuguese and English interface."""
import streamlit as st


def em_ingles():
    return st.query_params.get('lang', 'pt').lower() in {'en', 'en-us', 'english'}


def texto(portugues, ingles):
    return ingles if em_ingles() else portugues


def idioma_query():
    return '?lang=en' if em_ingles() else '?lang=pt'


def alternador_html(base=''):
    atual = 'EN' if em_ingles() else 'PT'
    destino = 'pt' if em_ingles() else 'en'
    return (f'<span class="language-switch"><span class="language-current">{atual}</span>'
            f'<a href="{base}?lang={destino}" target="_self">{destino.upper()}</a></span>')
