# Validação da entrega

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
