# Mapeamento da página inicial — referência enviada pelo usuário

Inspeção visual realizada em todos os 11 PNGs. Origem:
`C:/Users/PGD SE7/Downloads/AquaSentinel-main/AquaSentinel-main/Imagens`.
Este documento mapeia a montagem; não altera o site nem os arquivos de imagem.

## Estrutura da referência

Referência visual de 1536 × 1152 px. Coordenadas abaixo são aproximações visuais,
medidas a partir do canto superior esquerdo, e não posições fixas para todas as telas.
Margens laterais do conteúdo próximas de 75 px. Fundo branco com tons azulados suaves.

| Bloco | Região aproximada (x, y, largura, altura) | Conteúdo |
|---|---|---|
| Cabeçalho | 75, 15, 1385, 85 | Logo à esquerda; Sobre, Como funciona, Mapa, Dúvidas e menu de três pontos à direita |
| Apresentação: texto | 75, 140, 730, 440 | Selo Faça a diferença, título, descrição e dois botões |
| Apresentação: arte | 640, 100, 896, 585 | Paisagem, frase, mão, celular e balão; composição na lateral direita |
| Introdução dos passos | 75, 620, 1050, 75 | É muito simples + frase de apoio |
| Cartões | 75, 710, 1390, 245 | Três etapas e um cartão de participação |
| Faixa de benefícios | 75, 980, 1390, 78 | Linha divisória e quatro benefícios alinhados |
| Rodapé decorativo | 0, 1055, 1536, 97 | Ondas; assinatura Água limpa move vidas no canto direito |

## Correspondência de todos os arquivos

| Arquivo exato | Conteúdo visual conferido | Aplicação na página |
|---|---|---|
| `Logo.png` | Gota com olho, nome AquaSentinela e slogan já incorporados | Cabeçalho, canto superior esquerdo. Usar a marca completa uma vez, sem repetir nome/slogan como texto ao lado |
| `mão e fundo.png` | Paisagem da baía, mão, celular com foto de lixo, frase Rios vivos, cidades melhores e balão Juntos por águas mais limpas para todos | Arte principal do lado direito. Os textos e detalhes do celular estão dentro do PNG e não devem ser adicionados outra vez |
| `F1.png` | Câmera azul com lente branca | Primeiro cartão, acima de Tire uma foto; região visível do ícone perto de x=210–287, y=735–800 |
| `F2.png` | Pino azul/verde sobre um mapa dobrado | Segundo cartão, acima de Confirme a localização; perto de x=560–654, y=729–803 |
| `F3.png` | Três barras crescentes turquesa | Terceiro cartão, acima de Informe o nível; perto de x=920–976, y=734–791 |
| `F4.png` | Grupo de três pessoas, arco e raios | Quarto cartão azul-claro, acima do texto Sua participação fortalece...; perto de x=1260–1350, y=725–805 |
| `F1.1.png` | Folha em degradê verde/turquesa | Primeiro benefício, à esquerda de Cidadãos engajados; perto de x=117–157, y=1007–1050. Reutilizar em tamanho pequeno no selo Faça a diferença, perto de x=90–115, y=150–178 |
| `F2.2.png` | Alvo circular azul/turquesa | Segundo benefício, à esquerda de Ações mais rápidas; perto de x=456–500, y=1006–1051 |
| `F3.3.png` | Três linhas onduladas azuis/turquesa | Terceiro benefício, à esquerda de Rios e Baía mais limpos; perto de x=830–891, y=1011–1050 |
| `F4.4.png` | Contorno de coração turquesa | Quarto benefício, à esquerda de Tecnologia a serviço do bem comum; perto de x=1185–1232, y=1006–1053 |
| `g.png` | Duas camadas de ondas azul-claras | Faixa decorativa na base, ocupando a largura total. Este arquivo não contém a assinatura Água limpa move vidas |

## Conteúdo dos cartões

1. `F1.png` + círculo 1 + **Tire uma foto**: Registre o lixo ou resíduo no rio, canal ou na baía.
2. `F2.png` + círculo 2 + **Confirme a localização**: O local é identificado pelo seu celular.
   Na implementação, preservar a alternativa manual quando o GPS não estiver disponível.
