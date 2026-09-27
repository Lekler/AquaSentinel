"""Apresentação pública de locais: condição, cobertura e prioridade separadas."""
from html import escape
import logging
from urllib.parse import urlencode

import streamlit as st

from observacao import CORES_NIVEIS, FUSO, data_registro, ultima_descricao
from relatos import obter_foto
from wps import pontuar

AVISO_COBERTURA = ('Mais ocorrências não significam automaticamente mais poluição. '
                  'Dias distintos medem cobertura de observação, não gravidade nem observadores independentes.')


def nivel_html(nivel):
    cor = CORES_NIVEIS.get(nivel, '#94a3b8')
    return (f'<span class="nivel-observado"><i style="background:{cor}"></i>'
            f'{escape(nivel)}</span>')


def legenda(camada):
    if camada == 'Condição ambiental':
        itens = ''.join(nivel_html(n) for n in CORES_NIVEIS)
        titulo = 'Nível observado pelo usuário · última observação do período'
    else:
        itens = ''.join(f'<span class="nivel-observado"><i style="background:{cor}"></i>{nome}</span>'
                        for nome, cor in [('1 dia', '#bfdbfe'), ('2–3 dias', '#60a5fa'),
                                          ('4–7 dias', '#2563eb'), ('8+ dias', '#1e3a8a')])
        titulo = 'Cobertura de observação · número de dias diferentes observados'
    st.html(f'<div class="mapa-legenda" role="note"><strong>{titulo}</strong>'
            f'<div class="mapa-legenda-itens">{itens}</div>'
            '<small>Todos os marcadores têm o mesmo tamanho. As cores não representam WPS.</small></div>')


def link_local(identificador):
    base = st.get_option('server.baseUrlPath').strip('/')
    return ('/' + base if base else '') + '/local?' + urlencode({'id': identificador})


def resumo_grupo(resumo):
    ocorrencias = 'ocorrência' if resumo['total'] == 1 else 'ocorrências'
    dias = 'dia de observação' if resumo['dias'] == 1 else 'dias diferentes de observação'
    st.write(f"**{resumo['total']} {ocorrencias} neste local** · "
             f"**{resumo['dias']} {dias}** · "
             f"{ultima_descricao(resumo['dias_desde_ultima'])}.")


def detalhes_ocorrencia(registro, revisados, chave):
    # Revalida a visibilidade também ao buscar os bytes da fotografia.
    try:
        atual, foto, anotada = obter_foto(registro['id'])
        if atual.get('revisao') != 'validado' or atual.get('consentimento_publicacao') is not True:
            st.info('Esta observação não está disponível para publicação.')
            return
    except Exception:
        logging.exception('Falha ao carregar evidência pública')
        st.warning('A fotografia desta observação está indisponível.')
        foto = anotada = None
    s = pontuar(registro, revisados, agora=data_registro(registro))
    condicao, prioridade = st.columns(2)
    with condicao:
        st.markdown('#### Nível observado pelo usuário')
        st.html(nivel_html(registro.get('nivel_informado', 'Não informado')))
        st.text(f"Local: {registro['nome']}")
        st.text(f"Data do registro: {data_registro(registro).astimezone(FUSO):%d/%m/%Y %H:%M}")
        st.text('Status de revisão: validado')
        st.caption('Condição declarada e revisada; não é uma classificação de gravidade pela IA.')
    with prioridade:
        st.markdown('#### WPS / prioridade calculada')
        st.metric('WPS · índice experimental', f"{s['wps']:.1f} / 100")
        st.progress(min(1., max(0., s['wps'] / 100)))
        st.caption(f"Prioridade {s['faixa_wps'].lower()} · calculada na data do registro.")
        st.metric('CS · confiança combinada', f"{s['cs']:.1f}%")
    a, b = st.columns(2)
    a.metric('Objetos detectados na foto', int(registro.get('total') or 0))
    confianca = registro.get('confianca_media')
    b.metric('Confiança média da IA', 'Sem detecções' if confianca is None else f'{confianca:.1f}%')
    st.caption('WPS = 70% do nível declarado (W) + 30% da frequência de fotos distintas (F), '
               'no mesmo corpo hídrico confirmado, em 200 m e nos 30 dias anteriores ao registro. '
               'Similaridades pendentes/reutilizadas não ampliam F. A fórmula experimental foi mantida; '
               'F pode aumentar com mais fotos e não comprova mais poluição. '
               'CS = confiança média × 0,8; não é probabilidade calibrada de acerto.')
    if foto:
        st.image(foto, caption='Foto da observação', width='stretch')
        if st.checkbox('Mostrar foto com detecções', key=f'anotada-{chave}-{registro["id"]}'):
            st.image(anotada, caption='Objetos identificados pelo modelo', width='stretch')
    from evidencia_visual import mostrar_evidencia
    st.caption(f"Corpo hídrico: {registro.get('waterbody_id') or 'Não identificado'} · "
               f"{registro.get('waterbody_nome') or 'Aguardando vinculação pela equipe'}")
    mostrar_evidencia(registro)


def historico_local(resumo, revisados, chave):
    st.subheader('Linha do tempo')
    st.caption('Datas de registro no horário de Brasília. Não comprovam a data de captura da foto.')
    registros = list(reversed(resumo['registros']))
    st.dataframe([{'Data': data_registro(r).astimezone(FUSO).strftime('%d/%m/%Y %H:%M'),
                   'Nível observado': r['nivel_informado'],
                   'Objetos detectados': int(r.get('total') or 0),
                   'Revisão': 'Validado'} for r in registros], hide_index=True, width='stretch')
    por_id = {r['id']: r for r in registros}
    selecionado = st.selectbox('Observação para ver foto e detalhes', list(por_id),
        format_func=lambda ident: (f"{data_registro(por_id[ident]).astimezone(FUSO):%d/%m/%Y %H:%M} — "
                                  f"{por_id[ident]['nivel_informado']} · {ident[:8]}"),
        key=f'observacao-{chave}')
    detalhes_ocorrencia(por_id[selecionado], revisados, chave)
