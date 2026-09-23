# 💧 AquaSentinela

Site experimental para moradores e equipes registrarem **focos de lixo em canais da Baía de Guanabara**. O fluxo principal tem duas telas: envio de foto e localização; mapa dos relatos revisados. A equipe confere os envios antes de exibi-los publicamente.

Este MVP foi iniciado por [Alexandre Rodrigues (Lekler)](https://github.com/Lekler). A identidade visual e as artes enviadas pela **Alessandra Vaz dos Anjos Santos** estão em `Imagens/`. A interface atual segue o escopo acordado na 3ª reunião da equipe (19/09/2026).

[![Testes](https://github.com/Lekler/AquaSentinel/actions/workflows/tests.yml/badge.svg)](https://github.com/Lekler/AquaSentinel/actions/workflows/tests.yml)

## O que funciona

- Envio ou captura de foto pelo navegador do celular, nome do local e coordenadas.
- Compressão da foto e remoção dos metadados EXIF antes de gravá-la.
- Triagem visual **manual e provisória**: baixo, moderado ou alto. As cores do mapa mostram essa classificação somente após revisão humana.
- Fila de revisão protegida por senha da equipe; relatos rejeitados não aparecem no mapa.
- Banco SQLite para teste local ou PostgreSQL para vários usuários em uma implantação online.

**Ainda não há modelo de IA conectado, fórmula final do W-index, GPS automático, login de cidadãos/órgãos nem relatório PDF.** A opção “equipe/órgão” é autodeclarada e não recebe confiança adicional. O mapa não expressa risco de enchente nem diagnóstico de qualidade da água. A chuva e o ARI v2 anteriores ficam preservados em `legacy_app.py` e descritos em [README-ARI-v2.md](README-ARI-v2.md), fora da experiência principal.

## Executar no macOS

Instale Python 3.12 e, na pasta do projeto:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
export AQUASENTINEL_ALLOW_LOCAL_DB=1
export AQUASENTINEL_REVIEW_PASSWORD='defina-uma-senha-forte-aqui'
python -m streamlit run app.py
```

Abra `http://localhost:8501`. O banco local fica em `dados/relatos.sqlite3` e não entra no Git. Para alterar seu caminho, use `AQUASENTINEL_DB`. A senha de revisão é necessária apenas para validar ou rejeitar relatos.

## Publicar durante o hackathon

Recomendação: **Streamlit Community Cloud + PostgreSQL gerenciado**, como Supabase. O código pode continuar no repositório privado; no Streamlit, configure o aplicativo como público para que qualquer pessoa com o link consiga abrir. O serviço exige que a conta Streamlit tenha acesso ao repositório GitHub. O arquivo inicial é `app.py`, na branch `main`, com Python 3.12 e dependências em `requirements.txt`.

1. Crie um projeto PostgreSQL e copie a conexão **Session pooler (porta 5432)** no painel do provedor. No Supabase, esse modo aceita IPv4; a conexão direta pode depender de IPv6.
2. Entre em [share.streamlit.io](https://share.streamlit.io/), conecte sua conta GitHub e crie um app a partir de `Lekler/AquaSentinel`, `main`, `app.py`.
3. Em **Advanced settings → Secrets**, adicione, com seus valores reais:

```toml
AQUASENTINEL_DATABASE_URL = "postgresql://USUARIO:SENHA@HOST:5432/postgres"
AQUASENTINEL_REVIEW_PASSWORD = "uma-senha-longa-e-exclusiva"
```

4. Publique o app e teste em um telefone: enviar foto, revisar com a senha, abrir o mapa em outra sessão. Confirme que o relato continua lá após reiniciar o app.
5. Torne o app **público** nas configurações de compartilhamento e divulgue seu endereço `*.streamlit.app`.

Nunca salve a senha ou a URL do banco no repositório. O app só aceita envios quando encontra um banco PostgreSQL ou quando a opção local de desenvolvimento está explicitamente ativa. O Streamlit Community Cloud não garante persistência de arquivos locais; por isso SQLite não é indicado para os relatos online. O projeto PostgreSQL deve ser monitorado quanto a espaço, especialmente por conter fotos comprimidas.

**Antes de divulgar:** defina a senha de revisão, confirme o funcionamento do banco externo, faça o teste de ponta a ponta e verifique os termos de uso para fotos reais. A senha da equipe é uma solução temporária para o hackathon; o login institucional precisará de autenticação individual e verificação de vínculo.

## Estrutura

| Arquivo | Papel |
| --- | --- |
| `app.py` | Site responsivo de envio, mapa e revisão |
| `relatos.py` | Validação, imagens e armazenamento SQLite/PostgreSQL |
| `Imagens/` | Identidade visual da Alessandra |
| `legacy_app.py`, `ari.py`, `historico.py`, `motor.py`, `previsao.py` | Protótipo anterior de chuva e ARI, preservado para referência |
| `tests/` | Testes automatizados |

Para executar os testes: `python -m pip install -r requirements-dev.txt` e `python -m pytest -q`.

## Próximos passos da equipe

1. Integrar o modelo de imagem e a fórmula final do W-index, com confiança e possibilidade de correção humana.
2. Obter localização do navegador com consentimento e permitir ajustar o ponto no mapa. Fotos capturadas no navegador não garantem GPS no EXIF.
3. Implementar contas para pessoas e órgãos, com verificação institucional e trilha de auditoria por revisor.
4. Acrescentar proteção contra relatos repetidos e abuso, política de retenção e remoção de imagens.
5. Gerar relatório PDF após estabilizar os campos e a pontuação.

Contribuições são bem-vindas; consulte [CONTRIBUTING.md](CONTRIBUTING.md). Licença [MIT](LICENSE).
