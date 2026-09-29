from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
import streamlit as st
import pytest
from streamlit.testing.v1 import AppTest
from previsao import ErroPrevisao

APP = str(Path(__file__).resolve().parents[1] / 'painel_ari.py')


@pytest.fixture(autouse=True)
def banco_isolado(tmp_path, monkeypatch):
    monkeypatch.setenv('AQUASENTINEL_DB', str(tmp_path/'app.sqlite3'))
    st.cache_data.clear()


def resposta():
    t = int(datetime.now(timezone.utc).timestamp()) // 3600 * 3600
    return {'consultado_em': datetime.now(timezone.utc).isoformat(), 'url': 'https://api.open-meteo.com/v1/forecast',
            'dados': {'timezone': 'America/Sao_Paulo',
                      'hourly_units': {'time': 'unixtime', 'precipitation': 'mm', 'precipitation_probability': '%'},
                      'hourly': {'time': [t+i*3600 for i in range(72)], 'precipitation': [30.0]*72,
                                 'precipitation_probability': [90.0]*72}}}


def test_fluxo_cache_coordenadas_e_falha():
    st.cache_data.clear()
    with patch('previsao.consultar_previsao', return_value=resposta()) as consulta:
        app = AppTest.from_file(APP, default_timeout=15).run()
        assert not app.exception
        assert not app.metric
        app.button(key="atualizar").click().run()
        assert not app.exception
        assert app.session_state['resultado']['ari_score'] == 65.33
        assert len(app.metric) == 4
        assert consulta.call_count == 1
        app.selectbox[0].select('Alto')
        app.button(key="atualizar").click().run()
        assert not app.exception
        assert app.session_state['resultado']['ari_score'] == 86.67
        assert consulta.call_count == 1
        app.number_input[0].set_value(-23.)
        app.button(key="atualizar").click().run()
        assert consulta.call_count == 2
        next(c for c in app.checkbox if c.label=='Consultar API sem usar cache').check()
        app.button(key="atualizar").click().run()
        assert not app.exception
        assert consulta.call_count == 3
        consulta.side_effect = ErroPrevisao('Serviço indisponível (HTTP 503).')
        app.button(key="atualizar").click().run()
        assert not app.exception
        assert app.error and '503' in app.error[0].value
        assert not app.metric
        consulta.side_effect = None
        app.button(key="atualizar").click().run()
        assert not app.exception
        assert len(app.metric) == 4
        assert not app.error
    st.cache_data.clear()


def test_nome_vazio_sem_consulta():
    with patch('previsao.consultar_previsao') as consulta:
        app = AppTest.from_file(APP, default_timeout=15).run()
        app.text_input[0].set_value('   ')
        app.button(key="atualizar").click().run()
        assert not app.exception
        assert app.error
        consulta.assert_not_called()


def test_historico_e_confirmacao_exigem_senha_da_equipe(monkeypatch):
    monkeypatch.setenv('AQUASENTINEL_REVIEW_PASSWORD', 'senha-teste')
    app = AppTest.from_file(APP, default_timeout=15).run()
    assert not app.exception
    assert not any(b.label == 'Confirmar relato' for b in app.button)
    assert not any(c.label=='Condição transcrita de fonte oficial' for c in app.checkbox)
    app.button(key='atualizar').click().run()
    assert not any(b.key == 'salvar' for b in app.button)


def test_triagem_e_revisao_persistente(monkeypatch):
    from historico import listar
    monkeypatch.setenv('AQUASENTINEL_REVIEW_PASSWORD', 'senha-teste')
    with patch('previsao.consultar_previsao', return_value=resposta()) as consulta:
        app = AppTest.from_file(APP, default_timeout=15).run()
        app.slider[0].set_value(70)
        app.button(key="atualizar").click().run()
        assert not app.exception
        assert app.session_state['resultado']['status_validacao'] == 'pendente'
        assert not app.metric
        consulta.assert_not_called()
        app.text_input(key='senha_revisao').set_value('senha-teste')
        next(b for b in app.button if b.label=='Entrar').click().run()
        app.button(key='salvar').click().run()
        app.button(key='salvar').click().run()
        assert len(listar()) == 1
        app.text_input(key='responsavel_revisao').set_value('Pessoa revisora')
        [b for b in app.button if b.label == 'Confirmar relato'][0].click().run()
        assert not app.exception
        assert listar()[0]['status_validacao'] == 'confirmado_humano'
        app.button(key='nova').click().run()
        app.slider[0].set_value(90)
        app.button(key="atualizar").click().run()
        assert not app.exception
        assert app.session_state['resultado']['componentes']['F'] == 25
        app.button(key='salvar').click().run()
        assert not app.exception  # inclusive mapa do histórico


def test_transbordamento_com_api_indisponivel(monkeypatch):
    monkeypatch.setenv('AQUASENTINEL_REVIEW_PASSWORD', 'senha-teste')
    with patch('previsao.consultar_previsao', side_effect=ErroPrevisao('HTTP 503')):
        app = AppTest.from_file(APP, default_timeout=15).run()
        app.text_input(key='senha_revisao').set_value('senha-teste')
        next(b for b in app.button if b.label=='Entrar').click().run()
        app.selectbox[1].select('Transbordamento')
        app.checkbox[1].check()
        app.text_input[2].set_value('Fonte oficial, estação e horário de exemplo')
        app.button(key="atualizar").click().run()
        assert not app.exception
        assert app.session_state['resultado']['avaliacao_urgente']
        assert app.session_state['resultado']['ari_score'] is None
        assert any('transbordamento' in e.value for e in app.error)
