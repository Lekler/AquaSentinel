# Validação da entrega

## Página inicial com identidade visual — 19/09/2026

- Substituída a home simples pela composição da referência com os 11 PNGs do usuário.
- Hashes dos PNGs copiados conferidos com os arquivos da pasta Imagens: iguais.
- Seis testes do fluxo fotográfico passaram após a troca da home.
- AppTest verificou o carregamento da home e o acesso a registro, mapa e ARI.
- Links e imagens embutidas inspecionados; SVGs são transportados como `img`
  porque o sanitizador de `st.html` remove SVG inline.
- CSS da home isolado por presença de `.aqua-page`; não troca o tema dos formulários.
- Layout com quebras para tablet e celular, menus HTML nativos e foco de teclado.
- Serviço local respondeu HTTP 200. Não houve inspeção visual em navegador:
  o inventário de navegadores da automação estava vazio. Fidelidade pixel a pixel
  e aparência real em dispositivos ainda não foram verificadas.

## Integração fotográfica — 19/09/2026

- 121 testes passaram em Windows/Python 3.12, incluindo os 99 testes anteriores.
- Novos testes: NMS entre classes, IDs, fronteiras da confiança, ausência de
  detecções, validação de imagens, hash independente dos metadados, coordenadas,
  reenvios idempotentes, Excel, recortes ZIP e navegação entre páginas.
- Fluxo de interface via Streamlit AppTest: upload, detecção, preenchimento,
  salvamento, leitura, downloads, vínculo ARI, troca por imagem inválida e
  preservação do rascunho ao navegar. Nova foto exige nova confirmação.
- Teste ponta a ponta adicional com `models/best.pt` real e frame 50 da gravação
  local `rodada_20260919_195907`: 8 itens, 58,55% de confiança média, triagem de
  baixa confiança. A foto foi salva em banco temporário, reaberta no mapa e
  vinculada ao ARI; o Excel reaberto tinha oito linhas de itens.
- Um frame anterior sem detecções produziu total zero e média ausente.
- `pip check`: nenhuma dependência quebrada.

O frame de teste já continha anotações do contador antigo: é um teste de integração,
não uma amostra apropriada para medir precisão. As evidências locais ficam em
`validacao_local/`, ignorada pelo Git, sem contaminar o banco de trabalho.

Não foi possível fazer inspeção visual no navegador, pois não havia navegador
conectado à automação. Captura por câmera e permissão/GPS real precisam de teste
no dispositivo. O fluxo de upload foi exercitado pelo AppTest, inclusive com a rede real.
Não há validação de autenticidade de imagens nem calibração do acúmulo/risco.

## Atualização ARI de 19/09/2026

99 testes passaram em Python 3.12.14 (1,61 s). A suíte cobre a fórmula composta,
normalização, ausência de nível, limites de chuva em 24h e de recorrência,
confiança, confirmação humana, persistência SQLite, IDs únicos, distância,
janela de 30 dias e transbordamento oficial mesmo sem previsão disponível.
Os testes de interface usam fonte meteorológica controlada e banco temporário.

As decisões sobre lacunas do rascunho e as limitações de fontes manuais estão
descritas no README. Esta validação verifica software, não calibra risco hidrológico.

## Registro da versão inicial

Executada em 15/09/2026, macOS Apple Silicon, Python 3.12.14, Streamlit 1.63.0.
Versões completas registradas em `requirements-lock.txt`.

## Resultado

- **55 testes passaram** (`python -m pytest -q`, 11,06 s).
- Cálculos: fronteiras de chuva e prioridade, fórmula e monotonicidade.
- Tempo/dados: hora exata, virada do dia, exclusão de intervalos passados/parciais, 24 horas completas, dados inválidos e probabilidade ausente.
- Cliente: parâmetros por coordenadas, timeout, conexão, HTTP 400/429/500/503 e JSON inválido.
- Interface: carregamento, consulta, mudança de Waste Score, reutilização de cache, mudança de coordenadas, bypass do cache, falha sem resultado antigo, recuperação e nome vazio.
- Consulta HTTPS real executada pelo cliente Python final e pelo formulário no navegador.
- Interface inspecionada visualmente em 1280 × 720: formulário, cartões, métricas e gráfico horário.
- Servidor iniciado em `http://localhost:8501`, restrito ao computador local.

## Evidência da consulta real

Ponto demonstrativo: -22.9068, -43.1729. Waste Score: 70.
Coleta: 2026-09-15T17:23:09.174716+00:00.
Janela: 2026-09-15T15:00:00-03:00 até 2026-09-16T15:00:00-03:00.

| Métrica | Resultado |
| --- | --- |
| Máximo horário | 5.9 mm/h |
| Acumulado 6h | 1.0 mm |
| Acumulado 24h | 12.9 mm |
| Pico de probabilidade | 82.0% |
| Rainfall Score | 50 — Moderada |
| Priority Score | 59.0 — Alta |

Este registro é evidência histórica do teste, não previsão atualizada. Novas consultas podem mudar conforme a hora e as atualizações do provedor. O aplicativo sempre consulta a API/cache e não lê este registro.

Não foram realizados testes de carga, validação hidrológica ou calibração com ocorrências reais. Os testes não demonstram capacidade de prever inundações.
