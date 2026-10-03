"""Executa o detector real e empacota o acervo, sem inserir relatos de campo no banco.

Uso: python scripts/preparar_acervo.py --imagens CAMINHO
As coordenadas são referências aproximadas atribuídas à apresentação, não EXIF/GPS.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from visao import Detector
from relatos import criar_registro

FONTE_BOTAS = 'https://novaiguacu.rj.gov.br/2025/01/20/nova-iguacu-intensifica-limpeza-de-rios-e-valoes-para-evitar-enchentes-causadas-pelas-chuvas-de-verao-2/'
FONTE_BACIA = 'https://www.inea.rj.gov.br/biodiversidade-territorio/conheca-as-unidades-de-conservacao/apa-do-alto-iguacu/'
FONTE_ILHA = 'https://prefeitura.rio/infraestrutura/orla-da-ilha-do-governador-e-entregue-a-populacao-apos-reforma-e-reurbanizacao-de-quatro-praias/'
FONTE_BICA = 'https://www.rio.rj.gov.br/web/guest/exibeconteudo?id=6082231'
# Títulos descrevem a imagem; nomes geográficos são referências da apresentação.
PONTOS = [
    ('Frame 1010.png', 'Resíduos entre raízes e margem', 'Rio Botas · Comendador Soares, Nova Iguaçu', -22.752, -43.478, FONTE_BOTAS),
    ('Frame 169.png', 'Objeto flutuante junto ao concreto', 'Rio Botas · Santa Eugênia, Nova Iguaçu', -22.759, -43.450, FONTE_BOTAS),
    ('Frame 1981.png', 'Recipientes acumulados na água', 'Baía de Guanabara · Praia da Bica, Jardim Guanabara', -22.8216, -43.1900, FONTE_BICA),
    ('Frame 2021.png', 'Embalagem próxima à passagem de água', 'Rio Botas · Caioaba, Nova Iguaçu', -22.737, -43.441, FONTE_BOTAS),
    ('Frame 313.png', 'Embalagens claras na superfície', 'Rio Botas · Engenho Pequeno, Nova Iguaçu', -22.726, -43.423, FONTE_BOTAS),
    ('Frame 344.png', 'Objetos dispersos na água', 'Rio Botas · Heliópolis, Belford Roxo', -22.747, -43.392, 'https://prefeituradebelfordroxo.rj.gov.br/2025/09/25/corpo-de-bombeiros-em-parceria-com-secretaria-de-protecao-animal-resgatam-macaco-prego-e-jiboia/'),
    ('Frame 44.png', 'Garrafa isolada na superfície', 'Rio Iguaçu · Baixada Fluminense, trecho oeste', -22.686, -43.410, FONTE_BACIA),
    ('Frame 546.png', 'Resíduos entre a vegetação aquática', 'Rio Iguaçu · Baixada Fluminense, trecho central', -22.708, -43.365, FONTE_BACIA),
    ('Frame 646.png', 'Material claro flutuante', 'Rio Iguaçu · Baixada Fluminense, trecho leste', -22.725, -43.321, FONTE_BACIA),
    ('Frame 713.png', 'Garrafa junto à margem vegetada', 'Rio Sarapuí · Baixada Fluminense, trecho oeste', -22.795, -43.401, 'https://transparencia.duquedecaxias.rj.gov.br/portal/images/arquivos/docs/Licitacoes/62882.2014.pdf'),
    ('Frame 774.png', 'Sacola branca na água', 'Rio Sarapuí · Baixada Fluminense, trecho central', -22.773, -43.363, 'https://transparencia.duquedecaxias.rj.gov.br/portal/images/arquivos/docs/Licitacoes/62882.2014.pdf'),
    ('Frame 815.png', 'Sacola transparente na margem', 'Rio Sarapuí · Baixada Fluminense, trecho leste', -22.748, -43.310, 'https://transparencia.duquedecaxias.rj.gov.br/portal/images/arquivos/docs/Licitacoes/62882.2014.pdf'),
    ('Frame 871.png', 'Recipiente claro na água escura', 'Baía de Guanabara · Praia da Bandeira, Ilha do Governador', -22.815, -43.173, FONTE_ILHA),
    ('Frame 882.png', 'Acúmulo de embalagens no canal', 'Baía de Guanabara · Cocotá, Ilha do Governador', -22.803, -43.177, FONTE_ILHA),
    ('Frame 940.png', 'Recipientes agrupados na margem', 'Baía de Guanabara · Pitangueiras, Ilha do Governador', -22.817, -43.178, FONTE_ILHA),
    ('Frame 987.png', 'Sacola e resíduos na borda da água', 'Baía de Guanabara · Praia da Guanabara, Freguesia', -22.787, -43.166, FONTE_ILHA),
    ('frame0074_jpg.jpg', 'Pequenos objetos dispersos', 'Baía de Guanabara · Bancários, Ilha do Governador', -22.785, -43.181, 'https://www.rio.rj.gov.br/web/guest/exibeconteudo?id=4360872'),
    ('frame0217_jpg.jpg', 'Embalagem vermelha flutuante', 'Baía de Guanabara · Ribeira, Ilha do Governador', -22.826, -43.170, 'https://multirio.rio.rj.gov.br/index.php/reportagens/906-conheca-os-15-bairros-que-integram-a-20-regiao-administrativa-ilha-do-governador'),
    ('frame0451_jpg.jpg', 'Sacolas e embalagens na superfície', 'Baía de Guanabara · Zumbi, Ilha do Governador', -22.823, -43.176, 'https://www.rio.rj.gov.br/web/guest/exibeconteudo?id=4360872'),
    ('frame0463_jpg.jpg', 'Recipientes espalhados na água', 'Baía de Guanabara · Moneró, Ilha do Governador', -22.788, -43.201, 'https://www.rio.rj.gov.br/web/guest/exibeconteudo?id=4360872'),
    ('yr.png', 'Objeto claro junto à estrutura', 'Baía de Guanabara · Galeão, Ilha do Governador', -22.818, -43.244, 'https://www.rio.rj.gov.br/web/guest/exibeconteudo?id=4360872'),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--imagens', type=Path, required=True)
    args = parser.parse_args()
    faltantes = [p[0] for p in PONTOS if not (args.imagens / p[0]).is_file()]
    if faltantes:
        parser.error(f'Imagens ausentes: {faltantes}')
    destino = ROOT / 'assets' / 'acervo'
    destino.mkdir(parents=True, exist_ok=True)
    detector = Detector(ROOT / 'models' / 'best.pt')
    registros, hashes = [], set()
    for arquivo, titulo, local, lat, lon, fonte in PONTOS:
        analise, foto, anotada = detector.analisar((args.imagens / arquivo).read_bytes())
        if analise['image_hash'] in hashes:
            raise ValueError(f'Imagem duplicada: {arquivo}')
        hashes.add(analise['image_hash'])
        r = criar_registro(analise, local, lat, lon, 'Pouco', origem='acervo_de_testes')
        r.update(id='acervo-' + analise['image_hash'][:16], titulo=titulo,
                 arquivo_original=arquivo, nivel_informado='Não classificado',
                 origem_localizacao='atribuida_para_demonstracao',
                 coordenadas_aproximadas=True, local_captura_confirmado=False,
                 fonte_geografica=fonte, revisao='analise_tecnica',
                 observacoes='Localização de referência atribuída ao acervo; não comprova o local de captura.',
                 conjunto='acervo-apresentacao-2026-10', validacao_campo=False)
        (destino / f"{r['id']}.jpg").write_bytes(foto)
        (destino / f"{r['id']}-ia.jpg").write_bytes(anotada)
        registros.append(r)
        print(f"{arquivo}: {r['total']} itens; confiança {r['confianca_media']}", flush=True)
    (destino / 'registros.json').write_text(json.dumps(registros, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    print(f'Concluído: {len(registros)} imagens, {sum(r["total"] for r in registros)} detecções mantidas.')


if __name__ == '__main__':
    main()
