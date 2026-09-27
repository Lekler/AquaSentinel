# Publicação de teste no Cloud Run

Projeto: `aquasentinel-509900`. Use a branch
`feat/aquaverify-hotspots-corpos-hidricos`, mantendo `main` intacta.

O Dockerfile executa Streamlit na porta fornecida pelo Cloud Run e instala
PyTorch para CPU. O modelo e as imagens de interface entram no contêiner;
bancos, fotografias de usuários, logs e segredos ficam fora.

## Preparação

Execute os comandos na raiz desta branch, em uma conta com acesso ao projeto.
O projeto precisa de faturamento habilitado e permissões para Cloud Run,
Cloud Build e Artifact Registry. A publicação e a execução podem gerar custos.

```sh
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com \
  --project=aquasentinel-509900
```

## Criar o serviço de teste

```sh
gcloud run deploy aquasentinel-teste \
  --project=aquasentinel-509900 \
  --region=southamerica-east1 \
  --source=. \
  --port=8080 \
  --memory=2Gi \
  --cpu=1 \
  --concurrency=80 \
  --min-instances=0 \
  --max-instances=1 \
  --timeout=3600 \
  --session-affinity \
  --allow-unauthenticated
```

Esse comando cria um endereço público de teste. O limite de instâncias reduz
o escalonamento, mas não estabelece um teto financeiro. Não use fotos pessoais
ou dados reais no teste inicial.

## Persistência

Sem configuração de PostgreSQL, o aplicativo usa SQLite local. No Cloud Run,
esses arquivos são temporários e podem desaparecer quando a instância parar.
Esse modo serve apenas para teste descartável.

Antes de receber ocorrências reais, configure um PostgreSQL persistente e
forneça `AQUASENTINEL_DATABASE_URL`, `AQUASENTINEL_DATABASE_PASSWORD` e
`AQUASENTINEL_REVIEW_PASSWORD` por referências ao Secret Manager. Não coloque
senhas em arquivos versionados nem reutilize o banco oficial para testes.

## Conferência

Abra o endereço retornado e verifique Início, Sobre, Dúvidas, envio de foto,
análise e navegação ao mapa. Relatos só aparecem publicamente após revisão.
O endpoint `/_stcore/health` deve responder `ok`.

O Cloud Run limita a duração das conexões WebSocket; após o timeout, o navegador
pode reconectar e perder o rascunho da sessão. Relatos persistidos no PostgreSQL
continuam disponíveis. A afinidade de sessão é de melhor esforço.

Esta configuração ainda precisa de validação por build e execução no Cloud Run.

## Atualizar o serviço existente com esta versão

No Cloud Shell, baixe a nova branch em uma pasta separada. Isso preserva os
arquivos locais usados na primeira implantação em `~/AquaSentinel`.

```sh
git clone --branch feat/aquaverify-hotspots-corpos-hidricos --single-branch \
  https://github.com/Lekler/AquaSentinel.git ~/AquaSentinel-aquaverify
cd ~/AquaSentinel-aquaverify
git log -1 --oneline
gcloud run deploy aquasentinel \
  --project=aquasentinel-509900 \
  --source=. \
  --region=southamerica-east1 \
  --concurrency=80
```

Se a pasta já existir com esta branch, use `git pull --ff-only` dentro dela.
O deploy atualiza o serviço existente e preserva suas demais configurações.
O limite anterior de 8 requisições concorrentes com uma instância produziu
respostas 429 nos arquivos da interface; esta versão usa 80.

Antes de substituir uma instância com dados reais em SQLite, preserve os dados
e configure persistência. O Git não transfere registros ou fotos do banco.

Depois da publicação, recarregue o navegador e verifique: Bloqueando em preto,
legenda, duas camadas, filtros, clique no ponto e página de histórico do local.

Na área da equipe, cadastre os corpos hídricos para gerar os códigos WB-BG,
vincule os relatos existentes e use a indexação de fotos antigas em lotes.
Novas fotos recebem pHash ao salvar. Confira [AQUAVERIFY.md](AQUAVERIFY.md)
antes de interpretar os índices e o selo de persistência. Nenhuma foto antiga é
automaticamente agrupada por nome ou declarada falsa por similaridade.
