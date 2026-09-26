"""AquaSentinel — demo de previsão e prioridade operacional."""
from datetime import datetime, timezone
from html import escape
import hmac
import json
import logging
import os
import sqlite3
from uuid import uuid4
import altair as alt
import pandas as pd
import streamlit as st
from motor import DadosInvalidos, analisar_previsao, validar_entrada
from ari import CLASSES_RESIDUOS, NIVEIS_RIO, calcular_ari, triar_confianca
from historico import listar, salvar, confirmar, contar_proximos
from previsao import ErroPrevisao, consultar_previsao
from i18n import alternador_html, texto


@st.cache_data(ttl=45 * 60, max_entries=128, show_spinner=False)
def previsao_em_cache(latitude, longitude):
    return consultar_previsao(latitude, longitude)


def formatar(valor, casas=1):
    return f'{valor:.{casas}f}'.replace('.', ',')


def cartao(titulo, valor, nivel, detalhe, cor):
    st.markdown(f'''<div class="score-card" style="border-top:4px solid {cor}">
    <div class="eyebrow">{escape(titulo)}</div><div class="score">{escape(valor)}<span> / 100</span></div>
    <span class="badge" style="color:{cor}">{escape(nivel)}</span>
    <p>{escape(detalhe)}</p></div>''', unsafe_allow_html=True)

st.markdown('''<style>
.block-container{padding-top:2.2rem;max-width:1240px}
h1{letter-spacing:-1.7px;font-weight:750!important}
h2,h3{letter-spacing:-.5px}
.hero{background:linear-gradient(115deg,#103b4a,#116779);border-radius:18px;padding:26px 32px;color:white;margin:6px 0 24px}
.hero h2{color:white;font-size:29px;margin:5px 0 9px}.hero p{color:#d7edf0;margin:0;max-width:720px;font-size:16px}
.eyebrow{font-size:12px;font-weight:750;letter-spacing:1.8px;text-transform:uppercase}
.hero .eyebrow{color:#a8ece6}.score-card{background:white;border:1px solid #dce6ea;border-radius:14px;padding:22px;min-height:212px}
.score{font-size:46px;line-height:1.5;font-weight:750;letter-spacing:-2px}.score span{font-size:17px;color:#637981;letter-spacing:0}
.badge{display:inline-block;background:#f0f5f6;border-radius:20px;padding:4px 12px;font-size:13px;font-weight:750}
.score-card p{color:#526b75;font-size:13px;margin:13px 0 0}
[data-testid="stMetric"]{background:white;padding:15px;border-radius:12px;border:1px solid #dce6ea}
[data-testid="stMetricValue"]{font-size:27px}
</style>''', unsafe_allow_html=True)
st.markdown(f'<div class="ari-language">{alternador_html("/avaliacao")}</div>', unsafe_allow_html=True)

base_navegacao = '/' + st.get_option('server.baseUrlPath').strip('/')
base_navegacao = base_navegacao.rstrip('/')
st.html(f'<nav aria-label="Navegação"><a href="{base_navegacao}/" target="_self">{texto("Início", "Home")}</a> · <a href="{base_navegacao}/mapa" target="_self">{texto("Mapa e registros", "Map and reports")}</a></nav>')

st.title(texto('Chuva e ARI · experimental', 'Rain and ARI · experimental'))
st.info('Este painel é um estudo separado. A prioridade de resíduos deste MVP usa WPS e CS no mapa. O ARI não é previsão de inundação nem substitui alerta oficial.')
st.caption(texto('AQUASENTINEL RISK INDEX · BAÍA DE GUANABARA · MVP / HACKATHON', 'AQUASENTINEL RISK INDEX · GUANABARA BAY · MVP / HACKATHON'))
st.markdown(f'''<div class="hero"><div class="eyebrow">{texto('Prever para priorizar', 'Forecast to prioritize')}</div>
<h2>{texto('Chuva no horizonte. Ação no lugar certo.', 'Rain ahead. Action in the right place.')}</h2>
<p>{texto('Combine resíduos, chuva em 24 horas, condição do rio e recorrência para priorizar avaliações nos canais.', 'Combine waste, 24-hour rainfall, river conditions and recurrence to prioritize canal assessments.')}</p></div>''', unsafe_allow_html=True)

try:
    registros = listar()
except Exception:
    logging.exception('Falha ao abrir histórico ARI')
    st.error(texto('Não foi possível abrir o histórico. Tente novamente ou avise a equipe.', 'The history could not be opened. Please try again or contact the team.'))
    st.stop()

