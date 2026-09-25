# Como contribuir com o AquaSentinel

O AquaSentinel foi iniciado por [Lekler](https://github.com/Lekler) como um MVP de hackathon. A base foi organizada para receber novos módulos de forma incremental.

## Fluxo sugerido

1. Crie uma branch a partir de `main`: `git switch -c tipo/resumo-da-mudanca`.
2. Instale as dependências de desenvolvimento: `python -m pip install -r requirements-dev.txt`.
3. Implemente uma mudança pequena e focada.
4. Execute `python -m pytest -q`.
5. Abra um pull request explicando o problema, a solução e como a mudança foi testada.

Prefixos úteis para branches: `feat/`, `fix/`, `docs/`, `test/` e `refactor/`.

## Organização do código

- `app.py`: interface Streamlit e cache.
- `motor.py`: validação, métricas e regras de pontuação.
- `previsao.py`: integração com Open-Meteo.
- `tests/`: testes automatizados.

Mantenha regras meteorológicas e de negócio fora da camada visual. Mudanças em fórmulas, pesos ou faixas devem vir acompanhadas de justificativa, atualização do README e testes de fronteira.

## Novos módulos

Integrações com histórico hídrico, Alerta Rio, reconhecimento de resíduos, persistência, autenticação e notificações devem manter a diferença entre:

- previsão meteorológica;
- observação de chuva ou nível;
- prioridade operacional;
- risco hidrológico validado.

Não apresente a prioridade heurística do MVP como alerta oficial ou previsão de inundação.

## Dados e credenciais

Não envie chaves, tokens, arquivos `.env`, dados pessoais ou bases restritas para o repositório. Documente variáveis de ambiente necessárias em um arquivo `.env.example` sem valores secretos.

Ao adicionar uma fonte, registre origem, licença, unidade, fuso, frequência de atualização e comportamento quando os dados estiverem ausentes.
