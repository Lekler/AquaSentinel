"""Exportações com lista explícita de campos; credenciais nunca integram o conjunto."""
import csv
from io import BytesIO, StringIO
import json
import math
from datetime import datetime, timezone
from openpyxl import Workbook
from observacao import data_registro, FUSO
from versoes import EXPORTACAO

DICIONARIO = [
    ('id', 'texto', 'Identificador único da ocorrência.'),
    ('registrado_em', 'ISO 8601', 'Data/hora de envio; não comprova a captura.'),
    ('nome', 'texto', 'Referência do local declarada pelo participante.'),
    ('waterbody_id', 'texto', 'Código do corpo hídrico; nulo quando indisponível.'),
    ('waterbody_confirmado', 'booleano', 'Vinculação ao corpo hídrico confirmada pela equipe.'),
    ('latitude', 'graus WGS84', 'Latitude confirmada pelo participante.'),
    ('longitude', 'graus WGS84', 'Longitude confirmada pelo participante.'),
    ('gps_precisao_m', 'm', 'Precisão informada pelo navegador, apenas se as coordenadas ainda correspondem ao GPS.'),
    ('origem_localizacao', 'categoria', 'GPS confirmado ou posição informada manualmente.'),
    ('nivel_informado', 'categoria', 'Sem resíduos, Pouco, Moderado, Muito poluído ou Bloqueando; declaração humana.'),
    ('total', 'objetos/foto', 'Detecções na foto, sem garantia de unicidade entre fotos.'),
    ('confianca_media', '%', 'Média da confiança das detecções; não probabilidade de autenticidade.'),
    ('revisao', 'categoria', 'nao_revisado, validado ou rejeitado.'),
    ('etapa', 'categoria', 'Etapa do ciclo de acompanhamento.'),
    ('revisor', 'texto', 'Nome informado pela equipe; não comprova identidade institucional.'),
    ('modo', 'categoria', 'oportunistico ou estruturado.'),
    ('sessao_id', 'texto', 'Sessão estruturada vinculada, quando houver.'),
    ('image_hash', 'SHA-256', 'Hash da imagem de entrada para identidade exata.'),
    ('model_hash', 'SHA-256', 'Hash do arquivo de pesos utilizado.'),
    ('modelo_runtime', 'texto', 'Biblioteca e versão usadas na inferência.'),
    ('versao_app', 'texto', 'Versão gravada na criação; nula em dados legados sem versão.'),
    ('versao_metodologia', 'texto', 'Regra metodológica gravada na criação.'),
    ('wps_versao', 'texto', 'Versão WPS utilizada; ausente no legado sem declaração.'),
    ('cs_versao', 'texto', 'Versão CS utilizada; ausente no legado sem declaração.'),
    ('aquaverify_versao', 'texto', 'Versão AquaVerify utilizada.'),
    ('wps', 'índice 0–100', 'Retrato calculado na gravação/revisão; não risco ou diagnóstico.'),
    ('cs', 'índice 0–100', 'Confiança média multiplicada por 0,8; não probabilidade calibrada.'),
    ('aquaverify', 'índice 0–100', 'Qualidade documental armazenada; não probabilidade de verdade.'),
    ('indices_calculados_em', 'ISO 8601', 'Instante do cálculo armazenado de WPS e CS.'),
    ('observacoes', 'texto', 'Nota livre do participante.'),
    ('sinais_ambientais', 'lista/texto JSON', 'Sinais opcionais declarados; vazio não significa ausência.'),
    ('contexto_detalhe', 'texto', 'Complemento ambiental sem diagnóstico.')]
CAMPOS = [c[0] for c in DICIONARIO]


def registrar_indices(registro, anteriores):
    from wps import pontuar
    from versoes import WPS, CS, AQUAVERIFY
    # Não reatribui retroativamente versões de criação a registros legados.
    if not registro.get('versoes_indices'):
        return
    agora = datetime.now(timezone.utc)
    indices = pontuar(registro, anteriores, agora=data_registro(registro))
    registro['indices_snapshot'] = {'wps': indices['wps'], 'cs': indices['cs'],
        'calculados_em': agora.isoformat(), 'versoes': {'wps': WPS, 'cs': CS, 'aquaverify': AQUAVERIFY}}


