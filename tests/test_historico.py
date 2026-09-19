from datetime import datetime, timedelta, timezone
import pytest
from historico import salvar, listar, confirmar, contar_proximos, distancia_m
from motor import DadosInvalidos

AGORA = datetime(2026,9,19,15,tzinfo=timezone.utc)


def registro(id='1', status='aceito', dias=1, lat=-22.9):
    return {'id':id, 'status_validacao':status, 'registrado_em':(AGORA-timedelta(days=dias)).isoformat(),
            'latitude':lat, 'longitude':-43.1}


def test_filtro_espacial_temporal_e_validacao():
    itens = [registro('1'),registro('1'),registro('2','pendente'),registro('3','excluido'),
             registro('4',dias=31),registro('5',dias=-1),registro('6',lat=-23.5),
             registro('7',dias=30),registro('8',dias=0),registro('9','confirmado_humano')]
    assert contar_proximos(itens,-22.9,-43.1,AGORA) == 3
    assert contar_proximos(itens,-22.9,-43.1,AGORA,excluir_id='1') == 2
    assert distancia_m(-22.9,-43.1,-22.9,-43.1) == 0


def test_raio_inclusivo():
    r = registro(lat=-22.899)
    d = distancia_m(-22.9,-43.1,r['latitude'],r['longitude'])
    assert contar_proximos([r],-22.9,-43.1,AGORA,raio_m=d) == 1
    assert contar_proximos([r],-22.9,-43.1,AGORA,raio_m=d-.01) == 0


def test_persistencia_idempotencia_e_confirmacao(tmp_path, monkeypatch):
    monkeypatch.setenv('AQUASENTINEL_DB',str(tmp_path/'teste.sqlite3'))
    r = registro(status='pendente')
    assert salvar(r)
    assert not salvar(r)
    assert len(listar()) == 1
    with pytest.raises(DadosInvalidos): confirmar('1','')
    confirmar('1','Revisor')
    assert listar()[0]['status_validacao'] == 'confirmado_humano'
    assert listar()[0]['revisor'] == 'Revisor'
    with pytest.raises(DadosInvalidos): confirmar('1','Revisor')
    with pytest.raises(DadosInvalidos): confirmar('inexistente','Revisor')


def test_confirmacao_futura_nao_antecipa_historico():
    r = registro(status='confirmado_humano')
    r['validado_em'] = (AGORA+timedelta(days=1)).isoformat()
    assert contar_proximos([r],-22.9,-43.1,AGORA) == 0
