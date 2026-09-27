# AquaSentinela — MVP do hackathon

Aplicativo colaborativo para registrar resíduos em rios e canais da Baía de Guanabara. Esta versão reúne o novo site da equipe, detecção de plásticos em fotografias, localização, revisão humana, mapa de pontos revisados e o módulo experimental de chuva. O objetivo é apoiar **triagem de resíduos**, sem afirmar qualidade da água, doença ou risco de inundação.

**Autoria:** MVP inicial de previsão de chuva e priorização criado por Lekler para o AquaSentinel; interface, fluxo fotográfico e modelo recebidos da equipe e integrados nesta versão. O projeto foi organizado para que outras pessoas possam executar, estudar e adaptar o código.

## Executar no macOS

Requer Python 3.12. Na raiz do repositório:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

Abra o endereço local mostrado no terminal. Para Windows, use `setup.bat` e `run.bat`. O arquivo `models/best.pt` precisa estar presente; a primeira instalação baixa bibliotecas de IA e pode demorar. Sem PostgreSQL, o app usa SQLite em `dados/ocorrencias.sqlite3`, apenas para desenvolvimento local.

## Fluxo

1. **Início** apresenta o projeto.
2. **Registrar ocorrência** recebe uma foto, executa o detector de quatro classes de plástico, pede nome do local, coordenadas e o nível observado pela pessoa. O app solicita confirmação dos dados e autorização para publicação antes de salvar. A barra abaixo da foto acompanha a preparação, o carregamento do modelo e a identificação. O envio fica **pendente**; na confirmação, **Ir para o mapa** abre os registros públicos.
3. **Mapa e registros** mostra somente ocorrências **validadas por um revisor** e com autorização de publicação. A equipe acessa a fila com a senha configurada no ambiente. Relatos rejeitados permanecem no banco para auditoria, mas não aparecem no mapa.
4. **Chuva e ARI · experimental** mantém a integração Open-Meteo e os cálculos anteriores para estudo. Consultas são públicas; salvar, confirmar e consultar o histórico exigem a senha da equipe. O ARI é separado do WPS/CS e não é um alerta de inundação.

5. **Sobre** apresenta o projeto, seu funcionamento e os limites da análise.
6. **Dúvidas** reúne orientações sobre fotos, carregamento, localização, revisão e downloads.

O cabeçalho personalizado dá acesso às páginas sem exibir o menu padrão durante a navegação. O rodapé usa `assets/home/f.png` e `assets/home/g.png` em toda a largura.

O modelo `best.pt` reconhece `other_plastic`, `plastic_bag`, `plastic_bottle` e `plastic_package`. Ele **não** classifica a gravidade do acúmulo. Contagens e confiança de detecção não são massa, obstrução ou prova de autenticidade da foto.

## Metodologia de resíduos: WPS e CS

Esta implementação segue a metodologia WPS/CS fornecida pela equipe como **heurística experimental**, com as limitações abaixo:

| Componente | Cálculo no MVP |
|---|---|
| `W` | Nível informado e confirmado na revisão: sem resíduos 0, pouco 25, moderado 60, muito poluído/bloqueando 100 |
| `F` | 1 foto distinta validada = 25; 2 = 50; 3–4 = 75; 5 ou mais = 100 |
| `WPS` | `0,70 × W + 0,30 × F`, de 0 a 100 |
| `CS` | Confiança média das detecções × confiabilidade da fonte comunitária (0,8), exibida em % |

Para `F`, contam fotos distintas registradas nos últimos **30 dias**, a até **200 m**, com o mesmo código de corpo hídrico confirmado e revisão validada. SHA-256 impede reenvios idênticos; similaridades pendentes ou reutilizadas não ampliam F. Sem código confirmado, a frequência fica restrita ao próprio registro. **Não existe identidade verificada dos autores**: duas fotos podem vir da mesma pessoa. Por isso, `F` é uma aproximação de recorrência, não comprova independência nem aumento de poluição.

Faixas WPS: 0–24 baixa, 25–49 moderada, 50–74 alta, 75–100 crítica. Faixas CS: abaixo de 60% baixa, 60–79% moderada, 80% ou mais alta. A confiança do detector **não é probabilidade calibrada de acerto**. Todas as submissões usam confiabilidade 0,8; o app não concede 1,0 a quem apenas declara vínculo institucional. Sem detecções, o CS é 0 e exige interpretação humana. Ausência de pontos não prova ausência de resíduos.

Exemplo: W=100, F=75 e confiança média=94% produzem WPS=92,5 e CS=75,2%.

## Arquitetura e dados

Veja [AquaVerify e hotspots persistentes](docs/AQUAVERIFY.md) para regras,
pesos, limiares e limitações da nova versão. Na área autenticada de revisão,
cadastre os corpos hídricos, vincule os registros antigos e indexe fotos legadas
para pHash. Os códigos são internos ao projeto. O hotspot usa recorrência,
persistência temporal, WPS e qualidade da evidência; não é classificação de risco.

