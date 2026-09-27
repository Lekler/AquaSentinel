"""Rastreabilidade, antes/depois e ferramentas autenticadas de acompanhamento."""
from datetime import datetime, timezone
import streamlit as st
from ciclo import historico_eventos, mudar_etapa, TRANSICOES
from monitoramento import listar_entidades, cadastrar_trecho, metricas_sessao, revisar_sessao
from evolucao import registrar_acao, comparar_acao, TIPOS_ACAO
from observacao import FUSO


def rastreabilidade(r):
    st.markdown('#### Rastreabilidade do registro')
    gps = r.get('gps') or {}
    st.dataframe([{'Campo': nome, 'Valor': str(valor)} for nome, valor in [
        ('ID', r['id']), ('Data de registro', r['registrado_em']),
        ('SHA-256 da imagem', r.get('image_hash', 'Não registrado')),
        ('Modelo', r.get('modelo_arquivo', 'best.pt · nome legado')),
        ('Versão do runtime do modelo', r.get('modelo_runtime', 'Não registrada')),
        ('SHA-256 do modelo', r.get('model_hash', 'Não registrado')),
        ('Versão do aplicativo', r.get('versao_app', 'Legada · não registrada')),
        ('Versão da metodologia', r.get('versao_metodologia', 'Legada · não registrada')),
        ('Método pHash', (r.get('phash') or {}).get('versao', 'Não registrado')),
        ('Data da revisão', r.get('validado_em', 'Aguardando revisão')),
        ('Modo', r.get('modo', 'oportunistico')), ('Sessão', r.get('sessao_id', 'Não se aplica')),
        ('Localização', f"{r['latitude']}, {r['longitude']}"),
        ('Origem da localização', r.get('origem_localizacao', 'Não registrada')),
        ('Precisão GPS declarada (m)', gps.get('accuracy', 'Indisponível') if gps.get('latitude') == r['latitude']
         and gps.get('longitude') == r['longitude'] else 'Indisponível ou coordenadas ajustadas manualmente'),
        ('Revisor', r.get('revisor', 'Aguardando revisão')), ('Status de revisão', r.get('revisao')),
        ('Etapa de acompanhamento', r.get('etapa') or ('validada' if r.get('revisao') == 'validado' else 'aguardando revisão')),
    ]], hide_index=True, width='stretch')
    st.caption('Hashes identificam os arquivos/pixels usados; não comprovam autenticidade, data ou local da captura.')
    st.markdown('#### Ciclo de vida')
    st.dataframe([{'Data': e['data'], 'Etapa': e['etapa'], 'Responsável': e['responsavel'],
                   'Nota': e['nota']} for e in historico_eventos(r)], hide_index=True, width='stretch')


def antes_depois(grupo, registros):
    ids = {r['id'] for r in grupo['registros']}
    acoes = [a for a in listar_entidades('acao') if a['registro_id'] in ids]
    st.subheader('Ações e histórico antes/depois')
    if not acoes:
        st.info('Nenhuma ação registrada neste local. Isso não significa que nenhuma ação ocorreu.')
    for acao in sorted(acoes, key=lambda a: a['data'], reverse=True):
        with st.expander(f"{acao['tipo']} · {acao['data'][:10]} · {acao['responsavel']}"):
            st.text(acao['descricao'])
            lados = comparar_acao(acao, registros)
            for coluna, (nome, lado) in zip(st.columns(2), lados.items()):
                with coluna:
                    st.markdown('#### ' + ('Antes da ação' if nome == 'antes' else 'Depois da ação'))
                    if lado:
                        r = lado['registro']
                        st.text(f"{r['registrado_em'][:16]} · {r['nivel_informado']}")
                        st.metric('WPS', f"{lado['wps']:.1f}")
                        from relatos import obter_foto
                        atual, foto, _ = obter_foto(r['id'])
                        if atual.get('revisao') == 'validado' and atual.get('consentimento_publicacao'):
                            st.image(foto, caption=f"Registro {r['id'][:8]}")
                    else:
                        st.info('Não temos observação pública deste lado da ação.')
            if lados['antes'] and lados['depois']:
                delta = lados['depois']['wps'] - lados['antes']['wps']
                st.write(f'Variação descritiva do WPS: {delta:+.1f} pontos.')
            st.caption('Compara a última observação antes e a primeira depois da ação no mesmo grupo. '
                       'Datas são de registro. Mudanças de enquadramento, frequência e evidência podem alterar '
                       'o resultado; a comparação não demonstra que a ação causou a mudança.')


