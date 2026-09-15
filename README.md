# 💧 AquaSentinel

**MVP executável de previsão de chuva e priorização de ocorrências em canais urbanos.** Interface em português, consulta real ao Open-Meteo e cálculo transparente de pontuações. Feito em Python 3.12 + Streamlit para demonstrar sem separar frontend e backend.

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-MVP-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Licença MIT](https://img.shields.io/badge/licen%C3%A7a-MIT-2EA44F)](LICENSE)
[![Testes](https://github.com/Lekler/AquaSentinel/actions/workflows/tests.yml/badge.svg)](https://github.com/Lekler/AquaSentinel/actions/workflows/tests.yml)

Criado por **[Lekler](https://github.com/Lekler)** para o projeto AquaSentinel. Este repositório começa com o módulo de *rainfall forecast* e priorização e foi estruturado para que o time possa baixar, testar, adaptar e adicionar novos módulos.

> A prioridade é uma heurística operacional para apoiar vistorias. Não representa probabilidade de inundação, alerta oficial, diagnóstico hidráulico ou orientação de segurança.

## Baixar e executar

Você pode [baixar a versão mais recente em ZIP](https://github.com/Lekler/AquaSentinel/archive/refs/heads/main.zip) e descompactar, ou clonar o repositório:

```bash
git clone https://github.com/Lekler/AquaSentinel.git
cd AquaSentinel
```

Como o repositório está privado, o download e o clone exigem uma conta GitHub autorizada como colaboradora.

### macOS e Linux

Pré-requisitos: Python 3.12 e internet para instalar dependências e consultar a previsão. Se necessário, instale o Python pelo [site oficial](https://www.python.org/downloads/macos/) ou com `brew install python@3.12` se já usar Homebrew.

No Terminal, entre na pasta extraída ou clonada:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Abra **http://localhost:8501**. Para encerrar, use `Control+C` no Terminal. Para reiniciar, ative `.venv` e repita o último comando. Não é necessário banco de dados, serviço externo de backend ou chave de API.

Alternativa com [uv](https://docs.astral.sh/uv/): `uv venv --python 3.12 .venv`, `uv pip install --python .venv/bin/python -r requirements.txt` e `.venv/bin/python -m streamlit run app.py`.

### Windows (PowerShell)

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

`requirements.txt` contém faixas compatíveis. `requirements-lock.txt`, quando presente, registra as versões efetivamente testadas e pode substituir esse arquivo na instalação.

## Adaptar e ampliar

As regras de negócio ficam em `motor.py`, isoladas da interface, e o cliente meteorológico fica em `previsao.py`. Assim, o time pode trocar o Streamlit por FastAPI ou outro frontend sem reescrever o cálculo.

Para contribuir, crie uma branch a partir de `main`, faça uma alteração pequena e focada, execute os testes e abra um pull request. Consulte [CONTRIBUTING.md](CONTRIBUTING.md) para o fluxo sugerido. Ideias futuras e decisões técnicas estão em **Próximos passos** no fim deste documento.

## Roteiro de demo (2 minutos)

1. Informe nome do canal, latitude/longitude e Waste Score. O ponto inicial é demonstrativo, no Rio; não identifica um canal real cadastrado.
2. Clique em **Atualizar previsão**. A consulta usa as coordenadas informadas e previsão real — não há dados simulados de fallback.
3. Mostre as três pontuações, intensidade máxima, acumulados de 6h/24h e gráfico horário.
4. Mude o Waste Score e atualize: para a mesma localização, a previsão vem do cache de até 45 minutos; a prioridade é recalculada.
5. Abra **Como calculamos** para explicar a fórmula. Em **Dados da consulta**, baixe o JSON para integrar com o app do time.
6. Para uma consulta nova à API, marque **Consultar API sem usar cache**. Evite repetir sem necessidade.

Sem chuva no dia da apresentação, o resultado real pode ser baixo ou zero. Para explicar um cenário intenso, use o exemplo matemático abaixo, explicitamente hipotético; o aplicativo não troca previsão real por cenário fictício.

## Arquitetura

```text
Formulário Streamlit: nome + latitude/longitude + Waste Score
    → validação de entrada
    → cache em memória por coordenadas (45 min, máximo 128 entradas)
    → cliente HTTPS Open-Meteo (timeout de conexão e leitura)
    → seleção de 24 intervalos futuros completos
    → métricas + Rainfall Score + Priority Score
    → cartões, níveis, gráfico, tabela e download JSON
```

- `app.py`: interface, cache e estado da última consulta por sessão.
- `previsao.py`: requisição HTTP e erros explícitos.
- `motor.py`: validação, janela temporal, métricas e regras puras reutilizáveis em FastAPI.
- `tests/`: testes de cálculos, contrato HTTP e fluxo da interface.
- `.streamlit/config.toml`: tema, uso local e telemetria do Streamlit desativada.

A separação permite reaproveitar o motor em um endpoint futuro sem reescrever as regras. O MVP não expõe uma API HTTP de negócio: usa o próprio servidor Streamlit.

## Integração Open-Meteo

Endpoint: `https://api.open-meteo.com/v1/forecast`.

Parâmetros: `latitude`, `longitude`, `hourly=precipitation,precipitation_probability`, `forecast_days=3`, `timezone=auto`, `timeformat=unixtime`, `precipitation_unit=mm`. A seleção de modelo é a padrão do provedor. Três dias garantem espaço para uma janela futura de 24h mesmo perto da meia-noite.

A documentação do Open-Meteo define `precipitation` como o total da **hora anterior ao timestamp**. O MVP interpreta cada registro como um intervalo terminado naquele instante, calcula em UTC e exibe o fuso retornado pela API.

**Janela:** começa na próxima hora cheia UTC (ou na hora atual quando a consulta ocorre exatamente na hora cheia). Se a consulta for às 12h30 no Rio, são analisados os intervalos de 13h–14h até 12h–13h do dia seguinte. A primeira soma de 6h vai de 13h a 19h. Isso exclui a hora parcialmente passada, sem inventar uma distribuição sub-horária. O horário exato da janela está visível. Em locais cujo fuso não é múltiplo de uma hora, o alinhamento UTC pode corresponder a meia hora local.

| Campo JSON | Definição |
| --- | --- |
| `max_1h_mm` | Máximo dos 24 totais horários; equivalente à intensidade média máxima em mm/h para intervalos de 1h. |
| `acumulado_6h_mm` | Soma dos seis primeiros intervalos da janela, não a maior soma móvel. |
| `acumulado_24h_mm` | Soma dos 24 intervalos. |
| `precipitation_probability_peak` | Máxima probabilidade horária na janela; não é a probabilidade de chover em qualquer momento das 24h. |
| `rainfall_score`, `level` | Pontuação e categoria obtidas de `max_1h_mm`. |
| `priority_score`, `priority_level` | Pontuação e nível de prioridade operacional. |
| `janela_inicio`, `janela_fim`, `timezone` | Cobertura temporal com fuso. |
| `consultado_em`, `calculado_em` | Horários da coleta HTTP e do cálculo. Coleta não é emissão do modelo. |
| `horas` | Série de intervalos, precipitação e probabilidade para auditoria. |

### Erros, ausência de dados e cache

- Timeout, conexão, HTTP 429/4xx/5xx, JSON inválido e formato inesperado geram mensagem explícita; não geram chuva zero.
- Precipitação ausente, negativa, não finita, unidades erradas ou cobertura incompleta impedem o cálculo.
- Probabilidade `null` em qualquer hora deixa o pico como **Indisponível** (`null` no JSON), com aviso; volume e score continuam disponíveis. Probabilidade não participa da fórmula.
- São rejeitadas séries com horários duplicados, fora de ordem ou com lacunas.
- Uma consulta que falha remove o resultado anterior, evitando apresentá-lo como resposta atual.
- O cache guarda a resposta por até 45 minutos por coordenadas, em memória do servidor. Ao atualizar, a janela é calculada de novo com a hora atual. Reiniciar o processo limpa o cache. Não há atualização automática em segundo plano.
- O resultado exibido é um retrato da última consulta. O usuário precisa atualizar; a interface mostra horário da coleta e sinaliza idade ≥ 45 min quando é renderizada.
- Timeout configurado: 5s de conexão e 20s de leitura, sem tentativas automáticas.

## Pontuação de chuva

A [legenda oficial do Alerta Rio](https://websempre.rio.rj.gov.br/estacoes/) apresenta as categorias de intensidade. **A conversão dessas categorias para score de 0 a 100 é uma heurística do MVP, não uma pontuação oficial do Alerta Rio.**

| Intensidade de referência (mm/h) | Categoria | Rainfall Score |
| --- | --- | ---: |
| < 0,2 | Sem chuva significativa (rótulo do MVP) | 0 |
| 0,2–5,0 | Fraca | 25 |
| 5,1–25,0 | Moderada | 50 |
| 25,1–50,0 | Forte | 75 |
| > 50,0 | Muito forte | 100 |

**Precisão e lacunas:** a legenda é expressa com uma casa decimal. Para valores de maior precisão não arredondamos antes de classificar: `5 < x <= 25` recebe 50, `25 < x <= 50` recebe 75. Assim 5,01 recebe 50 e 25,01 recebe 75. Este fechamento contínuo das lacunas é uma decisão explícita do MVP. Os limites 5,0, 25,0 e 50,0 ficam na faixa inferior.

As categorias são aplicadas ao máximo horário previsto; não ao acumulado de 6h ou 24h. A probabilidade não multiplica o score. Todas essas decisões podem ser calibradas após avaliação com dados locais.

## Prioridade operacional

```text
l = WasteScore / 100
r = RainfallScore / 100
p = 100 × (0,6·l + 0,2·r + 0,2·l·r)
```

Faixas **criadas para o MVP**: baixa `p < 25`; média `25 ≤ p < 50`; alta `50 ≤ p < 75`; crítica `75 ≤ p ≤ 100`. Calcula-se o nível antes do arredondamento; o score é exibido/exportado com duas casas decimais.

Exemplo hipotético: Waste Score 70 e máximo horário de 30 mm → Rainfall Score 75 → `100 × (0,42 + 0,15 + 0,105) = 67,5` → prioridade **Alta**.

A fórmula cresce com chuva e resíduos. Sem resíduos, chuva máxima produz prioridade 20; com resíduos máximos e sem chuva, produz 60. Isso expressa o foco operacional em resíduos. Não corresponde a segurança do local nem a risco hidrológico.

## Testes

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Os testes automatizados não precisam de rede e usam respostas controladas. Verificam fronteiras de classificação, fórmula, janela futura, ausência de dados, falhas HTTP, cache por coordenadas e sucesso/erro na interface Streamlit. Para verificar a integração real manualmente:

```bash
python -c 'from previsao import consultar_previsao; from motor import analisar_previsao; import json; print(json.dumps(analisar_previsao(consultar_previsao(-22.9068, -43.1729)["dados"]), ensure_ascii=False, indent=2))'
```

Veja `VALIDACAO.md` para os resultados efetivamente executados na entrega.

## Limitações

- Previsão de modelo em grade: coordenada solicitada não implica medição no próprio canal. A célula meteorológica pode ser diferente da coordenada exata.
- `precipitation` inclui chuva, pancadas e equivalente de neve. É um indicador prático no contexto do Rio, não uma seleção de chuva líquida para todos os climas.
- A previsão tem incerteza; acumulados recentes observados, nível/vazão, bacia, declividade, impermeabilização e capacidade do canal ainda não entram no modelo.
- Waste Score é manual. Não há reconhecimento de imagem, persistência de ocorrências, ranking de múltiplos canais, autenticação ou notificações.
- “Crítica” é somente uma faixa de prioridade interna, não um estágio oficial da cidade.
- Nomes e Waste Score ficam em memória da sessão; coordenadas são enviadas ao provedor. O JSON exportado contém dados da ocorrência. Não há credenciais embutidas.
- O endpoint gratuito público é destinado a uso não comercial; antes de uso comercial, confirme o plano e os limites na [página de preços](https://open-meteo.com/en/pricing). Atribuição do provedor permanece visível na interface.

## Próximos passos

1. Cadastrar canais e bacias contribuintes, validar coordenadas e vincular foto, severidade e confiança do modelo de resíduos.
2. Integrar chuva **observada** das estações do Alerta Rio: verificar meio de acesso, termos, frequência, qualidade e defasagem; associar estações à bacia, sem confundir observação com previsão. Começar pelo [portal de estações](https://websempre.rio.rj.gov.br/estacoes/) e pela [página institucional](https://www.sistema-alerta-rio.com.br/).
3. Incorporar histórico hídrico com identificadores comuns, fuso, unidades e tratamento de faltantes: precipitação antecedente, nível, vazão e capacidade do canal. Não atribuir peso arbitrário ao histórico sem validação.
4. Avaliar retrospectivamente a prioridade contra ocorrências e vistorias conhecidas; ajustar pesos/limiares com agentes comunitários e especialistas. Só então estudar um modelo específico de risco de inundação.
5. Expor um endpoint FastAPI reutilizando `motor.py` e `previsao.py`; adicionar banco de dados, fila de atualizações, cache compartilhado e ranking de canais.

## Referências

- [Open-Meteo — API e semântica das variáveis](https://open-meteo.com/en/docs)
- [Open-Meteo — atribuição e licença](https://open-meteo.com/en/terms)
- [Alerta Rio — legenda de intensidade](https://websempre.rio.rj.gov.br/estacoes/)

Fontes consultadas em 15/09/2026. O MVP não é afiliado ao Alerta Rio ou ao Open-Meteo.

## Licença e autoria

Copyright © 2026 Lekler. O código é disponibilizado sob a [Licença MIT](LICENSE), permitindo uso, estudo, modificação e redistribuição com preservação do aviso de copyright e da licença.
