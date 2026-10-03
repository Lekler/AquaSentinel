from pathlib import Path
from streamlit.testing.v1 import AppTest
from interface_idioma import traduzir

APP = str(Path(__file__).resolve().parents[1] / 'app.py')


def test_idioma_persiste_na_navegacao_e_pode_voltar(tmp_path, monkeypatch):
    monkeypatch.setenv('AQUASENTINEL_DB', str(tmp_path / 'idioma.sqlite3'))
    app = AppTest.from_file(APP, default_timeout=30)
    app.query_params['lang'] = 'en'
    app.run()
    for page in ['mapa', 'dados', 'duvidas', 'monitoramento']:
        app.switch_page(f'app_pages/{page}.py')
        app.query_params.clear()
        app.run()
        assert not app.exception
        assert app.session_state['idioma'] == 'en'
    app.switch_page('app_pages/mapa.py').run()
    period = app.selectbox(key='mapa-periodo')
    assert '30 days' in period.options
    period.select('30 dias').run()
    assert not app.exception
    assert app.session_state['mapa-periodo'] == '30 dias'
    app.query_params['lang'] = 'pt'
    app.run()
    assert app.session_state['idioma'] == 'pt'
    assert '30 dias' in app.selectbox(key='mapa-periodo').options


def test_traducao_preserva_identificadores_e_dados():
    assert traduzir('WB-BG-001', True) == 'WB-BG-001'
    assert traduzir('Canal do Fundão', True) == 'Canal do Fundão'
    assert traduzir('Moderado', True) == 'Moderate'
    assert traduzir('Moderado', False) == 'Moderado'
