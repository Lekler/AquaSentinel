"""Explicações de evidência e persistência, com critérios sempre consultáveis."""
import streamlit as st
from aquaverify import avaliar, explicar, AVISO
from hotspots import avaliar_hotspot


def mostrar_evidencia(registro):
    q = avaliar(registro)
    st.markdown('#### AquaVerify / Qualidade da Evidência')
    st.write(f"**Qualidade da evidência {q['faixa']} · {q['indice']:.1f}/100**")
    st.caption(AVISO)
    st.dataframe(q['criterios'], hide_index=True, width='stretch')
    st.caption('Rubrica experimental v1: alta ≥ 75, média ≥ 45, baixa < 45. '
               'Pesos e limiares não foram calibrados como probabilidade.')
    texto, motivos = explicar(registro)
    st.write(texto)
    for motivo in motivos:
        st.write('• ' + motivo)
    if (registro.get('similaridade') or {}).get('quantidade'):
        st.warning('Esta imagem parece semelhante a uma anterior. A equipe deve verificar se é '
                   'uma nova observação, reutilização ou falso positivo. Isso não comprova fraude.')


def mostrar_hotspot(registros):
    h = avaliar_hotspot(registros)
    st.markdown('#### Hotspot persistente' if h['persistente'] else '#### Persistência em acompanhamento')
    ultima = ('hoje' if h['ultima_dias'] == 0 else f"há {h['ultima_dias']} dias") if h['ultima_dias'] is not None else 'indisponível'
    st.write(f"**{h['ocorrencias']} ocorrências · {h['dias']} dias diferentes · última observação {ultima}**")
    st.caption('Janela própria de 90 dias, independente do filtro do mapa. '
               'Classificação experimental de persistência observada; não é previsão nem alerta ambiental. '
               'Mais uploads não significam mais poluição. Ausência do selo não comprova ausência de problema.')
    with st.expander('Por que recebeu ou não o selo de persistência?'):
        st.write(f"Evidências elegíveis: {h['elegiveis']} · dias com resíduos: {h['dias_residuos']} · "
                 f"intervalo: {h['amplitude_dias']} dias · recorrência: {h['recorrencia']}% · "
                 f"WPS mediano: {h['wps_mediano']} · AquaVerify mediano: {h['qualidade_mediana']}")
        st.dataframe([{'Critério': nome, 'Atendido': 'Sim' if ok else 'Não'}
                      for nome, ok in h['criterios'].items()], hide_index=True, width='stretch')
        st.caption('Exige revisão e corpo hídrico confirmado, AquaVerify ≥ 60, índice histórico completo '
                   'e nenhuma similaridade pendente. A observação mais recente de cada dia tem um voto; '
                   'fotos idênticas/reutilizadas não ampliam a persistência. Os limiares são heurísticos.')


def gestao_catalogo(todos):
    """Chamado exclusivamente após autenticação da equipe de revisão."""
    from corpos_hidricos import listar_corpos, cadastrar_corpo
    from relatos import vincular_corpo, indexar_fotos_antigas, resolver_similaridade, obter_foto
    st.markdown('#### Cadastro de corpos hídricos e evidências antigas')
    st.caption('Códigos WB-BG são internos ao projeto, não identificadores oficiais. '
               'Inclua município/trecho no nome para distinguir corpos hídricos homônimos.')
    responsavel = st.text_input('Responsável pelo cadastro/vinculação', key='cadastro-responsavel', max_chars=100)
    nome = st.text_input('Nome padronizado do corpo hídrico', key='cadastro-corpo', max_chars=100)
    if st.button('Cadastrar corpo hídrico'):
        try:
            corpo = cadastrar_corpo(nome, responsavel)
            st.success(f"Cadastrado: {corpo['id']} · {corpo['nome']}")
        except ValueError as exc:
            st.error(str(exc))
    catalogo = listar_corpos()
    if catalogo:
        st.dataframe(catalogo, hide_index=True)
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