foto_origem = st.session_state.get('foto_para_ari')
if foto_origem:
    st.info(texto(f"Foto vinculada: {foto_origem['nome']} · {foto_origem['total']} itens identificados. Confira a classe de acúmulo e a confiança da avaliação no formulário. A confiança do detector e a quantidade de objetos não são convertidas automaticamente em gravidade ambiental.", f"Linked photo: {foto_origem['nome']} · {foto_origem['total']} items identified. Check the accumulation class and assessment confidence in the form. Detector confidence and object count are not automatically converted into environmental severity."))
    st.caption(texto(f"ID do relato: {foto_origem['id']} · Nível informado pela pessoa: {foto_origem['nivel_informado']}", f"Report ID: {foto_origem['id']} · Level reported by the person: {foto_origem['nivel_informado']}"))
    if st.button(texto('Desvincular foto e fazer consulta manual', 'Unlink photo and run a manual assessment')):
        for chave in ('foto_para_ari', 'resultado', 'erro', 'identidade_ocorrencia', 'ocorrencia_id'):
            st.session_state.pop(chave, None)
        st.rerun()

with st.sidebar:
    st.header(texto('Consultar ocorrência', 'Assess an occurrence'))
    st.caption(texto('Informe o local e uma avaliação manual de resíduos para explorar a previsão.', 'Enter the location and a manual waste assessment to explore the forecast.'))
    senha_configurada = os.environ.get('AQUASENTINEL_REVIEW_PASSWORD', '')
    senha_equipe = st.session_state.get('senha_ari', '')
    autorizado = bool(senha_configurada and senha_equipe) and hmac.compare_digest(senha_equipe, senha_configurada)
    with st.form('consulta'):
        nome = st.text_input(texto('Nome do canal / ocorrência', 'Canal / occurrence name'), foto_origem['nome'] if foto_origem else texto('Canal de demonstração · Rio', 'Demo canal · River'), max_chars=100)
        latitude = st.number_input('Latitude', min_value=-90.0, max_value=90.0, value=float(foto_origem['latitude']) if foto_origem else -22.9068, step=0.0001, format='%.6f')
        longitude = st.number_input('Longitude', min_value=-180.0, max_value=180.0, value=float(foto_origem['longitude']) if foto_origem else -43.1729, step=0.0001, format='%.6f')
        classe = st.selectbox('Acúmulo de resíduos (W)', list(CLASSES_RESIDUOS), index=1)
        waste = CLASSES_RESIDUOS[classe]
        confianca = st.slider(texto('Confiança da classificação (%)', 'Classification confidence (%)'), 0, 100, 85)
        st.caption('Classe de acúmulo e confiança desta avaliação são informadas pela equipe. A análise de objetos da foto está em Registrar ocorrência e não comprova a gravidade ambiental.')
        confirmado = st.checkbox(texto('Confirmar avaliação humana (confiança de 60 a <80%)', 'Confirm human assessment (confidence from 60 to <80%)'), disabled=not autorizado)
        revisor = st.text_input(texto('Responsável pela confirmação', 'Person responsible for confirmation'), max_chars=100, disabled=not autorizado)
        condicao = st.selectbox('Condição do rio (L)', ['Indisponível'] + list(NIVEIS_RIO))
        nivel = None if condicao == 'Indisponível' else condicao
        oficial = st.checkbox('Condição transcrita de fonte oficial', disabled=not autorizado)
        fonte_nivel = st.text_input('Referência da fonte / estação / horário observado', max_chars=300)
        st.caption('O nível é informado manualmente. A referência permite rastrear a observação; não há consulta automática ao INEA.')
        raio = st.number_input('Raio para recorrência (metros)', min_value=1, max_value=10000, value=500, step=100)
        st.caption('F usa registros ARI validados dos últimos 30 dias no histórico compartilhado, dentro deste raio.')
        forcar = st.checkbox('Consultar API sem usar cache', help='Normalmente a previsão é reutilizada por até 45 minutos para as mesmas coordenadas.')
        enviar = st.form_submit_button(texto('Atualizar previsão', 'Update forecast'), type='primary', width="stretch", key='atualizar')
    st.caption('As coordenadas iniciais são um ponto de demonstração no Rio, sem associação a um canal cadastrado.')
    st.divider()
    st.markdown('**Como funciona**\n\n1. Localizar a ocorrência\n2. Consultar a chuva prevista\n3. Combinar chuva e resíduos')
    st.caption('Cache: 45 min · Sem chave de API\n\nAo consultar, as coordenadas são enviadas ao Open-Meteo.')
    if st.button('Nova ocorrência', key='nova'):
        for chave in ('resultado', 'erro', 'identidade_ocorrencia', 'ocorrencia_id'):
            st.session_state.pop(chave, None)
    st.caption('Atualizar a previsão mantém a ocorrência atual. Use Nova ocorrência para registrar outro relato no mesmo ponto.')
    with st.expander('Acesso da equipe ao histórico'):
        st.text_input('Senha da equipe', type='password', key='senha_ari')

