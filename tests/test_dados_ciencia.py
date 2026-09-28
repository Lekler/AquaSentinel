from datetime import date
from io import BytesIO
import json
from pathlib import Path
import pytest
from openpyxl import load_workbook
from streamlit.testing.v1 import AppTest
from test_fotos import amostra
from relatos import salvar_foto, revisar_foto, obter_foto
from ciclo import hash_chave
from dados_abertos import exportar, linha, filtrar, observation, DICIONARIO
from ambiente import validar_contexto

APP = str(Path(__file__).resolve().parents[1]/'app.py')


@pytest.fixture(autouse=True)
def banco(tmp_path, monkeypatch):
    monkeypatch.setenv('AQUASENTINEL_DB', str(tmp_path/'dados.sqlite3'))


def salvo():
    r, foto, anotada = amostra()
    r.update(recibo_hash=hash_chave('segredo'), consentimento_publicacao=True,
             contexto_ambiental=validar_contexto(['Aves', 'Espuma'], 'Observado da margem.'))
    return salvar_foto(r, foto, anotada)[0]


def test_versoes_snapshot_e_legado():
    r = salvo()
    assert r['versoes_indices']['wps'] == 'WPS v1'
    assert r['indices_snapshot']['cs'] == 64
    assert linha(r)['model_hash'] == 'a'*64
    revisar_foto(r['id'], 'validado', 'Equipe')
    assert obter_foto(r['id'])[0]['indices_snapshot']['wps'] > r['indices_snapshot']['wps']
    antigo = {**r}
    antigo.pop('versoes_indices')
    antigo.pop('indices_snapshot')
    assert linha(antigo)['wps'] is None and linha(antigo)['wps_versao'] is None


@pytest.mark.parametrize('formato', ['CSV', 'Excel', 'JSON', 'GeoJSON'])
def test_exportacao_whitelist_sem_segredos(formato):
    r = salvo()
    r.update(nome='=HYPERLINK("https://example.org")', segredo='nao-exportar')
    data = exportar([r], formato)
    if formato == 'Excel':
        wb = load_workbook(BytesIO(data))
        assert wb['Observações']['C2'].data_type == 's'
        assert len(list(wb['Dicionário'].rows)) == len(DICIONARIO)+1
        texto = str(list(wb['Observações'].values))
    else:
        texto = data.decode('utf-8-sig')
    assert 'recibo_hash' not in texto and 'segredo' not in texto and r['recibo_hash'] not in texto
    if formato == 'GeoJSON':
        feature = json.loads(texto)['features'][0]
        assert feature['geometry']['coordinates'] == [-43., -22.]
    if formato == 'JSON':
        item = json.loads(texto)['records'][0]
        assert set(item) == {'Observation', 'Location', 'FeatureOfInterest', 'ObservedProperty', 'metadata'}
        assert item['Observation']['phenomenonTime'] is None


def test_filtros_datas_locais_e_revisao():
    r = salvo()
    r.update(registrado_em='2026-09-28T01:00:00+00:00', waterbody_id='WB-BG-001')
    assert filtrar([r], date(2026,9,27), date(2026,9,27), 'WB-BG-001', 'Moderado', 'aguardando revisão', 'Não revisado') == [r]
    assert not filtrar([r], date(2026,9,28), None)
    assert not filtrar([r], corpo='WB-BG-002')
    assert not filtrar([r], nivel='Pouco')
    assert not filtrar([r], status='resolvida')
    assert not filtrar([r], revisao='Revisado')


def test_contexto_nao_muda_indices_e_gps_ajustado():
    r = salvo()
    assert r['contexto_ambiental']['sinais'] == ['Aves', 'Espuma']
    with pytest.raises(ValueError):
        validar_contexto(['diagnóstico'])
    r['gps'] = {'latitude': -21., 'longitude': -43., 'accuracy': 8}
    assert linha(r)['gps_precisao_m'] is None
    r['gps']['latitude'] = -22.
    assert linha(r)['gps_precisao_m'] == 8


def test_paginas_e_exportacao_privada_na_interface():
    r = salvo()
    app = AppTest.from_file(APP, default_timeout=20).run()
    for pagina in ['sobre', 'como_funciona', 'contato', 'duvidas', 'dados']:
        app.switch_page(f'app_pages/{pagina}.py').run()
        assert not app.exception
    assert app.metric[0].value == '0'  # Pendente não aparece na origem pública.
    app.button_group[0].set_value('Meus registros').run()
    app.text_area(key='dados-recibos').set_value(r['id'] + '; errado')
    next(b for b in app.button if b.label == 'Autorizar meus registros').click().run()
    assert app.error and app.metric[0].value == '0'
    app.text_area(key='dados-recibos').set_value(r['id'] + '; segredo')
    next(b for b in app.button if b.label == 'Autorizar meus registros').click().run()
    assert not app.exception and app.metric[0].value == '1'
    next(s for s in app.selectbox if s.label == 'Revisão').select('Revisado').run()
    assert app.metric[0].value == '0'
    next(b for b in app.button if b.label == 'Limpar acesso aos meus registros').click().run()
    assert not app.exception and app.metric[0].value == '0'
