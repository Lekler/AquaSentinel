"""Sessões estruturadas com recibo privado; listagem pública somente após revisão."""
import streamlit as st
from monitoramento import (listar_entidades, iniciar_sessao, sessao_autorizada,
                           encerrar_sessao, metricas_sessao)
from relatos import listar_fotos
from registro_visual import cabecalho, rodape

cabecalho('Monitoramento estruturado', 'Sessões com trecho, duração e extensão observada.',
          False, 'Structured monitoring', 'Sessions with segment, duration and observed length.', '/monitoramento')
st.info('Registros oportunísticos são fotos avulsas. Uma sessão estruturada tem trecho e tempo definidos. '
        'As taxas abaixo não são calculadas para envios oportunísticos.')
trechos = {t['id']: t for t in listar_entidades('trecho')}
with st.expander('Iniciar sessão de monitoramento', expanded=not st.session_state.get('monitor_id')):
    if trechos:
        trecho = st.selectbox('Trecho planejado', list(trechos),
            format_func=lambda i:f"{trechos[i]['waterbody_id']} · {trechos[i]['nome']}")
        st.caption(f"Extensão planejada: {trechos[trecho]['extensao_m']:g} m. Informe a extensão realmente observada ao encerrar.")
        consentimento = st.checkbox('Autorizo publicar os dados da sessão após revisão.')
        if st.button('Iniciar sessão', disabled=bool(st.session_state.get('monitor_id'))):
            try:
                s, chave = iniciar_sessao(trecho, consentimento)
                st.session_state.update(monitor_id=s['id'], monitor_chave=chave)
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
    else:
        st.info('A equipe precisa cadastrar corpos hídricos e trechos planejados na área de revisão do mapa.')
with st.expander('Retomar sessão pelo código'):
    ident = st.text_input('ID da sessão', key='retomar-id')
    chave = st.text_input('Código privado da sessão', type='password', key='retomar-chave')
    if st.button('Retomar sessão'):
        try:
            sessao_autorizada(ident, chave)
            st.session_state.update(monitor_id=ident, monitor_chave=chave)
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
todos = listar_fotos()
if st.session_state.get('monitor_id'):
    try:
        s = sessao_autorizada(st.session_state.monitor_id, st.session_state.monitor_chave)
        st.subheader(s['trecho_nome'])
        st.text(f"{s['waterbody_id']} · início {s['inicio']} · {s['status']}")
        st.download_button('Guardar recibo da sessão', f"ID: {s['id']}\nCódigo privado: {st.session_state.monitor_chave}\n",
                           file_name=f"sessao-{s['id'][:8]}.txt", mime='text/plain')
        st.caption('Guarde o recibo para retomar a sessão após fechar o navegador. Não compartilhe o código privado.')
        m = metricas_sessao(s, todos)
        st.metric('Fotos vinculadas', m['fotos'])
        if s['status'] == 'em andamento':
            st.page_link('app_pages/registrar.py', label='Adicionar foto à sessão', icon=':material/photo_camera:')
            metros = st.number_input('Extensão efetivamente observada (m)', .1, 100000., value=100.)
            cobertura = st.checkbox('Observei o trecho informado e evitei fotografar os mesmos itens em fotos sobrepostas.')
            zero = st.checkbox('Observei o trecho e nenhum resíduo foi visto (não significa ausência de dado).')
            if st.button('Encerrar sessão'):
                try:
                    encerrar_sessao(s['id'], st.session_state.monitor_chave, metros, cobertura, zero)
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
        else:
            st.text(f"Duração: {s['duracao_min']:.1f} min · extensão: {s['extensao_observada_m']:g} m · revisão: {s['revisao']}")
            st.success('Sessão encerrada e disponível para revisão.')
        if st.button('Sair desta sessão no navegador'):
            st.session_state.pop('monitor_id', None); st.session_state.pop('monitor_chave', None)
            st.rerun()
    except ValueError as exc:
        st.error(str(exc))
st.subheader('Sessões públicas revisadas')
linhas = []
for s in listar_entidades('sessao'):
    if s.get('status') != 'encerrada' or s.get('revisao') != 'validado' or not s.get('consentimento_publicacao'):
        continue
    m = metricas_sessao(s, todos)
    linhas.append({'Trecho':s['trecho_nome'], 'Corpo hídrico':s['waterbody_id'], 'Início':s['inicio'],
                   'Duração (min)':round(s['duracao_min'], 1), 'Extensão (m)':s['extensao_observada_m'],
                   'Fotos':m['fotos'], 'Fotos validadas':m['fotos_validadas'],
                   'Sem resíduos observados':s['sem_residuos'], 'Itens/m':m['itens_m'],
                   'Itens/100 m':m['itens_100m'], 'Itens/min de sessão':m['itens_min']})
if linhas:
    st.dataframe(linhas, hide_index=True, width='stretch')
else:
    st.info('Ainda não há sessões públicas revisadas.')
st.caption('Itens são detecções somadas nas fotos, não objetos únicos garantidos. Taxas exigem sessão validada, '
           'cobertura declarada e todas as fotos validadas sem similaridade pendente/reutilização. '
           'Campo vazio é indisponível, não zero. Duração é o intervalo entre início e encerramento da sessão.')
rodape()
