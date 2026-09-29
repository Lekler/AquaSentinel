from pathlib import Path
from interface_idioma import st
from exportacao import gerar_excel, gerar_pacote
from visao import Detector
from i18n import em_ingles, texto

TRIAGEM = {
    'sem_deteccao': 'Nenhum resíduo reconhecido pelo modelo',
    'baixa_confianca': 'Detecções com baixa confiança — revisar',
    'revisao_recomendada': 'Detecções com confiança intermediária — revisar',
    'deteccao_consistente': 'Detecções com confiança média alta',
}

TRIAGEM_EN = {
    'sem_deteccao': 'No waste recognized by the model',
    'baixa_confianca': 'Low-confidence detections — review',
    'revisao_recomendada': 'Intermediate-confidence detections — review',
    'deteccao_consistente': 'High-confidence detections',
}


@st.cache_resource(max_entries=1, show_spinner=False)
def carregar_detector():
    return Detector(Path(__file__).parent / 'models' / 'best.pt')


def mostrar_analise(analise, anotada, exibir_imagem=True, titulo=True, aviso=True):
    from collections import Counter
    if titulo:
        st.subheader(texto('Resultado da análise', 'Analysis result'))
    if not analise.get('total'):
        st.info(texto('Nenhum resíduo foi identificado automaticamente nesta imagem. O registro ainda poderá ser analisado durante a revisão.',
                      'No waste was automatically identified in this image. The report can still be assessed during review.'))
    else:
        with st.container(horizontal=True):
            st.metric(texto('Itens identificados', 'Items identified'), analise['total'], border=True)
            media = analise.get('confianca_media')
            if media is not None:
                st.metric(texto('Confiança da IA', 'AI confidence'), f'{media:.1f}%', border=True)
        classes = Counter(d['classe_pt'] for d in analise.get('itens', []))
        from interface_idioma import traduzir
        st.write(texto('Classes identificadas: ', 'Identified classes: ') + ', '.join(f'{traduzir(c)} ({n})' for c,n in classes.items()))
        if aviso:
            st.caption(texto('A equipe revisará o registro antes de publicar no mapa.', 'The team will review the report before publishing it on the map.'))
    if exibir_imagem:
        st.image(anotada, caption=texto('Identificação pela IA', 'AI identification'))


def downloads(registro, foto, anotada, prefixo):
    with st.container(horizontal=True, horizontal_alignment='right'):
        st.download_button(texto('Baixar foto identificada', 'Download identified photo'), anotada,
            file_name=f"aquasentinela-{registro['id'][:8]}-identificada.jpg",
            mime='image/jpeg', icon=':material/image:', key=f'{prefixo}_imagem')
        st.download_button(texto('Baixar Excel', 'Download Excel'), gerar_excel(registro),
            file_name=f"aquasentinela-{registro['id'][:8]}.xlsx",
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            icon=':material/table_view:', key=f'{prefixo}_excel')
    with st.expander(texto('Outros arquivos · pacote completo', 'Other files · complete package')):
        if st.button(texto('Preparar pacote com fotos e recortes', 'Prepare photo and crop package'), key=f'{prefixo}_preparar'):
            with st.spinner(texto('Preparando evidências…', 'Preparing evidence…')):
                st.session_state.pacote_foto = (registro['id'], gerar_pacote(registro, foto, anotada))
        pacote = st.session_state.get('pacote_foto')
        if pacote and pacote[0] == registro['id']:
            st.download_button(texto('Baixar pacote ZIP', 'Download ZIP package'), pacote[1], file_name=f"aquasentinela-{registro['id'][:8]}.zip",
                               mime='application/zip', key=f'{prefixo}_zip')


def abrir_ari(registro):
    st.session_state.foto_para_ari = registro
    for chave in ('resultado', 'erro', 'identidade_ocorrencia', 'ocorrencia_id'):
        st.session_state.pop(chave, None)
    st.switch_page('painel_ari.py')
