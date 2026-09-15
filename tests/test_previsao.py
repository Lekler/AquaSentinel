from unittest.mock import Mock, patch
import pytest
import requests
from previsao import ErroPrevisao, consultar_previsao


def test_consulta_parametros_reais():
    response = Mock()
    response.json.return_value = {'hourly': {}}
    response.url = 'https://api.open-meteo.com/v1/forecast'
    with patch('previsao.requests.get', return_value=response) as get:
        r = consultar_previsao(-22.9068,-43.1729)
    assert r['dados'] == {'hourly': {}}
    p = get.call_args.kwargs
    assert p['params']['latitude'] == -22.9068
    assert p['params']['longitude'] == -43.1729
    assert p['params']['timeformat'] == 'unixtime'
    assert p['timeout'] == (5,20)


@pytest.mark.parametrize('erro', [requests.Timeout(), requests.ConnectionError()])
def test_falhas_rede(erro):
    with patch('previsao.requests.get', side_effect=erro):
        with pytest.raises(ErroPrevisao): consultar_previsao(0,0)


@pytest.mark.parametrize('status', [400,429,500,503])
def test_erros_http(status):
    response = Mock(status_code=status)
    response.raise_for_status.side_effect = requests.HTTPError(response=response)
    with patch('previsao.requests.get', return_value=response):
        with pytest.raises(ErroPrevisao, match=str(status)): consultar_previsao(0,0)


@pytest.mark.parametrize('dados', [[], {'error': True}])
def test_json_inesperado(dados):
    response = Mock()
    response.json.return_value = dados
    with patch('previsao.requests.get', return_value=response):
        with pytest.raises(ErroPrevisao): consultar_previsao(0,0)


def test_json_invalido():
    response = Mock()
    response.json.side_effect = ValueError('invalid JSON')
    with patch('previsao.requests.get', return_value=response):
        with pytest.raises(ErroPrevisao, match='JSON'): consultar_previsao(0,0)
