from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

from streamlit.testing.v1 import AppTest
from test_fotos import amostra
from relatos import criar_registro, salvar_foto, revisar_foto

APP = str(Path(__file__).resolve().parents[1] / 'app.py')


def preparar(tmp_path, monkeypatch):
    monkeypatch.setenv('AQUASENTINEL_DB', str(tmp_path / 'mapa.sqlite3'))
    analise, foto, anotada = amostra()
    r = criar_registro(analise, 'Canal de teste', -22.83, -43.24, 'Bloqueando')
    r['consentimento_publicacao'] = True
    salvar_foto(r, foto, anotada)
    revisar_foto(r['id'], 'validado', 'Equipe')
    return r, foto, anotada


def test_mapa_camadas_periodos_detalhes_e_pagina(tmp_path, monkeypatch):
    r, _, _ = preparar(tmp_path, monkeypatch)
    app = AppTest.from_file(APP, default_timeout=20).run()
    app.switch_page('app_pages/mapa.py').run()
    assert not app.exception
    assert any(m.label == 'Locais observados' and m.value == '1' for m in app.metric)
    chart = app.get('deck_gl_json_chart')[0]
    spec = json.loads(chart.proto.json)
    layer = spec['layers'][0]
    assert layer['radiusMinPixels'] == layer['radiusMaxPixels'] == 10
    assert layer['data'][0]['cor'] == [0, 0, 0]
    assert 'simbolo' not in layer['data'][0]
    assert len(spec['layers']) == 1
    app.button_group(key='mapa-camada').set_value('Cobertura de observação').run()
    assert not app.exception
    spec = json.loads(app.get('deck_gl_json_chart')[0].proto.json)
    assert spec['layers'][0]['data'][0]['cor'] == [191, 219, 254]
    app.selectbox(key='mapa-periodo').select('Todo o período').run()
    app.button(key=f'abrir-{r["id"]}').click().run()
    assert not app.exception
    assert any(m.label == 'WPS · índice experimental' for m in app.metric)
    assert app.get('imgs') or app.get('image'), [node.type for node in app]
    app.switch_page('app_pages/local.py')
    app.query_params['id'] = r['id']
    app.run()
    assert not app.exception
    assert any(m.label == 'Dias diferentes observados' and m.value == '1' for m in app.metric)
    assert any('Bloqueando' in str(df.value) for df in app.dataframe)


def test_pagina_nao_expoe_id_privado(tmp_path, monkeypatch):
    r, _, _ = preparar(tmp_path, monkeypatch)
    r.update(consentimento_publicacao=False, revisao='validado')
    with patch('relatos.listar_fotos', return_value=[r]), patch('relatos.obter_foto') as foto:
        app = AppTest.from_file(APP, default_timeout=20).run()
        app.switch_page('app_pages/local.py')
        app.query_params['id'] = r['id']
        app.run()
        assert not app.exception and not app.metric
        foto.assert_not_called()


def test_filtro_antigo_e_sem_residuos_continua_visivel(tmp_path, monkeypatch):
    r, _, _ = preparar(tmp_path, monkeypatch)
    r.update(revisao='validado', nivel_informado='Sem resíduos',
             registrado_em=(datetime.now(timezone.utc)-timedelta(days=40)).isoformat())
    with patch('relatos.listar_fotos', return_value=[r]):
        app = AppTest.from_file(APP, default_timeout=20).run()
        app.switch_page('app_pages/mapa.py').run()
        assert not app.exception and app.metric[0].value == '0'
        app.selectbox(key='mapa-periodo').select('90 dias').run()
        assert not app.exception and app.metric[0].value == '1'


def test_clique_no_ponto_abre_detalhes_e_ignora_id_desconhecido(tmp_path, monkeypatch):
    r, _, _ = preparar(tmp_path, monkeypatch)
    for ident, esperado in [(r['id'], True), ('id-privado-injetado', False)]:
        evento = SimpleNamespace(selection={'objects': {'locais': [{'id': ident}]}})
        with patch('streamlit.pydeck_chart', return_value=evento):
            app = AppTest.from_file(APP, default_timeout=20).run()
            app.switch_page('app_pages/mapa.py').run()
            assert not app.exception
            assert bool(app.get('image')) == esperado
            assert any(m.label == 'CS · confiança combinada' for m in app.metric) == esperado
