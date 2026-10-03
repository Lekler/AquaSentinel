from interface_idioma import st
from registro_visual import cabecalho, rodape
from pathlib import Path
from i18n import texto as traduz

cabecalho('Sobre o AquaSentinel', 'Um jeito de observar, registrar e cuidar das nossas águas, com a participação de todos.', False,
          'About AquaSentinel', 'A way to observe, record and care for our waters, with everyone taking part.', '/sobre')
sobre, trabalho = st.tabs([traduz('Sobre o AquaSentinel', 'About AquaSentinel'), traduz('Conheça nosso trabalho', 'Get to know our work')])
with sobre:
    with st.container(border=True):
        st.subheader('Por que esse projeto existe?')
        st.write('O lixo nos rios, canais e na Baía de Guanabara prejudica a paisagem, afeta a vida dos animais e torna mais difícil cuidar desses espaços. Muitas vezes, o problema é visto por quem vive ou passa por perto, mas essas observações ficam dispersas. O AquaSentinel nasceu para reunir esses registros, acompanhar o que acontece em cada local ao longo do tempo e ajudar comunidades, pesquisadores e equipes responsáveis a planejar ações de cuidado e limpeza.')
        st.subheader('O que queremos fazer?')
        st.write('O AquaSentinel reúne fotos, locais e datas dos registros para ajudar a acompanhar o lixo visível nas águas. As imagens passam por uma análise de IA e pela revisão da equipe antes de serem publicadas. Com o tempo, esse histórico pode apoiar a participação da comunidade, a pesquisa e o planejamento de ações.')
    a, b = st.columns(2)
    with a, st.container(border=True):
        st.subheader('Sua participação faz a diferença!')
        st.write('Você conhece um rio, canal ou trecho da Baía de Guanabara que precisa de atenção? Sua foto pode ajudar a dar visibilidade ao que acontece ali. Participe do AquaSentinel e ajude a transformar o seu olhar sobre a cidade em um convite para cuidar das nossas águas.')
    with b, st.container(border=True):
        st.subheader('Como a tecnologia ajuda?')
        st.write('Você tira uma foto, e a inteligência artificial ajuda a identificar os resíduos visíveis na imagem. Assim, sua observação se transforma em um registro que pode ser acompanhado junto com outros feitos na região. A equipe confere os resultados para que as informações apresentadas sejam claras e confiáveis.')
    with st.container(border=True):
        st.subheader('Cuidar da água também é cuidar da vida!')
        st.write('O projeto segue a ideia de Saúde Única (One Health): o ambiente, os animais e as pessoas estão ligados. Nossos registros ajudam a observar sinais no ambiente e a incentivar o cuidado com esses espaços!')
        for col, titulo, texto in zip(st.columns(3), ['Ambiente', 'Animais e natureza', 'Pessoas'], [
            'Observamos as águas, as margens e os resíduos que aparecem nas imagens.',
            'Prestamos atenção à vegetação e aos animais que vivem nesses locais ou circulam perto dos resíduos.',
            'Incentivamos a participação, a educação ambiental e o cuidado com a segurança de quem faz os registros.']):
            col.markdown(f'**{titulo}**')
            col.write(texto)
    with st.container(border=True):
        st.subheader('Para quem é o AquaSentinel?')
        st.write('Para comunidades, educadores, estudantes, pesquisadores, organizações ambientais e equipes que desejam acompanhar lugares ao longo do tempo e registrar suas ações.')
    with st.container(border=True):
        st.subheader('O que queremos transformar')
        st.write('Queremos que cada registro ajude a contar a história de um lugar: onde o lixo aparece, quais áreas ainda precisam de atenção e o que muda depois de uma ação de limpeza. Ao acompanhar essas informações ao longo do tempo, fica mais fácil decidir onde agir e observar os resultados.')
        with st.container(horizontal=True):
            st.page_link('app_pages/como_funciona.py', label='Conhecer o fluxo completo', icon=':material/route:')
            st.page_link('app_pages/contato.py', label='Colaborar com o projeto', icon=':material/mail:')

with trabalho:
    st.subheader('Nossa equipe')
    st.html('<style>.st-key-fotos-equipe [data-testid="stImage"] img {height:320px;object-fit:contain;object-position:center;background:#f5fbfc;border-radius:12px}</style>')
    fotos = sorted((Path(__file__).resolve().parents[1] / 'assets' / 'equipe').glob('*.jpeg'))
    with st.container(key='fotos-equipe'):
        for inicio in range(0, len(fotos), 3):
            for col, foto in zip(st.columns(3), fotos[inicio:inicio + 3]):
                with col, st.container(border=True):
                    st.image(str(foto), width='stretch')
                    st.markdown(f'**{foto.stem}**')

rodape()
