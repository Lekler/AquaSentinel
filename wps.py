"""Triagem experimental de resíduos; independente do painel de chuva/ARI."""
from datetime import datetime, timedelta, timezone
from historico import distancia_m

W_POR_NIVEL = {'Sem resíduos': 0, 'Pouco': 25, 'Moderado': 60,
               'Muito poluído': 100, 'Bloqueando': 100}
RAIO_M = 200
JANELA_DIAS = 30


def faixa_wps(valor):
    if valor < 25:
        return 'Baixa'
    if valor < 50:
        return 'Moderada'
    if valor < 75:
        return 'Alta'
    return 'Crítica'


def faixa_cs(valor):
    return 'Alta' if valor >= 80 else 'Moderada' if valor >= 60 else 'Baixa'


def pontuar(registro, revisados, agora=None):
    """Conta fotos distintas revisadas no mesmo corpo hídrico, raio e janela.

    Sem identidade verificada dos autores, F é apenas uma aproximação de
    recorrência e não comprova relatos independentes.
    """
    agora = agora or datetime.now(timezone.utc)
    if agora.tzinfo is None:
        agora = agora.replace(tzinfo=timezone.utc)
    data_minima = agora - timedelta(days=JANELA_DIAS)
    hashes = set()
    for item in revisados:
        if item.get('revisao') != 'validado':
            continue
        try:
            data = datetime.fromisoformat(item['registrado_em'])
            if data.tzinfo is None:
                data = data.replace(tzinfo=timezone.utc)
            mesmo_local = item['nome'].strip().casefold() == registro['nome'].strip().casefold()
            proximo = distancia_m(float(item['latitude']), float(item['longitude']),
                                  float(registro['latitude']), float(registro['longitude'])) <= RAIO_M
        except (KeyError, TypeError, ValueError):
            continue
        if data_minima <= data <= agora and mesmo_local and proximo:
            hashes.add(item.get('image_hash') or item['id'])
    quantidade = len(hashes)
    f = 0 if quantidade == 0 else 25 if quantidade == 1 else 50 if quantidade == 2 else 75 if quantidade <= 4 else 100
    w = W_POR_NIVEL.get(registro.get('nivel_informado'), 0)
    wps = round(.70 * w + .30 * f, 1) if w else 0.0
    confianca_ia = (registro.get('confianca_media') or 0) / 100
    # Sem autenticação institucional, todo relato usa confiabilidade comunitária.
    fonte = .8
    cs = round(100 * confianca_ia * fonte, 1)
    return {'w': w, 'f': f, 'recorrencias': quantidade, 'wps': wps,
            'faixa_wps': faixa_wps(wps), 'cs': cs, 'faixa_cs': faixa_cs(cs),
            'confiabilidade_fonte': fonte}