def equipe_acompanhamento(todos):
    from corpos_hidricos import listar_corpos
    st.markdown('#### Planejamento de trechos e acompanhamento')
    responsavel = st.text_input('Responsável pelas operações', key='operacao-responsavel', max_chars=100)
    corpos = {c['id']: c for c in listar_corpos()}
    with st.expander('Cadastrar trecho no plano de monitoramento'):
        st.caption('Cadastre também trechos sem observações para que apareçam como lacunas. '
                   'O ponto é uma referência; não é a delimitação geográfica de todo o trecho.')
        nome = st.text_input('Nome/descrição do trecho', key='trecho-nome', max_chars=100)
        corpo = st.selectbox('Corpo hídrico do trecho', [None, *corpos], key='trecho-corpo',
            format_func=lambda i: f"{i} · {corpos[i]['nome']}" if i else 'Selecione')
        a,b,c = st.columns(3)
        lat = a.number_input('Latitude de referência', -90., 90., value=-22.9, key='trecho-lat', format='%.6f')
        lon = b.number_input('Longitude de referência', -180., 180., value=-43.2, key='trecho-lon', format='%.6f')
        metros = c.number_input('Extensão planejada (m)', .1, 100000., value=100., key='trecho-metros')
        if st.button('Cadastrar trecho planejado'):
            try:
                t = cadastrar_trecho(nome, corpo, lat, lon, metros, responsavel)
                st.success(f"Trecho cadastrado: {t['id']}")
            except ValueError as exc:
                st.error(str(exc))
    with st.expander('Revisar sessões de monitoramento'):
        sessoes = {s['id']:s for s in listar_entidades('sessao')
                   if s['status'] == 'encerrada' and s['revisao'] == 'nao_revisado'}
        if sessoes:
            ident = st.selectbox('Sessão para revisão', list(sessoes),
                format_func=lambda i: f"{sessoes[i]['trecho_nome']} · {sessoes[i]['inicio'][:16]}")
            s = sessoes[ident]
            st.write({k:s.get(k) for k in ('id','trecho_nome','waterbody_id','inicio','fim','duracao_min',
                                          'extensao_observada_m','quantidade_fotos','sem_residuos','cobertura_confirmada')})
            vinculadas = [r for r in todos if r.get('sessao_id') == ident]
            st.dataframe([{'ID':r['id'], 'Nível':r['nivel_informado'], 'Revisão':r['revisao']} for r in vinculadas])
            st.caption('Confira as fotos na fila de relatos. A validação da sessão não valida automaticamente suas fotos.')
            decisao = st.selectbox('Decisão da sessão', ['validado','rejeitado'])
            if st.button('Salvar revisão da sessão'):
                try:
                    revisar_sessao(ident, decisao, responsavel)
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
        else:
            st.info('Nenhuma sessão encerrada aguardando revisão.')
    validos = {r['id']:r for r in todos if r.get('revisao') == 'validado'}
    if not validos:
        return
    with st.expander('Atualizar ciclo de vida / registrar ação'):
        ident = st.selectbox('Ocorrência para acompanhamento', list(validos),
            format_func=lambda i:f"{validos[i]['nome']} · {i[:8]}", key='operacao-relato')
        atual = validos[ident].get('etapa', 'validada')
        etapa = st.selectbox('Próxima etapa', sorted(TRANSICOES.get(atual, set())), index=None,
                             key=f'operacao-etapa-{ident}-{atual}')
        nota = st.text_area('Justificativa pública da etapa', max_chars=1000, key='operacao-nota')
        if st.button('Salvar etapa de acompanhamento'):
            try:
                mudar_etapa(ident, etapa, responsavel, nota)
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
        tipo = st.selectbox('Tipo de ação realizada', TIPOS_ACAO)
        dia = st.date_input('Data da ação', value=datetime.now(FUSO).date())
        hora = st.time_input('Hora da ação (Brasília)')
        descricao = st.text_area('Descrição pública da ação', max_chars=1000)
        if st.button('Registrar ação para comparação antes/depois'):
            try:
                registrar_acao(ident, tipo, datetime.combine(dia, hora, tzinfo=FUSO), descricao, responsavel)
                st.success('Ação registrada. A comparação aparece na página do local.')
            except ValueError as exc:
                st.error(str(exc))
