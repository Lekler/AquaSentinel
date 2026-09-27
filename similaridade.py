"""pHash DCT de 64 bits + recortes candidatos; triagem, nunca prova de fraude.

SHA-256 continua sendo a identidade exata dos pixels em visao.py. O pHash usa
baixas frequências, compara distância de Hamming <= 6 e recortes de 80/60%.
Não é invariável a recortes arbitrários, grandes rotações ou montagens.
"""
from io import BytesIO
from functools import lru_cache
from datetime import datetime
import numpy as np
from PIL import Image, ImageOps

VERSAO = 'phash-dct-recortes-v1'
LIMIAR = 6


def data_captura_exif(conteudo):
    """Somente horário EXIF, sem copiar metadados privados; não autentica a captura."""
    try:
        with Image.open(BytesIO(conteudo)) as im:
            exif = im.getexif()
            valor = exif.get_ifd(0x8769).get(36867) or exif.get(306)
            return datetime.strptime(str(valor), '%Y:%m:%d %H:%M:%S').isoformat() if valor else None
    except (ValueError, TypeError, OSError, KeyError, SyntaxError):
        return None


@lru_cache(maxsize=1)
def matriz_dct():
    return np.cos(np.pi * np.arange(8)[:, None] * (2*np.arange(32)+1) / 64)


def phash(imagem):
    pixels = np.asarray(imagem.convert('L').resize((32, 32), Image.Resampling.LANCZOS), dtype=float)
    if pixels.std() < 8:
        return None  # Imagens uniformes não geram correspondências confiáveis.
    bloco = matriz_dct() @ pixels @ matriz_dct().T
    valores = bloco.flatten()
    bits = valores > np.median(valores[1:])
    bits[0] = False
    return f'{sum(int(b) << i for i, b in enumerate(bits)):016x}'


def assinatura(conteudo):
    with Image.open(BytesIO(conteudo)) as original:
        imagem = ImageOps.exif_transpose(original).convert('RGB')
        imagem.thumbnail((1024, 1024))
        w, h = imagem.size
        recortes = set()
        for escala in (.8, .6):
            cw, ch = round(w*escala), round(h*escala)
            for x in (0, (w-cw)//2, w-cw):
                for y in (0, (h-ch)//2, h-ch):
                    valor = phash(imagem.crop((x, y, x+cw, y+ch)))
                    if valor:
                        recortes.add(valor)
        return {'versao': VERSAO, 'principal': phash(imagem), 'recortes': sorted(recortes)}


def distancia(a, b):
    if not a or not b or a.get('versao') != VERSAO or b.get('versao') != VERSAO:
        return None
    pa, pb = a.get('principal'), b.get('principal')
    pares = [(pa, pb)] + [(pa, x) for x in b.get('recortes', [])] + [(x, pb) for x in a.get('recortes', [])]
    valores = [(int(x, 16) ^ int(y, 16)).bit_count() for x, y in pares if x and y]
    return min(valores) if valores else None


def comparar(registro, anteriores):
    matches = []
    faltantes = 0
    for r in anteriores:
        if r['id'] == registro.get('id'):
            continue
        if r.get('image_hash') == registro.get('image_hash'):
            matches.append({'id': r['id'], 'tipo': 'identica', 'distancia': 0})
            continue
        if not r.get('phash') or r['phash'].get('versao') != VERSAO:
            faltantes += 1
            continue
        d = distancia(registro.get('phash'), r['phash'])
        if d is not None and d <= LIMIAR:
            matches.append({'id': r['id'], 'tipo': 'semelhante', 'distancia': d})
    matches.sort(key=lambda m: (m['distancia'], m['id']))
    return {'verificada': True, 'versao': VERSAO, 'limiar': LIMIAR,
            'comparadas': len(anteriores), 'sem_indice': faltantes,
            'quantidade': len(matches), 'candidatas': matches[:10]}
