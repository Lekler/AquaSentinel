# Publicação de teste no Cloud Run

Projeto: `aquasentinel-509900`. Use a branch
`feat/interface-registro-sobre-duvidas`, mantendo `main` intacta.

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
  --concurrency=4 \
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
