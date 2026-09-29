"""Address/CEP search reused by photo reporting and planned segments."""
from interface_idioma import st
from i18n import texto
from enderecos import buscar_endereco


def _escolher(contexto):
    from localizacao import aplicar_posicao
    resultados = st.session_state.get(f'{contexto}-enderecos') or []
    indice = st.session_state.get(f'{contexto}-endereco-selecionado', 0)
    if isinstance(indice, int) and 0 <= indice < len(resultados):
        aplicar_posicao(resultados[indice], contexto)
        if contexto == 'foto' and not st.session_state.get('foto_salva_id'):
            nome = st.session_state.get('foto_nome', '')
            if not nome.strip() or nome == st.session_state.get('foto-endereco-nome-auto'):
                nome = resultados[indice]['label'][:100]
                st.session_state['foto_nome'] = nome
                st.session_state['foto-endereco-nome-auto'] = nome


def busca_endereco(contexto='foto', compacto=False):
    bloqueado = contexto == 'foto' and bool(st.session_state.get('foto_salva_id'))
    with st.form(f'buscar-endereco-{contexto}', border=False):
        if compacto:
            campo, acao = st.columns([3, 1.25], vertical_alignment='bottom')
        else:
            campo = acao = st.container()
        with campo:
            consulta = st.text_input(texto('CEP ou endereço completo', 'Postal code or full address'),
                placeholder=texto('Ex.: 21941-901 ou rua, número, cidade e estado', 'Example: 21941-901 or street, number, city and state'),
                max_chars=180, key=f'{contexto}-endereco-busca', disabled=bloqueado)
        with acao:
            buscar = st.form_submit_button(texto('Buscar endereço', 'Find address'), disabled=bloqueado, width='stretch')
    mudou = False
    if buscar:
        st.session_state.pop(f'{contexto}-enderecos', None)
        st.session_state.pop(f'{contexto}-endereco-selecionado', None)
        try:
            with st.spinner(texto('Buscando local…', 'Finding location…')):
                resultados = buscar_endereco(consulta)
            st.session_state[f'{contexto}-enderecos'] = resultados
            if resultados:
                _escolher(contexto)
                mudou = True
            else:
                st.info(texto('Nenhum local encontrado. Inclua cidade e estado, use o GPS ou escolha no mapa.',
                              'No location found. Include city and state, use GPS or choose on the map.'))
        except ValueError as exc:
            st.warning(str(exc))
    resultados = st.session_state.get(f'{contexto}-enderecos') or []
    if resultados:
        st.selectbox(texto('Locais sugeridos', 'Suggested locations'), range(len(resultados)),
            format_func=lambda i:resultados[i]['label'], key=f'{contexto}-endereco-selecionado',
            on_change=lambda:_escolher(contexto), disabled=bloqueado)
        st.caption(texto('A busca sugere uma referência aproximada. Confira e ajuste o marcador; o CEP não identifica o ponto exato.',
                         'Search suggests an approximate reference. Check and adjust the marker; a postal code does not identify the exact point.'))
    st.caption(texto('Ao buscar, o endereço é consultado em Photon / © OpenStreetMap; CEP em ViaCEP.',
                     'Search uses Photon / © OpenStreetMap for addresses and ViaCEP for postal codes.'))
    return mudou
