"""Acervo versionado: inferência real, referências geográficas atribuídas.

Mantido fora dos relatos de campo, da revisão humana, WPS e recorrência.
Não depende de SQLite persistente nem executa o modelo ao abrir o mapa.
"""
import json
from pathlib import Path

PASTA = Path(__file__).resolve().parent / 'assets' / 'acervo'


def listar_acervo():
    arquivo = PASTA / 'registros.json'
    return json.loads(arquivo.read_text(encoding='utf-8')) if arquivo.exists() else []


def obter_imagens(registro):
    # IDs só podem vir do manifesto versionado, nunca de um caminho do cliente.
    ident = registro['id']
    if ident not in {r['id'] for r in listar_acervo()}:
        raise ValueError('Imagem não pertence ao acervo.')
    return ((PASTA / f'{ident}.jpg').read_bytes(),
            (PASTA / f'{ident}-ia.jpg').read_bytes())


def mostrar_acervo():
    import pydeck as pdk
    from interface_idioma import st
    from i18n import texto
    from mapa_base import estilo_url
    from interface_fotos import downloads

    registros = listar_acervo()
    if not registros:
        st.info(texto('Nenhuma imagem no acervo.', 'No images in the collection.'))
        return
    busca = st.text_input(texto('Buscar por local ou imagem', 'Search by location or image'), key='acervo-busca')
    from corpos_hidricos import normalizar
    filtrados = [r for r in registros if normalizar(busca) in normalizar(r['nome'] + ' ' + r['titulo'])]
    if not filtrados:
        st.info(texto('Nenhum resultado para essa busca.', 'No results for this search.'))
        return
    a, b = st.columns(2)
    a.metric(texto('Imagens no acervo', 'Collection images'), len(filtrados))
    b.metric(texto('Itens identificados nas imagens', 'Items identified in images'), sum(r['total'] for r in filtrados))
    pontos = [{'id': r['id'], 'latitude': r['latitude'], 'longitude': r['longitude'],
               'local': r['nome'], 'titulo': r['titulo'], 'total': r['total']} for r in filtrados]
    vista = (pdk.ViewState(latitude=filtrados[0]['latitude'], longitude=filtrados[0]['longitude'], zoom=13)
             if len(filtrados) == 1 else
             pdk.data_utils.compute_view([[r['longitude'], r['latitude']] for r in filtrados], view_proportion=1))
    vista.pitch = 0
    vista.zoom = min(vista.zoom, 13)
    evento = st.pydeck_chart(pdk.Deck(map_style=estilo_url(), map_provider='maplibre',
        initial_view_state=vista, layers=[pdk.Layer('ScatterplotLayer', id='acervo', data=pontos,
            get_position='[longitude, latitude]', get_fill_color=[0, 164, 185],
            get_radius=10, radius_units='pixels', radius_min_pixels=10, radius_max_pixels=10,
            stroked=True, get_line_color=[255, 255, 255], line_width_min_pixels=2, pickable=True)],
        tooltip={'text': '{local}\n{titulo}\n{total} itens identificados'}),
        on_select='rerun', selection_mode='single-object', key='acervo-mapa')
    por_id = {r['id']: r for r in filtrados}
    selecao = evento.selection.get('objects', {}).get('acervo', [])
    clicado = selecao[0].get('id') if selecao else None
    # Atualiza uma vez por clique, permitindo também navegar pelo seletor.
    if clicado in por_id and clicado != st.session_state.get('acervo-ultimo-clique'):
        st.session_state['acervo-foto'] = clicado
        st.session_state['acervo-ultimo-clique'] = clicado
    if st.session_state.get('acervo-foto') not in por_id:
        st.session_state['acervo-foto'] = next(iter(por_id))
    escolhido = st.selectbox(texto('Imagem e local de referência', 'Image and reference location'), list(por_id),
        format_func=lambda ident: por_id[ident]['nome'] + ' — ' + por_id[ident]['titulo'], key='acervo-foto')
    r = por_id[escolhido]
    foto, anotada = obter_imagens(r)
    st.subheader(r['titulo'])
    st.caption(r['nome'])
    original, identificada = st.columns(2)
    original.image(foto, caption=texto('Foto original', 'Original photo'), width='stretch')
    identificada.image(anotada, caption=texto('Identificação pela IA', 'AI identification'), width='stretch')
    a, b, c = st.columns(3)
    a.metric(texto('Itens identificados', 'Items identified'), r['total'])
    b.metric(texto('Detecções do modelo', 'Model detections'), r['deteccoes_modelo'])
    c.metric(texto('Confiança média da IA', 'Mean AI confidence'),
             '—' if r['confianca_media'] is None else f"{r['confianca_media']:.1f}%")
    downloads(r, foto, anotada, 'acervo-' + r['id'])
    with st.expander(texto('Detalhes das identificações', 'Detection details')):
        st.dataframe([{'ID': d['item_id'], 'Classe': d['classe_pt'], 'Confiança (%)': d['confidence_pct']}
                      for d in r['itens']], hide_index=True)