### Mapa, cobertura e histórico por local

- **Condição ambiental:** a cor representa o nível declarado na última observação
  do período: cinza = sem resíduos, verde = pouco, amarelo = moderado,
  laranja = muito poluído, preto = bloqueando. A legenda fica sempre visível
  junto ao mapa. Todos os marcadores têm raio fixo de 10 pixels.
- **Cobertura de observação:** uma camada independente em tons de azul representa
  dias distintos (1, 2–3, 4–7, 8+), não gravidade. Mais ocorrências não significam
  automaticamente mais poluição nem autores independentes.
- Filtros: 7, 15, 30, 90 dias e todo o período. Os limites são dias de calendário,
  incluindo hoje, no fuso `America/Sao_Paulo`; datas são as de registro, não uma
  comprovação do momento de captura. Datas futuras são excluídas dos resumos.
- Observações validadas e autorizadas são agrupadas pelo código `WB-BG` confirmado
  em até 200 m da primeira observação. Não há encadeamento espacial nem união por
  nome livre. Registros sem código confirmado ficam separados até vinculação.
  Isso identifica trechos aproximados, não delimita todo um corpo hídrico.
- Clique no ponto para foto, nível, data, objetos, confiança média, revisão,
  WPS e CS. A lista abaixo oferece o mesmo acesso ao histórico.
- `/local?id=<id-de-observacao-publica>` abre a página individual: totais,
  dias observados, primeira/última observação, nível recente e anteriores,
  principais resíduos e recorrência (dias com resíduos declarados / dias
  observados). O histórico completo independe do filtro do mapa.
- WPS aparece como número e barra separados da condição observada. A fórmula
  original foi mantida; em detalhes históricos é recalculada na data do registro,
  usando as fotos atualmente validadas dos 30 dias anteriores. Não é um snapshot
  de decisões passadas de revisão. CS mantém confiança média × 0,8.
- A quantidade total identificada soma detecções nas fotos: não deduplica objetos
  entre fotos. Dados pendentes, rejeitados e sem autorização ficam fora de todos
  os resumos e páginas públicas.

```text
app.py → Streamlit multipágina
app_pages/sobre.py e app_pages/duvidas.py → informações e ajuda
home_visual.py e registro_visual.py → cabeçalhos, fotos e rodapé
assets/ → imagens, estilos e recursos do mapa
app_pages/registrar.py → visao.py (YOLO) → relatos.py → SQLite/PostgreSQL
app_pages/mapa.py → revisão humana + wps.py → mapa público
painel_ari.py → previsao.py (Open-Meteo) + ari.py/motor.py → historico.py
```

`relatos_foto` guarda foto reduzida, foto anotada e metadados em uma transação; `ocorrencias` guarda as avaliações ARI. O banco antigo `relatos` de versões anteriores **não é apagado**, mas seus registros não são convertidos automaticamente para o novo fluxo fotográfico. Antes de uma migração, faça backup e defina uma regra para consentimento e revisão desses relatos.

Para usar PostgreSQL compartilhado, configure variáveis de ambiente ou [Secrets do Streamlit](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management):

```toml
AQUASENTINEL_DATABASE_URL = "postgresql://USUARIO@HOST:5432/postgres"
AQUASENTINEL_DATABASE_PASSWORD = "SENHA_DO_BANCO"
AQUASENTINEL_REVIEW_PASSWORD = "SENHA_DIFERENTE_PARA_REVISAO"
```

Não coloque valores reais no Git. A conexão usa TLS. Se a senha de revisão não estiver configurada, a revisão fica desabilitada. O banco SQLite local é efêmero em hospedagens como Streamlit Community Cloud; configure PostgreSQL para produção. O app em produção é atualizado automaticamente quando `main` muda no GitHub.

## Limitações e próximos passos

- O nível `W` é informado por pessoa e confirmado manualmente; falta um modelo treinado especificamente para severidade de acúmulo.
- Revisão por senha compartilhada é suficiente para demo curta, mas precisa virar autenticação individual e trilha de auditoria antes de operação real.
- Fotos, GPS e local são declarados/confirmados por usuários. Falta checagem de EXIF, área de cobertura, ponto hídrico padronizado e denúncias abusivas.
- Recorrência precisa deduplicar autores, fotos semelhantes e relatos quase simultâneos.
- Calibrar confiança do detector, pesos/faixas WPS e CS com exemplos locais rotulados.
- Integrar histórico hídrico, dados do Alerta Rio/INEA e chuva apenas como contexto, sem misturá-los à prioridade de resíduos até validação técnica.
- Definir retenção de fotos, proteção de dados, moderação e capacidade do banco para uso além do hackathon.

## Testar e contribuir

```sh
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
```

Veja [CONTRIBUTING.md](CONTRIBUTING.md). Não envie bancos locais, fotografias de usuários, senhas ou arquivos `.env` ao repositório. O modelo fornecido pela equipe está em `models/best.pt`; confirme a licença dos pesos antes de redistribuir o repositório publicamente.
