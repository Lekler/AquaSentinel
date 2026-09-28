from interface_idioma import st
from i18n import texto
from registro_visual import cabecalho, rodape

cabecalho('Dúvidas', 'Encontre ajuda para fazer seu registro.', mostrar_etapas=False,
          titulo_ingles='Questions', descricao_ingles='Find help with your report.', caminho='/duvidas')

perguntas = [
    ('Como posso participar?', 'How can I participate?',
     'Abra “Registrar ocorrência”, tire uma foto ou envie uma imagem, aguarde a análise, confira a localização e informe o nível de resíduos. Confirme os dados, autorize a publicação e clique em “Enviar ocorrência”. O relato passa por revisão da equipe antes de aparecer no mapa público.',
     'Open “Report an occurrence”, take a photo or upload an image, wait for analysis, check the location and report the waste level. Confirm the details, authorize publication and submit the report. The team reviews it before it appears on the public map.'),
    ('Quais fotos posso enviar?', 'Which photos can I upload?',
     'Você pode enviar JPG, PNG ou WEBP de até 12 MB. Procure uma imagem nítida em que os resíduos estejam visíveis.',
     'You can upload JPG, PNG or WEBP files up to 12 MB. Choose a clear image with visible waste.'),
    ('Por que a análise está carregando?', 'Why is the analysis loading?',
     'O sistema prepara a foto, carrega o modelo de IA e identifica os resíduos. A barra abaixo da foto mostra essas etapas, não uma estimativa de tempo. O primeiro carregamento pode demorar mais. Se ocorrer um erro, use “Tentar a análise novamente”.',
     'The system prepares the photo, loads the AI model and identifies waste. The bar below the photo shows these stages, not an estimated duration. The first load may take longer. If an error occurs, use “Try the analysis again”.'),
    ('Preciso permitir o acesso à localização?', 'Do I need to allow location access?',
     'Não. Você pode usar o GPS do navegador ou informar as coordenadas manualmente. Confira o ponto no mapa antes de enviar.',
     'No. You can use browser GPS or enter coordinates manually. Check the map point before submitting.'),
    ('A câmera não abre. O que faço?', 'The camera does not open. What can I do?',
     'Confira a permissão de câmera no navegador. No celular, abra o site por HTTPS. Você também pode tirar a foto com o celular e usar “Enviar foto”.',
     'Check camera permissions in your browser. On mobile, open the site over HTTPS. You can also take a photo with your phone and use “Upload photo”.'),
    ('A IA confirma se a foto é verdadeira?', 'Does AI confirm that the photo is authentic?',
     'Não. A confiança indica o reconhecimento dos objetos. Ela não comprova a autenticidade, a data ou o local da foto. Nenhuma detecção também não significa ausência de lixo.',
     'No. Confidence indicates object recognition. It does not prove the authenticity, date or location of the photo. No detections does not mean there is no waste.'),
    ('Como escolho o nível do local?', 'How do I choose the site level?',
     'Escolha entre “Sem resíduos”, “Pouco”, “Moderado”, “Muito poluído” e “Bloqueando”, conforme o que você observou. Esse nível é informado por você; a IA conta objetos visíveis e não determina se o canal está bloqueado.',
     'Choose “No visible waste”, “Low”, “Moderate”, “Very polluted” or “Blocking” based on what you observed. You provide this level; AI counts visible objects and does not determine whether the canal is blocked.'),
    ('Onde encontro o registro e os arquivos?', 'Where can I find my report and files?',
     'Após enviar, você pode baixar a foto identificada, o Excel ou o pacote ZIP na confirmação. O botão “Ir para o mapa” abre os registros públicos; sua ocorrência aparecerá após revisão e validação pela equipe. Os dados ficam no banco configurado para o projeto.',
     'After submitting, you can download the identified photo, Excel file or ZIP package on the confirmation screen. “Go to the map” opens public reports; yours appears after team review and validation. Data is stored in the project database.'),
]

for indice, (pt, en, resposta_pt, resposta_en) in enumerate(perguntas):
    with st.expander(texto(pt, en), expanded=indice == 0):
        st.write(texto(resposta_pt, resposta_en))

for pergunta, resposta in [
    ('Por que meu registro não apareceu?', 'O mapa publica somente registros validados pela equipe e com autorização de publicação. Confira também o período, a camada e os filtros. Use seu recibo em Acompanhar meu registro para consultar a etapa.'),
    ('Como a IA funciona?', 'O modelo procura padrões visuais de objetos na foto. As caixas representam detecções, não objetos únicos em todo o território. Confiança baixa, similaridade e outras limitações exigem conferência humana. Veja a metodologia em Transparência.'),
    ('O GPS fica público?', 'Sim. As coordenadas confirmadas, a foto e o local ficam públicos após autorização e validação. A precisão disponível também integra os metadados. Não envie a localização de sua casa nem fotografe pessoas identificáveis sem autorização.'),
    ('Como corrigir um registro?', 'Não há edição direta pelo participante nesta versão. Guarde o ID e use um canal oficial em Fale Conosco quando disponível. A equipe precisa avaliar a correção; não envie outra foto idêntica para substituir o registro.'),
    ('Como usar os dados?', 'Abra Dados e Ciência Aberta, escolha a origem e aplique os filtros. Leia o dicionário e as limitações antes de analisar. Registros públicos podem ser exportados; os seus registros pendentes exigem recibo privado. A licença de reutilização ainda depende de definição pela equipe.'),
    ('Como colaborar?', 'Contribua com observações seguras, inclusive sem resíduos, ou participe de um monitoramento estruturado. Propostas de parceria podem ser encaminhadas pelos canais oficiais em Fale Conosco. Não há ranking por quantidade de envios.')]:
    with st.expander(pergunta):
        st.write(resposta)
with st.container(horizontal=True):
    st.page_link('app_pages/como_funciona.py', label='Como funciona')
    st.page_link('app_pages/dados.py', label='Dados e Ciência Aberta')
if st.button(texto('Registrar ocorrência', 'Report an occurrence'), type='primary'):
    st.switch_page('app_pages/registrar.py')
from contato_visual import mostrar_contato
mostrar_contato()
rodape()
