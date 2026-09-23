# Como contribuir com o AquaSentinela

O AquaSentinela foi iniciado por [Lekler](https://github.com/Lekler) como um MVP de hackathon. A identidade visual enviada pela Alessandra está em `Imagens/`. A base foi organizada para receber novos módulos de forma incremental.

## Fluxo sugerido

1. Crie uma branch a partir de `main`: `git switch -c tipo/resumo-da-mudanca`.
2. Instale as dependências de desenvolvimento: `python -m pip install -r requirements-dev.txt`.
3. Implemente uma mudança pequena e focada.
4. Execute `python -m pytest -q`.
5. Abra um pull request explicando o problema, a solução e como a mudança foi testada.

Prefixos úteis para branches: `feat/`, `fix/`, `docs/`, `test/` e `refactor/`.

## Organização do código

- `app.py`: envio de fotos, mapa público e revisão.
- `relatos.py`: validação de dados, imagem e persistência.
- `legacy_app.py`, `motor.py`, `previsao.py`: demonstração anterior de chuva, fora do fluxo principal.
- `tests/`: testes automatizados.

Mantenha regras de pontuação e persistência fora da camada visual. Mudanças na pontuação W devem vir acompanhadas da definição acordada pela equipe, atualização do README e testes de fronteira.

## Novos módulos

As próximas integrações são reconhecimento de resíduos, GPS com consentimento, contas individuais, revisão com trilha de auditoria e relatório PDF. Não atribua maior confiabilidade a um relato apenas porque o remetente declarou ser de um órgão. O mapa atual usa uma triagem visual provisória, não um índice validado de risco à saúde.

## Dados e credenciais

Não envie chaves, tokens, arquivos `.env`, `.streamlit/secrets.toml`, fotos de usuários, dados pessoais ou bases restritas para o repositório. Documente novas variáveis no README sem valores secretos.

Ao adicionar uma fonte, registre origem, licença, unidade, fuso, frequência de atualização e comportamento quando os dados estiverem ausentes.
