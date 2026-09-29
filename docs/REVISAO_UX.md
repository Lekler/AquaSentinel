# Registro e revisão

O cidadão envia uma foto, confirma a localização, escolhe a condição observada e pode incluir contexto ambiental. O resultado apresenta itens, classes e confiança, quando existem detecções. A ausência de detecção não é tratada como ausência comprovada de resíduos. Coordenadas manuais e informações opcionais ficam recolhidas.

O mapa usa [Esri World Street Map](https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer), com atribuições Esri e fontes creditadas no mapa. A instância Leaflet e seus tiles permanecem entre atualizações. Clique, arraste e edição de coordenadas atualizam o marcador; deslocamentos para fora da tela fazem pan, preservando zoom. O círculo usa apenas a precisão informada pelo GPS e some após salvar. Não indica a extensão da ocorrência.

A equipe entra com a senha configurada em AQUASENTINEL_REVIEW_PASSWORD. A sessão é local ao navegador, dura uma hora e é invalidada pela troca da senha. A interface só constrói as ferramentas depois de autenticar. Sair encerra o acesso da sessão.

A revisão segue: ocorrência, evidência, IA, localização, informações declaradas, qualidade e decisão. Uma caixa permite alternar entre a foto anotada e a original. Critérios, hashes e versões ficam em Ver detalhes técnicos. As regras de revisão, índices e agrupamento não mudaram.

Corpos hídricos recebem automaticamente códigos WB-BG. Nomes são comparados ignorando maiúsculas, acentos e espaços redundantes. A edição mantém o ID e rejeita nome já cadastrado. Tipo e nota são opcionais. Registros históricos guardam seu retrato original; o vínculo continua pelo ID, não pelo nome. A migração cria apenas a tabela adicional corpos_detalhes, tanto no SQLite quanto no PostgreSQL.

Validação automatizada cobre mapa persistente, precisão, descarte do componente, autenticação/saída/expiração, revisão, edição do catálogo, não exposição de ferramentas e fluxo de envio. Inspeção visual em navegador e implantação Cloud Run devem ser feitas após o build; não há navegador conectado nesta sessão.
