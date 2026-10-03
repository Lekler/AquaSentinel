# Acervo de apresentação

21 imagens fornecidas pelo responsável pelo projeto, analisadas pelo mesmo
`models/best.pt` e pela mesma supressão de sobreposições do envio normal.
O modelo identificou 56 objetos neste processamento; isso não é uma avaliação
de precisão (não foram fornecidas anotações de referência).

As cinco fotos de equipe preservam os nomes dos arquivos originais.

## Geografia e proveniência

Os títulos descrevem o conteúdo visual. As localizações são referências
aproximadas atribuídas para demonstração, não locais comprovados de captura.
Não há validação de campo nem classificação humana de poluição nesses registros.
Cada JSON inclui fonte geográfica, origem da localização, hash da foto, hash
do modelo, parâmetros e resultados reais de inferência. A fonte respalda a
existência do rio/bairro, não a associação com a fotografia nem coordenadas GPS.
As consultas Overpass foram recusadas pelos servidores; não foi realizada
validação cartográfica de cada coordenada contra a geometria do rio.

Fontes: Prefeitura de Nova Iguaçu (trechos do Rio Botas), Prefeitura de Belford
Roxo (Heliópolis), INEA (bacia Iguaçu/Botas), documento municipal de Duque de
Caxias (Sarapuí), Prefeitura do Rio e MultiRio (orlas da Ilha do Governador).
Links específicos ficam em `fonte_geografica` de cada registro.

O mapa tem dois conjuntos: **Acervo de imagens** e **Ocorrências da comunidade**.
O acervo não é inserido no banco de denúncias, não passa por uma revisão humana
fictícia e não alimenta recorrência, hotspots, WPS ou estatísticas públicas de campo.
Com registros públicos existentes, a comunidade continua sendo a seleção inicial.
Sem eles, o mapa abre o acervo. Os pontos usam uma cor neutra, sem nível inventado.

## Cloud e reprodução

Fotos normalizadas, fotos identificadas e manifesto estão em `assets/acervo`;
as fotos da equipe estão em `assets/equipe`. Tudo acompanha o Git e funciona
em uma instalação nova no Cloud sem importar um SQLite local. O mapa lê os
resultados prontos; o envio de novas imagens continua executando a rede.

Para reprocessar as imagens originais:

```powershell
python scripts/preparar_acervo.py --imagens "CAMINHO/para ajustar o sistema"
python -m pytest tests/test_acervo.py -q
```

Foram encontrados 21 arquivos na pasta fornecida, não 22. Não foi fabricada
uma imagem adicional. A localização atribuída também consta no Excel e JSON.
