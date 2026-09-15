from datetime import datetime, timezone
import pytest
from motor import DadosInvalidos, analisar_previsao, calcular_prioridade, classificar_chuva, validar_entrada

AGORA = datetime(2026, 9, 15, 15, 30, tzinfo=timezone.utc)


def amostra():
    inicio = int(datetime(2026, 9, 15, 0, tzinfo=timezone.utc).timestamp())
    return {'timezone': 'America/Sao_Paulo',
            'hourly_units': {'time': 'unixtime', 'precipitation': 'mm', 'precipitation_probability': '%'},
            'hourly': {'time': [inicio + i * 3600 for i in range(72)],
                       'precipitation': [1.] * 72, 'precipitation_probability': [60.] * 72}}


@pytest.mark.parametrize('mm,score', [(0,0),(.199,0),(.2,25),(5,25),(5.01,50),(5.1,50),(25,50),(25.01,75),(25.1,75),(50,75),(50.01,100),(100,100)])
def test_faixas(mm, score):
    assert classificar_chuva(mm)[0] == score


@pytest.mark.parametrize('l,r,p', [(0,0,0),(100,0,60),(0,100,20),(100,100,100),(70,75,67.5)])
def test_formula(l, r, p):
    assert calcular_prioridade(l,r)[0] == p


@pytest.mark.parametrize('w,nivel', [(0,'Baixa'),(24,'Baixa'),(25,'Média'),(49,'Média'),(50,'Alta'),(74,'Alta'),(75,'Crítica'),(100,'Crítica')])
def test_limites_prioridade(w, nivel):
    # r = 0,5 => prioridade = 10 + 0,7*waste
    p, n = calcular_prioridade((w - 10)/.7, 50) if w >= 10 and w <= 80 else calcular_prioridade(0 if w == 0 else 100, 0 if w == 0 else 100)
    assert n == nivel


def test_janela_futura_sem_horas_passadas():
    d = amostra()
    d['hourly']['precipitation'][15] = 500  # passado
    d['hourly']['precipitation'][16] = 500  # intervalo em andamento
    d['hourly']['precipitation'][17] = 6
    d['hourly']['precipitation'][41] = 500  # fora da janela
    r = analisar_previsao(d, AGORA)
    assert r['max_1h_mm'] == 6
    assert r['acumulado_6h_mm'] == 11
    assert r['acumulado_24h_mm'] == 29
    assert r['rainfall_score'] == 50
    assert r['janela_inicio'] == '2026-09-15T13:00:00-03:00'
    assert r['janela_fim'] == '2026-09-16T13:00:00-03:00'
    assert r['horas'][0]['fim'] == '2026-09-15T14:00:00-03:00'
    assert r['precipitation_probability_peak'] == 60


def test_hora_exata_e_virada_dia():
    r = analisar_previsao(amostra(), datetime(2026,9,15,23,0,tzinfo=timezone.utc))
    assert r['janela_inicio'] == '2026-09-15T20:00:00-03:00'
    assert len(r['horas']) == 24
    assert r['acumulado_24h_mm'] == 24


@pytest.mark.parametrize('tipo', ['nulo','negativo','nan','faltando','duplicado','fora_ordem','unidade','curto','raiz'])
def test_resposta_invalida(tipo):
    d = amostra()
    if tipo == 'nulo': d['hourly']['precipitation'][20] = None
    elif tipo == 'negativo': d['hourly']['precipitation'][20] = -1
    elif tipo == 'nan': d['hourly']['precipitation'][20] = float('nan')
    elif tipo == 'faltando': d['hourly']['precipitation'].pop()
    elif tipo == 'duplicado': d['hourly']['time'][20] = d['hourly']['time'][19]
    elif tipo == 'fora_ordem': d['hourly']['time'].reverse()
    elif tipo == 'unidade': d['hourly_units']['precipitation'] = 'inch'
    elif tipo == 'curto':
        for k in d['hourly']: d['hourly'][k] = d['hourly'][k][:20]
    else: d = []
    with pytest.raises(DadosInvalidos): analisar_previsao(d, AGORA)


def test_probabilidade_ausente_nao_vira_zero():
    d = amostra()
    d['hourly']['precipitation_probability'][20] = None
    r = analisar_previsao(d, AGORA)
    assert r['precipitation_probability_peak'] is None
    assert r['rainfall_score'] == 25


@pytest.mark.parametrize('args', [('',0,0,20), ('Canal',91,0,20), ('Canal',0,-181,20), ('Canal',0,0,101), ('Canal',0,0,float('nan'))])
def test_entrada_invalida(args):
    with pytest.raises(DadosInvalidos): validar_entrada(*args)


def test_monotonicidade_e_limites():
    for l in range(101):
        anterior = -1
        for r in range(101):
            p,_ = calcular_prioridade(l,r)
            assert 0 <= p <= 100 and p >= anterior
            anterior = p
