# 💧 AquaSentinel

MVP criado por [Lekler](https://github.com/Lekler) para avaliações de canais na Baía de Guanabara. O **AquaSentinel Risk Index (ARI)** combina resíduos, previsão de chuva, condição do rio e recorrência. A versão 2 implementa o documento “AquaSentinel Risk Index”, contextualizado pela reunião da equipe.

[![Testes](https://github.com/Lekler/AquaSentinel/actions/workflows/tests.yml/badge.svg)](https://github.com/Lekler/AquaSentinel/actions/workflows/tests.yml)

O ARI é experimental, não representa probabilidade de inundação nem alerta oficial. Os limiares precisam ser calibrados por bacia.

## Baixar e executar

[Baixar ZIP](https://github.com/Lekler/AquaSentinel/archive/refs/heads/main.zip), ou:

```bash
git clone https://github.com/Lekler/AquaSentinel.git
cd AquaSentinel
```

Repositórios privados exigem acesso de colaborador. Instale Python 3.12 e entre na pasta extraída ou clonada.

macOS/Linux:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run app.py
```

Abra http://localhost:8501. Encerre com Control+C. Internet é necessária para previsão e mapas, sem chave de API. SQLite está incluído no Python. `requirements-lock.txt` registra as versões da validação original; `requirements.txt` define faixas compatíveis.

## Demonstrar

1. Informe local, classe de resíduos e confiança. Classe/confiança são entradas manuais para futura integração com IA; nenhum modelo de imagem roda neste MVP.
2. Informe a condição do rio, se disponível. Se transcrita de fonte oficial, marque essa origem e identifique fonte/estação e horário observado.
3. Atualize a previsão. Veja o ARI, componentes, pesos e contribuições em **Como calculamos**.
4. Salve a ocorrência no histórico. Atualizar a previsão mantém a ocorrência atual. Use **Nova ocorrência** para outro relato no mesmo ponto; mudar nome/coordenadas também inicia outra ocorrência.
5. Relatos de confiança entre 60 e menos de 80% exigem confirmação humana, no formulário inicial ou no histórico, com identificação do responsável.
6. Novas ocorrências próximas consideram os relatos validados anteriores. O histórico mostra avaliações salvas, mapa de hotspots e exportação JSON.

O banco começa vazio. Confirmar um relato pendente o habilita para a recorrência futura; não recalcula seu ARI usando previsão antiga. Para uma avaliação atualizada, faça nova consulta.

## Fórmula

Componentes de 0–100:

| Componente | Regra |
| --- | --- |
| W — resíduos | Baixo 25; moderado 60; alto 100 |
| R — acumulado previsto em 24h | <10 mm: 0; 10–30: 25; >30–50: 50; >50–80: 75; >80: 100 |
| L — condição do rio | Vigilância 0; atenção 25; alerta 50; alerta máximo 75; transbordamento 100 |
| F — registros anteriores validados | 0: 0; 1: 25; 2–3: 50; 4–5: 75; 6 ou mais: 100 |

```text
ARI (0–1) = (0,40×W + 0,25×R + 0,25×L + 0,10×F) / 100
ARI exibido (0–100) = ARI × 100
```

Exemplo: W=60, R=50, L=50, F=50 → ARI=0,54 → 54/100 → Alto.

| ARI exibido | Classe | Cor | Interpretação |
| --- | --- | --- | --- |
| 0 ≤ ARI <25 | Baixo | Verde | Monitorar |
| 25 ≤ ARI <50 | Moderado | Amarelo | Intensificar monitoramento |
| 50 ≤ ARI <75 | Alto | Laranja | Avaliação prioritária |
| 75 ≤ ARI ≤100 | Crítico | Vermelho | Avaliação urgente recomendada |

Classificação antes do arredondamento. JSON: `ari` (0–1), `ari_score` (0–100), `ari_level`, `componentes`, `pesos_efetivos`, `contribuicoes`, `cobertura_pesos`, `parcial` e `versao_metodologia=ari-2`.

### Confiança

- C ≥80%: aceita.
- 60% ≤ C <80%: pendente até confirmação de responsável identificado.
- C <60%: excluída do ARI e recorrência, mesmo com confirmação marcada.

Confiança controla aceitação; não multiplica W nem comprova veracidade. O modelo e a conversão das detecções em classes serão integrados pela equipe.

### Nível ausente e transbordamento

Sem L, o componente fica `null`, nunca zero por conveniência. Calculamos **ARI parcial** dividindo a soma ponderada de W, R e F por 0,75. Pesos efetivos: 0,40/0,75; 0,25/0,75; 0,10/0,75. Cobertura original de 75% e condição parcial ficam visíveis. O resultado não equivale ao ARI completo e pode ficar numericamente maior.

Transbordamento informado como oficial com referência produz `avaliacao_urgente=true` e hotspot vermelho independentemente do ARI. O índice numérico é preservado. A sinalização funciona também com erro da API ou relato pendente/excluído. A origem oficial é declarada pelo operador: o MVP não consulta/verifica o INEA automaticamente. Confira a atualidade da observação e sua referência.

### Recorrência

Contamos IDs distintos aceitos ou confirmados nos últimos 30 dias, em raio configurável (padrão 500 m), usando distância Haversine. Incluímos os limites de raio e de 30 dias; excluímos a ocorrência atual, relatos futuros e confirmações posteriores ao instante analisado.

Reenviar o mesmo ID não duplica nem sobrescreve a ocorrência salva. Relatos novos criados propositalmente no mesmo ponto contam separadamente; deduplicação por foto/identidade é futura. Ausência de relatos nesta instalação não significa ausência de problemas na região. O histórico não é um catálogo completo de enchentes e não é compartilhado entre computadores.

## Decisões sobre lacunas do documento

- “25–29” deixava 30–49 sem classe: adotado **25 a menos de 50**.
- “>6” omitia seis registros: adotado **6 ou mais**.
- Faixas de chuva sobrepostas: limite superior na faixa inferior (30→25; 50→50; 80→75).
- Escalas 0–1 e 0–100: ambas são explícitas, incluindo os extremos.
- Janela de 30 dias e raio padrão de 500 m são escolhas de protótipo.
- ARI parcial com pesos reajustados é uma decisão desta implementação; o rascunho não definia a política sem L.
- As interrogações na confiança foram resolvidas com triagem e confirmação registradas.
- Poluição Q continua pendente, pois ainda não há normalização ou peso definido.

Essas decisões precisam ser revisadas pela equipe e calibradas por bacia.

## Previsão e falhas

Cliente real: `https://api.open-meteo.com/v1/forecast`, latitude/longitude, `hourly=precipitation,precipitation_probability`, `timezone=auto`, `timeformat=unixtime`, `forecast_days=3`, `precipitation_unit=mm`. Cache de 45 minutos por coordenadas, máximo 128 entradas, com opção de ignorar cache. Timeout: conexão 5s, leitura 20s.

O timestamp do provedor representa o fim do intervalo de precipitação. Usamos 24 intervalos futuros completos a partir da próxima hora cheia UTC (ou a própria hora, se exata). Consulta às 12h30 no Rio usa 13h de hoje até 13h de amanhã. A soma de 6h usa os primeiros seis intervalos. Datas são mostradas no fuso retornado. Coleta não é emissão do modelo.

Erros HTTP, timeout, JSON inválido, unidades erradas ou precipitação incompleta impedem ARI e geram mensagem explícita. Probabilidade incompleta fica `null`, com aviso, sem afetar R. Não há atualização em segundo plano. Relatos pendentes/excluídos dispensam a consulta meteorológica.

`max_1h_mm`, `acumulado_6h_mm`, `acumulado_24h_mm`, `precipitation_probability_peak` e `horas` continuam disponíveis. Agora `rainfall_score` é R do acumulado de 24h. A classificação horária anterior está em `rainfall_intensity_score` e `rainfall_intensity_level`. O campo legado `level` continua sendo a categoria horária; use `ari_level` para o índice. Os antigos `priority_score`/`priority_level` saem da exportação principal. `calcular_prioridade` permanece em `motor.py` somente para compatibilidade.

## Estrutura e extensão

- `ari.py`: regras puras, normalização, triagem e urgência.
- `historico.py`: SQLite, confirmação e contagem espacial/temporal.
- `motor.py`: métricas meteorológicas e funções legadas.
- `previsao.py`: cliente HTTP.
- `app.py`: formulário, explicações, gráfico, histórico e hotspots.
- `tests/`: testes automatizados.

Banco padrão: `dados/ocorrencias.sqlite3`, ignorado pelo Git. A variável `AQUASENTINEL_DB` permite outro caminho. Faça backup do arquivo para preservar os relatos. O banco é criado na primeira abertura. Revisão registra responsável e horário; o MVP local não autentica revisores. As avaliações salvas são retratos históricos, não alertas atualizados automaticamente.

A IA pode fornecer classe e confiança a `calcular_ari`; uma integração hidrológica pode fornecer condição, referência e proveniência. Mapas e planos técnicos da equipe permanecem no repositório como referências, ainda sem alimentar L ou Q automaticamente.

Próximos passos: modelo de imagem; fonte oficial com controle de defasagem; identificação de bacias; definição de Q; autenticação; histórico compartilhado; calibração retrospectiva. Consulte [CONTRIBUTING.md](CONTRIBUTING.md).

## Testes

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Os testes usam banco temporário e previsão controlada, sem rede e sem alterar o histórico real. Cobrem fórmulas, fronteiras, confiança, persistência, recorrência, revisão, reenvios e transbordamento com falha de API. [VALIDACAO.md](VALIDACAO.md) contém o registro da demo inicial.

## Fontes e autoria

Proposta: documento “AquaSentinel Risk Index”, recebido em 19/09/2026. Notas da reunião usadas como contexto; a transcrição pessoal não foi publicada.

Dados: [Open-Meteo](https://open-meteo.com/en/docs), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Confira as [condições para uso comercial](https://open-meteo.com/en/pricing). As categorias horárias legadas se baseiam no [Alerta Rio](https://websempre.rio.rj.gov.br/estacoes/); as faixas novas de R são limiares do protótipo, não oficiais.

Copyright © 2026 Lekler. [Licença MIT](LICENSE). Sem credenciais embutidas. Coordenadas são enviadas ao Open-Meteo; mapas carregam recursos externos; ocorrências e revisores ficam no banco local e nas exportações.
