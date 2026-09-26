import streamlit as st
from i18n import texto
from registro_visual import cabecalho, rodape

cabecalho('Sobre', 'Mais olhos pelos nossos rios.', mostrar_etapas=False,
          titulo_ingles='About', descricao_ingles='More eyes on our rivers.', caminho='/sobre')

with st.container(border=True):
    st.subheader(texto('Uma foto pode fazer a diferença', 'A photo can make a difference'))
    st.write(texto(
        'O AquaSentinela reúne registros com foto e localização para ajudar a identificar resíduos nos rios, canais e na Baía de Guanabara. A participação de cada pessoa ajuda a mostrar os pontos que precisam de atenção.',
        'AquaSentinela brings together photo and location reports to help identify waste in rivers, canals and Guanabara Bay. Everyone can help highlight places that need attention.'))

with st.container(border=True):
    st.subheader(texto('Como funciona', 'How it works'))
    st.markdown(texto(
        '1. Tire uma foto ou envie uma imagem do local.\n2. Aguarde a identificação de resíduos pela IA.\n3. Confira a localização e informe o nível de resíduos observado.\n4. Autorize a publicação e envie a ocorrência para revisão. Após validação pela equipe, ela aparece em **Mapa e registros**.',
        '1. Take a photo or upload an image of the location.\n2. Wait for AI waste identification.\n3. Check the location and report the waste level you observed.\n4. Authorize publication and submit the report for review. After team validation, it appears in **Map and reports**.'))

with st.container(border=True):
    st.subheader(texto('Tecnologia para apoiar o cuidado ambiental', 'Technology to support environmental care'))
    st.write(texto(
        'A inteligência artificial identifica plásticos visíveis e estima a quantidade de itens na foto. A avaliação ambiental · ARI combina informações do local com a previsão de chuva para apoiar a análise.',
        'Artificial intelligence identifies visible plastics and estimates the number of items in a photo. Environmental assessment · ARI combines site information with the rain forecast to support analysis.'))
    st.write(texto(
        'Os resultados precisam de revisão: a IA pode deixar de reconhecer objetos ou confundi-los. A confiança não comprova a autenticidade da foto nem determina, sozinha, a gravidade ambiental.',
        'Results need review: AI may miss or confuse objects. Confidence does not prove photo authenticity or determine environmental severity on its own.'))

if st.button(texto('Registrar ocorrência', 'Report an occurrence'), type='primary'):
    st.switch_page('app_pages/registrar.py')
rodape()
