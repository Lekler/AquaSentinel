"""Elementos de marca da página de registro, usando os assets originais."""
import base64
from pathlib import Path
from home_visual import imagem, icone, CAMERA_REGISTRO
from i18n import alternador_html, em_ingles, idioma_query, texto
import streamlit as st


def cabecalho(titulo_pagina='Registrar ocorrência', descricao='Uma foto ajuda a cuidar das nossas águas.', mostrar_etapas=True, titulo_ingles='Register an occurrence', descricao_ingles='One photo helps care for our waters.', caminho='/registrar'):
    css=(Path(__file__).parent/'assets'/'registro.css').read_text(encoding='utf-8')
    base=st.get_option('server.baseUrlPath').strip('/')
    base='/' + base if base else ''
    sobre = texto('Sobre', 'About')
    mapa = texto('Mapa', 'Map')
    duvidas = texto('Dúvidas', 'Questions')
    sobre_texto = texto('AquaSentinela reúne registros de resíduos e avaliação ambiental para ajudar a cuidar dos rios e canais.', 'AquaSentinela brings together waste reports and environmental assessments to help care for rivers and canals.')
    duvidas_texto = texto('Envie uma foto, confira o ponto no mapa e informe o nível observado. A confiança da IA mede o reconhecimento de objetos, não a autenticidade da imagem.', 'Send a photo, check the point on the map and report the observed level. AI confidence measures object recognition, not image authenticity.')
    etapas = ('<div class="registro-steps"><span>① Photo</span><span>② Location</span><span>③ Level</span><span>④ Send</span></div>' if em_ingles() else
               '<div class="registro-steps"><span>① Foto</span><span>② Localização</span><span>③ Nível</span><span>④ Enviar</span></div>') if mostrar_etapas else ''
    query = idioma_query()
    st.html(f'<style>{css}</style><header class="registro-header"><a href="{base}/{query}" target="_self">{imagem("Logo.png",descricao="AquaSentinela")}</a><nav>{alternador_html(base + caminho or "/")}<details><summary>{sobre}</summary><p>{sobre_texto}</p></details><a href="{base}/mapa{query}" target="_self">{mapa}</a><details><summary>{duvidas}</summary><p>{duvidas_texto}</p></details></nav></header>')
    st.html(f'<div class="registro-title"><div><h1>{texto(titulo_pagina, titulo_ingles)}</h1><p>{texto(descricao, descricao_ingles)}</p></div>{etapas}</div>')


def titulo(numero,texto,descricao):
    st.html(f'<div class="card-heading"><b>{numero}</b><div><h2>{texto}</h2><p>{descricao}</p></div></div>')


def fotos(rascunho):
    def quadro(conteudo,label):
        if conteudo:
            src='data:image/jpeg;base64,'+base64.b64encode(conteudo).decode('ascii')
            return f'<figure><img src="{src}" alt="{label}"><figcaption>{label}</figcaption></figure>'
        legenda = texto(label, 'Your photo' if label == 'Sua foto' else 'AI identification')
        instrucoes = texto('Tire uma foto ou envie do seu celular.', 'Take a photo or upload one from your phone.')
        return f'<figure class="foto-vazia">{icone(CAMERA_REGISTRO,"#7794b7")}<strong>{legenda}</strong><small>{instrucoes}</small></figure>'
    st.html('<div class="foto-pair">'+quadro(rascunho['foto'] if rascunho else None,'Sua foto')+quadro(rascunho['anotada'] if rascunho else None,'Identificação pela IA')+'</div>')


def rodape():
    st.html('<footer class="registro-footer"><p>'+imagem('F1.1.png')+' '+texto('Seu registro ajuda a cuidar das nossas águas.', 'Your report helps care for our waters.')+'</p>'+imagem('g.png','registro-waves')+'</footer>')
