# Transparência, monitoramento e acompanhamento

Versão do aplicativo: `2026.09-transparencia-v1`. Mantém os recursos de mapa,
histórico, AquaVerify, pHash e hotspots da versão anterior.

## Páginas e acesso

- `/transparencia`: metodologia, IA, dados, limitações, revisão humana, versões
  e seis indicadores gerais. Disponível também no menu inicial e em “Explorar e acompanhar”.
- `/monitoramento`: iniciar/retomar/encerrar sessões estruturadas e consultar
  sessões públicas revisadas. Não é um ranking de participantes.
- `/lacunas`: mapa dos trechos cadastrados no plano, incluindo trechos nunca observados.
- `/acompanhamento`: feedback privado por ID + código do recibo.
- A página de cada local inclui ações, antes/depois e rastreabilidade das fotos.

## Rastreabilidade e privacidade

Novos registros guardam versão do aplicativo e metodologia; novas análises
guardam o nome dos pesos e a versão do runtime Ultralytics. O SHA-256 do modelo
continua sendo o identificador exato dos pesos. Na consulta da observação são
mostrados ID, data de envio, hash da imagem/modelo, versões, coordenadas, origem,
precisão GPS quando aplicável, revisor, status e eventos do ciclo de vida.
Versões ausentes em dados legados não são inventadas. Eventos legados reconstruídos
a partir dos metadados são identificados como tal. Hashes não provam autenticidade.

Ao salvar um novo relato, o participante baixa um recibo com ID e código aleatório
privado. O servidor armazena somente SHA-256 do código. Não há recuperação de
códigos perdidos nem atribuição retroativa a registros antigos. O formulário de
acompanhamento exige o código mesmo para pendentes/rejeitados; ID sozinho não dá acesso.
O site mostra validação e posição temporal do relato no grupo nos 30 dias anteriores
ao envio, considerando o conjunto atualmente validado. Não há e-mail ou mensagem
automática, conta individual ou ranking por volume de denúncias.

## Seleção de localização

Durante a seleção, o círculo Leaflet tem raio igual à precisão GPS (metros)
quando disponível e válida. Seleção manual ou ajuste do marcador passa a mostrar
um círculo de referência de 25 m, explicitamente sem significado de precisão GPS.
Após salvar, o componente fica somente com o marcador nas coordenadas persistidas,
sem círculo nem arraste. Os mapas públicos também não mostram círculo de precisão.

## Planejamento e sessões estruturadas

A equipe autenticada cadastra trechos com código próprio, corpo hídrico WB-BG,
nome, ponto de referência e extensão planejada em metros. A coordenada é uma
referência, não uma geometria completa ou delimitação oficial.

O participante escolhe um trecho, autoriza publicação e inicia a sessão. Início e
fim são horários do servidor. O recibo privado da sessão permite retomá-la em outro
navegador. Na página de fotos, o modo estruturado vincula os novos relatos à sessão;
corpo hídrico/trecho vêm da sessão. Cada foto continua exigindo revisão individual.
O modo oportunístico permanece disponível e não gera taxas por esforço.

Ao encerrar, o participante declara extensão efetivamente observada, confirma
cobertura e que evitou repetir os itens em fotos sobrepostas. Fotos novas não podem
ser vinculadas a sessões encerradas. Não há pausa: duração é o tempo decorrido de
início a fim, e não uma medida automaticamente verificada de tempo ativo.

Taxas são disponibilizadas somente se a sessão estiver encerrada e validada,
a cobertura declarada, e todas as fotos vinculadas forem públicas, validadas, do
corpo hídrico confirmado e sem reutilização/similaridade pendente:

- itens/m = soma de detecções aceitas ÷ extensão efetivamente observada;
- itens/100 m = itens/m × 100;
- itens/min = soma de detecções aceitas ÷ duração da sessão.

Não há deduplicação garantida de objetos entre fotos. São taxas de detecções
fotográficas declaradas, não uma estimativa validada da densidade real de resíduos.
Fotos rejeitadas ou pendentes deixam as taxas indisponíveis, não iguais a zero.

Uma sessão pode ser encerrada sem fotos se houver declaração explícita de que o
trecho foi observado sem resíduos; requer revisão humana. Fotos com resíduos ou
detecções incompatíveis impedem essa declaração. Após validação e confirmação
de cobertura, a sessão zero tem taxas zero e conta como observação no mapa de lacunas.

## Lacunas e observações sem resíduos

Fotos “Sem resíduos” permanecem no histórico e na cobertura. O mapa principal
permite ocultar esses locais na camada ambiental sem remover os registros.
O mapa de lacunas usa trechos planejados, não toda a região nem todos os rios.

- Não temos dado: nenhuma observação pública validada do trecho.
- Sem observação recente: última observação há 30 dias ou mais.
- Pouco observado: 1–3 dias diferentes nos últimos 30 dias.
- Muito observado: 4+ dias diferentes nos últimos 30 dias.

Datas usam America/Sao_Paulo. Vários uploads e sessões no mesmo dia contam um dia.
Mostra idade da última observação e “Este trecho precisa de nova observação” nos
trechos sem dado ou sem observação recente. “Nenhum resíduo visto” depende de uma
declaração validada, nunca da ausência de registros ou detecções.
Fotos oportunísticas usam corpo hídrico confirmado e até 200 m do ponto de referência;
sessões usam seu trecho cadastrado. Trechos próximos podem ter áreas sobrepostas.

## Ações e ciclo de vida

A equipe registra limpeza, vistoria, intervenção ou mobilização, com data/hora,
descrição pública e responsável, vinculada a um relato validado de um corpo confirmado.
A comparação escolhe a última observação pública anterior e a primeira posterior
no mesmo grupo e mostra foto, nível, WPS e variação. Um lado ausente é “não temos
observação”, nunca zero. Datas são de envio, não de captura comprovada. Comparação
é descritiva: não atribui causalidade à ação, nem declara o local resolvido automaticamente.

As etapas disponíveis são recebida, aguardando revisão, validada, recorrente,
encaminhada, ação realizada, acompanhamento e resolvida; rejeitada preserva a
decisão negativa de revisão. Recebimento/revisão geram eventos automaticamente.
A equipe atualiza etapas posteriores com justificativa pública. Registrar uma ação
documenta um evento; a etapa “ação realizada” é confirmada separadamente pela equipe.
É possível reabrir uma resolvida para acompanhamento/recorrência, preservando eventos.
Uma ocorrência pendente não pode ser marcada resolvida. A senha é compartilhada;
nome do responsável não equivale a uma identidade individual autenticada.

## Indicadores e persistência

Total recebido, total validado e recebidos em 30 dias contam relatos fotográficos.
Corpos monitorados incluem relatos públicos confirmados e sessões públicas validadas,
inclusive as explicitamente sem resíduos. Hotspots e total de objetos usam apenas
relatos públicos validados. A soma de objetos pode contar o mesmo objeto em fotos distintas.

Novas tabelas `aqua_entidades` (trechos/sessões/ações) e `aqua_eventos` são criadas
sem apagar ou sobrescrever o histórico existente. Usam o mesmo SQLite/PostgreSQL
configurado. SQLite de Cloud Run continua temporário: use PostgreSQL persistente
e preserve dados reais antes de substituir a instância.
