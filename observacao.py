"""Condição declarada e cobertura temporal, independentes do WPS.

Agrupos usam o primeiro registro público como âncora (200 m), sem encadear
pontos distantes. Exige código de corpo hídrico confirmado pela equipe.
Registros sem código confirmado ficam separados até vinculação humana.
"""
from collections import Counter
from datetime import datetime, timedelta, timezone
import math
import unicodedata
from zoneinfo import ZoneInfo

from historico import distancia_m

FUSO = ZoneInfo('America/Sao_Paulo')
RAIO_LOCAL_M = 200
CORES_NIVEIS = {'Sem resíduos': '#94a3b8', 'Pouco': '#22a55b',
                'Moderado': '#facc15', 'Muito poluído': '#f97316',
                'Bloqueando': '#000000'}
PERIODOS = {'7 dias': 7, '15 dias': 15, '30 dias': 30, '90 dias': 90,
            'Todo o período': None}


def data_registro(registro):
    try:
        data = datetime.fromisoformat(registro['registrado_em'])
        return data.replace(tzinfo=timezone.utc) if data.tzinfo is None else data
    except (KeyError, ValueError, TypeError):
        return None


def nome_normalizado(nome):
    texto = unicodedata.normalize('NFKD', nome.casefold())
    return ' '.join(''.join(c for c in texto if not unicodedata.combining(c)).split())


def publicos(registros):
    """Única regra de visibilidade para mapa, agregados e páginas públicas."""
    return [r for r in registros if r.get('revisao') == 'validado'
            and r.get('consentimento_publicacao') is True]


def filtrar_periodo(registros, dias=None, agora=None):
    agora = agora or datetime.now(timezone.utc)
    hoje = agora.astimezone(FUSO).date()
    inicio = hoje - timedelta(days=dias - 1) if dias else None
    return [r for r in registros if (data := data_registro(r)) is not None
            and data <= agora and (inicio is None or data.astimezone(FUSO).date() >= inicio)]


def agrupar_locais(registros):
    grupos = []
    validos = []
    for r in publicos(registros):
        try:
            lat, lon = float(r['latitude']), float(r['longitude'])
            if (data_registro(r) is not None and r.get('id') and r.get('nome')
                    and math.isfinite(lat) and math.isfinite(lon)
                    and -90 <= lat <= 90 and -180 <= lon <= 180):
                validos.append(r)
        except (KeyError, TypeError, ValueError):
            continue
    for r in sorted(validos, key=lambda r: (data_registro(r), r['id'])):
        nome = r.get('waterbody_id') if r.get('waterbody_confirmado') else None
        chave = nome or f'sem-identificacao:{r["id"]}'
        candidatos = [(distancia_m(float(r['latitude']), float(r['longitude']),
                                   g['latitude'], g['longitude']), g)
                      for g in grupos if g['chave_corpo'] == chave]
        candidatos = [(d, g) for d, g in candidatos if d <= RAIO_LOCAL_M]
        if candidatos:
            grupo = min(candidatos, key=lambda par: (par[0], par[1]['id']))[1]
        else:
            grupo = {'id': r['id'], 'nome': (r.get('waterbody_nome') or r['nome']) if nome else r['nome'],
                     'waterbody_id': nome, 'chave_corpo': chave,
                     'latitude': float(r['latitude']), 'longitude': float(r['longitude']),
                     'registros': []}
            grupos.append(grupo)
        grupo['registros'].append(r)
    return grupos


def resumo_local(registros, agora=None):
    agora = agora or datetime.now(timezone.utc)
    ordenados = sorted(filtrar_periodo(registros, agora=agora),
                       key=lambda r: (data_registro(r), r['id']))
    if not ordenados:
        return None
    datas = {data_registro(r).astimezone(FUSO).date() for r in ordenados}
    dias_residuos = {data_registro(r).astimezone(FUSO).date() for r in ordenados
                    if r.get('nivel_informado') in CORES_NIVEIS
                    and r['nivel_informado'] != 'Sem resíduos'}
    classes = Counter()
    for r in ordenados:
        classes.update(r.get('por_classe') or {})
    ultima = data_registro(ordenados[-1]).astimezone(FUSO)
    return {'total': len(ordenados), 'dias': len(datas), 'dias_residuos': len(dias_residuos),
            'primeira': data_registro(ordenados[0]).astimezone(FUSO), 'ultima': ultima,
            'dias_desde_ultima': (agora.astimezone(FUSO).date() - ultima.date()).days,
            'recente': ordenados[-1], 'registros': ordenados,
            'objetos': sum(int(r.get('total') or 0) for r in ordenados),
            'classes': classes.most_common()}


def cor_cobertura(dias):
    return '#bfdbfe' if dias == 1 else '#60a5fa' if dias <= 3 else '#2563eb' if dias <= 7 else '#1e3a8a'


def rgb(cor):
    return [int(cor[i:i+2], 16) for i in (1, 3, 5)]


def ultima_descricao(dias):
    return 'última ocorrência hoje' if dias == 0 else 'última ocorrência há 1 dia' if dias == 1 else f'última ocorrência há {dias} dias'
