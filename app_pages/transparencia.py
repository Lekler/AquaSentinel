from pathlib import Path
from hashlib import sha256
from interface_idioma import st
from registro_visual import cabecalho, rodape
from relatos import listar_fotos
from evolucao import indicadores
from versoes import APP, METODOLOGIA, MONITORAMENTO, WPS, CS, AQUAVERIFY
from monitoramento import listar_entidades

cabecalho('Transparência', 'Como os dados são produzidos, revisados e interpretados.', False,
          'Transparency', 'How observations are produced, reviewed and interpreted.', '/transparencia')
st.subheader('Indicadores gerais')
try:
    valores = indicadores(listar_fotos(), sessoes=listar_entidades('sessao'))
    for inicio in (0, 3):
        for col, (nome, valor) in zip(st.columns(3), list(valores.items())[inicio:inicio+3]):
            col.metric(nome, valor)
except Exception:
    import logging
    logging.exception('Indicadores indisponíveis')
    st.warning('Indicadores temporariamente indisponíveis.')
st.caption('Recebidos e validados são contagens de relatos fotográficos, sem expor dados individuais não públicos. '
           'Corpos hídricos incluem sessões públicas validadas, inclusive observações sem resíduos. '
           'Objetos e hotspots usam somente registros públicos validados. '
           'Objetos são detecções somadas nas fotos, não itens únicos entre fotos. Não há ranking de usuários.')
st.subheader('Metodologia')
st.write('O nível ambiental é declarado pelo usuário e revisado pela equipe. WPS combina o nível (70%) '
         'com frequência de fotos distintas (30%); CS combina confiança média da IA com fator comunitário 0,8. '
         'Cobertura conta dias diferentes e não intensidade de poluição. Hotspots descrevem persistência observada.')
st.write('Registro oportunístico é uma foto avulsa. Monitoramento estruturado registra início, fim, trecho e extensão '
         'efetivamente observada. Itens por metro, por 100 m e por minuto só aparecem para sessões aptas e revisadas.')
st.subheader('Inteligência artificial')
st.write('O detector identifica sacolas, garrafas, embalagens e outros plásticos. A confiança é uma medida do modelo '
         'para os objetos detectados, não probabilidade de a denúncia ser verdadeira. O modelo não determina '
         'autenticidade, gravidade, contaminação ou bloqueio do canal. Não há ficha completa do conjunto de treinamento '
         'disponível nesta aplicação; o hash identifica os pesos efetivamente utilizados.')
st.subheader('Dados e rastreabilidade')
st.write('São registrados foto, localização declarada/confirmada, precisão do GPS quando disponível, data de envio, '
         'SHA-256, pHash, versão/hash do modelo, resultado, revisor e histórico de etapas. O histórico público mostra '
         'a evolução das observações; a equipe autenticada consulta os detalhes técnicos. A data de captura EXIF, quando existe, não é autenticada.')
st.write('Somente relatos validados e autorizados são publicados. Códigos de recibo e de sessão são privados e '
         'armazenados no banco como hash. O remetente acompanha sua ocorrência no site; não enviamos notificações '
         'externas automaticamente. Registros “Sem resíduos” permanecem no histórico.')
st.subheader('Limitações e lacunas')
st.write('“Não temos dado” é diferente de “o trecho foi observado e nenhum resíduo foi visto”. O mapa de lacunas '
         'cobre os trechos cadastrados no plano; não representa todos os rios da região. Coordenadas manuais, '
         'GPS, nomes de corpos hídricos e comprimentos podem conter erros. Ausência de detecção não prova ausência de lixo.')
st.write('pHash sinaliza possíveis semelhanças e pode errar. Taxas por extensão dependem de cobertura declarada '
         'e podem repetir o mesmo objeto entre fotos. Comparações antes/depois são descritivas e não demonstram '
         'que a ação causou a mudança. Limiares e pesos são heurísticas experimentais.')
st.subheader('Revisão humana e ciclo de vida')
st.write('Todos os relatos aguardam revisão antes da publicação. A equipe confirma o corpo hídrico e avalia '
         'similaridade. Depois pode documentar recorrência, encaminhamento, ação, acompanhamento e resolução, '
         'com responsável, data e justificativa. “Resolvida” é uma decisão registrada pela equipe, não uma garantia automática da IA.')
st.caption('A área da equipe usa senha compartilhada e nome informado pelo revisor; não há autenticação individual de revisores.')
st.subheader('Versões')
st.dataframe([{'Componente':'Aplicativo','Versão':APP}, {'Componente':'Metodologia WPS','Versão':METODOLOGIA},
              {'Componente':'Monitoramento','Versão':MONITORAMENTO}, {'Componente':'AquaVerify','Versão':AQUAVERIFY},
              {'Componente':'WPS','Versão':WPS}, {'Componente':'CS','Versão':CS},
              {'Componente':'Hotspot','Versão':'hotspot-persistente-v1'},
              {'Componente':'Similaridade','Versão':'phash-dct-recortes-v1'}], hide_index=True)
modelo = Path(__file__).resolve().parents[1]/'models'/'best.pt'
if modelo.is_file():
    st.caption('SHA-256 dos pesos do modelo disponíveis nesta versão')
    st.code(sha256(modelo.read_bytes()).hexdigest())
st.caption('Registros legados sem versão gravada são identificados como legados; não recebem retroativamente a versão atual.')
with st.expander('Critérios detalhados de AquaVerify, pHash e hotspots'):
    from i18n import em_ingles
    st.markdown((Path(__file__).resolve().parents[1]/'docs'/('AQUAVERIFY.en.md' if em_ingles() else 'AQUAVERIFY.md')).read_text(encoding='utf-8'))
st.page_link('app_pages/lacunas.py', label='Ver lacunas de monitoramento')
st.page_link('app_pages/dados.py', label='Consultar dados, dicionário e changelog')
rodape()
