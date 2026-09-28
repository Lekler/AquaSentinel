import streamlit as st
from registro_visual import cabecalho, rodape
from editorial import espaco_foto

cabecalho('Sobre o AquaSentinela', 'Ciência cidadã para conhecer e cuidar das nossas águas.', False,
          'About AquaSentinela', 'Citizen science to understand and care for our waters.', '/sobre')
with st.container(border=True):
    st.subheader('O problema que nos reúne')
    st.write('Resíduos em rios, canais e na Baía de Guanabara precisam ser observados ao longo do tempo. '
             'Uma fotografia mostra um recorte: sozinha, não descreve todo o corpo hídrico nem sua condição atual.')
    st.subheader('Nosso propósito')
    st.write('Conectar fotografias, localização, revisão e histórico para tornar as observações ambientais '
             'mais organizadas e úteis à participação social, à pesquisa e ao planejamento de ações.')
a, b = st.columns(2)
with a, st.container(border=True):
    st.subheader('Ciência cidadã · citizen science')
    st.write('Moradores, estudantes e pessoas que circulam pelo território podem contribuir com observações. '
             'A contribuição ganha contexto com metodologia, rastreabilidade e revisão humana. '
             'Mais envios não significam automaticamente mais poluição.')
with b, st.container(border=True):
    st.subheader('IA como apoio')
    st.write('O modelo identifica objetos visíveis na imagem e apresenta contagens e confiança. '
             'Pode omitir ou confundir objetos. A equipe revisa a evidência antes da publicação; '
             'a IA não comprova autenticidade, bloqueio do canal ou contaminação.')
with st.container(border=True):
    st.subheader('One Health · um contexto compartilhado')
    st.write('O projeto aproxima o cuidado com o ambiente, a fauna e a dimensão humana. '
             'Os sinais registrados são observações ambientais, sem diagnóstico médico ou veterinário.')
    for col, titulo, texto in zip(st.columns(3), ['Ambiente', 'Fauna / ecossistema', 'Dimensão humana'], [
        'Água, margens, resíduos e sinais visíveis no território.',
        'Vegetação, aves, fauna aquática e animais próximos aos resíduos.',
        'Participação, educação ambiental e segurança de quem observa.']):
        col.markdown(f'**{titulo}**')
        col.write(texto)
with st.container(border=True):
    st.subheader('Para quem é')
    st.write('Comunidades, educadores, estudantes, pesquisadores, organizações ambientais e equipes '
             'que precisam acompanhar locais e documentar ações. O uso científico exige considerar '
             'cobertura desigual, revisão e limitações dos índices.')
st.subheader('Nossa equipe')
st.caption('Galeria em preparação. Fotos, nomes e funções serão incluídos após confirmação da equipe.')
for numero, col in enumerate(st.columns(3), 1):
    with col:
        espaco_foto(f'Integrante {numero:02d}', 'Nome e função a inserir')
st.subheader('O projeto em imagens')
temas = [('Equipe', 'Pessoas que constroem o AquaSentinela'),
         ('Baía', 'O território que queremos acompanhar'), ('Campo', 'Observação e trabalho de campo'),
         ('Drones', 'Tecnologia em campo'), ('Desenvolvimento', 'Construção da plataforma'),
         ('Testes', 'Validação e aprendizado')]
for inicio in (0, 3):
    for col, (tema, legenda) in zip(st.columns(3), temas[inicio:inicio+3]):
        with col:
            espaco_foto(tema, legenda)
with st.container(border=True):
    st.subheader('Nossa visão de impacto')
    st.write('Construir memória dos locais, revelar lacunas de observação e apoiar ações acompanhadas '
             'por evidências antes e depois. Essa é uma visão de trabalho, não uma promessa de resultado ambiental.')
    with st.container(horizontal=True):
        st.page_link('app_pages/como_funciona.py', label='Conhecer o fluxo completo', icon=':material/route:')
        st.page_link('app_pages/contato.py', label='Colaborar com o projeto', icon=':material/mail:')
rodape()
