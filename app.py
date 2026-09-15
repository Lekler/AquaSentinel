"""AquaSentinel — demo de previsão e prioridade operacional."""
from datetime import datetime, timezone
from html import escape
import json
import altair as alt
import pandas as pd
import streamlit as st
from motor import DadosInvalidos, analisar_previsao, calcular_prioridade, validar_entrada
from previsao import ErroPrevisao, consultar_previsao

st.set_page_config(page_title='AquaSentinel · Chuva e prioridade', page_icon='💧', layout='wide')

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

st.title('💧 AquaSentinel')
st.caption('INTELIGÊNCIA PARA CANAIS URBANOS · MVP / HACKATHON')
st.markdown('''<div class="hero"><div class="eyebrow">Prever para priorizar</div>
<h2>Chuva no horizonte. Ação no lugar certo.</h2>
<p>Combine a previsão de precipitação com a presença de resíduos para apoiar a priorização de vistorias nos canais.</p></div>''', unsafe_allow_html=True)

with st.sidebar:
    st.header('Consultar ocorrência')
    st.caption('Informe o local e a pontuação de resíduos identificada pela equipe ou pelo modelo de IA.')
    with st.form('consulta'):
        nome = st.text_input('Nome do canal / ocorrência', 'Canal de demonstração · Rio', max_chars=100)
        latitude = st.number_input('Latitude', min_value=-90.0, max_value=90.0, value=-22.9068, step=0.0001, format='%.4f')
        longitude = st.number_input('Longitude', min_value=-180.0, max_value=180.0, value=-43.1729, step=0.0001, format='%.4f')
        waste = st.slider('Pontuação de resíduos (Waste Score)', 0, 100, 70, help='0 = nenhum resíduo; 100 = severidade máxima. Entrada manual neste MVP.')
        forcar = st.checkbox('Consultar API sem usar cache', help='Normalmente a previsão é reutilizada por até 45 minutos para as mesmas coordenadas.')
        enviar = st.form_submit_button('Atualizar previsão', type='primary', use_container_width=True)
    st.caption('As coordenadas iniciais são um ponto de demonstração no Rio, sem associação a um canal cadastrado.')
    st.divider()
    st.markdown('**Como funciona**\n\n1. Localizar a ocorrência\n2. Consultar a chuva prevista\n3. Combinar chuva e resíduos')
    st.caption('Cache: 45 min · Sem chave de API\n\nAo consultar, as coordenadas são enviadas ao Open-Meteo.')

if enviar:
    # Uma falha nunca deixa a pontuação da ocorrência anterior parecendo atual.
    st.session_state.pop('resultado', None)
    st.session_state.pop('erro', None)
    try:
        validar_entrada(nome, latitude, longitude, waste)
        if forcar:
            previsao_em_cache.clear(latitude, longitude)
        with st.spinner('Consultando previsão e calculando prioridade…'):
            bruto = previsao_em_cache(latitude, longitude)
            previsao = analisar_previsao(bruto['dados'])
        p, nivel = calcular_prioridade(waste, previsao['rainfall_score'])
        st.session_state.resultado = {
            **previsao, 'nome': nome.strip(), 'latitude': latitude, 'longitude': longitude,
            'waste_score': waste, 'priority_score': p, 'priority_level': nivel,
            'consultado_em': bruto['consultado_em'], 'fonte': 'Open-Meteo', 'url_fonte': bruto['url'],
            'versao_metodologia': 'mvp-1',
        }
    except (ErroPrevisao, DadosInvalidos) as exc:
        st.session_state.erro = str(exc)

if st.session_state.get('erro'):
    st.error(st.session_state.erro)
    st.info('Nenhuma pontuação foi gerada para esta consulta. Confira os dados e use “Atualizar previsão” para tentar novamente.')

resultado = st.session_state.get('resultado')
if resultado:
    r = resultado
    st.subheader(r['nome'])
    st.caption(f"Ocorrência consultada: {r['latitude']:.4f}, {r['longitude']:.4f} · Resíduos: {r['waste_score']}/100. Alterações no formulário só são aplicadas ao atualizar.")
    cores = {'Baixa': '#226F56', 'Média': '#93620A', 'Alta': '#AD4D1B', 'Crítica': '#B33042'}
    cols = st.columns(3)
    with cols[0]:
        cartao('Prioridade operacional', formatar(r['priority_score'], 2), r['priority_level'], 'Combinação de resíduos, chuva e interação.', cores[r['priority_level']])
    with cols[1]:
        cartao('Pontuação de chuva', str(r['rainfall_score']), r['level'], 'Baseada no maior volume previsto em 1 hora.', '#087F8C')
    with cols[2]:
        cartao('Pontuação de resíduos', str(r['waste_score']), 'Informada pela equipe', 'Entrada manual; reconhecimento por IA é uma próxima integração.', '#42617B')
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
        st.altair_chart(chart, use_container_width=True)
        st.caption('Cada barra representa uma hora completa. Probabilidade é a chance horária de precipitação; o pico não representa a chance de chuva em toda a janela.')
    with metodo:
        st.markdown('**Pontuação de chuva (Rainfall Score)** — usa o máximo de precipitação em 1h nas 24h analisadas.')
        st.table(pd.DataFrame({'Intensidade (mm/h)': ['< 0,2', '0,2–5,0', '5,1–25,0', '25,1–50,0', '> 50,0'], 'Chuva': ['Sem chuva significativa', 'Fraca', 'Moderada', 'Forte', 'Muito forte'], 'Score': [0, 25, 50, 75, 100]}))
        st.caption('Categorias de intensidade baseadas no Alerta Rio; transformação em score criada para o MVP. Valores entre 5,0 e 5,1 ou entre 25,0 e 25,1 entram na faixa superior, sem arredondamento prévio.')
        st.code('l = WasteScore / 100\nr = RainfallScore / 100\nPriorityScore = 100 × (0,6·l + 0,2·r + 0,2·l·r)', language=None)
        st.markdown('**Faixas de prioridade do MVP:** baixa < 25; média ≥ 25 e < 50; alta ≥ 50 e < 75; crítica ≥ 75. A classificação usa o valor antes do arredondamento.')
        st.caption('Os acumulados e a probabilidade são contexto visual: não entram diretamente nesta fórmula.')
    with dados:
        st.dataframe(df[['Intervalo', 'precipitacao_mm', 'probabilidade_pct']].rename(columns={'precipitacao_mm': 'Precipitação (mm)', 'probabilidade_pct': 'Probabilidade (%)'}), hide_index=True, use_container_width=True)
        st.download_button('Baixar resultado JSON', json.dumps(r, ensure_ascii=False, indent=2, allow_nan=False), file_name='aquasentinel-previsao.json', mime='application/json')
else:
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

st.divider()
st.caption('Protótipo de apoio à priorização. Não é previsão de inundação, alerta oficial nem orientação de segurança. Pesos e faixas de score ainda precisam de validação local.')
st.markdown('Dados: [Open-Meteo](https://open-meteo.com/) · [Licença CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) · Categorias: [Alerta Rio](https://websempre.rio.rj.gov.br/estacoes/)')
