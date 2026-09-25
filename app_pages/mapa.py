"""Mapa público de pontos revisados e fila privada de revisão."""
import hmac
import logging
import os

import pandas as pd
import pydeck as pdk
import streamlit as st

from interface_fotos import mostrar_analise
from relatos import listar_fotos, obter_foto, revisar_foto
from registro_visual import cabecalho, rodape
from wps import pontuar

CORES = {'Baixa': [54, 166, 113], 'Moderada': [239, 184, 47],
         'Alta': [240, 113, 51], 'Crítica': [206, 55, 54]}

cabecalho('Mapa e registros', 'Pontos revisados e prioridade experimental de resíduos.',
          False, 'Map and reports', 'Reviewed points and experimental waste priority.', '/mapa')
try:
    todos = listar_fotos()
except Exception:
    logging.exception('Falha ao carregar relatos')
    st.error('Não foi possível carregar os relatos. Tente novamente ou avise a equipe.')
    st.stop()

revisados = [r for r in todos if r.get('revisao') == 'validado' and r.get('consentimento_publicacao')]
ativos = [r for r in revisados if r.get('nivel_informado') != 'Sem resíduos']
pontuados = [(r, pontuar(r, revisados)) for r in ativos]

st.subheader('Pontos monitorados')
a, b, c = st.columns(3)
a.metric('Ocorrências revisadas', len(revisados))
b.metric('Pontos ativos', len(ativos))
c.metric('Aguardando revisão', len([r for r in todos if r.get('revisao') == 'nao_revisado']))
st.caption('Cor e tamanho do ponto representam o WPS. O CS indica a confiança das detecções combinada com a confiabilidade da fonte. Os índices são experimentais.')

if pontuados:
    pontos = [{'latitude': float(r['latitude']), 'longitude': float(r['longitude']),
               'cor': CORES[s['faixa_wps']], 'raio': 90 + s['wps'] * 3,
               'local': r['nome'], 'wps': s['wps'], 'cs': s['cs']}
              for r, s in pontuados]
    df = pd.DataFrame(pontos)
    camada = pdk.Layer('ScatterplotLayer', data=df, get_position='[longitude, latitude]',
                       get_fill_color='cor', get_radius='raio', radius_min_pixels=6,
                       radius_max_pixels=26, pickable=True, opacity=.85)
    vista = pdk.ViewState(latitude=float(df.latitude.mean()), longitude=float(df.longitude.mean()), zoom=10)
    st.pydeck_chart(pdk.Deck(map_style=None, initial_view_state=vista, layers=[camada],
                             tooltip={'html': '<b>{local}</b><br/>WPS {wps} · CS {cs}%',
                                      'style': {'backgroundColor': '#07345c', 'color': 'white'}}),
                    width='stretch')
    for r, s in sorted(pontuados, key=lambda item: item[1]['wps'], reverse=True):
        with st.expander(f"{r['nome']} · WPS {s['wps']:.1f} ({s['faixa_wps']}) · CS {s['cs']:.1f}% ({s['faixa_cs']})"):
            st.write(f"**W:** {s['w']} · **F:** {s['f']} · **Recorrências revisadas:** {s['recorrencias']} · **Confiança da IA:** {r.get('confianca_media') or 0}% · **Fonte comunitária:** 0,8")
            st.caption('W vem do nível informado e confirmado na revisão humana; a IA identifica classes de plástico, não mede gravidade. F usa fotos distintas no mesmo local, em 200 m e 30 dias. Sem cadastro de autores, independência entre pessoas não é verificável. CS não é probabilidade calibrada de acerto.')
            st.write(f"**Revisado por:** {r.get('revisor', '—')} · **Data:** {r.get('validado_em', '—')[:16]}")
            try:
                _, foto, anotada = obter_foto(r['id'])
                st.image(anotada, caption='Detecções do modelo')
            except Exception:
                logging.exception('Falha ao carregar evidência')
                st.warning('A evidência desta ocorrência está indisponível.')
else:
    st.info('Ainda não há pontos ativos revisados. Novos relatos aparecem aqui após validação pela equipe.')

st.caption('A ausência de pontos não significa ausência de resíduos. A localização é informada ou confirmada pelo usuário; o app não comprova onde ou quando a foto foi tirada.')

senha_configurada = os.environ.get('AQUASENTINEL_REVIEW_PASSWORD', '')
with st.expander('Área da equipe de revisão'):
    if not senha_configurada:
        st.info('A revisão está desabilitada até configurar AQUASENTINEL_REVIEW_PASSWORD.')
    else:
        senha = st.text_input('Senha da equipe', type='password', key='senha_revisao')
        autorizado = bool(senha) and hmac.compare_digest(senha, senha_configurada)
        if senha and not autorizado:
            st.error('Senha incorreta.')
        if autorizado:
            pendentes = [r for r in todos if r.get('revisao') == 'nao_revisado']
            st.write(f'{len(pendentes)} relato(s) aguardando revisão.')
            if pendentes:
                por_id = {r['id']: r for r in pendentes}
                escolhido = st.selectbox('Relato', list(por_id),
                    format_func=lambda ident: f"{por_id[ident]['nome']} · {por_id[ident]['registrado_em'][:16]}")
                registro, foto, anotada = obter_foto(escolhido)
                st.write(f"**Local:** {registro['nome']} · **Coordenadas:** {registro['latitude']}, {registro['longitude']} · **Nível declarado:** {registro['nivel_informado']}")
                st.write(f"**Observações:** {registro.get('observacoes') or '—'}")
                mostrar_analise(registro, anotada)
                st.image(foto, caption='Foto enviada')
                revisor = st.text_input('Nome do revisor', max_chars=100)
                col1, col2 = st.columns(2)
                decisao = 'validado' if col1.button('Validar relato', type='primary') else 'rejeitado' if col2.button('Rejeitar relato') else None
                if decisao:
                    try:
                        revisar_foto(escolhido, decisao, revisor)
                        st.success('Revisão salva.')
                        st.rerun()
                    except Exception as exc:
                        logging.exception('Falha ao revisar relato')
                        st.error(f'Não foi possível salvar a revisão: {exc}')
rodape()
