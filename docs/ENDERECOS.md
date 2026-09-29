# Localização por endereço, CEP e GPS

O primeiro atalho das páginas internas é Mapa e Registros. Em Registrar ocorrência e Cadastrar trecho, a localização pode ser escolhida por CEP/endereço, GPS ou clique/arraste no mapa. Latitude e longitude ficam em Ajustar coordenadas manualmente.

A busca acontece somente ao clicar em Buscar endereço. Ela sugere o primeiro resultado e permite selecionar outro. O CEP é consultado no [ViaCEP](https://viacep.com.br/); rua/bairro/cidade resultantes são buscados no [Photon](https://github.com/komoot/photon). Endereços completos vão diretamente ao Photon, limitado a resultados no Brasil. Nenhuma foto é enviada a esses serviços.

Resultados são aproximados: CEP pode representar uma rua ou município; número de imóvel pode não existir na base. Confira o marcador antes de salvar. A sugestão não recebe precisão GPS e não ganha pontuação de geolocalização. O GPS continua usando a posição e precisão fornecidas pelo navegador somente após clicar no botão e autorizar. O mapa aceita ajuste manual depois de qualquer modalidade.

Os resultados são armazenados em cache por 24 horas (até 512 consultas). Chamadas externas são serializadas e espaçadas em pelo menos 1,1 segundo por processo. Não há busca automática a cada tecla. O servidor público Photon permite uso moderado e não garante disponibilidade; para maior demanda, configure uma instância própria/serviço compatível em AQUASENTINEL_PHOTON_URL (URL completa do endpoint /api/). A interface mantém GPS e mapa disponíveis quando uma consulta falha.

A ocorrência fotográfica e o trecho usam estados separados. Uma foto já salva não bloqueia o mapa de cadastro de trecho. A busca preenche o nome da ocorrência quando vazio ou previamente preenchido pela própria busca; um nome editado pela pessoa é preservado.

O endereço público do Cloud Run não é alterado por esta versão. É possível configurar um [domínio próprio](https://docs.cloud.google.com/run/docs/mapping-custom-domains), com domínio e DNS sob controle do projeto. A conta local disponível nesta sessão não teve permissão para consultar o serviço aquasentinel-509900; a publicação deve ser feita pelo Cloud Shell autorizado.
