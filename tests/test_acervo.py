from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile

from openpyxl import load_workbook
from PIL import Image
from streamlit.testing.v1 import AppTest
from acervo import listar_acervo, obter_imagens
from exportacao import gerar_excel, gerar_pacote
from observacao import publicos

APP = str(Path(__file__).resolve().parents[1] / 'app.py')


def test_acervo_real_exportavel_e_separado_de_registros_de_campo():
    registros = listar_acervo()
    assert len(registros) == 21
    assert len({r['image_hash'] for r in registros}) == 21
    assert len({(r['latitude'], r['longitude']) for r in registros}) == 21
    assert publicos(registros) == []
    for r in registros:
        assert r['total'] == len(r['itens'])
        assert r['origem_localizacao'] == 'atribuida_para_demonstracao'
        assert r['validacao_campo'] is False
        assert r['model_hash'] and r['fonte_geografica'].startswith('https://')
        assert r['total'] + r['duplicadas_removidas'] == r['deteccoes_modelo']
        assert len({d['item_id'] for d in r['itens']}) == r['total']
        assert abs(r['confianca_media'] - sum(d['confidence'] for d in r['itens']) / r['total'] * 100) <= .01
        foto, anotada = obter_imagens(r)
        for data in (foto, anotada):
            with Image.open(BytesIO(data)) as im:
                assert list(im.size) == r['dimensoes']
                im.verify()
        planilha = load_workbook(BytesIO(gerar_excel(r)))
        assert planilha['Detecções'].max_row == r['total'] + 1
        with ZipFile(BytesIO(gerar_pacote(r, foto, anotada))) as pacote:
            assert json.loads(pacote.read('registro.json'))['image_hash'] == r['image_hash']


def test_mapa_acervo_busca_selecao_downloads_e_equipe(tmp_path, monkeypatch):
    monkeypatch.setenv('AQUASENTINEL_DB', str(tmp_path / 'acervo.sqlite3'))
    app = AppTest.from_file(APP, default_timeout=30).run()
    app.switch_page('app_pages/mapa.py').run()
    assert not app.exception
    assert any(len(json.loads(m.proto.json)['layers'][0]['data']) == 21 for m in app.get('deck_gl_json_chart'))
    assert len(app.get('download_button')) == 2
    for r in listar_acervo():
        app.selectbox(key='acervo-foto').select(r['id']).run()
        assert not app.exception
        assert any(h.value == r['titulo'] for h in app.subheader)
    app.text_input(key='acervo-busca').set_value('bica').run()
    assert not app.exception
    assert any(m.label == 'Imagens no acervo' and m.value == '1' for m in app.metric)
    app.text_input(key='acervo-busca').set_value('inexistente123').run()
    assert not app.exception and any('Nenhum resultado' in i.value for i in app.info)
    app.switch_page('app_pages/sobre.py').run()
    assert not app.exception
    nomes = ['Alessandra Vaz', 'Alexandre Rodrigues', 'Felipe Mamed', 'Larisa de Sá', 'Marcela Rabelo']
    for nome in nomes:
        assert any(nome in m.value for m in app.markdown)
