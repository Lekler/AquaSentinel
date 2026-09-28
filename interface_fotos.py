from pathlib import Path
import pandas as pd
import streamlit as st
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


def mostrar_analise(analise, anotada, exibir_imagem=True):
    st.subheader(texto('Resultado da análise', 'Analysis result'))
    with st.container(horizontal=True):
        st.metric(texto('Itens identificados', 'Items identified'), analise['total'], border=True)
        media = analise['confianca_media']
        st.metric(texto('Confiança média', 'Average confidence'), '—' if media is None else f'{media:.1f}%', border=True)
        st.metric(texto('Caixas duplicadas removidas', 'Duplicate boxes removed'), analise['duplicadas_removidas'], border=True)
    mensagem = (TRIAGEM_EN if em_ingles() else TRIAGEM)[analise['triagem']]
    if analise['triagem'] == 'deteccao_consistente':
        st.success(mensagem)
    else:
        st.warning(mensagem)
    st.caption(texto('A confiança mede o reconhecimento dos objetos. Ela não verifica se a foto é autêntica, recente ou tirada no local informado. Sem detecções não significa ausência de lixo.', 'Confidence measures object recognition. It does not verify that a photo is authentic, recent or taken at the reported location. No detections does not mean there is no waste.'))
    if analise['possivel_limite']:
        st.warning(texto('O limite de detecções foi atingido. Esta contagem pode estar incompleta.', 'The detection limit was reached. This count may be incomplete.'))
    if exibir_imagem:
        st.image(anotada, caption=texto('Identificações nesta fotografia · IDs MAR são locais a este registro.', 'Identifications in this photo · MAR IDs are local to this report.'))
    if analise['itens']:
        st.dataframe(pd.DataFrame([{'ID': d['item_id'], texto('Classe', 'Class'): d['classe_pt'],
                       texto('Confiança (%)', 'Confidence (%)'): d['confidence_pct']} for d in analise['itens']]),
                     hide_index=True, width='stretch')
    with st.container():
        from aquaverify import explicar
        explicacao, motivos = explicar(analise)
        st.write(explicacao)
        for motivo in motivos:
            st.caption(motivo)
        if (analise.get('similaridade') or {}).get('quantidade'):
            st.warning('A imagem parece semelhante a uma anterior. Isso exige conferência humana e não comprova fraude.')
        st.write(texto('O modelo reconhece sacolas, garrafas, embalagens e outros plásticos. Caixas muito sobrepostas são reduzidas a uma identificação, mantendo a mais confiante. Objetos próximos ainda podem se confundir; esta é uma estimativa dos itens visíveis.', 'The model recognizes bags, bottles, packaging and other plastics. Heavily overlapping boxes are reduced to one identification, keeping the most confident one. Nearby objects may still be confused; this is an estimate of visible items.'))
        st.write(texto(f"O modelo retornou {analise['deteccoes_modelo']} detecções após seu filtro interno; {analise['duplicadas_removidas']} caixas foram removidas na deduplicação adicional.", f"The model returned {analise['deteccoes_modelo']} detections after its internal filter; {analise['duplicadas_removidas']} boxes were removed by additional deduplication."))
        st.caption(texto('Média aritmética das confianças dos itens mantidos: abaixo de 60% → baixa; 60 a menos de 80% → intermediária; a partir de 80% → alta. Essas faixas organizam a revisão e não validam a autenticidade ou a gravidade ambiental.', 'Arithmetic mean of retained item confidence: below 60% → low; 60 to below 80% → intermediate; 80% and above → high. These ranges organize review and do not validate authenticity or environmental severity.'))


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
