"""Detecção em uma fotografia. IDs locais não implicam identidade entre fotos."""
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
import math
from pathlib import Path
import threading
import warnings

from PIL import Image, ImageDraw, ImageFont, ImageOps, UnidentifiedImageError

CLASSES_PT = {
    'other_plastic': 'Outros plásticos', 'plastic_bag': 'Sacola plástica',
    'plastic_bottle': 'Garrafa plástica', 'plastic_package': 'Embalagem plástica',
}
MAX_BYTES = 12 * 1024 * 1024
MAX_PIXELS = 24_000_000
LIMITES = {'confidence': .40, 'iou': .55, 'image_size': 640, 'max_det': 1000}


def preparar_imagem(conteudo):
    if not conteudo or len(conteudo) > MAX_BYTES:
        raise ValueError('Envie uma foto de até 12 MB.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(conteudo)) as origem:
                if origem.format not in ('JPEG', 'PNG', 'WEBP'):
                    raise ValueError('Formato não suportado. Use JPG, PNG ou WEBP.')
                if origem.width * origem.height > MAX_PIXELS:
                    raise ValueError('A foto deve ter no máximo 24 megapixels.')
                if getattr(origem, 'n_frames', 1) != 1:
                    raise ValueError('Envie uma fotografia estática, sem animação.')
                imagem = ImageOps.exif_transpose(origem).convert('RGB')
                imagem.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError,
            Image.DecompressionBombWarning) as exc:
        raise ValueError('Não foi possível ler essa imagem. Envie outra foto válida.') from exc
    # A identidade ignora nome e metadados; não é um detector de edição/fraude.
    digest = sha256(f'{imagem.size}:RGB:'.encode() + imagem.tobytes()).hexdigest()
    original_size = imagem.size
    imagem.thumbnail((1920, 1920))
    return imagem, digest, original_size


def jpeg(imagem):
    arquivo = BytesIO()
    imagem.save(arquivo, format='JPEG', quality=92)
    return arquivo.getvalue()


def iou(a, b):
    inter = max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    return inter / max(area_a + area_b - inter, 1e-9)


def remover_duplicadas(candidatas, largura, altura, limiar=.55):
    """NMS entre classes: retém a caixa mais confiante quando IoU > limiar."""
    validas = []
    for d in candidatas:
        x1, y1, x2, y2 = map(float, d['bbox'])
        conf = float(d['confidence'])
        if not all(math.isfinite(v) for v in (x1, y1, x2, y2, conf)) or not 0 <= conf <= 1:
            continue
        bbox = [max(0, min(largura, x1)), max(0, min(altura, y1)),
                max(0, min(largura, x2)), max(0, min(altura, y2))]
        if bbox[2] > bbox[0] and bbox[3] > bbox[1]:
            validas.append({**d, 'bbox': bbox, 'confidence': conf})
    mantidas = []
    for d in sorted(validas, key=lambda item: item['confidence'], reverse=True):
        if not any(iou(d['bbox'], outra['bbox']) > limiar for outra in mantidas):
            mantidas.append(d)
    return mantidas


def resumir(candidatas, largura, altura):
    mantidas = remover_duplicadas(candidatas, largura, altura, LIMITES['iou'])
    # Numeração em ordem de posição para facilitar a inspeção da imagem.
    mantidas.sort(key=lambda d: (d['bbox'][1], d['bbox'][0]))
    itens = [{**d, 'item_id': f'MAR-{i:04d}', 'confidence_pct': round(d['confidence'] * 100, 2),
              'classe_pt': CLASSES_PT.get(d['class_name'], d['class_name'])}
             for i, d in enumerate(mantidas, 1)]
    media = sum(d['confidence'] for d in mantidas) * 100 / len(mantidas) if mantidas else None
    status = ('sem_deteccao' if media is None else 'baixa_confianca' if media < 60
              else 'revisao_recomendada' if media < 80 else 'deteccao_consistente')
    return {'itens': itens, 'total': len(itens), 'deteccoes_modelo': len(candidatas),
            'duplicadas_removidas': len(candidatas) - len(itens),
            'confianca_media': round(media, 2) if media is not None else None,
            'triagem': status, 'autenticidade': 'nao_verificada',
            'por_classe': dict(Counter(d['classe_pt'] for d in itens)),
            'possivel_limite': len(candidatas) >= LIMITES['max_det']}


def anotar(imagem, itens):
    imagem = imagem.copy()
    desenho = ImageDraw.Draw(imagem)
    tamanho = max(12, imagem.width // 85)
    fonte = None
    for nome in ('arial.ttf', 'DejaVuSans.ttf'):
        try:
            fonte = ImageFont.truetype(nome, tamanho)
            break
        except OSError:
            continue
    fonte = fonte or ImageFont.load_default(size=tamanho)
    for d in itens:
        bbox = d['bbox']
        cor = '#087F8C' if d['confidence'] >= .8 else '#C97400'
        desenho.rectangle(bbox, outline=cor, width=max(2, imagem.width // 500))
        texto = f"{d['item_id']} {d['classe_pt']} {d['confidence_pct']:.1f}%"
        limites = desenho.textbbox((0, 0), texto, font=fonte)
        w, h = limites[2] - limites[0] + 8, limites[3] - limites[1] + 8
        x, y = max(0, min(bbox[0], imagem.width-w)), max(0, bbox[1]-h)
        desenho.rectangle((x, y, x+w, y+h), fill=cor)
        desenho.text((x+4, y+2-limites[1]), texto, fill='white', font=fonte)
    return jpeg(imagem)


class Detector:
    def __init__(self, caminho):
        from ultralytics import YOLO
        self.caminho = Path(caminho)
        if not self.caminho.is_file():
            raise FileNotFoundError('Modelo não encontrado. Coloque best.pt na pasta models.')
        self.model_hash = sha256(self.caminho.read_bytes()).hexdigest()
        self.modelo = YOLO(str(self.caminho))
        self.lock = threading.Lock()

    def analisar(self, conteudo):
        imagem, digest, tamanho_original = preparar_imagem(conteudo)
        # O predictor Ultralytics é mutável; o modelo compartilhado é serializado.
        with self.lock:
            resultado = self.modelo.predict(imagem, conf=LIMITES['confidence'],
                iou=LIMITES['iou'], imgsz=LIMITES['image_size'],
                max_det=LIMITES['max_det'], agnostic_nms=False, verbose=False)[0]
            candidatas = [{'bbox': box, 'confidence': conf, 'class_id': int(classe),
                           'class_name': resultado.names[int(classe)]}
                          for box, conf, classe in zip(resultado.boxes.xyxy.cpu().tolist(),
                              resultado.boxes.conf.cpu().tolist(), resultado.boxes.cls.cpu().tolist())]
        resumo = resumir(candidatas, *imagem.size)
        resumo.update(image_hash=digest, model_hash=self.model_hash,
                      analisado_em=datetime.now(timezone.utc).isoformat(),
                      dimensoes=list(imagem.size), dimensoes_originais=list(tamanho_original),
                      parametros=dict(LIMITES), metodo='foto-nms-1',
                      classes_modelo=list(self.modelo.names.values()))
        return resumo, jpeg(imagem), anotar(imagem, resumo['itens'])
