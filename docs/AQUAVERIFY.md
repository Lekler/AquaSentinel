# AquaVerify, corpos hídricos e persistência observada

Esta versão acrescenta regras experimentais transparentes. Não classifica um
local como “risco”, não autentica denúncias e não prevê eventos ambientais.

## Cadastro e identificação

A equipe autenticada cadastra nomes padronizados em **Mapa → Área da equipe de
revisão**. O banco atribui códigos internos permanentes `WB-BG-001`, `WB-BG-002`
etc. Não são códigos oficiais nem contêm delimitações geográficas. Inclua
município/trecho no nome para distinguir homônimos. A normalização evita criar
duas entradas que diferem somente em acentos, espaços ou maiúsculas.

O usuário escolhe um código ou “Não identificado”. O nome livre permanece como
descrição do ponto. A equipe confirma a associação na revisão ou vincula um
registro antigo; cada mudança de vínculo guarda responsável, data e ID anterior.
Somente o código confirmado + proximidade de até 200 m da âncora definem o grupo.
Registros sem confirmação ficam isolados, mesmo com nomes iguais. Não há migração
automática por nome. O catálogo deve usar o mesmo PostgreSQL persistente dos relatos.

## AquaVerify v1

O índice 0–100 mede completude e qualidade documental, não probabilidade de a
denúncia ser verdadeira. Alta ≥ 75; média ≥ 45; baixa < 45. Não é calibrado.

| Critério | Máximo | Regra |
|---|---:|---|
| Imagem válida | 20 | Arquivo decodificado/validado pelo servidor |
| Resolução | 10 | Menor lado ≥480 px: 10; ≥240 px: 5; abaixo: 0 |
| Detecção | 10 | Ao menos um objeto reconhecido; ausência não invalida relato |
| Confiança da IA | 15 | Média das detecções × 0,15 |
| Localização | 10 | GPS do navegador confirmado: 10; manual/ajustada: 3 |
| Precisão GPS | 5 | Até 50 m: 5; até 200 m: 2; ausente/pior: 0 |
| Duplicidade/similaridade | 10 | Índice completo, imagem informativa e nenhuma correspondência pendente |
| Data/hora | 5 | Envio registrado pelo servidor; EXIF opcional sem bônus |
| Revisão humana | 15 | Validação pela equipe |

GPS e EXIF são metadados declarados, não comprovação do local/data. Alterar as
coordenadas remove a contribuição de GPS. Evidências legadas sem informação
recebem zero naquele critério; informações não são inventadas.

## SHA-256 e pHash

O SHA-256 dos pixels orientados continua sendo a identidade exata, com restrição
única no banco. Um reenvio idêntico retorna o registro original, sem sobrescrever.

O pHash independente usa DCT das imagens em escala de cinza 32×32, bloco de baixas
frequências 8×8 e mediana sem DC. Distância de Hamming ≤6 gera uma candidata.
Há assinaturas da imagem inteira e de recortes em grade de 80% e 60%, comparando
inteira↔inteira e inteira↔recorte. Imagens quase uniformes não geram equivalência.
O método cobre redimensionamento, recompressão e várias pequenas alterações ou
recortes, mas não todos os recortes arbitrários, montagens ou grandes rotações.
Pode produzir falsos positivos/negativos; nunca conclui fraude ou falsidade.

A comparação ocorre ao analisar e novamente na transação de salvamento, incluindo
fotos privadas/pendentes para evitar reenvios. O público recebe apenas o aviso;
fotos e detalhes das candidatas só aparecem na área autenticada da equipe.
Salvamentos são serializados durante a comparação para tratar envios simultâneos.

Fotos anteriores sem pHash são sinalizadas como índice incompleto. A equipe usa
**Indexar / reavaliar similaridade das fotos antigas** (lotes de até 100 imagens,
sem rodar YOLO novamente). Repita até completar. A rotina reconcilia correspondências
cronologicamente e invalida decisões antigas se surgirem novas candidatas.
O revisor pode resolver uma candidata como independente/falso positivo ou reutilizada,
com justificativa. Não há exclusão automática. Similaridades não resolvidas ou
reutilizadas não aumentam a frequência WPS nem a persistência.

Referências técnicas: [pHash — desenho e limites](https://phash.org/docs/design.html),
[pHash — assinatura perceptual](https://phash.org/docs/howto.html),
[Pillow — manipulação de imagens](https://pillow.readthedocs.io/en/stable/reference/Image.html).

## Hotspot persistente v1

A classificação tem janela fixa de 90 dias e independe do filtro do mapa. Usa
somente relatos públicos validados, corpo hídrico confirmado, AquaVerify ≥60,
pHash informativo, comparação histórica completa e ausência de similaridade
pendente/reutilizada. SHA idêntico conta uma vez. Não comprova autores independentes.

Cada dia (America/Sao_Paulo) tem um voto: o relato elegível mais recente daquele dia.
Todos os critérios abaixo precisam ser atendidos:

1. Pelo menos 3 dias diferentes com resíduos declarados.
2. Intervalo de pelo menos 14 dias entre primeiro e último dia com resíduos.
3. Resíduos em pelo menos 60% dos dias elegíveis observados.
4. WPS mediano dos dias com resíduos ≥50, recalculado na data de cada relato.
5. AquaVerify mediano ≥60.
6. Último relato público elegível, ainda com resíduos e há no máximo 30 dias.
7. Um único corpo hídrico confirmado no trecho.

O selo, contagens, última observação e motivos ficam nos detalhes e na página do
local. O mapa permite filtrar somente hotspots persistentes; cor e tamanho dos
pontos continuam representando a camada selecionada, não este selo.
Sem cumprir os critérios, aparece “Persistência em acompanhamento”. Isso não
significa ausência de problema. Mais ocorrências não significam mais poluição.
As datas são as de registro; persistência observada não significa monitoramento contínuo.

## Explicabilidade e revisão

As telas e a planilha AquaVerify explicam quantidade, confiança média, baixa
confiança (<60%), faixa intermediária (<80%), limite de detecções, coordenadas,
identificação do corpo hídrico e pendências de similaridade. Caixas sobrepostas
são removidas por IoU >0,55 mantendo a mais confiante, dentro de cada foto.
Essa deduplicação não equivale a contar objetos únicos entre fotografias.
Todos os relatos continuam exigindo revisão antes da publicação.
