from datetime import datetime, timedelta, timezone

from wps import pontuar


def registro(ident, dias=0, hash_=None):
    return {'id': ident, 'nome': 'Canal do Fundão', 'latitude': -22.83,
            'longitude': -43.24, 'registrado_em': (datetime.now(timezone.utc)
            - timedelta(days=dias)).isoformat(), 'image_hash': hash_ or ident,
            'nivel_informado': 'Muito poluído', 'confianca_media': 94,
            'revisao': 'validado', 'waterbody_id': 'WB-BG-001', 'waterbody_confirmado': True}


def test_exemplo_metodologia_separa_prioridade_e_confianca():
    atual = registro('a')
    outros = [atual, registro('b'), registro('c'), registro('d')]
    resultado = pontuar(atual, outros)
    assert resultado['w'] == 100
    assert resultado['f'] == 75
    assert resultado['wps'] == 92.5
    assert resultado['cs'] == 75.2
    assert resultado['faixa_wps'] == 'Crítica'
    assert resultado['faixa_cs'] == 'Moderada'


def test_recorrencia_exige_revisao_e_foto_distinta():
    atual = registro('a')
    repetida = registro('b', hash_='a')
    pendente = registro('c')
    pendente['revisao'] = 'nao_revisado'
    antigo = registro('d', dias=31)
    outro_local = registro('e')
    outro_local['nome'] = 'Rio Estrela'
    outro_local['waterbody_id'] = 'WB-BG-002'
    resultado = pontuar(atual, [atual, repetida, pendente, antigo, outro_local])
    assert resultado['recorrencias'] == 1
    assert resultado['f'] == 25


def test_sem_residuos_nao_cria_hotspot_ativo():
    atual = registro('a')
    atual['nivel_informado'] = 'Sem resíduos'
    assert pontuar(atual, [atual])['wps'] == 0
