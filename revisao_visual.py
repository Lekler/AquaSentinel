"""A single review sequence; all entry points require team authentication."""
import logging
from interface_idioma import st
from i18n import texto
from equipe_auth import autenticado


def area_equipe(todos):
    if not autenticado():
        return
    from relatos import obter_foto, revisar_foto
    from corpos_hidricos import listar_corpos
    from evidencia_visual import gestao_catalogo
    from acompanhamento_visual import equipe_acompanhamento, rastreabilidade
    from interface_fotos import mostrar_analise
    from aquaverify import avaliar, explicar
    from observacao import agrupar_locais, resumo_local, publicos
    from mapa_visual import nivel_html, resumo_grupo
    responsavel = st.text_input('Responsável da equipe', key='equipe-responsavel', max_chars=100)
    with st.expander(texto('Revisar ocorrências', 'Review reports'), expanded=True):
        fila = st.selectbox(texto('Lista de revisão', 'Review list'),
            [texto('Aguardando revisão', 'Awaiting review'), texto('Todos os registros', 'All reports')], key='revisao-fila')
        pendentes = {r['id']:r for r in todos if fila == texto('Todos os registros', 'All reports') or r.get('revisao') == 'nao_revisado'}
        if not pendentes:
            st.info(texto('Nenhum registro aguardando revisão.', 'No reports awaiting review.'))
        else:
            ident = st.selectbox(texto('Ocorrência', 'Report'), list(pendentes),
                format_func=lambda i:f"{pendentes[i]['nome']} · {pendentes[i]['registrado_em'][:10]} · {i[:8]}", key='revisao-relato')
            r, foto, anotada = obter_foto(ident)
            st.caption(f"ID: {r['id']} · {r['registrado_em'][:16]} · {r.get('revisao', '')}")
            st.subheader(texto('Evidência', 'Evidence'))
            original = st.checkbox(texto('Ver foto original', 'View original photo'), key=f'revisao-original-{ident}')
            st.image(foto if original else anotada or foto, caption=r['nome'], width='stretch')
            st.subheader(texto('Análise da IA', 'AI analysis'))
            mostrar_analise(r, anotada, exibir_imagem=False, titulo=False, aviso=False)
            st.subheader(texto('Localização', 'Location'))
            st.write(f"{r['latitude']:.6f}, {r['longitude']:.6f}")
            gps = r.get('gps') or {}
            precisao = gps.get('accuracy') if gps.get('latitude') == r['latitude'] and gps.get('longitude') == r['longitude'] else None
            st.caption(texto(f'Precisão do GPS: {precisao:g} m', f'GPS accuracy: {precisao:g} m') if precisao is not None else texto('Localização manual ou precisão indisponível.', 'Manual location or accuracy unavailable.'))
            corpos = {c['id']:c for c in listar_corpos()}
            opcoes = [None, *corpos]
            corpo = st.selectbox('Confirmar corpo hídrico do relato', opcoes,
                index=opcoes.index(r.get('waterbody_id')) if r.get('waterbody_id') in opcoes else 0,
                format_func=lambda i:f"{i} — {corpos[i]['nome']}" if i else 'Ainda não identificado', key=f'revisao-corpo-{ident}')
            st.subheader(texto('Informações declaradas', 'Reported information'))
            st.html(nivel_html(r['nivel_informado']))
            if r.get('observacoes'):st.text(r['observacoes'])
            contexto = r.get('contexto_ambiental') or {}
            st.write(', '.join(contexto.get('sinais', [])) or texto('Sem contexto ambiental informado.', 'No environmental context provided.'))
            if contexto.get('detalhe'):st.text(contexto['detalhe'])
            if corpo:
                from historico import distancia_m
                anteriores = [a for a in publicos(todos) if a['id'] != ident and a.get('waterbody_confirmado')
                    and a.get('waterbody_id') == corpo and distancia_m(r['latitude'],r['longitude'],a['latitude'],a['longitude']) <= 200]
                if anteriores:
                    st.markdown(texto('**Histórico próximo · até 200 m**', '**Nearby history · within 200 m**'))
                    resumo_grupo(resumo_local(anteriores))
            st.subheader(texto('Qualidade da evidência', 'Evidence quality'))
            q = avaliar(r)
            st.metric('AquaVerify', f"{q['indice']:.1f} / 100", delta=None)
            st.caption(texto('Qualidade e completude da evidência; não é probabilidade de veracidade.', 'Evidence quality and completeness; not a probability of truth.'))
            with st.expander(texto('Ver detalhes técnicos', 'View technical details')):
                st.dataframe(q['criterios'], hide_index=True, width='stretch')
                if r.get('itens'):
                    st.dataframe([{'ID': item['item_id'], 'Classe': item['classe_pt'],
                        'Confiança (%)': item['confidence_pct']} for item in r['itens']], hide_index=True, width='stretch')
                st.caption(texto(f"Caixas duplicadas removidas: {r.get('duplicadas_removidas',0)}. Mantida a identificação de maior confiança entre caixas muito sobrepostas.",
                                 f"Duplicate boxes removed: {r.get('duplicadas_removidas',0)}. The highest-confidence detection is retained among heavily overlapping boxes."))
                rastreabilidade(r)
                from wps import pontuar
                from observacao import data_registro
                indices = pontuar(r, publicos(todos), agora=data_registro(r))
                st.write(f"WPS: {indices['wps']:.1f} / 100 · CS: {indices['cs']:.1f}%")
            st.subheader(texto('Decisão do revisor', 'Reviewer decision'))
            _, motivos = explicar(r)
            for motivo in motivos:
                if 'Todos os relatos' not in motivo:
                    st.caption(motivo)
            sim_decisao, justificativa = None, ''
            if (r.get('similaridade') or {}).get('quantidade'):
                st.warning(texto('Há imagens semelhantes. Compare antes de decidir.', 'Similar images found. Compare before deciding.'))
                for candidata in r['similaridade'].get('candidatas', []):
                    with st.expander(texto('Comparar com registro anterior ', 'Compare with previous report ') + candidata['id'][:8]):
                        try:
                            anterior, f, _ = obter_foto(candidata['id'])
                            st.image(f, caption=anterior['registrado_em'][:16])
                        except ValueError:st.info('Evidência anterior indisponível.')
                sim_decisao = st.selectbox('Decisão sobre similaridade', [None,'independente','reutilizada'],
                    format_func=lambda v:{None:'Não resolvida','independente':'Nova observação / falso positivo','reutilizada':'Imagem reutilizada'}[v],key=f'sim-decisao-{ident}')
                justificativa = st.text_input('Justificativa da decisão de similaridade',max_chars=500,key=f'sim-just-{ident}')
            a,b=st.columns(2)
            decisao='validado' if a.button('Validar relato',type='primary') else 'rejeitado' if b.button('Rejeitar relato') else None
            if decisao and autenticado():
                try:
                    revisar_foto(ident,decisao,responsavel,corpo,sim_decisao,justificativa)
                    st.rerun()
                except ValueError as exc:st.error(str(exc))
                except Exception:
                    logging.exception('Falha ao revisar relato')
                    st.error(texto('Não foi possível salvar a revisão.', 'Unable to save the review.'))
    with st.expander(texto('Corpos hídricos', 'Water bodies')):
        gestao_catalogo(todos, responsavel)
    with st.expander(texto('Monitoramento e ações', 'Monitoring and actions')):
        equipe_acompanhamento(todos, responsavel)
