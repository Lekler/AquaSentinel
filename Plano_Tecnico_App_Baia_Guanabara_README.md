# Plano técnico da componente hídrica

## Aplicativo de detecção e classificação de resíduos em canais da Baía de Guanabara

Documento de referência para o desenvolvimento de um aplicativo destinado à detecção e classificação de resíduos, registro de indícios de esgoto, análise do contexto hidrológico e priorização de inspeções.

> **Escopo:** Baía de Guanabara e sub-bacias contribuintes, com protótipo inicialmente concentrado no Canal do Mangue e no sistema Cunha-Fundão.

## Sumário

1. [Resumo executivo](#resumo-executivo)
2. [Objetivo e entregáveis](#1-objetivo-e-entregáveis)
3. [Recorte territorial](#2-recorte-territorial)
4. [Base histórica do estudo da Marinha](#3-base-histórica-do-estudo-da-marinha)
5. [Pontos georreferenciados](#4-pontos-georreferenciados)
6. [Esgoto e drenagem urbana](#5-esgoto-e-drenagem-urbana)
7. [Dados necessários](#6-dados-necessários)
8. [Classificação dos resíduos](#7-classificação-dos-resíduos)
9. [Inteligência artificial e risco](#8-inteligência-artificial-e-risco)
10. [Arquitetura funcional](#9-arquitetura-funcional-do-aplicativo)
11. [Modelo mínimo de dados](#10-modelo-mínimo-de-dados)
12. [Fontes de dados](#11-fontes-de-dados)
13. [Plano do protótipo](#12-o-que-pode-ser-usado-no-protótipo)
14. [Limitações e controles](#13-limitações-e-controles)
15. [Conclusão](#14-conclusão)
16. [Referências](#referências-e-portais)

## Resumo executivo

Este documento define a componente hídrica de um aplicativo destinado a detectar e classificar acúmulos de resíduos em canais urbanos que contribuem para a Baía de Guanabara. A solução proposta combina fotografias georreferenciadas, inteligência artificial, rede hidrográfica, chuva, maré, nível da água, características do canal e indícios de lançamento de esgoto.

O objetivo não é apenas localizar lixo, mas estimar quando o acúmulo pode reduzir a seção de escoamento, favorecer alagamentos, transportar poluentes ou alcançar a Baía.

O recorte territorial inclui a Baía e as sub-bacias que drenam para ela. Para o protótipo, recomenda-se priorizar o Canal do Mangue, o Canal do Fundão e o Canal do Cunha. A expansão pode abranger Pavuna-Meriti, Iguaçu-Sarapuí, rios do fundo da Baía e o setor de São Gonçalo.

O estudo da Marinha, realizado entre 2001 e 2003, fornece uma malha histórica de pontos e aponta maior comprometimento das regiões de fundo e noroeste, enquanto o canal central e a entrada apresentam maior renovação pela maré.

A arquitetura deve manter separados:

- a classificação visual do resíduo;
- a confiança do modelo de inteligência artificial;
- o risco hídrico calculado.

A inteligência artificial pode reconhecer materiais e segmentar a área ocupada. O risco depende também de chuva, nível, maré, posição na rede de drenagem e recorrência. Indícios visuais de esgoto não devem ser apresentados como confirmação laboratorial. O aplicativo deve registrar a incerteza, a fonte e a data de cada dado.

O produto mínimo viável deve entregar mapa, captura fotográfica orientada, classificação inicial, percentual de obstrução, contexto de chuva e maré, histórico do ponto, prioridade de inspeção e validação humana. Registros de campo e de limpeza formarão a base para calibrar o índice de risco e melhorar o modelo de visão computacional.

## 1. Objetivo e entregáveis

O objetivo é fornecer à equipe de desenvolvimento uma especificação funcional e de dados para construir o módulo hídrico do aplicativo. O sistema deverá transformar observações visuais em registros comparáveis e territorialmente vinculados à rede de drenagem.

- Mapa da Baía de Guanabara, rios, canais, sub-bacias e pontos de monitoramento.
- Registro de fotografias com GPS, horário, orientação da câmera e identificação do corpo hídrico.
- Detecção e classificação de resíduos por inteligência artificial.
- Estimativa da área ocupada e do grau de obstrução do canal.
- Integração de chuva, maré, nível, vazão e direção do escoamento, quando disponíveis.
- Registro de indícios de esgoto sem emitir diagnóstico laboratorial.
- Índice de risco hídrico e fila de prioridade para inspeção ou limpeza.
- Histórico antes e depois da intervenção para validação e treinamento do modelo.

## 2. Recorte territorial

O limite do projeto deve ser a bacia contribuinte da Baía de Guanabara, não apenas o contorno do espelho d'água. Devem ser incluídas as áreas urbanas cujo escoamento superficial ou rede de canais conduz resíduos e efluentes para a Baía.

Regiões que drenam para a Baía de Sepetiba, sistemas lagunares de Jacarepaguá ou emissários oceânicos devem permanecer em camadas separadas.

![Caminho simplificado de resíduos e efluentes até a Baía de Guanabara](assets/fluxo-territorial.png)

### 2.1. Locais prioritários

| Local | Motivo para priorização | Fase |
|---|---|---|
| Canal do Mangue | Histórico de esgoto e resíduos; ligação com a região portuária e com o coletor Cidade Nova | MVP |
| Canal do Fundão e Canal do Cunha | Drenagem urbana densa, proximidade da Maré e comunicação direta com a Baía | MVP |
| Pavuna-Meriti | Grande eixo urbano entre o Rio de Janeiro e a Baixada Fluminense | Expansão |
| Iguaçu-Sarapuí | Aporte da Baixada e influência no setor noroeste | Expansão |
| Rios Estrela, Suruí, Iriri, Guapi e Macacu | Fundo da Baía, manguezais e transição entre áreas urbanas e ambientais | Expansão |
| São Gonçalo e Maruí | Aporte urbano do lado leste da Baía | Expansão |

## 3. Base histórica do estudo da Marinha

O relatório *Monitoramento e Prevenção da Poluição Hídrica da Baía de Guanabara* consolida atividades executadas entre agosto de 2001 e maio de 2003 pela EMGEPRON, Marinha e Petrobras. O estudo deve ser tratado como referência histórica e metodológica. Seus pontos podem orientar o desenho da rede do aplicativo, mas a situação ambiental e a infraestrutura de saneamento precisam ser atualizadas.

| Componente | Descrição | Aplicação no aplicativo |
|---|---|---|
| Vigilância integrada | Sobrevoos, embarcações e registros fotográficos de manchas e possíveis fontes | Modelo para inspeção georreferenciada e histórico de ocorrências |
| Monitoramento automático | Dez boias destinadas a alarmes de hidrocarbonetos, com centrais na REDUC e Ilha d'Água | Referência para futura integração de sensores; os resultados não constam do estudo |
| Água superficial | Dezesseis estações bimestrais com parâmetros físicos, químicos e biológicos | Malha inicial de pontos e seleção de variáveis |
| Campanhas oceanográficas | Trinta e cinco estações com água superficial, fundo e sedimentos | Base espacial para áreas costeiras, desembocaduras e validação ambiental |
| Cartografia | Carta eletrônica com sensibilidade, dutos, monoboias e instalações | Conceito de mapa multicamadas para a plataforma |

### 3.1. Principais conclusões ambientais

- A região noroeste foi apontada como a mais comprometida, com elevada eutrofização, nutrientes e clorofila.
- A entrada da Baía e o canal central apresentaram melhores condições pela renovação promovida pelas marés.
- Hidrocarbonetos elevados foram observados sobretudo no noroeste e no fundo da Baía.
- A chuva contribui para o aporte de sedimentos e poluentes nas bordas.
- A qualidade da água resulta de múltiplas fontes: esgoto doméstico, lixo, efluentes industriais, óleo e atividades portuárias.

### 3.2. Parâmetros levantados

| Grupo | Parâmetros | Uso proposto |
|---|---|---|
| Hidrológico | Chuva, maré, nível, vazão, direção e velocidade do escoamento | Contextualizar transporte, retenção e risco de obstrução |
| Físico-químico | Temperatura, salinidade, oxigênio dissolvido, turbidez e condutividade | Caracterizar mistura, renovação e degradação |
| Nutrientes | Amônia, nitrato, nitrito e fosfato | Indicar enriquecimento por esgoto e matéria orgânica |
| Biológico | Clorofila-a, feofitina, zooplâncton e *E. coli* em campanhas atuais | Apoiar avaliação sanitária e eutrofização |
| Poluentes | Óleos, graxas, hidrocarbonetos e metais | Distinguir resíduos sólidos de contaminação química |

## 4. Pontos georreferenciados

A tabela original aparenta registrar graus e minutos decimais, embora utilize símbolos de forma inconsistente. A conversão adotada foi:

```text
coordenada decimal = -(graus + minutos/60)
```

Os sinais são negativos porque os pontos estão ao sul do Equador e a oeste de Greenwich. Cada par de latitude e longitude deve permanecer associado ao nome do ponto e a um código único. As coordenadas precisam ser confrontadas com imagens, hidrografia oficial e levantamento de campo antes do uso operacional.

| ID | Nome do ponto/local | Latitude | Longitude | Busca no Google Earth |
|---|---|---:|---:|---|
| BG-001 | Ponta de Tubiacanga | -22.775000 | -43.230500 | `-22.775000, -43.230500` |
| BG-002 | Próximo ao Canal do Galeão | -22.797167 | -43.269333 | `-22.797167, -43.269333` |
| BG-003 | Ponte do Galeão | -22.835833 | -43.240000 | `-22.835833, -43.240000` |
| BG-004 | Caju | -22.884833 | -43.150000 | `-22.884833, -43.150000` |
| BG-005 | Ilha d'Água | -22.809833 | -43.161667 | `-22.809833, -43.161667` |
| BG-006 | Depósito Petrobras | -22.812500 | -43.119333 | `-22.812500, -43.119333` |
| BG-007 | Canal do Mangue | -22.895000 | -43.210000 | `-22.895000, -43.210000` |
| BG-008 | Canal do Fundão | -22.866667 | -43.231667 | `-22.866667, -43.231667` |
| BG-009 | Rio Iguaçu | -22.758333 | -43.227167 | `-22.758333, -43.227167` |
| BG-010 | Boca Larga | -22.757667 | -43.218000 | `-22.757667, -43.218000` |
| BG-011 | Rio Estrela | -22.726167 | -43.199167 | `-22.726167, -43.199167` |
| BG-012 | Rio Suruí | -22.698167 | -43.110833 | `-22.698167, -43.110833` |
| BG-013 | Rio Iriri | -22.684000 | -43.084000 | `-22.684000, -43.084000` |
| BG-014 | Rio Guapi | -22.696667 | -43.043333 | `-22.696667, -43.043333` |
| BG-015 | Rio Macacu | -22.728333 | -43.046667 | `-22.728333, -43.046667` |
| BG-016 | Itaboraí APA | -22.745000 | -43.058333 | `-22.745000, -43.058333` |
| BG-017 | São Gonçalo | -22.803333 | -43.073333 | `-22.803333, -43.073333` |
| BG-018 | Maruí | -22.856667 | -43.110000 | `-22.856667, -43.110000` |
| BG-019 | Ilha do Caju | -22.880000 | -43.118333 | `-22.880000, -43.118333` |
| BG-020 | Ribeira | -22.827333 | -43.138500 | `-22.827333, -43.138500` |
| BG-021 | Canal Lage Rachada | -22.783333 | -43.126000 | `-22.783333, -43.126000` |

Para abrir um ponto no Google Earth, copie a última coluna e cole no campo de busca. No banco de dados, `nome_ponto`, `latitude` e `longitude` devem ser campos obrigatórios e vinculados ao mesmo ID.

Os registros “Barcas” e “Canal de Gragoatá” foram excluídos da conversão por apresentarem provável erro de digitação ou formatação ambígua. A localização operacional deve usar SIRGAS 2000 ou WGS 84, guardando também a coordenada original e a fonte.

### 4.1. Mapa da Baía de Guanabara

![Mapa da Baía de Guanabara com pontos hídricos e infraestrutura sanitária](assets/mapa-baia-guanabara.png)

O mapa contém:

- 21 pontos hídricos históricos, de `BG-001` a `BG-021`;
- 10 pontos de infraestrutura sanitária, incluindo ETEs e elevatórias;
- nome, latitude e longitude de cada ponto;
- corpo receptor ou destino conhecido do efluente;
- distância entre cada ponto hídrico e a infraestrutura sanitária mais próxima;
- camadas separadas para abertura no Google Earth.

Arquivos geoespaciais:

- [Dados em CSV](data/pontos-baia-guanabara.csv)
- [Camadas para Google Earth em KML](data/pontos-baia-guanabara.kml)

> **Atenção:** os triângulos representam a localização das ETEs e o corpo receptor documentado. Não representam necessariamente a coordenada exata da boca de descarga. O ponto da ETE São Gonçalo é aproximado e precisa ser confirmado antes do uso operacional.

## 5. Esgoto e drenagem urbana

A modelagem deve separar esgoto sanitário, drenagem pluvial e ligações irregulares. Em um sistema separador, o esgoto segue para coleta e tratamento, enquanto a chuva segue para galerias e canais. Na prática, lançamentos irregulares, extravasamentos e captação em tempo seco conectam os dois sistemas.

O aplicativo deve registrar essa relação sem transformar observação visual em diagnóstico conclusivo.

![Fluxo sanitário esperado com coleta e tratamento](assets/fluxo-sanitario.png)

### 5.1. Infraestrutura relevante

| Sistema | Informação disponível | Uso no projeto |
|---|---|---|
| ETE Alegria | Capacidade divulgada de até 2.500 L/s; atende o Centro e parte da Zona Norte; modernização em andamento | Referência principal de destino sanitário no setor oeste da Baía |
| Coletor Cidade Nova | 4,128 km; redução projetada de 700 L/s antes lançados no Canal do Mangue; atendimento estimado de 163 mil pessoas | Relacionar melhoria da coleta com observações no Canal do Mangue |
| Sistema da Maré | Projeto com 4,5 km de coletor-tronco e 18 km de redes secundárias; destinação à ETE Alegria | Relacionar Canal do Cunha e Fundão com expansão do saneamento |
| Captação em tempo seco | Intercepta fluxo de drenagem em períodos sem chuva e o encaminha para tratamento | Distinguir operação sanitária, chuva e descarga irregular |
| Elevatórias e extravasamentos | Bombeiam esgoto para coletores ou ETEs; falhas podem gerar descarga emergencial | Cadastrar infraestrutura e ocorrências operacionais |

Valores divulgados por concessionárias ou projetos devem ser armazenados como capacidade nominal ou redução projetada, nunca como vazão instantânea medida. Cada número deve conter fonte, data, unidade e situação: existente, em obras, planejado ou medido.

### 5.2. Indícios de esgoto no canal

- Fluxo contínuo em galeria ou tubulação durante período sem chuva.
- Água escura ou acinzentada, espuma persistente, óleo, gordura ou odor relatado.
- Resíduos sanitários, excesso de matéria orgânica, algas ou mortandade de peixes.
- Baixa transparência, alta turbidez ou descarga visível de tubulação.
- Recorrência no mesmo ponto e coincidência com falhas ou extravasamentos conhecidos.

A confirmação requer análises como *E. coli*, coliformes termotolerantes, DBO, DQO, oxigênio dissolvido, nitrogênio amoniacal, nitrato, fosfato, sólidos suspensos, óleos e graxas, condutividade e turbidez.

## 6. Dados necessários

### 6.1. Camadas estáticas

| Camada | Campos mínimos | Finalidade |
|---|---|---|
| Hidrografia | ID, nome, geometria, sentido, ordem e corpo receptor | Vincular ocorrência ao canal e calcular caminho até a Baía |
| Sub-bacias | ID, nome, área, exutório e município | Agrupar ocorrências e chuva contribuinte |
| Drenagem | Galerias, bueiros, pontes, grades, comportas e ecobarreiras | Identificar pontos de retenção e obstrução |
| Saneamento | Redes, coletores, elevatórias, ETEs, emissários e áreas atendidas | Interpretar escoamento de esgoto e destino previsto |
| Território | Uso do solo, impermeabilização, população, vias e comunidades | Estimar geração e mobilização de resíduos |
| Risco | Alagamentos, cotas baixas, áreas sensíveis e unidades de conservação | Priorizar impacto social e ambiental |

### 6.2. Dados dinâmicos

| Variável | Atualização desejada | Uso |
|---|---|---|
| Chuva de 15 min, 1 h, 24 h e 96 h | 5 a 15 minutos | Mobilização, lavagem urbana e resposta rápida |
| Nível da água | 5 a 15 minutos, quando disponível | Seção livre e tendência de elevação |
| Vazão e velocidade | Horária ou por campanha | Capacidade de transporte dos resíduos |
| Maré | Horária | Represamento e renovação nos canais próximos à Baía |
| Vento | Horária | Deslocamento de lixo flutuante no espelho d'água |
| Ocorrências e limpeza | A cada registro | Recorrência, tempo de resposta e massa retirada |
| Qualidade da água | Campanha ou sensor | Contextualização sanitária e ambiental |

## 7. Classificação dos resíduos

| Código | Classe | Exemplos |
|---|---|---|
| PL | Plástico rígido | Garrafas, potes e embalagens rígidas |
| PF | Plástico flexível | Sacolas, filmes e embalagens flexíveis |
| IS | Isopor | Fragmentos e embalagens de poliestireno |
| OR | Orgânico e vegetação | Galhos, folhas, restos alimentares e macrófitas |
| MD | Madeira | Tábuas, pallets e fragmentos |
| PN | Pneus e borracha | Pneus inteiros ou partes |
| VO | Volumosos | Móveis, colchões e eletrodomésticos |
| CC | Construção civil | Entulho, concreto e cerâmica |
| ME | Metais | Latas, chapas e sucata |
| PE | Potencialmente perigosos | Perfurocortantes, hospitalares, químicos ou recipientes suspeitos |
| MX | Misturados | Acúmulo sem classe predominante |
| ND | Não determinado | Imagem insuficiente ou objeto não reconhecido |

### 7.1. Posição e obstrução

A posição hídrica deve ser registrada como flutuante disperso, flutuante concentrado, preso em vegetação, retido em grade ou ecobarreira, acumulado sob ponte, depositado na margem, parcialmente submerso, depositado no leito ou bloqueando galeria.

| Classe | Ocupação visual da seção | Interpretação inicial |
|---|---:|---|
| 0 - Ausente | 0% | Sem resíduo visível |
| 1 - Traços | Menos de 10% | Ocorrência pontual |
| 2 - Baixo | 10% a 25% | Acúmulo sem restrição importante aparente |
| 3 - Moderado | 25% a 50% | Redução perceptível da seção |
| 4 - Alto | 50% a 75% | Possível comprometimento do escoamento |
| 5 - Crítico | Mais de 75% | Bloqueio significativo ou estrutura obstruída |

As faixas são regras iniciais de anotação. Não são limites oficiais e devem ser calibradas considerando largura, profundidade, vazão, tipo de estrutura e inspeção técnica.

## 8. Inteligência artificial e risco

> Esta seção apresenta uma proposta inicial, sujeita ao estudo e à validação pela equipe de desenvolvimento.

A visão computacional deve combinar detecção de objetos e segmentação. A detecção identifica itens individualizados, enquanto a segmentação estima a fração da água, margem ou seção ocupada pelo conjunto de resíduos.

Um item volumoso pode representar maior risco que dezenas de pequenas garrafas. Por isso, contagem e área ocupada devem permanecer separadas.

| Saída da IA | Exemplo |
|---|---|
| Classe predominante | Plástico misto |
| Objetos visíveis | 40 |
| Área ocupada | 32% |
| Posição | Retido sob ponte |
| Obstrução | Moderada |
| Confiança do modelo | 87% |

### 8.1. Índice inicial de risco hídrico

```text
R = 0,35O + 0,25C + 0,15N + 0,15M + 0,10H
```

Em que:

- `O`: obstrução;
- `C`: chuva recente;
- `N`: nível e velocidade de subida;
- `M`: influência da maré;
- `H`: recorrência histórica.

Cada componente deve ser normalizado entre zero e um. Os pesos são heurísticos e deverão ser recalibrados com ocorrências reais.

| Faixa | Risco | Ação sugerida |
|---|---|---|
| 0,00 a 0,20 | Muito baixo | Registrar e acompanhar |
| 0,21 a 0,40 | Baixo | Verificar na rotina |
| 0,41 a 0,60 | Moderado | Programar inspeção |
| 0,61 a 0,80 | Alto | Priorizar inspeção e limpeza |
| 0,81 a 1,00 | Crítico | Acionar avaliação imediata conforme protocolo |

## 9. Arquitetura funcional do aplicativo

![Integração entre observação, inteligência artificial, contexto hídrico e resposta operacional](assets/fluxo-aplicativo.png)

### 9.1. Módulos

| Módulo | Funções principais |
|---|---|
| Mapa | Canais, sub-bacias, estações, ocorrências, saneamento e áreas de risco |
| Coleta de campo | Foto, GPS, horário, orientação, observações e segurança |
| Visão computacional | Detecção, segmentação, classe, área, obstrução e confiança |
| Contexto hídrico | Chuva, nível, vazão, maré, vento e distância até a Baía |
| Contexto sanitário | Rede, coletor, ETE, descarga observada e indícios de esgoto |
| Risco e prioridade | Índice, explicação dos fatores e fila de inspeção |
| Validação | Correção humana, auditoria, antes e depois e resultado da limpeza |
| Painel | Mapa de calor, recorrência, tempo de atendimento e resíduos removidos |

## 10. Modelo mínimo de dados

| Entidade | Campos mínimos |
|---|---|
| Ocorrência | `id`, `data_hora`, `usuario`, `fonte`, `status`, `observacoes` |
| Localização | `id_ponto`, `nome_ponto`, `latitude`, `longitude`, `precisao_gps`, `canal`, `sub_bacia`, `margem`, `distancia_baia` |
| Imagem | `arquivo`, `orientacao`, `qualidade`, `data`, `hash`, `autorizacao_uso` |
| Resíduo | `classes`, `objetos`, `area`, `posicao`, `obstrucao`, `confianca` |
| Hidrologia | `chuva`, `nivel`, `vazao`, `tendencia`, `mare`, `vento`, `fontes` |
| Esgoto | `tubulacao_visivel`, `fluxo_sem_chuva`, `indicios`, `rede_prevista`, `destino`, `ete`, `confirmacao_laboratorial` |
| Risco | `componentes_normalizados`, `indice`, `classe`, `justificativa` |
| Intervenção | `responsavel`, `inspecao`, `retirada`, `massa`, `fotos_finais`, `tempo_resposta` |
| Proveniência | `fonte`, `data_aquisicao`, `licenca`, `validade`, `controle_qualidade` |

`nome_ponto`, `latitude` e `longitude` são campos obrigatórios e inseparáveis.

## 11. Fontes de dados

| Fonte | Conteúdo | Observação |
|---|---|---|
| Estudo da Marinha | Pontos, qualidade da água, sedimento, hidrocarbonetos e diagnóstico histórico | Referência de 2001 a 2003; requer atualização |
| DATA.RIO e Rio-Águas | Hidrografia, drenagem, sub-bacias, uso do solo e saneamento municipal | Base principal para o município do Rio |
| Alerta Rio | Chuva em tempo real e séries históricas | Associar estação à sub-bacia, não apenas ao ponto mais próximo |
| SIGA Baía de Guanabara | Camadas, estações, hidrografia, KML, shapefile e serviços ArcGIS | Base regional para toda a RH-V |
| INEA | Qualidade da água, IQA, dados brutos, alertas e Procon Água | Prioridade para validação ambiental |
| ANA HidroWeb e Atlas Esgotos | Estações, séries hídricas, ETEs, carga e corpos receptores | A API nova pode exigir credenciais |
| SINISA | Cobertura, volumes, redes, tratamento, extravasamentos e prestadores | Atualização anual; verificar o ano de referência |
| Marinha/CHM | Marés e informações hidrográficas | Aplicar às áreas sob influência estuarina |
| Concessionárias | Capacidade, obras, redes e operação | Distinguir dado medido, nominal e projetado |

## 12. O que pode ser usado no protótipo

1. Importar hidrografia, sub-bacias e limites da Baía em SIRGAS 2000.
2. Validar em imagem os pontos históricos do Canal do Mangue, Fundão, Galeão, Iguaçu e Caju.
3. Cadastrar pontos adicionais a montante no Canal do Cunha e nas áreas de maior recorrência.
4. Definir protocolo fotográfico com enquadramentos a montante, jusante, margens e seção transversal.
5. Montar conjunto inicial de imagens anotadas com classes de material, posição e obstrução.
6. Integrar chuva do Alerta Rio e maré oficial; adicionar nível onde houver estação adequada.
7. Implementar classificação, segmentação e exibição da confiança do modelo.
8. Calcular índice de risco explicável e permitir correção humana.
9. Testar no Canal do Mangue e no sistema Canal do Cunha/Fundão.
10. Registrar inspeção, limpeza e imagem posterior para validar o benefício operacional.

### 12.1. Critérios de aceite do MVP

- Localizar corretamente a ocorrência no canal e na sub-bacia.
- Classificar pelo menos cinco grupos: plástico, orgânico, madeira, volumoso e misto.
- Estimar a área ocupada e atribuir classe de obstrução.
- Apresentar chuva recente, maré e origem dos dados.
- Separar confiança da IA, indício de esgoto e risco hídrico.
- Permitir validação e correção por usuário autorizado.
- Exibir histórico antes e depois da limpeza.
- Funcionar com dados simulados claramente identificados quando uma integração estiver indisponível.

## 13. Limitações e controles

- As coordenadas históricas precisam de validação espacial antes do uso operacional.
- Fotografia não confirma presença de esgoto ou contaminante químico.
- O índice de risco é apoio à decisão e não substitui vistoria técnica ou alerta oficial.
- A ausência de sensor não significa ausência de risco; deve existir a opção de dado indisponível.
- Capacidade nominal de ETE e redução projetada não equivalem à vazão efetivamente tratada.
- Imagens devem evitar identificação desnecessária de pessoas, placas e residências.
- Registros cidadãos precisam de moderação, rastreabilidade e mecanismo contra duplicidade.
- Pontos de campo devem ser avaliados quanto a trânsito, margem instável, contaminação e segurança pública.

## 14. Conclusão

A contribuição hídrica do aplicativo está em conectar o que aparece na imagem ao funcionamento do canal e da bacia. A mesma quantidade de resíduos pode representar situações distintas conforme a largura, a chuva, a maré, o nível e a existência de pontes, grades ou bueiros. O sistema deve apresentar essa explicação de maneira transparente.

O estudo da Marinha fornece uma rede histórica coerente para iniciar a organização espacial e identificar setores mais vulneráveis. A atualização deve combinar as camadas atuais do DATA.RIO, SIGA Baía de Guanabara, INEA, ANA, SINISA, Marinha e concessionárias.

O protótipo deve concentrar-se no Canal do Mangue e no sistema Cunha-Fundão, onde é possível demonstrar a relação entre resíduos, esgoto, chuva, drenagem urbana e impacto sobre a Baía de Guanabara.

## Referências e portais

- EMGEPRON, Marinha do Brasil e Petrobras. *Monitoramento e prevenção da poluição hídrica da Baía de Guanabara*. Relatório técnico preliminar, atividades de 2001 a 2003.
- [DATA.RIO - Hidrografia](https://www.data.rio/datasets/hidrografia-2/about)
- [DATA.RIO - Sub-bacias hidrográficas](https://www.data.rio/datasets/4c62ab6686774fb3858a8ca27c38780a_0/about)
- [Alerta Rio - Dados pluviométricos](https://www.sistema-alerta-rio.com.br/download/dados-pluviometricos/)
- [SIGA Baía de Guanabara](https://sigaaguas.org.br/home/sigaguanabara/conheca.html)
- [INEA - Região Hidrográfica V Baía de Guanabara](https://www.inea.rj.gov.br/rh-v-baia-de-guanabara/)
- [ANA - HidroWebService](https://www.ana.gov.br/hidrowebservice/swagger-ui/index.html)
- [ANA - Atlas Esgotos](https://www.ana.gov.br/atlasesgotos/)
- [Ministério das Cidades - SINISA](https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/sinisa/resultados-sinisa/resultados-sinisa-2025)
- [Fundação Rio-Águas - Plano Municipal de Saneamento Básico](https://fundacaorioaguas.prefeitura.rio/wp-content/uploads/sites/48/2024/03/E2-Diagnostico-Sistemas-Existentes-Agua-e-Esgoto_APs-1-2-e-3-PMSB-AE.pdf)
- [Programa de Saneamento Ambiental - Coletores-tronco](https://psam.eco.br/implantacao-de-coletores-tronco)
- [Águas do Rio - Modernização da ETE Alegria](https://www.aguasdorio.com.br/ete-alegria-passa-por-modernizacao-inedita-para-aprimorar-o-tratamento-de-esgoto/)

---

**Local:** Rio de Janeiro  
**Data de referência:** setembro de 2026
