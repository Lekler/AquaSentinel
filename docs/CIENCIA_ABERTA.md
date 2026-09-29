# Ciência aberta, contexto ambiental e páginas internas

A branch `feat/ciencia-aberta-layout-one-health` inclui as versões anteriores.
O CSS novo é aplicado somente onde existe o cabeçalho interno. Não altera a
inicial, seus assets ou a configuração global de tema.

## Conteúdo editorial

Sobre reúne problema, propósito, ciência cidadã, IA, One Health, público-alvo,
equipe e visão de impacto. A galeria da equipe agora identifica os integrantes,
com a foto e uma mini-bio de Alexandre Rodrigues já incluídas; as demais fotos
continuam como espaços reservados até confirmação individual. Há ainda seis
espaços editoriais para equipe, Baía, campo, drones, desenvolvimento e testes.
Os espaços e legendas estão em `app_pages/sobre.py`. O tutorial está em Como
funciona e o menu interno permite acessar todas as páginas.

Fale Conosco só mostra contatos configurados: `AQUASENTINEL_CONTACT_EMAIL` e
`AQUASENTINEL_CONTACT_URL` (HTTPS). Sem configuração, informa indisponibilidade.
Não há formulário que simule envio nem mensagens enviadas automaticamente.

## One Health Context v1

Sinais opcionais: animal próximo ao resíduo, vegetação, fauna aquática, aves,
espuma, mancha superficial, possível descarga/efluente e outro sinal ambiental.
São declarações, não detecções confirmadas, diagnóstico ou identificação causal.
Ausência de preenchimento significa não informado. Não alteram índices ou
prioridades. A visualização separa ambiente, fauna/ecossistema e dimensão humana;
esta última trata participação e segurança, sem coletar sintomas.

## Exportação e autorização

Dados públicos usam a mesma regra do mapa: revisão validada e consentimento
de publicação. Para dados próprios, o participante fornece um ou mais pares
`ID; código privado`. Cada acesso é revalidado no banco. Não se infere autoria
por IP, nome ou localização. O recibo é uma credencial de posse e não verifica
identidade pessoal. Códigos ficam na sessão do navegador/servidor durante o uso;
o botão Limpar acesso remove a autorização dessa sessão. Não entram nos arquivos.

Filtragem por datas inclusivas no fuso de Brasília, corpo hídrico, nível,
etapa e revisado/não revisado. A seleção da origem não amplia a autorização.
Os formatos contêm a mesma seleção de ocorrências fotográficas. Sessões sem
foto continuam acessíveis em Monitoramento, não são inventadas como fotografias.

CSV usa UTF-8 com BOM e vírgula. Excel inclui aba Dicionário. GeoJSON usa
FeatureCollection e Point em WGS84, ordem longitude/latitude. Geometria inválida
é nula. A lista explícita de campos exclui tokens, hashes de recibos e detalhes
privados de similaridade. Campos textuais perigosos para fórmulas recebem
apóstrofo em CSV/Excel. JSON preserva os textos originais.

O dicionário completo (`dados_abertos.DICIONARIO`) informa unidades, significado
e tipos de cada campo plano. Nulos significam indisponibilidade; zeros são
valores efetivamente informados/calculados. Listas em CSV/Excel usam texto JSON.

## Perfil interno aqua-observation-v1

Inspirado no [OGC SensorThings 1.1](https://docs.ogc.org/is/18-088/18-088.html),
sem API OGC, Datastreams/Sensors completos ou declaração de conformidade.

| Objeto/campo | Significado e unidade |
| --- | --- |
| Observation.id | ID textual da ocorrência |
| Observation.phenomenonTime | Nulo: não existe instante de captura verificado |
| Observation.resultTime | Instante de registro em ISO 8601; não data de captura comprovada |
| Observation.result.nivel | Categoria declarada pelo participante |
| Observation.result.objetos | Contagem de detecções na fotografia |
| Location.location | Ponto GeoJSON, graus WGS84, longitude/latitude |
| Location.encodingType | Formato da geometria |
| FeatureOfInterest.id/name | Código/nome do corpo hídrico ou referência da ocorrência sem vinculação |
| FeatureOfInterest.feature | Ponto de observação; não geometria completa do corpo hídrico |
| ObservedProperty | Lista de propriedades observadas com nome e unidade |
| metadata.schema | Versão do perfil interno |
| metadata.capture_time_verified | False: captura não autenticada |
| metadata.sensorthings_conformant | False: perfil interno, não certificação |
| metadata.record | Campos planos definidos no dicionário |

Os [princípios FAIR](https://www.go-fair.org/fair-principles/) orientam IDs,
acesso definido, formatos e proveniência. A licença dos dados/fotos ainda
precisa de decisão da equipe. Acesso público não implica licença irrestrita.

## Índices e compatibilidade

Novos registros salvam WPS v1, CS v1 e AquaVerify v1 em `versoes_indices`.
As fórmulas vigentes não mudaram. `indices_snapshot` guarda WPS/CS no envio e
na revisão, data do cálculo e versões, usando a janela temporal da ocorrência.
O mapa mantém avaliação dinâmica; novos vínculos/revisões do histórico podem
produzir valores diferentes do retrato exportado. AquaVerify exporta o valor
armazenado, não uma estimativa de verdade. Campos ausentes em legados permanecem
ausentes/nulos; não há migração que invente versões anteriores.

Veja [CHANGELOG.md](CHANGELOG.md). A inicial é preservada por escopo de CSS e
ausência de alterações em `inicio.py`, `home_visual.py` e `assets/home.css`.
