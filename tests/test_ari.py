import pytest
from ari import calcular_ari, pontuar_chuva_24h, pontuar_recorrencia, triar_confianca
from motor import DadosInvalidos


@pytest.mark.parametrize('mm,score', [(0,0),(9.99,0),(10,25),(30,25),(30.01,50),(50,50),(50.01,75),(80,75),(80.01,100)])
def test_chuva_acumulada(mm, score):
    assert pontuar_chuva_24h(mm) == score


@pytest.mark.parametrize('n,score', [(0,0),(1,25),(2,50),(3,50),(4,75),(5,75),(6,100),(9,100)])
def test_recorrencia(n, score):
    assert pontuar_recorrencia(n) == score


@pytest.mark.parametrize('c,status', [(0,'excluido'),(59.99,'excluido'),(60,'pendente'),(79.99,'pendente'),(80,'aceito'),(100,'aceito')])
def test_confianca(c,status):
    assert triar_confianca(c) == status


def test_confirmacao_nao_multiplica_w():
    r = calcular_ari('Alto', 90, 6, 'Transbordamento', 70, True, 'Revisor')
    assert r['ari'] == 1 and r['ari_score'] == 100
    assert r['status_validacao'] == 'confirmado_humano'
    assert not r['avaliacao_urgente']  # manual, não oficial
    assert triar_confianca(59, True, 'Revisor') == 'excluido'


def test_formula_completa():
    r = calcular_ari('Moderado', 40, 2, 'Alerta')
    assert r['ari_score'] == 54 and r['ari'] == .54
    assert r['ari_level'] == 'Alto'
    assert not r['parcial']
    assert sum(r['contribuicoes'].values()) == 54


def test_nivel_ausente_diferente_vigilancia():
    parcial = calcular_ari('Alto',90,6)
    completo = calcular_ari('Alto',90,6,'Vigilância')
    assert parcial['ari_score'] == 100
    assert parcial['cobertura_pesos'] == .75
    assert parcial['componentes']['L'] is None
    assert completo['ari_score'] == 75


@pytest.mark.parametrize('c', [50,70,90])
def test_overflow_independente_de_ari(c):
    r = calcular_ari('Baixo', None, 0, 'Transbordamento', c, nivel_oficial=True, fonte_nivel='Estação exemplo, horário observado')
    assert r['avaliacao_urgente'] and r['ari_score'] is None
    assert r['cor_hotspot'] == '#C73545'


@pytest.mark.parametrize('c', [50,70])
def test_pendentes_excluidos_sem_ari(c):
    assert calcular_ari('Alto',90,6,'Transbordamento',c)['ari'] is None


def test_limites_ari():
    # W=25, R=0, L=50, F=25 → 25 exatos; W=100 R=0 L=0 F=100 → 50
    assert calcular_ari('Baixo',0,1,'Alerta')['ari_level'] == 'Moderado'
    assert calcular_ari('Alto',0,6,'Vigilância')['ari_level'] == 'Alto'
    assert calcular_ari('Alto',90,6,'Vigilância')['ari_level'] == 'Crítico'
    assert calcular_ari('Baixo',0,0,'Vigilância')['ari_level'] == 'Baixo'


@pytest.mark.parametrize('valor', [-1, float('nan'), float('inf'), True, '10'])
def test_invalidos(valor):
    with pytest.raises(DadosInvalidos): pontuar_chuva_24h(valor)
    with pytest.raises(DadosInvalidos): triar_confianca(valor)


def test_revisor_e_fonte_obrigatorios():
    with pytest.raises(DadosInvalidos): triar_confianca(65,True,'')
    with pytest.raises(DadosInvalidos): calcular_ari('Baixo',0,0,'Transbordamento',nivel_oficial=True)
    with pytest.raises(DadosInvalidos): pontuar_recorrencia(1.5)
