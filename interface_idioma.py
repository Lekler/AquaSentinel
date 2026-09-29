"""Adapter de apresentação: traduz rótulos sem alterar valores gravados ou retornos dos widgets."""
from functools import lru_cache
from html import escape, unescape
import json
from pathlib import Path
import re
import streamlit as original
from i18n import em_ingles


@lru_cache(maxsize=1)
def catalogo():
    resultado={}
    for arquivo in sorted((Path(__file__).parent/'locales').glob('en*.json')):
        resultado.update(json.loads(arquivo.read_text(encoding='utf-8')))
    return resultado


@lru_cache(maxsize=1)
def modelos():
    saida=[]
    for origem, destino in catalogo().items():
        if '{0}' not in origem or not re.search(r'[A-Za-zÀ-ÿ]{3}', origem):
            continue
        partes=re.split(r'(\{\d+\})', origem)
        pattern=''.join(f'(?P<v{p[1:-1]}>.*?)' if re.fullmatch(r'\{\d+\}',p) else re.escape(p) for p in partes)
        saida.append((re.compile('^'+pattern+'$', re.S),destino))
    return saida


def traduzir(valor, ingles=None):
    if not isinstance(valor,str) or not (em_ingles() if ingles is None else ingles):
        return valor
    texto=valor.strip()
    if texto in catalogo():
        return valor.replace(texto,catalogo()[texto],1)
    for modelo, destino in modelos():
        m=modelo.fullmatch(texto)
        if m:
            return destino.format(*(traduzir(m.group('v'+str(i)), True) for i in range(len(m.groups()))))
    # Markdown formatting and compound labels retain their structure.
    enumerado=re.fullmatch(r'(\d+[.)] )(.*)',texto,re.S)
    if enumerado:
        return enumerado[1]+traduzir(enumerado[2],True)
    frases=re.split(r'(?<=\.) (?=[A-ZÀ-Ý])',valor)
    if len(frases)>1:
        return ' '.join(traduzir(f,True) for f in frases)
    if '\n' in valor:
        return '\n'.join(traduzir(l, True) for l in valor.split('\n'))
    for sep in (' · ', ': ', ' — '):
        if sep in valor:
            return sep.join(traduzir(l, True) for l in valor.split(sep))
    m=re.fullmatch(r'(\*\*|#{1,6} |• )(.*?)(\*\*)?',texto)
    if m:
        return m[1]+traduzir(m[2], True)+(m[3] or '')
    return valor


def html_idioma(html):
    if not em_ingles():
        return html
    # Preserve CSS, SVG paths, image bytes and URLs verbatim.
    parts=re.split(r'(<style\b[^>]*>.*?</style>|<[^>]+>)',html,flags=re.S|re.I)
    for i,p in enumerate(parts):
        if not p.startswith('<'):
            parts[i]=escape(traduzir(unescape(p)),quote=False)
        elif not p.lower().startswith('<style'):
            parts[i]=re.sub(r'(aria-label|alt|title)="([^"]*)"',lambda m:m[1]+'="'+escape(traduzir(unescape(m[2])),quote=True)+'"',p)
    return ''.join(parts)


def dados(valor):
    if isinstance(valor,str): return traduzir(valor)
    if isinstance(valor,list): return [dados(v) for v in valor]
    if isinstance(valor,tuple): return tuple(dados(v) for v in valor)
    if isinstance(valor,dict): return {traduzir(k):dados(v) for k,v in valor.items()}
    try:
        import pandas as pd
        if isinstance(valor,pd.DataFrame):
            return valor.map(lambda v: traduzir(v) if isinstance(v,str) else v).rename(columns=traduzir)
    except ImportError:
        pass
    return valor


class Interface:
    def __init__(self, alvo): self._alvo=alvo
    def __enter__(self): self._alvo.__enter__();return self
    def __exit__(self,*args):return self._alvo.__exit__(*args)
    def __getattr__(self,nome):
        fn=getattr(self._alvo,nome)
        if nome=='sidebar':return Interface(fn)
        if nome in {'session_state','query_params','cache_data','cache_resource','components','column_config','navigation','switch_page','rerun','stop','set_page_config','get_option','secrets','context','dialog','fragment'}:
            return fn
        if not callable(fn):return fn
        def chamar(*args,**kwargs):
            args=list(args)
            for k in ('label','help','placeholder','caption','text','title'):
                if k in kwargs:kwargs[k]=dados(kwargs[k])
            if nome in {'selectbox','multiselect','segmented_control','radio','pills'}:
                fmt=kwargs.get('format_func',str)
                ingles=em_ingles()
                kwargs['format_func']=lambda value: traduzir(fmt(value), ingles)
                if nome in {'selectbox','multiselect'}:
                    kwargs.setdefault('placeholder',traduzir('Selecione'))
            if args:
                if nome=='html' or nome=='markdown' and kwargs.get('unsafe_allow_html'):
                    args[0]=html_idioma(args[0])
                elif nome in {'write','dataframe','table','json','tabs'}:
                    args=[dados(v) for v in args]
                elif nome not in {'Page','image','download_button','page_link','link_button','progress','columns','container','empty','form','pydeck_chart','line_chart','bar_chart','altair_chart','plotly_chart','code'}:
                    args[0]=traduzir(args[0])
                elif nome in {'download_button','link_button'}:
                    args[0]=traduzir(args[0])
                if nome=='metric' and len(args)>1:args[1]=traduzir(args[1])
            result=fn(*args,**kwargs)
            if nome in {'columns','tabs'}:return [Interface(c) for c in result]
            if nome in {'container','expander','popover','empty','form'}:return Interface(result)
            return result
        return chamar


st=Interface(original)
