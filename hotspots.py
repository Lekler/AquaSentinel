"""Persistência observada experimental. Não estima perigo ou probabilidade."""
from datetime import datetime, timezone
from statistics import median
from aquaverify import avaliar
from observacao import publicos, filtrar_periodo, data_registro, FUSO
from wps import pontuar

VERSAO = 'hotspot-persistente-v1'


def avaliar_hotspot(registros, agora=None):
    agora = agora or datetime.now(timezone.utc)
    janela = sorted(filtrar_periodo(publicos(registros), 90, agora),
                    key=lambda r: (data_registro(r), r['id']))
    elegiveis = []
    vistos = set()
    for r in janela:
        similar = (r.get('similaridade') or {}).get('quantidade', 0)
        identidade = r.get('image_hash') or r['id']
        if (r.get('waterbody_id') and r.get('waterbody_confirmado')
                and avaliar(r)['indice'] >= 60
                and (r.get('phash') or {}).get('principal')
                and (r.get('similaridade') or {}).get('verificada')
                and not (r.get('similaridade') or {}).get('sem_indice', 0)
                and (not similar or r.get('similaridade_decisao') == 'independente')
                and r.get('similaridade_decisao') != 'reutilizada'
                and identidade not in vistos):
            elegiveis.append(r)
            vistos.add(identidade)
    # Uma observação (a mais recente) por dia: uploads não multiplicam o peso diário.
    por_dia = {data_registro(r).astimezone(FUSO).date(): r for r in elegiveis}
    com_residuos = {d: r for d, r in por_dia.items() if r.get('nivel_informado')
                   in ('Pouco', 'Moderado', 'Muito poluído', 'Bloqueando')}
    dias = sorted(com_residuos)
    amplitude = (dias[-1]-dias[0]).days if dias else 0
    recorrencia = len(dias)/len(por_dia) if por_dia else 0
    wps = median([pontuar(r, elegiveis, data_registro(r))['wps'] for r in com_residuos.values()]) if dias else 0
    qualidade = median([avaliar(r)['indice'] for r in com_residuos.values()]) if dias else 0
    recente = janela[-1] if janela else None
    atraso = (agora.astimezone(FUSO).date()-data_registro(recente).astimezone(FUSO).date()).days if recente else None
    criterios = {
        'Pelo menos 3 dias distintos com resíduos e evidência elegível': len(dias) >= 3,
        'Observações com resíduos separadas por pelo menos 14 dias': amplitude >= 14,
        'Resíduos em pelo menos 60% dos dias elegíveis observados': recorrencia >= .6,
        'WPS mediano dos dias com resíduos de pelo menos 50': wps >= 50,
        'AquaVerify mediano de pelo menos 60/100': qualidade >= 60,
        'Última observação há no máximo 30 dias e ainda com resíduos':
            atraso is not None and atraso <= 30 and recente.get('nivel_informado')
            in ('Pouco', 'Moderado', 'Muito poluído', 'Bloqueando'),
        'Última observação com evidência elegível': bool(recente) and recente['id'] in {r['id'] for r in elegiveis},
        'Um único corpo hídrico confirmado neste trecho': len({r['waterbody_id'] for r in elegiveis}) == 1,
    }
    return {'versao': VERSAO, 'persistente': all(criterios.values()), 'criterios': criterios,
            'ocorrencias': len(janela), 'dias': len({data_registro(r).astimezone(FUSO).date() for r in janela}),
            'elegiveis': len(elegiveis), 'dias_residuos': len(dias), 'amplitude_dias': amplitude,
            'recorrencia': round(recorrencia*100, 1), 'wps_mediano': round(wps, 1),
            'qualidade_mediana': round(qualidade, 1), 'ultima_dias': atraso}