3. `F3.png` + círculo 3 + **Informe o nível**: Diga o quanto de resíduo há no local.
   Etiquetas: Pouco (verde), Moderado (amarelo), Muito (laranja), Bloqueando (vermelho).
4. `F4.png`, sem círculo numerado: Sua participação fortalece um ambiente mais saudável
   para as pessoas e a vida marinha. Fundo azul-claro e pequena onda decorativa embaixo.

## Faixa inferior, da esquerda para a direita

1. `F1.1.png`: **Cidadãos engajados** / Mais olhos pelos nossos rios.
2. `F2.2.png`: **Ações mais rápidas** / Informações que viram impacto.
3. `F3.3.png`: **Rios e Baía mais limpos** / Um futuro melhor pra todos.
4. `F4.4.png`: **Tecnologia a serviço do bem comum**, dividido em duas linhas.

## Elementos feitos no código, sem PNG específico

- Links do menu e botão arredondado com três pontos.
- Fundo arredondado e texto do selo Faça a diferença; folha vem de `F1.1.png`.
- Título Viu lixo em um rio ou canal? / Mostre pra gente., com azul-marinho e turquesa.
- Texto Uma foto ajuda a identificar pontos que precisam de atenção e contribui para
  proteger nossos rios e a Baía de Guanabara.
- Botão Registrar ocorrência: fundo em degradê, câmera branca e seta branca.
  A câmera branca do botão é diferente da ilustração azul `F1.png`.
- Botão Ver mapa: fundo claro, contorno azul/turquesa, mapa de traço azul e seta azul.
  Esse mapa simples é diferente do pino sobre mapa de `F2.png`.
- Título É muito simples e texto Em poucos passos, você registra e nos ajuda a cuidar das nossas águas.
- Cartões, sombras, bordas, números 1/2/3 e seus círculos azuis.
- Etiquetas coloridas dos quatro níveis.
- Separadores horizontais e verticais da faixa de benefícios.
- Pequeno traço ondulado sob o cartão de participação.
- Assinatura Água limpa move vidas e pequeno traço ondulado à direita.

## Tamanhos, transparência e cuidados de montagem

| Arquivos | Dimensões originais | Observação |
|---|---|---|
| Todos os `F*.png` | 1254 × 1254 | O desenho ocupa áreas diferentes em cada arquivo; a caixa externa igual não significa tamanho visual igual |
| `Logo.png` | 2172 × 724 | Marca completa com margens transparentes |
| `g.png` | 2172 × 724 | Grande área transparente acima das ondas; não usar toda a altura como espaçamento do rodapé |
| `mão e fundo.png` | 1448 × 1086 | Uma composição única; precisa caber sem esticar nem cortar o celular |

Todos possuem canal alfa e pixels transparentes reais. Há pequenas sobras de
recorte, halos claros/coloridos e pontos dispersos em alguns contornos, especialmente
nos ícones lineares e na arte principal. Isso não é fundo preto: o visualizador
mostra a transparência sobre preto. Conferir as bordas sobre o fundo final branco.

Na implementação, alinhar pelo desenho visível, compensando as margens transparentes,
e manter a proporção. Não esticar os quadrados para preencher o espaço dos cartões.
Os PNGs fornecidos são versões dos elementos da referência, não recortes idênticos
em todos os detalhes: a marca usa olho e algumas ilustrações têm desenho/proporção próprios.

Como a arte principal já contém textos rasterizados, reduzir muito essa composição
no celular reduz a legibilidade desses textos. No desktop ficará à direita; em telas
estreitas, deverá ir abaixo do texto principal, sem cobrir título ou botões.

Os textos principais, botões e cartões continuam elementos reais do site. Os
arquivos decorativos terão texto alternativo adequado ou vazio quando redundantes.
Os destinos funcionais principais permanecem: Registrar ocorrência → fluxo de foto;
Ver mapa/Mapa → mapa e registros. A avaliação ARI continua acessível na navegação.
