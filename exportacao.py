"""Excel compatível com os campos do contador e pacote com evidências."""
from datetime import datetime
from io import BytesIO
import json
from math import floor, ceil
import zipfile
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from PIL import Image
from visao import jpeg


def texto_seguro(valor):
    # Campos de relatos nunca viram fórmulas executáveis no Excel.
    if isinstance(valor, str) and valor.startswith(('=', '+', '-', '@')):
        return "'" + valor
    return valor


def gerar_excel(registro):
    from aquaverify import avaliar, explicar
    qualidade = avaliar(registro)
    wb = Workbook()
    resumo = wb.active
    resumo.title = 'Resumo'
    resumo.append(['AquaSentinela — análise de fotografia', 'Valor'])
    dados = [
        ('ID da ocorrência', registro['id']), ('Local', registro['nome']),
        ('Corpo hídrico (código interno)', registro.get('waterbody_id') or 'Não identificado'),
        ('Corpo hídrico confirmado', 'Sim' if registro.get('waterbody_confirmado') else 'Não'),
        ('AquaVerify — qualidade da evidência', f"{qualidade['indice']}/100 — {qualidade['faixa']}"),
        ('AquaVerify — interpretação', 'Qualidade documental; não é probabilidade de denúncia verdadeira.'),
        ('pHash — método', (registro.get('phash') or {}).get('versao', 'Não disponível')),
        ('pHash — principal', (registro.get('phash') or {}).get('principal', 'Não informativo')),
        ('Latitude', registro['latitude']), ('Longitude', registro['longitude']),
        ('Origem da localização', registro.get('origem_localizacao', 'informada_pelo_usuario')),
        ('Registro (UTC)', registro['registrado_em']), ('Origem da foto', registro['origem_foto']),
        ('Nível informado pela pessoa', registro['nivel_informado']),
        ('Itens identificados na foto', registro['total']),
        ('Detecções retornadas pelo modelo', registro['deteccoes_modelo']),
        ('Caixas duplicadas removidas', registro['duplicadas_removidas']),
        ('Confiança média (%)', registro['confianca_media']), ('Triagem da detecção', registro['triagem']),
        ('Autenticidade da foto', 'Não verificada pelo detector'), ('Observações', registro['observacoes']),
        ('SHA-256 da imagem (pixels)', registro['image_hash']), ('SHA-256 do modelo', registro['model_hash']),
        ('Confiança mínima (%)', registro['parametros']['confidence'] * 100),
        ('IoU de deduplicação', registro['parametros']['iou']),
        ('Método', 'Supressão de caixas sobrepostas; IDs únicos dentro desta foto.'),
        ('Limitação', 'Quantidade estimada de objetos visíveis. Não mede massa, volume ou bloqueio do canal.'),
        ('Confiança', 'Média aritmética das detecções mantidas; não é probabilidade de foto verdadeira.'),
        ('Classes do modelo', ', '.join(registro['classes_modelo'])),
        ('Limite do detector atingido', 'Sim — contagem pode estar truncada' if registro['possivel_limite'] else 'Não'),
    ]
    for linha in dados:
        resumo.append([texto_seguro(v) for v in linha])
    evidencia = wb.create_sheet('AquaVerify')
    evidencia.append(['Critério', 'Pontos', 'Máximo', 'Motivo'])
    for criterio in qualidade['criterios']:
        evidencia.append([texto_seguro(criterio[k]) for k in ('Critério', 'Pontos', 'Máximo', 'Motivo')])
    evidencia.column_dimensions['A'].width = 30
    evidencia.column_dimensions['D'].width = 100
    frase, motivos = explicar(registro)
    evidencia.append(['Explicação', None, None, texto_seguro(frase)])
    for motivo in motivos:
        evidencia.append(['Revisão', None, None, texto_seguro(motivo)])
    resumo.append([])
    resumo.append(['Classe detectada', 'Quantidade'])
    for classe, quantidade in registro['por_classe'].items():
        resumo.append([classe, quantidade])
    resumo.column_dimensions['A'].width = 42
    resumo.column_dimensions['B'].width = 90
    ws = wb.create_sheet('Detecções')
    ws.append(['ID do item', 'Classe', 'Confiança (%)', 'Data (UTC)', 'Hora (UTC)',
               'Track ID', 'Imagem do recorte', 'ID da ocorrência', 'X1', 'Y1', 'X2', 'Y2'])
    instante = datetime.fromisoformat(registro['analisado_em'])
    for d in registro['itens']:
        ws.append([d['item_id'], d['classe_pt'], d['confidence_pct'], instante.date(),
                   instante.time().replace(tzinfo=None), None, f"recortes/{d['item_id']}.jpg",
                   registro['id'], *[round(v, 2) for v in d['bbox']]])
    for i, largura in enumerate([18, 24, 20, 16, 16, 14, 30, 40, 12, 12, 12, 12], 1):
        ws.column_dimensions[get_column_letter(i)].width = largura
    for row in ws.iter_rows(min_row=2):
        row[2].number_format = '0.00'
        row[3].number_format = 'dd/mm/yyyy'
        row[4].number_format = 'hh:mm:ss'
    ws.auto_filter.ref = ws.dimensions
    for sheet in wb:
        sheet.freeze_panes = 'A2'
        sheet.sheet_view.showGridLines = False
        for cell in sheet[1]:
            cell.fill = PatternFill('solid', fgColor='087F8C')
            cell.font = Font(color='FFFFFF', bold=True)
        sheet.row_dimensions[1].height = 32
        for row in sheet.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = Alignment(vertical='top', wrap_text=True)
            sheet.row_dimensions[row[0].row].height = 32 if sheet == resumo else 22
    out = BytesIO()
    wb.save(out)
    return out.getvalue()


def gerar_pacote(registro, foto, anotada):
    out = BytesIO()
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as pacote:
        pacote.writestr('deteccoes.xlsx', gerar_excel(registro))
        pacote.writestr('foto.jpg', foto)
        pacote.writestr('foto_identificada.jpg', anotada)
        pacote.writestr('registro.json', json.dumps(registro, ensure_ascii=False, indent=2, allow_nan=False))
        pacote.writestr('LEIA-ME.txt', 'IDs MAR são locais à fotografia. Track ID está vazio porque não há vídeo.\n'
                          'foto.jpg foi orientada e redimensionada até 1920 px. Coordenadas das caixas referem-se a ela.\n'
                          'Confiança do detector não verifica autenticidade. Os recortes estão na pasta recortes.\n')
        imagem = Image.open(BytesIO(foto))
        for d in registro['itens']:
            x1, y1, x2, y2 = d['bbox']
            pacote.writestr(f"recortes/{d['item_id']}.jpg", jpeg(imagem.crop((floor(x1), floor(y1), ceil(x2), ceil(y2)))))
    return out.getvalue()