def linha(r):
    d = {k: r.get(k) for k in CAMPOS}
    gps = r.get('gps') or {}
    d['gps_precisao_m'] = gps.get('accuracy') if (gps.get('latitude') == r.get('latitude')
        and gps.get('longitude') == r.get('longitude') and gps) else None
    v = r.get('versoes_indices') or {}
    snapshot = r.get('indices_snapshot') or {}
    d.update(wps_versao=v.get('wps'), cs_versao=v.get('cs'), aquaverify_versao=v.get('aquaverify'),
             wps=snapshot.get('wps'), cs=snapshot.get('cs'),
             aquaverify=(r.get('aquaverify') or {}).get('indice'),
             indices_calculados_em=snapshot.get('calculados_em'),
             sinais_ambientais=(r.get('contexto_ambiental') or {}).get('sinais', []),
             contexto_detalhe=(r.get('contexto_ambiental') or {}).get('detalhe'))
    return d


def filtrar(registros, inicio=None, fim=None, corpo=None, nivel=None, status=None, revisao=None):
    resultado = []
    for r in registros:
        data = data_registro(r)
        if (inicio or fim) and data is None:
            continue
        dia = data.astimezone(FUSO).date() if data else None
        if inicio and dia < inicio or fim and dia > fim:
            continue
        if corpo and r.get('waterbody_id') != corpo or nivel and r.get('nivel_informado') != nivel:
            continue
        if status and r.get('etapa') != status:
            continue
        if revisao == 'Não revisado' and r.get('revisao', 'nao_revisado') != 'nao_revisado':
            continue
        if revisao == 'Revisado' and r.get('revisao', 'nao_revisado') not in ('validado', 'rejeitado'):
            continue
        resultado.append(r)
    return resultado


def geometria(r):
    try:
        lat, lon = float(r['latitude']), float(r['longitude'])
        if math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180:
            return {'type': 'Point', 'coordinates': [lon, lat]}
    except (KeyError, TypeError, ValueError):
        pass
    return None


def observation(r):
    """Perfil interno inspirado no SensorThings, sem declarar conformidade/API."""
    d = linha(r)
    return {'Observation': {'id': r['id'], 'phenomenonTime': None,
                           'resultTime': r.get('registrado_em'),
                           'result': {'nivel': d['nivel_informado'], 'objetos': d['total']}},
            'Location': {'encodingType': 'application/geo+json', 'location': geometria(r)},
            'FeatureOfInterest': {'id': r.get('waterbody_id') or r['id'],
                                  'name': r.get('waterbody_nome') or r.get('nome'),
                                  'feature': geometria(r)},
            'ObservedProperty': [{'name': 'Nível de resíduos declarado', 'unit': 'categoria'},
                                 {'name': 'Objetos detectados na fotografia', 'unit': 'objetos/foto'}],
            'metadata': {'schema': EXPORTACAO, 'capture_time_verified': False,
                         'sensorthings_conformant': False, 'record': d}}


def celula(valor):
    if isinstance(valor, (list, dict)):
        valor = json.dumps(valor, ensure_ascii=False, allow_nan=False)
    if isinstance(valor, str) and valor.lstrip().startswith(('=', '+', '-', '@')):
        return "'" + valor
    return valor


def exportar(registros, formato):
    linhas = [linha(r) for r in registros]
    if formato == 'JSON':
        return json.dumps({'schema': EXPORTACAO, 'records': [observation(r) for r in registros]},
                          ensure_ascii=False, indent=2, allow_nan=False).encode('utf-8')
    if formato == 'GeoJSON':
        return json.dumps({'type': 'FeatureCollection', 'features': [
            {'type': 'Feature', 'id': r['id'], 'geometry': geometria(r), 'properties': d}
            for r, d in zip(registros, linhas)]}, ensure_ascii=False, allow_nan=False).encode('utf-8')
    if formato == 'CSV':
        out = StringIO(newline='')
        writer = csv.DictWriter(out, fieldnames=CAMPOS)
        writer.writeheader()
        writer.writerows({k: celula(v) for k, v in d.items()} for d in linhas)
        return out.getvalue().encode('utf-8-sig')
    if formato == 'Excel':
        wb = Workbook()
        ws = wb.active
        ws.title = 'Observações'
        ws.append(CAMPOS)
        for d in linhas:
            ws.append([celula(d[k]) for k in CAMPOS])
        ws.freeze_panes = 'A2'
        ws.auto_filter.ref = ws.dimensions
        dic = wb.create_sheet('Dicionário')
        dic.append(['Campo', 'Unidade / tipo', 'Significado'])
        for item in DICIONARIO:
            dic.append(item)
        out = BytesIO()
        wb.save(out)
        return out.getvalue()
    raise ValueError('Formato desconhecido.')
