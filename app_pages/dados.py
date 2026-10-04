from datetime import date
from pathlib import Path
import json
from interface_idioma import st
from registro_visual import cabecalho, rodape
from relatos import listar_fotos
from observacao import publicos, data_registro, FUSO
from ciclo import consultar_recibo
from dados_abertos import DICIONARIO, filtrar, exportar, linha

cabecalho('Dados e Ciência Aberta', 'Entenda, filtre e reutilize observações com contexto.', False,
          'Data and open science', 'Understand and export observations with context.', '/dados')
with st.container(border=True):
    st.subheader('Princípios FAIR')
    a, b = st.columns(2)
    a.markdown('**Encontrável** · IDs de registros e corpos hídricos, metadados e versões.\n\n'
               '**Acessível** · dados públicos revisados; os próprios registros mediante recibo privado.')
    b.markdown('**Interoperável** · CSV, Excel, JSON e GeoJSON, com unidades documentadas.\n\n'
               '**Reutilizável** · metodologia, proveniência e limitações acompanham os dados.')
    st.caption('São princípios orientadores, não uma certificação FAIR. A licença de reutilização dos dados '
               'e fotos ainda precisa ser definida pela equipe; acesso público não equivale a licença irrestrita.')
    st.markdown('[Princípios GO FAIR](https://www.go-fair.org/fair-principles/) · '
                '[Modelo OGC SensorThings](https://docs.ogc.org/is/18-088/18-088.html)')
with st.container(border=True):
    st.subheader('Exportar observações')
    origem = st.segmented_control('Origem dos dados', ['Públicos validados', 'Meus registros'], default='Públicos validados')
    registros = []
    if origem == 'Meus registros':
        st.caption('Informe um código de acompanhamento por linha (recibos antigos: ID; código privado). Os códigos são usados apenas para autorizar '
                   'a consulta e nunca entram nos arquivos. Não há conta de usuário nem busca por nome de autor.')
        with st.form('autorizar-exportacao'):
            recibos = st.text_area('Recibos privados', height=110, key='dados-recibos')
            autorizar = st.form_submit_button('Autorizar meus registros')
        if autorizar:
            st.session_state.pop('dados-autorizados', None)
            try:
                pares = [v.split(';', 1) if ';' in v else ['', v] for v in recibos.splitlines() if v.strip()]
                if not pares or len(pares) > 100:
                    raise ValueError('Informe de 1 a 100 códigos de acompanhamento, um por linha.')
                for ident, chave in pares:
                    consultar_recibo(ident.strip(), chave.strip())
                st.session_state['dados-autorizados'] = [(i.strip(), c.strip()) for i, c in pares]
            except ValueError as exc:
                st.error(str(exc))
        try:
            registros = list({r['id']: r for r in (consultar_recibo(i, c) for i, c in st.session_state.get('dados-autorizados', []))}.values())
        except ValueError:
            st.session_state.pop('dados-autorizados', None)
            st.error('Um recibo não é mais válido. Autorize novamente.')
        if st.button('Limpar acesso aos meus registros'):
            st.session_state.pop('dados-autorizados', None)
            st.session_state.pop('dados-recibos', None)
            st.rerun()
    else:
        registros = publicos(listar_fotos())
    st.caption('As exportações desta página contêm ocorrências fotográficas. Sessões sem foto continuam no histórico '
               'de Monitoramento. Dados pendentes de outras pessoas nunca entram na exportação pública.')
    datas = [data_registro(r).astimezone(FUSO).date() for r in registros if data_registro(r)]
    periodo = st.date_input('Período de registro', value=(min(datas) if datas else date.today(), date.today()), key='dados-periodo')
    a, b = st.columns(2)
    corpo = a.selectbox('Corpo hídrico', ['Todos'] + sorted({r['waterbody_id'] for r in registros if r.get('waterbody_id')}))
    nivel = b.selectbox('Nível observado', ['Todos', 'Sem resíduos', 'Pouco', 'Moderado', 'Muito poluído', 'Bloqueando'])
    a, b = st.columns(2)
    status = a.selectbox('Status de acompanhamento', ['Todos'] + sorted({r['etapa'] for r in registros if r.get('etapa')}))
    revisao = b.selectbox('Revisão', ['Todos', 'Revisado', 'Não revisado'])
    if len(periodo) != 2:
        st.info('Selecione a data inicial e a final.')
        selecionados = []
    else:
        selecionados = filtrar(registros, *periodo, None if corpo == 'Todos' else corpo,
                              None if nivel == 'Todos' else nivel, None if status == 'Todos' else status, revisao)
    st.metric('Registros selecionados', len(selecionados))
    if selecionados:
        st.dataframe([linha(r) for r in selecionados], hide_index=True)
        formato = st.selectbox('Formato do arquivo', ['CSV', 'Excel', 'JSON', 'GeoJSON'])
        ext, mime = {'CSV': ('csv','text/csv'), 'Excel': ('xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                     'JSON': ('json','application/json'), 'GeoJSON': ('geojson','application/geo+json')}[formato]
        st.download_button(f'Baixar {formato}', exportar(selecionados, formato),
                           file_name=f'aquasentinela-observacoes.{ext}', mime=mime)
    else:
        st.info('Nenhum registro autorizado corresponde aos filtros.')
with st.expander('Dicionário de dados · campos, unidades e significado'):
    st.dataframe([{'Campo': c, 'Unidade / tipo': u, 'Significado': s} for c, u, s in DICIONARIO], hide_index=True)
    st.download_button('Baixar dicionário JSON', json.dumps(DICIONARIO, ensure_ascii=False, indent=2),
                       'dicionario-aquasentinela.json', 'application/json')
    st.caption('Nulo = indisponível; zero = valor informado/calculado. Em CSV, nulos ficam vazios e listas '
               'usam texto JSON. Textos iniciados por símbolos de fórmula recebem apóstrofo em CSV/Excel.')
with st.expander('Estrutura interna e versões dos índices'):
    st.write('O JSON organiza Observation, Location, FeatureOfInterest, ObservedProperty e metadata. '
             'É um perfil interno inspirado no OGC SensorThings, sem servidor ou declaração de conformidade. '
             'phenomenonTime permanece nulo quando a captura não é verificada; resultTime contém a data de registro.')
    st.markdown('**WPS v1** · prioridade experimental, não risco. 70% do nível + 30% da frequência.\n\n'
                '**CS v1** · confiança média × 0,8; não probabilidade calibrada.\n\n'
                '**AquaVerify v1** · qualidade documental; não probabilidade de a denúncia ser verdadeira.')
    st.caption('As versões são gravadas nas novas ocorrências. Dados antigos sem versão permanecem identificados '
               'como indisponíveis. WPS e CS exportados são retratos armazenados na gravação/revisão; '
               'reavaliações dinâmicas no mapa podem diferir se o histórico mudar.')
with st.expander('Changelog técnico'):
    from i18n import em_ingles
    st.markdown((Path(__file__).resolve().parents[1]/'docs'/('CHANGELOG.en.md' if em_ingles() else 'CHANGELOG.md')).read_text(encoding='utf-8'))
rodape()