if enviar:
    # Uma falha nunca deixa a pontuação da ocorrência anterior parecendo atual.
    st.session_state.pop('resultado', None)
    st.session_state.pop('erro', None)
    try:
        validar_entrada(nome, latitude, longitude, waste)
        identidade = (nome.strip(), latitude, longitude)
        if st.session_state.get('identidade_ocorrencia') != identidade:
            st.session_state.identidade_ocorrencia = identidade
            st.session_state.ocorrencia_id = f"foto-{foto_origem['id']}" if foto_origem else str(uuid4())
        agora = datetime.now(timezone.utc)
        quantidade = contar_proximos(registros, latitude, longitude, agora, raio_m=raio,
                                     excluir_id=st.session_state.ocorrencia_id)
        indice = calcular_ari(classe, None, quantidade, nivel, confianca, confirmado, revisor, oficial, fonte_nivel)
        previsao, bruto = {}, {}
        if indice['status_validacao'] in ('aceito', 'confirmado_humano'):
            if forcar:
                previsao_em_cache.clear(latitude, longitude)
            try:
                with st.spinner('Consultando previsão e calculando ARI…'):
                    bruto = previsao_em_cache(latitude, longitude)
                    previsao = analisar_previsao(bruto['dados'])
                indice = calcular_ari(classe, previsao['acumulado_24h_mm'], quantidade,
                                      nivel, confianca, confirmado, revisor, oficial, fonte_nivel)
            except (ErroPrevisao, DadosInvalidos) as exc:
                st.session_state.erro = str(exc)
        st.session_state.resultado = {
            **previsao, **indice, 'id': st.session_state.ocorrencia_id, 'registrado_em': agora.isoformat(),
            'nome': nome.strip(), 'latitude': latitude, 'longitude': longitude,
            'waste_score': waste, 'classe_residuos': classe, 'confianca': confianca,
            'origem_residuos': 'entrada_manual', 'revisor': revisor.strip() if confirmado else '',
            'foto_relato_id': foto_origem['id'] if foto_origem else None,
            'nivel_rio': nivel, 'nivel_oficial': oficial, 'fonte_nivel': fonte_nivel,
            'registros_anteriores': quantidade, 'raio_m': raio, 'janela_recorrencia_dias': 30,
            'rainfall_intensity_score': previsao.get('rainfall_score'),
            'rainfall_intensity_level': previsao.get('level'),
            'rainfall_score': indice['componentes']['R'],
            'consultado_em': bruto.get('consultado_em'), 'fonte': 'Open-Meteo', 'url_fonte': bruto.get('url'),
        }
    except (ErroPrevisao, DadosInvalidos) as exc:
        st.session_state.erro = str(exc)

if st.session_state.get('erro'):
    st.error(st.session_state.erro)
    st.info('ARI indisponível nesta consulta. Confira os dados e atualize a previsão para tentar novamente.')

resultado = st.session_state.get('resultado')
if resultado:
    r = resultado
    if r['avaliacao_urgente']:
        st.error('Avaliação urgente recomendada: transbordamento informado como oficial. Esta sinalização independe do valor do ARI e da validação do relato de resíduos.')
    if r['status_validacao'] == 'pendente':
        st.warning('Confiança entre 60 e <80%: relato aguardando confirmação humana. Não participa do ARI ou da recorrência enquanto estiver pendente.')
    elif r['status_validacao'] == 'excluido':
        st.warning('Confiança abaixo de 60%: relato excluído do cálculo e da recorrência.')
    if autorizado and st.button('Salvar ocorrência no histórico', key='salvar'):
        try:
            inserido = salvar(r)
            st.success('Ocorrência salva.' if inserido else 'Esta ocorrência já foi salva. Nenhuma duplicação foi criada.')
            registros = listar()
        except Exception:
            logging.exception('Falha ao salvar ARI')
            st.error('Não foi possível salvar a ocorrência no histórico compartilhado.')

