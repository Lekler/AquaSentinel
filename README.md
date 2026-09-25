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
2. **Registrar ocorrência** recebe uma foto, executa o detector de quatro classes de plástico, pede nome do local, coordenadas e o nível observado pela pessoa. O app solicita confirmação dos dados e autorização para publicação antes de salvar. O envio fica **pendente**.
3. **Mapa e registros** mostra somente ocorrências **validadas por um revisor** e com autorização de publicação. A equipe acessa a fila com a senha configurada no ambiente. Relatos rejeitados permanecem no banco para auditoria, mas não aparecem no mapa.
4. **Chuva e ARI · experimental** mantém a integração Open-Meteo e os cálculos anteriores para estudo. Consultas são públicas; salvar, confirmar e consultar o histórico exigem a senha da equipe. O ARI é separado do WPS/CS e não é um alerta de inundação.

O modelo `best.pt` reconhece `other_plastic`, `plastic_bag`, `plastic_bottle` e `plastic_package`. Ele **não** classifica a gravidade do acúmulo. Contagens e confiança de detecção não são massa, obstrução ou prova de autenticidade da foto.

## Metodologia de resíduos: WPS e CS

Esta implementação segue a metodologia WPS/CS fornecida pela equipe como **heurística experimental**, com as limitações abaixo:

| Componente | Cálculo no MVP |
|---|---|
| `W` | Nível informado e confirmado na revisão: sem resíduos 0, pouco 25, moderado 60, muito poluído/bloqueando 100 |
| `F` | 1 foto distinta validada = 25; 2 = 50; 3–4 = 75; 5 ou mais = 100 |
| `WPS` | `0,70 × W + 0,30 × F`, de 0 a 100 |
| `CS` | Confiança média das detecções × confiabilidade da fonte comunitária (0,8), exibida em % |

Para `F`, contam fotos distintas registradas nos últimos **30 dias**, a até **200 m**, com o mesmo nome de corpo hídrico e revisão validada. O hash da imagem reduz reenvios idênticos. **Não existe identidade verificada dos autores**: duas fotos podem vir da mesma pessoa. Por isso, `F` é uma aproximação de recorrência, e a independência entre relatos deve ser validada antes de uso operacional. O nome do corpo hídrico é texto livre; padronizar esse identificador é um próximo passo.

Faixas WPS: 0–24 baixa, 25–49 moderada, 50–74 alta, 75–100 crítica. Faixas CS: abaixo de 60% baixa, 60–79% moderada, 80% ou mais alta. A confiança do detector **não é probabilidade calibrada de acerto**. Todas as submissões usam confiabilidade 0,8; o app não concede 1,0 a quem apenas declara vínculo institucional. Sem detecções, o CS é 0 e exige interpretação humana. Ausência de pontos não prova ausência de resíduos.

Exemplo: W=100, F=75 e confiança média=94% produzem WPS=92,5 e CS=75,2%.

## Arquitetura e dados

```text
app.py → Streamlit multipágina
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
