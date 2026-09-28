"""Mapa de condição observada e cobertura, com revisão privada preservada."""
import hmac
import logging
import os

import pydeck as pdk
from interface_idioma import st

from interface_fotos import mostrar_analise
from relatos import listar_fotos, obter_foto, revisar_foto
from registro_visual import cabecalho, rodape
from observacao import (CORES_NIVEIS, PERIODOS, agrupar_locais, publicos,
                        filtrar_periodo, resumo_local, cor_cobertura, rgb, ultima_descricao)
from mapa_visual import (AVISO_COBERTURA, legenda, resumo_grupo, historico_local, link_local)
from evidencia_visual import mostrar_hotspot, mostrar_evidencia, gestao_catalogo
from hotspots import avaliar_hotspot
from interface_idioma import traduzir
from i18n import texto

cabecalho('Mapa e registros', 'Condição observada e cobertura de observação.',
          False, 'Map and reports', 'Observed condition and observation coverage.', '/mapa')
try:
    todos = listar_fotos()
except Exception:
    logging.exception('Falha ao carregar relatos')
    st.error('Não foi possível carregar os relatos. Tente novamente ou avise a equipe.')
    st.stop()

revisados = publicos(todos)
with st.container(key='mapa-filtros'):
    periodo = st.selectbox('Período de observação', list(PERIODOS), index=2, key='mapa-periodo')
    camada = st.segmented_control('Camada do mapa', ['Condição ambiental', 'Cobertura de observação'],
                                  default='Condição ambiental', key='mapa-camada') or 'Condição ambiental'
    modo = st.selectbox('Tipo de observação', ['Todos', 'Oportunístico', 'Monitoramento estruturado'], key='mapa-modo')
    st.info(AVISO_COBERTURA)
    st.caption('Agrupamento aproximado: mesmo código de corpo hídrico confirmado pela equipe, '
               'a até 200 m da primeira observação. Registros sem código confirmado ficam separados. '
               'O período inclui hoje e usa dias de calendário no horário de Brasília.')
    mostrar_sem_residuos = st.checkbox('Mostrar também locais observados sem resíduos', value=True)
    somente_hotspots = st.checkbox('Mostrar somente hotspots persistentes · avaliação dos últimos 90 dias', key='mapa-hotspots')
    st.page_link('app_pages/lacunas.py', label='Consultar trechos com lacunas de monitoramento')
if modo != 'Todos':
    revisados = [r for r in revisados if r.get('modo', 'oportunistico') == ('estruturado' if modo == 'Monitoramento estruturado' else 'oportunistico')]

# Agrupa o histórico completo antes de filtrar para preservar os IDs e âncoras dos locais.
grupos = []
for grupo in agrupar_locais(revisados):
    resumo = resumo_local(filtrar_periodo(grupo['registros'], PERIODOS[periodo]))
    if resumo:
        grupos.append({**grupo, 'resumo': resumo, 'hotspot': avaliar_hotspot(grupo['registros'])})
if somente_hotspots:
    grupos = [g for g in grupos if g['hotspot']['persistente']]
if not mostrar_sem_residuos and camada == 'Condição ambiental':
    grupos = [g for g in grupos if g['resumo']['recente']['nivel_informado'] != 'Sem resíduos']
a, b, c = st.columns(3)
a.metric('Observações no período', sum(g['resumo']['total'] for g in grupos))
b.metric('Locais observados', len(grupos))
c.metric('Dias diferentes · todo o mapa',
         (resumo_local([r for g in grupos for r in g['resumo']['registros']]) or {}).get('dias', 0))

with st.container(key='mapa-pontos'):
    st.subheader(camada)
    if grupos:
        pontos = []
        for g in grupos:
            resumo = g['resumo']
            hotspot = g['hotspot']
            nivel = resumo['recente']['nivel_informado']
            cor = (CORES_NIVEIS.get(nivel, '#94a3b8') if camada == 'Condição ambiental'
                   else cor_cobertura(resumo['dias']))
            pontos.append({'id': g['id'], 'latitude': g['latitude'], 'longitude': g['longitude'],
                           'cor': rgb(cor), 'local': g['nome'], 'nivel': traduzir(nivel),
                           'ocorrencias': resumo['total'], 'dias': resumo['dias'],
                           'corpo': g.get('waterbody_id') or traduzir('Não identificado'),
                           'hotspot': traduzir('Hotspot persistente' if hotspot['persistente'] else 'Persistência em acompanhamento'),
                           'ultima': traduzir(ultima_descricao(resumo['dias_desde_ultima']))})
        layer = pdk.Layer('ScatterplotLayer', id='locais', data=pontos,
                          get_position='[longitude, latitude]', get_fill_color='cor',
                          get_radius=10, radius_units='pixels', radius_min_pixels=10,
                          radius_max_pixels=10, stroked=True, get_line_color=[255, 255, 255],
                          line_width_min_pixels=2, pickable=True, opacity=1)
        vista = pdk.ViewState(latitude=sum(p['latitude'] for p in pontos)/len(pontos),
                             longitude=sum(p['longitude'] for p in pontos)/len(pontos), zoom=10)
        evento = st.pydeck_chart(pdk.Deck(map_style=None, initial_view_state=vista, layers=[layer],
            tooltip={'text': texto('{local} · {corpo}\nNível mais recente: {nivel}\n{ocorrencias} ocorrências neste local\n{dias} dias diferentes de observação\n{ultima}\nClique para foto e histórico.', '{local} · {corpo}\nLatest level: {nivel}\n{ocorrencias} reports at this location\n{dias} distinct observation days\n{ultima}\nClick for photos and history.')}),
            on_select='rerun', selection_mode='single-object', key=f'mapa-{periodo}-{camada}')
        legenda(camada)
        # Nunca usa metadados enviados pelo cliente para recuperar fotos: só IDs da lista pública atual.
        objetos = evento.selection.get('objects', {}).get('locais', [])
        por_id = {g['id']: g for g in grupos}
        ident = objetos[0].get('id') if objetos else None
        if ident in por_id:
            g = por_id[ident]
            st.subheader(g['nome'])
            resumo_grupo(g['resumo'])
            mostrar_hotspot(g['registros'], compacto=True)
            st.link_button('Abrir página deste local / corpo hídrico', link_local(g['id']))
            historico_local(g['resumo'], revisados, f'mapa-{g["id"]}-{periodo}')
    else:
        st.info('Nenhuma observação pública revisada neste período. Experimente Todo o período.')
        legenda(camada)