if resultado and resultado['ari_score'] is not None:
    r = resultado
    st.subheader(r['nome'])
    st.caption(f"Ocorrência consultada: {r['latitude']:.4f}, {r['longitude']:.4f} · Resíduos: {r['waste_score']}/100. Alterações no formulário só são aplicadas ao atualizar.")
    cols = st.columns(3)
    with cols[0]:
        cartao('ARI · índice composto', formatar(r['ari_score'], 2), r['ari_level'], r['acao'], r['cor_hotspot'])
    with cols[1]:
        cartao('Pontuação de chuva · R', str(r['rainfall_score']), 'Acumulado previsto em 24h', 'Faixas do protótipo a calibrar por bacia.', '#087F8C')
    with cols[2]:
        cartao('Pontuação de resíduos', str(r['waste_score']), 'Informada pela equipe', 'Classe de acúmulo avaliada pela equipe; detecções por foto disponíveis no registro.', '#42617B')
    st.caption(f"ARI normalizado: {formatar(r['ari'], 4)} · Confiança: {r['confianca']}% · Validação: {r['status_validacao']} · Registros anteriores: {r['registros_anteriores']}")
    if r['parcial']:
        st.warning('ARI parcial: nível do rio indisponível. Pesos W, R e F reajustados para somar 100%; cobertura original de 75%. Não compare como equivalente a um ARI completo.')
    st.caption(f"L: {r['componentes']['L'] if r['componentes']['L'] is not None else 'Indisponível'} · F: {r['componentes']['F']} · Raio: {r['raio_m']} m · Histórico: 30 dias")
    st.write('')
    cols = st.columns(4)
    cols[0].metric('Precipitação · 6 horas', f"{formatar(r['acumulado_6h_mm'])} mm")
    cols[1].metric('Precipitação · 24 horas', f"{formatar(r['acumulado_24h_mm'])} mm")
    cols[2].metric('Maior intensidade · 1 hora', f"{formatar(r['max_1h_mm'], 2)} mm/h")
    prob = r['precipitation_probability_peak']
    cols[3].metric('Pico de probabilidade · 24h', 'Indisponível' if prob is None else f'{formatar(prob, 0)}%')
    if prob is None:
        st.warning('Probabilidade incompleta na fonte: o pico das 24h está indisponível. A pontuação usa o volume previsto e continua calculável.')
    inicio, fim = datetime.fromisoformat(r['janela_inicio']), datetime.fromisoformat(r['janela_fim'])
    consulta = datetime.fromisoformat(r['consultado_em']).astimezone(inicio.tzinfo)
    idade = max(0, int((datetime.now(timezone.utc) - datetime.fromisoformat(r['consultado_em'])).total_seconds() / 60))
    st.caption(f"Janela: {inicio:%d/%m/%Y %H:%M} → {fim:%d/%m/%Y %H:%M} · {r['timezone']} · 24 intervalos completos a partir da próxima hora cheia.")
    st.caption(f"Fonte consultada em {consulta:%d/%m/%Y %H:%M} (há {idade} min). Este é o horário de consulta, não de emissão do modelo. Cache de até 45 min; use o botão para recalcular.")
    if idade >= 45:
        st.warning('Esta consulta tem 45 minutos ou mais. Atualize a previsão antes de usar as pontuações na demo.')
    grafico, metodo, dados = st.tabs(['Previsão por hora', 'Como calculamos', 'Dados da consulta'])
    with grafico:
        st.subheader('A chuva ao longo das próximas horas')
        df = pd.DataFrame(r['horas'])
        df['Intervalo'] = [f"{datetime.fromisoformat(a):%d/%m %H:%M}–{datetime.fromisoformat(b):%H:%M}" for a, b in zip(df.inicio, df.fim)]
        chart = alt.Chart(df).mark_bar(color='#138A97', cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
            x=alt.X('Intervalo:N', sort=None, title='Intervalo no horário local', axis=alt.Axis(labelAngle=-55)),
            y=alt.Y('precipitacao_mm:Q', title='Precipitação (mm em 1h)', scale=alt.Scale(domainMin=0)),
            tooltip=[alt.Tooltip('Intervalo:N'), alt.Tooltip('precipitacao_mm:Q', title='Precipitação (mm)', format='.2f'), alt.Tooltip('probabilidade_pct:Q', title='Probabilidade (%)')],
        ).properties(height=275)
        st.altair_chart(chart, width="stretch")
        st.caption('Cada barra representa uma hora completa. Probabilidade é a chance horária de precipitação; o pico não representa a chance de chuva em toda a janela.')
    with metodo:
        st.code('ARI (0–1) = (0,40×W + 0,25×R + 0,25×L + 0,10×F) / 100', language=None)
        st.table(pd.DataFrame({'Acumulado em 24h (mm)': ['<10', '10 a 30', '>30 a 50', '>50 a 80', '>80'], 'R': [0,25,50,75,100]}))
        st.markdown('**Faixas:** baixo <25; moderado ≥25 e <50; alto ≥50 e <75; crítico ≥75. Classificação antes do arredondamento. Sem L, a soma ponderada é dividida por 0,75.')
        st.dataframe(pd.DataFrame([{'Componente': k, 'Score': v, 'Peso efetivo': r['pesos_efetivos'].get(k), 'Contribuição (0–100)': r['contribuicoes'].get(k)} for k,v in r['componentes'].items()]), hide_index=True)
        st.caption('Probabilidade e máximo horário são contexto. A chuva do ARI usa o acumulado de 24h. A confiança controla a aceitação do relato; não multiplica W.')
    with dados:
        st.dataframe(df[['Intervalo', 'precipitacao_mm', 'probabilidade_pct']].rename(columns={'precipitacao_mm': 'Precipitação (mm)', 'probabilidade_pct': 'Probabilidade (%)'}), hide_index=True, width="stretch")
        st.download_button('Baixar resultado JSON', json.dumps(r, ensure_ascii=False, indent=2, allow_nan=False), file_name='aquasentinel-previsao.json', mime='application/json')
