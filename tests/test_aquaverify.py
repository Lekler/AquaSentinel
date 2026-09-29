from datetime import datetime, timedelta, timezone
from io import BytesIO
from copy import deepcopy

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance
import pytest

from similaridade import assinatura, distancia, comparar, LIMIAR, data_captura_exif
from aquaverify import avaliar, explicar
from hotspots import avaliar_hotspot
from observacao import agrupar_locais
from test_observacao import registro

AGORA = datetime(2026, 9, 27, 18, tzinfo=timezone.utc)


def imagem(semente=4):
    rng = np.random.default_rng(semente)
    im = Image.new('RGB', (800, 600), (70, 120, 160))
    draw = ImageDraw.Draw(im)
    for _ in range(100):
        x, y = rng.integers(0, 650), rng.integers(0, 450)
        draw.ellipse((x, y, x+int(rng.integers(10, 150)), y+int(rng.integers(10, 150))),
                     fill=tuple(int(v) for v in rng.integers(0, 255, 3)))
    return im


def bytes_imagem(im, qualidade=95):
    out = BytesIO()
    im.save(out, format='JPEG', quality=qualidade)
    return out.getvalue()


@pytest.mark.parametrize('transformacao', ['resize', 'compressao', 'brilho', 'recorte80', 'recorte60', 'pequena_edicao'])
def test_phash_transformacoes(transformacao):
    im = imagem()
    referencia = assinatura(bytes_imagem(im))
    if transformacao == 'resize':
        alterada = im.resize((400, 300))
    elif transformacao == 'brilho':
        alterada = ImageEnhance.Brightness(im).enhance(1.1)
    elif transformacao == 'recorte80':
        alterada = im.crop((80, 60, 720, 540))
    elif transformacao == 'recorte60':
        alterada = im.crop((0, 0, 480, 360))
    else:
        alterada = im.copy()
        if transformacao == 'pequena_edicao':
            ImageDraw.Draw(alterada).rectangle((10, 10, 25, 25), fill='red')
    candidata = assinatura(bytes_imagem(alterada, 35 if transformacao == 'compressao' else 95))
    assert distancia(referencia, candidata) <= LIMIAR


def test_phash_nao_confunde_uniformes_ou_imagens_distintas():
    uniforme = assinatura(bytes_imagem(Image.new('RGB', (800, 600), 'white')))
    assert uniforme['principal'] is None and distancia(uniforme, uniforme) is None
    assert distancia(assinatura(bytes_imagem(imagem(1))), assinatura(bytes_imagem(imagem(10)))) > LIMIAR


def evidencia(ident, dias=0, **extras):
    r = registro(ident, (AGORA-timedelta(days=dias)).isoformat(), nivel_informado='Muito poluído')
    r.update(imagem_valida=True, dimensoes_originais=[800, 600],
             phash={'principal': '1234', 'versao': 'phash-dct-recortes-v1'},
             similaridade={'verificada': True, 'sem_indice': 0, 'quantidade': 0}, **extras)
    return r


def test_aquaverify_pesos_limites_e_explicacao():
    r = evidencia('a')
    q = avaliar(r)
    assert sum(i['Máximo'] for i in q['criterios']) == 100
    assert q['faixa'] == 'alta' and 0 <= q['indice'] <= 100
    r.update(confianca_media=58, duplicadas_removidas=2, revisao='nao_revisado')
    frase, motivos = explicar(r)
    assert '58.0%' in frase and any('60%' in m for m in motivos)
    assert any('2 caixas' in m for m in motivos)
    assert avaliar(r)['indice'] < q['indice']
    r.update(confianca_media=float('nan'))
    assert 0 <= avaliar(r)['indice'] <= 100


def test_gps_ajustado_perde_pontos_e_precisao_indisponivel():
    r = evidencia('a', gps={'latitude': -22.83, 'longitude': -43.24, 'accuracy': 10},
                  origem_localizacao='geolocalizacao_navegador_confirmada')
    original = avaliar(r)['indice']
    r['latitude'] = -22.84
    assert avaliar(r)['indice'] == original-12


def test_hotspot_persistencia_exige_tempo_dias_qualidade_e_recencia():
    rs = [evidencia('a', 20), evidencia('b', 10), evidencia('c', 2)]
    h = avaliar_hotspot(rs, AGORA)
    assert h['persistente'] and h['dias'] == 3 and h['amplitude_dias'] == 18
    assert not avaliar_hotspot([evidencia(str(i), 2) for i in range(20)], AGORA)['persistente']
    assert not avaliar_hotspot([evidencia('a', 70), evidencia('b', 50), evidencia('c', 40)], AGORA)['persistente']
    rs[-1]['nivel_informado'] = 'Sem resíduos'
    assert not avaliar_hotspot(rs, AGORA)['persistente']


@pytest.mark.parametrize('alteracao', [
    {'similaridade': {'verificada': True, 'quantidade': 1, 'sem_indice': 0}},
    {'similaridade': {'verificada': True, 'quantidade': 0, 'sem_indice': 1}},
    {'waterbody_confirmado': False}, {'consentimento_publicacao': False},
    {'revisao': 'nao_revisado'}, {'imagem_valida': False, 'confianca_media': 0},
    {'image_hash': 'a'}, {'similaridade_decisao': 'reutilizada'},
])
def test_evidencia_insuficiente_nao_cria_hotspot(alteracao):
    rs = [evidencia('a', 20), evidencia('b', 10), evidencia('c', 2)]
    rs[-1].update(alteracao)
    assert not avaliar_hotspot(rs, AGORA)['persistente']


def test_sem_codigo_nao_agrupa_nomes_iguais():
    rs = [evidencia('a'), evidencia('b')]
    for r in rs:
        r.pop('waterbody_id')
    assert len(agrupar_locais(rs)) == 2
    rs[0]['waterbody_id'] = rs[1]['waterbody_id'] = 'WB-BG-001'
    rs[1]['nome'] = 'Descrição completamente diferente'
    assert len(agrupar_locais(rs)) == 1


def test_comparacao_sem_indice_e_sha_exato():
    r = evidencia('a')
    antigo = evidencia('b')
    antigo.pop('phash')
    assert comparar(r, [antigo])['sem_indice'] == 1
    antigo['image_hash'] = r['image_hash']
    assert comparar(r, [antigo])['candidatas'][0]['tipo'] == 'identica'
    assert data_captura_exif(bytes_imagem(imagem())) is None