st.caption('Ausência de observações não significa ausência de resíduos. A cor mostra a última '
           'condição declarada dentro do período, não garante a condição atual do local.')
if grupos:
    st.subheader('Locais e histórico')
    st.caption('Escolha um local para consultar as fotos e a evolução das observações.')
    for g in sorted(grupos, key=lambda g: g['nome'].casefold()):
        selo = ' · Hotspot persistente' if g['hotspot']['persistente'] else ''
        ocorrencias = 'ocorrência' if g['resumo']['total'] == 1 else 'ocorrências'
        dias = 'dia observado' if g['resumo']['dias'] == 1 else 'dias observados'
        with st.expander(f"{g['nome']} · {g['resumo']['recente']['nivel_informado']}{selo}"):
            resumo_grupo(g['resumo'])
            mostrar_hotspot(g['registros'], compacto=True)
            st.link_button('Ver histórico completo do local', link_local(g['id']))
            if st.button('Ver observações deste período', key=f'abrir-{g["id"]}'):
                st.session_state['mapa-local-aberto'] = g['id']
            if st.session_state.get('mapa-local-aberto') == g['id']:
                historico_local(g['resumo'], revisados, f'lista-{g["id"]}-{periodo}')

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
            responsavel = st.text_input('Responsável da equipe', key='equipe-responsavel', max_chars=100)
            with st.expander('1 · Revisar novos registros', expanded=True):
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
                    mostrar_evidencia(registro)
                    st.image(foto, caption='Foto enviada')
                    revisor = responsavel
                    from corpos_hidricos import listar_corpos
                    corpos = {c['id']: c for c in listar_corpos()}
                    opcoes = [None, *corpos]
                    sugerido = registro.get('waterbody_id')
                    corpo_id = st.selectbox('Confirmar corpo hídrico do relato', opcoes,
                        index=opcoes.index(sugerido) if sugerido in opcoes else 0,
                        format_func=lambda i: f"{i} · {corpos[i]['nome']}" if i else 'Ainda não identificado',
                        key=f'revisao-corpo-{escolhido}')
                    sim_decisao, justificativa = None, ''
                    if (registro.get('similaridade') or {}).get('quantidade'):
                        st.warning('Compare as imagens antes de considerar esta foto uma observação independente.')
                        for candidata in registro['similaridade'].get('candidatas', []):
                            if st.checkbox(f"Ver evidência anterior {candidata['id'][:8]}", key=f"comparar-{escolhido}-{candidata['id']}"):
                                try:
                                    anterior, foto_anterior, _ = obter_foto(candidata['id'])
                                    st.image(foto_anterior, caption=f"Registro anterior: {anterior['registrado_em'][:16]}")
                                except ValueError:
                                    st.info('Evidência anterior indisponível.')
                        sim_decisao = st.selectbox('Decisão sobre similaridade', [None, 'independente', 'reutilizada'],
                            format_func=lambda i: {None: 'Não resolvida', 'independente': 'Nova observação / falso positivo',
                                                   'reutilizada': 'Imagem reutilizada'}[i], key=f'sim-decisao-{escolhido}')
                        justificativa = st.text_input('Justificativa da decisão de similaridade', max_chars=500, key=f'sim-just-{escolhido}')
                    col1, col2 = st.columns(2)
                    decisao = 'validado' if col1.button('Validar relato', type='primary') else 'rejeitado' if col2.button('Rejeitar relato') else None
                    if decisao:
                        try:
                            revisar_foto(escolhido, decisao, revisor, corpo_id, sim_decisao, justificativa)
                            st.success('Revisão salva.')
                            st.rerun()
                        except Exception as exc:
                            logging.exception('Falha ao revisar relato')
                            st.error(f'Não foi possível salvar a revisão: {exc}')

            with st.expander('2 · Cadastrar ou vincular corpos hídricos'):
                gestao_catalogo(todos, responsavel)
            from acompanhamento_visual import equipe_acompanhamento
            with st.expander('3 · Planejar monitoramento ou registrar ações'):
                equipe_acompanhamento(todos, responsavel)

rodape()