elif not resultado:
    if not st.session_state.get('erro'):
        st.info('Comece pelo painel lateral: informe a ocorrência e clique em “Atualizar previsão”.')
    a, b, c = st.columns(3)
    with a:
        st.subheader('01 · Localize')
        st.write('Nome e coordenadas conectam o canal à previsão meteorológica.')
    with b:
        st.subheader('02 · Antecipe')
        st.write('Consulte intensidade, acumulados e probabilidade nas próximas horas.')
    with c:
        st.subheader('03 · Priorize')
        st.write('Combine a chuva prevista com a severidade dos resíduos, em uma escala de 0 a 100.')

if autorizado:
    with st.expander('Histórico compartilhado e confirmação humana'):
        st.caption('Registros salvos persistem no banco do projeto. A confirmação exige acesso à área da equipe; para uma nova avaliação, consulte novamente com previsão atualizada.')
        pendentes = [item for item in registros if item['status_validacao'] == 'pendente']
        if pendentes:
            with st.form('revisao'):
                por_id = {item['id']: item for item in pendentes}
                escolhido = st.selectbox('Ocorrência pendente', list(por_id), format_func=lambda i: f"{por_id[i]['nome']} · {por_id[i]['registrado_em']} · {i[:8]}")
                responsavel = st.text_input('Responsável pela revisão', max_chars=100, key='responsavel_revisao')
                if st.form_submit_button('Confirmar relato'):
                    try:
                        confirmar(escolhido, responsavel)
                        st.success('Relato confirmado. Ele passa a participar da recorrência nas próximas consultas.')
                        registros = listar()
                    except (DadosInvalidos, sqlite3.Error, OSError) as exc:
                        st.error(str(exc))
        if registros:
            st.dataframe(pd.DataFrame([{'Canal': item['nome'], 'Registrado em': item['registrado_em'], 'Validação': item['status_validacao'], 'ARI na consulta': item['ari_score'], 'Condição': 'Parcial' if item['parcial'] else 'Completo', 'Ação na consulta': item['acao']} for item in registros]), hide_index=True)
            st.download_button('Baixar histórico JSON', json.dumps(registros, ensure_ascii=False, indent=2, allow_nan=False), file_name='aquasentinel-historico.json', mime='application/json')
            pontos = [item for item in registros if item['ari_score'] is not None or item['avaliacao_urgente']]
            if pontos:
                st.caption('Hotspots das avaliações salvas, com suas cores originais. São registros históricos, não alertas atualizados automaticamente.')
                st.map(pd.DataFrame([{'latitude': item['latitude'], 'longitude': item['longitude'], 'cor': item['cor_hotspot']} for item in pontos]), color='cor')
        else:
            st.info('Nenhuma ocorrência salva ainda. A ausência de relatos neste histórico não significa ausência de problemas na região.')

else:
    st.caption("Histórico e confirmação humana disponíveis apenas à equipe de revisão.")
st.divider()
st.caption('Protótipo de apoio à priorização. Não é previsão de inundação, alerta oficial nem orientação de segurança. Pesos e faixas de score ainda precisam de validação local.')
st.markdown('Dados: [Open-Meteo](https://open-meteo.com/) · [Licença CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) · Intensidade horária legada: [Alerta Rio](https://websempre.rio.rj.gov.br/estacoes/)')
st.caption('As faixas de chuva em 24h e do ARI são propostas do protótipo e precisam de calibração por bacia.')
