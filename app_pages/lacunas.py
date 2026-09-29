from interface_idioma import st
import pydeck as pdk
from mapa_base import estilo_url
from monitoramento import listar_entidades, lacunas
from relatos import listar_fotos
from registro_visual import cabecalho, rodape
from observacao import rgb
from interface_idioma import traduzir

cabecalho('Lacunas de monitoramento', 'Onde já observamos e onde precisamos voltar.', False,
          'Monitoring gaps', 'Where observations exist and where to return.', '/lacunas')
st.caption('Plano de trechos cadastrados. Muito observado: 4+ dias distintos nos últimos 30 dias; '
           'pouco observado: 1–3 dias; sem observação recente: última há 30+ dias. '
           '“Não temos dado” significa nenhuma observação pública revisada para o trecho.')
dados = lacunas(listar_entidades('trecho'), listar_fotos(), listar_entidades('sessao'))
cores = {'Não temos dado':'#94a3b8', 'Sem observação recente':'#8b5cf6',
         'Pouco observado':'#93c5fd', 'Muito observado':'#1d4ed8'}
if dados:
    for t in dados:
        t['cor'] = rgb(cores[t['classe']])
        t['ultima'] = 'Nunca observado' if t['ultima_dias'] is None else f"Última observação há {t['ultima_dias']} dias."
        for campo in ('classe', 'ultima', 'estado', 'chamada'):
            t[campo] = traduzir(t[campo])
    layer = pdk.Layer('ScatterplotLayer', id='lacunas', data=dados, get_position='[longitude,latitude]',
        get_fill_color='cor', get_radius=10, radius_units='pixels', pickable=True)
    st.pydeck_chart(pdk.Deck(map_style=estilo_url(), map_provider='maplibre', layers=[layer], initial_view_state=pdk.ViewState(
        latitude=sum(t['latitude'] for t in dados)/len(dados), longitude=sum(t['longitude'] for t in dados)/len(dados), zoom=10),
        tooltip={'text':'{nome}\n{classe}\n{ultima}\n{estado}\n{chamada}'}))
    st.caption('Cinza: não temos dado · violeta: sem observação recente · azul-claro: pouco observado · azul-escuro: muito observado.')
    st.dataframe([{'Trecho':t['nome'], 'Corpo hídrico':t['waterbody_id'], 'Cobertura':t['classe'],
                   'Dias observados (30 dias)':t['dias_30'], 'Última observação':t['ultima'],
                   'Condição de informação':t['estado'], 'Chamada':t['chamada']} for t in dados], hide_index=True)
else:
    st.info('Ainda não há trechos no plano. A equipe pode cadastrar inclusive trechos nunca observados na área de revisão.')
st.caption('Fotos avulsas são associadas por corpo hídrico confirmado e até 200 m do ponto de referência. '
           'Sessões usam o trecho escolhido. Pontos próximos podem ter áreas de referência sobrepostas. '
           'Um ponto representa uma referência, não toda a geometria do trecho.')
st.page_link('app_pages/monitoramento.py', label='Iniciar monitoramento de um trecho')
rodape()
