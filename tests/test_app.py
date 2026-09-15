from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
import streamlit as st
from streamlit.testing.v1 import AppTest
from previsao import ErroPrevisao

APP = str(Path(__file__).resolve().parents[1] / 'app.py')


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
        app.button[0].click().run()
        assert not app.exception
        assert app.session_state['resultado']['priority_score'] == 67.5
        assert len(app.metric) == 4
        assert consulta.call_count == 1
        app.slider[0].set_value(100)
        app.button[0].click().run()
        assert not app.exception
        assert app.session_state['resultado']['priority_score'] == 90
        assert consulta.call_count == 1
        app.number_input[0].set_value(-23.)
        app.button[0].click().run()
        assert consulta.call_count == 2
        app.checkbox[0].check()
        app.button[0].click().run()
        assert not app.exception
        assert consulta.call_count == 3
        consulta.side_effect = ErroPrevisao('Serviço indisponível (HTTP 503).')
        app.button[0].click().run()
        assert not app.exception
        assert app.error and '503' in app.error[0].value
        assert not app.metric
        consulta.side_effect = None
        app.button[0].click().run()
        assert not app.exception
        assert len(app.metric) == 4
        assert not app.error
    st.cache_data.clear()


def test_nome_vazio_sem_consulta():
    with patch('previsao.consultar_previsao') as consulta:
        app = AppTest.from_file(APP, default_timeout=15).run()
        app.text_input[0].set_value('   ')
        app.button[0].click().run()
        assert not app.exception
        assert app.error
        consulta.assert_not_called()
