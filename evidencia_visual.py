"""Explicações de evidência e persistência, com critérios sempre consultáveis."""
from interface_idioma import st
from aquaverify import avaliar, explicar, AVISO
from hotspots import avaliar_hotspot


def mostrar_evidencia(registro):
    from equipe_auth import autenticado
    if not autenticado():
        return
    from resultado_visual import evidencia
    evidencia(registro)


def mostrar_hotspot(registros, compacto=False):
    h = avaliar_hotspot(registros)
    if not compacto:
        st.markdown('#### Hotspot persistente' if h['persistente'] else '#### Ainda sem persistência confirmada')
    ultima = ('hoje' if h['ultima_dias'] == 0 else f"há {h['ultima_dias']} dias") if h['ultima_dias'] is not None else 'indisponível'
    with st.expander('Entender a persistência'):
        st.write('A persistência procura sinais repetidos ao longo do tempo. Uma foto isolada não é suficiente.')
        st.caption('Avaliação dos últimos 90 dias. Mais envios não significam mais poluição; '
                   'a ausência de selo não garante ausência de resíduos.')
        st.write(f"Observações consideradas: {h['ocorrencias']} · Dias observados: {h['dias']} · Última observação: {ultima}")
        from equipe_auth import autenticado
        if not autenticado():
            return
        st.write(f"Evidências elegíveis: {h['elegiveis']} · dias com resíduos: {h['dias_residuos']} · "
                 f"intervalo: {h['amplitude_dias']} dias · recorrência: {h['recorrencia']}% · "
                 f"WPS mediano: {h['wps_mediano']} · AquaVerify mediano: {h['qualidade_mediana']}")
        st.dataframe([{'Critério': nome, 'Atendido': 'Sim' if ok else 'Não'}
                      for nome, ok in h['criterios'].items()], hide_index=True, width='stretch')
        st.caption('Exige revisão e corpo hídrico confirmado, AquaVerify ≥ 60, índice histórico completo '
                   'e nenhuma similaridade pendente. A observação mais recente de cada dia tem um voto; '
                   'fotos idênticas/reutilizadas não ampliam a persistência. Os limiares são heurísticos.')


def gestao_catalogo(todos, responsavel=None):
    """Chamado exclusivamente após autenticação da equipe de revisão."""
    from equipe_auth import autenticado
    if not autenticado():
        return
    from i18n import texto
    from corpos_hidricos import listar_corpos, cadastrar_corpo, atualizar_corpo, TIPOS
    from relatos import vincular_corpo, indexar_fotos_antigas, resolver_similaridade, obter_foto
    st.caption(texto('Cadastre o rio, canal, lagoa ou baía. Os códigos WB-BG são internos ao projeto.', 'Register the river, canal, lagoon or bay. WB-BG codes are internal to the project.'))
    if responsavel is None:
        responsavel = st.text_input('Responsável da equipe', key='cadastro-responsavel', max_chars=100)
    nome = st.text_input('Nome padronizado do corpo hídrico', key='cadastro-corpo', max_chars=100)
    tipo = st.selectbox(texto('Tipo', 'Type'), TIPOS, key='cadastro-tipo')
    obs = st.text_area(texto('Observação opcional', 'Optional note'), max_chars=500, key='cadastro-observacao')
    if st.button('Cadastrar corpo hídrico'):
        try:
            corpo = cadastrar_corpo(nome, responsavel, tipo, obs)
            st.success(f"Cadastrado: {corpo['id']} · {corpo['nome']}")
        except ValueError as exc:
            st.error(str(exc))
    catalogo = listar_corpos()
    if catalogo:
        st.dataframe(catalogo, hide_index=True)
        with st.expander(texto('Editar cadastro existente', 'Edit existing water body')):
            por_corpo = {c['id']:c for c in catalogo}
            editar = st.selectbox(texto('Corpo hídrico', 'Water body'), list(por_corpo),
                format_func=lambda i:f"{i} — {por_corpo[i]['nome']}", key='editar-corpo')
            atual = por_corpo[editar]
            st.caption(texto('O ID permanece o mesmo; os vínculos e o histórico são preservados.', 'The ID stays unchanged; links and history are preserved.'))
            novo_nome = st.text_input(texto('Nome', 'Name'), value=atual['nome'], max_chars=100, key=f'corpo-nome-{editar}')
            novo_tipo = st.selectbox(texto('Tipo', 'Type'), TIPOS, index=TIPOS.index(atual['tipo']), key=f'corpo-tipo-{editar}')
            nova_obs = st.text_area(texto('Observação opcional', 'Optional note'), value=atual['observacao'], max_chars=500, key=f'corpo-obs-{editar}')
            if st.button(texto('Salvar alterações do corpo hídrico', 'Save water body changes')):
                try:
                    atualizar_corpo(editar, novo_nome, responsavel, novo_tipo, nova_obs)
                    st.rerun()
                except ValueError as exc:st.error(str(exc))
    if todos:
        por_id = {r['id']: r for r in todos}
        ident = st.selectbox('Registro para vincular ao corpo hídrico', list(por_id),
            format_func=lambda i: f"{por_id[i]['nome']} · {por_id[i]['registrado_em'][:10]} · {i[:8]}", key='vinculo-relato')
        corpos = {c['id']: c for c in catalogo}
        corpo_id = st.selectbox('Corpo hídrico confirmado', [None, *corpos],
            format_func=lambda i: f"{i} · {corpos[i]['nome']}" if i else 'Selecione um corpo hídrico cadastrado', key='vinculo-corpo')
        if st.button('Confirmar vinculação deste registro'):
            try:
                vincular_corpo(ident, corpo_id, responsavel)
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
        if (por_id[ident].get('similaridade') or {}).get('quantidade'):
            if st.checkbox('Comparar evidências do registro existente', key=f'comparar-antigo-{ident}'):
                _, foto, _ = obter_foto(ident)
                st.image(foto, caption='Foto deste registro')
                for candidata in por_id[ident]['similaridade'].get('candidatas', []):
                    try:
                        anterior, foto, _ = obter_foto(candidata['id'])
                        st.image(foto, caption=f"Anterior: {anterior['registrado_em'][:16]} · {candidata['tipo']}")
                    except ValueError:
                        st.info('Uma evidência anterior está indisponível.')
            decisao = st.selectbox('Similaridade do registro existente', ['independente', 'reutilizada'],
                index=None, placeholder='Selecione após conferir as fotos', key=f'decisao-antigo-{ident}')
            motivo = st.text_input('Justificativa para o registro existente', max_chars=500, key=f'just-antigo-{ident}')
            if st.button('Salvar decisão de similaridade'):
                try:
                    resolver_similaridade(ident, decisao, responsavel, motivo)
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
    with st.expander('Ferramentas avançadas de imagens antigas'):
        faltantes = sum(not r.get('phash') for r in todos)
        st.caption(f'{faltantes} foto(s) antigas sem pHash. A indexação consulta apenas fotos já no banco.')
        if st.button('Indexar / reavaliar similaridade das fotos antigas'):
            try:
                total = indexar_fotos_antigas()
                st.success(f'{total} foto(s) indexadas neste lote (até 100). Atualize a página; repita se houver pendências.')
            except Exception:
                import logging
                logging.exception('Falha ao indexar fotos antigas')
                st.error('Não foi possível concluir a indexação. Nenhuma alteração deste lote foi salva.')
