"""Página compartilhável de um trecho/local, com todo o histórico público."""
import logging
import streamlit as st

from relatos import listar_fotos
from observacao import agrupar_locais, publicos, resumo_local
from mapa_visual import AVISO_COBERTURA, resumo_grupo, nivel_html, historico_local
from registro_visual import cabecalho, rodape
from evidencia_visual import mostrar_hotspot

cabecalho('Histórico do local', 'Observações ao longo do tempo.', False,
          'Location history', 'Observations over time.', '/local')
st.page_link('app_pages/mapa.py', label='Voltar ao mapa', icon=':material/arrow_back:')
try:
    revisados = publicos(listar_fotos())
except Exception:
    logging.exception('Falha ao carregar histórico público')
    st.error('Não foi possível carregar o histórico. Tente novamente.')
    st.stop()
ident = st.query_params.get('id')
grupos = agrupar_locais(revisados)
# Aceita qualquer ID público do grupo, preservando links após novas revisões retroativas.
grupo = next((g for g in grupos if ident in {r['id'] for r in g['registros']}), None)
resumo = resumo_local(grupo['registros']) if grupo else None
if not resumo:
    st.info('Local não encontrado ou sem observações públicas. Escolha um ponto no mapa.')
else:
    st.subheader(grupo['nome'])
    st.caption(f"Corpo hídrico: {grupo.get('waterbody_id') or 'Não identificado — aguardando vinculação'}")
    mostrar_hotspot(grupo['registros'])
    st.caption(f"Trecho aproximado de até 200 m da primeira observação · "
               f"{grupo['latitude']:.5f}, {grupo['longitude']:.5f} · Todo o período")
    st.info(AVISO_COBERTURA)
    resumo_grupo(resumo)
    a, b, c, d = st.columns(4)
    a.metric('Total de observações', resumo['total'])
    b.metric('Dias diferentes observados', resumo['dias'])
    c.metric('Primeira observação', resumo['primeira'].strftime('%d/%m/%Y'))
    d.metric('Última observação', resumo['ultima'].strftime('%d/%m/%Y'))
    st.markdown('#### Nível mais recente observado')
    st.html(nivel_html(resumo['recente']['nivel_informado']))
    st.caption('O nível mais recente não comprova a condição atual. Níveis anteriores aparecem na linha do tempo.')
    a, b = st.columns(2)
    a.metric('Quantidade total identificada nas fotos', resumo['objetos'])
    b.metric('Recorrência · dias com resíduos declarados', f"{resumo['dias_residuos']} de {resumo['dias']}")
    st.caption('Recorrência indica em quantos dias observados houve resíduos declarados. '
               'Não mede observação contínua nem aumento de poluição. O total de objetos soma '
               'detecções nas fotos; o mesmo objeto pode aparecer em fotos diferentes.')
    st.markdown('#### Principais resíduos identificados')
    if resumo['classes']:
        st.dataframe([{'Resíduo': nome, 'Detecções nas fotos': total}
                      for nome, total in resumo['classes']], hide_index=True, width='stretch')
    else:
        st.info('Não há objetos identificados pelo modelo nas observações deste local.')
    historico_local(resumo, revisados, f'local-{grupo["id"]}')
    from acompanhamento_visual import antes_depois
    antes_depois(grupo, revisados)
rodape()
