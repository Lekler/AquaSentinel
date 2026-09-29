from pathlib import Path
import sys
from unittest.mock import patch
import streamlit as st
from streamlit.testing.v1 import AppTest
import pytest
from test_fotos import amostra
from relatos import listar_fotos

APP = str(Path(__file__).resolve().parents[1] / 'app.py')


@pytest.fixture(autouse=True)
def banco(tmp_path, monkeypatch):
    monkeypatch.setenv('AQUASENTINEL_DB', str(tmp_path / 'ui.sqlite3'))
    st.cache_resource.clear()
    # AppTest cria um novo runtime por caso; registre o componente nesse runtime.
    sys.modules.pop('localizacao', None)


def iniciar():
    app = AppTest.from_file(APP, default_timeout=20).run()
    assert not app.exception
    app.switch_page('app_pages/registrar.py').run()
    assert not app.exception
    return app


def submit(app):
    next(b for b in app.button if b.label == 'Enviar ocorrência').click().run()


def test_fluxo_upload_salvar_revisar_e_abrir_mapa():
    r, foto, anotada = amostra()
    with patch('interface_fotos.carregar_detector') as carregar:
        carregar.return_value.analisar.return_value = (r, foto, anotada)
        app = iniciar()
        app.file_uploader[0].upload('foto.jpg', foto, 'image/jpeg').run()
        assert not app.exception and app.metric[0].value == '2'
        app.text_input(key='foto_nome').set_value('Canal real')
        app.number_input(key='foto_lat').set_value(-22.9)
        app.number_input(key='foto_lon').set_value(-43.1)
        app.button_group(key='foto_nivel').set_value('Moderado')
        app.multiselect(key='foto-sinais').select('Aves')
        app.text_area(key='foto-ambiente').set_value('Aves próximas à margem.')
        app.checkbox(key='foto_confirmacao').check()
        app.checkbox(key='foto_publicacao').check()
        submit(app)
        assert not app.exception
        assert len(listar_fotos()) == 1
        assert listar_fotos()[0]['contexto_ambiental']['sinais'] == ['Aves']
        assert any(b.label == 'Baixar Excel' for b in app.get('download_button'))
        assert any(b.label == 'Baixar foto identificada' for b in app.get('download_button'))
        assert carregar.return_value.analisar.call_count == 1
        from relatos import revisar_foto
        revisar_foto(listar_fotos()[0]['id'], 'validado', 'Teste')
        app.button(key='foto_abrir_mapa').click().run()
        assert not app.exception and any('Canal real' in e.label for e in app.get('expander'))


def test_captura_confirmada_substitui_upload_e_preserva_origem():
    r, foto, anotada = amostra()
    with patch('interface_fotos.carregar_detector') as carregar:
        carregar.return_value.analisar.return_value = (r, foto, anotada)
        app = iniciar()
        app.session_state['captura_pendente'] = foto
        app.run()
        assert not app.exception
        assert app.session_state['rascunho_foto']['origem'] == 'camera'
        app.run()
        assert carregar.return_value.analisar.call_count == 1


def test_gps_e_ajuste_manual_do_mapa():
    app = iniciar()
    gps = {'latitude':-22.9,'longitude':-43.1,'accuracy':12,'timestamp':100,'source':'gps'}
    with patch('localizacao.obter_localizacao', side_effect=[gps, None]):
        app.run()
    assert not app.exception
    assert app.number_input(key='foto_lat').value == -22.9
    assert app.session_state['foto_gps']['accuracy'] == 12
    ponto = {'latitude':-22.8,'longitude':-43.2,'source':'map'}
    with patch('localizacao.obter_localizacao', side_effect=[ponto, None]):
        app.run()
    assert not app.exception
    assert app.number_input(key='foto_lat').value == -22.8
    assert app.session_state['foto_gps'] is None
    assert not app.checkbox(key='foto_confirmacao').value


def test_troca_invalida_remove_analise_antiga_e_impede_salvar():
    r, foto, anotada = amostra()
    with patch('interface_fotos.carregar_detector') as carregar:
        carregar.return_value.analisar.return_value = (r, foto, anotada)
        app = iniciar()
        app.file_uploader[0].upload('foto.jpg', foto, 'image/jpeg').run()
        assert app.metric
        app.file_uploader[0].set_value(('errada.jpg', b'corrompida', 'image/jpeg')).run()
        assert not app.exception and app.error
        assert not app.metric
        assert next(b for b in app.button if b.label == 'Enviar ocorrência').disabled
        assert not listar_fotos()


def test_validacao_local_e_zero_deteccoes():
    from visao import resumir
    r, foto, anotada = amostra()
    r.update(resumir([], 100, 80))
    with patch('interface_fotos.carregar_detector') as carregar:
        carregar.return_value.analisar.return_value = (r, foto, anotada)
        app = iniciar()
        app.file_uploader[0].upload('foto.jpg', foto, 'image/jpeg').run()
        assert not app.metric
        assert any('Nenhum resíduo foi identificado automaticamente' in m.value for m in app.info)
        app.checkbox(key='foto_confirmacao').check()
        app.checkbox(key='foto_publicacao').check()
        submit(app)
        assert not app.exception and app.error and not listar_fotos()


def test_navegacao_sem_dados():
    app = AppTest.from_file(APP, default_timeout=15).run()
    for page in ('app_pages/mapa.py','painel_ari.py','app_pages/registrar.py','app_pages/inicio.py','app_pages/sobre.py','app_pages/duvidas.py'):
        app.switch_page(page).run()
        assert not app.exception


def test_reenvio_e_troca_pedem_nova_confirmacao():
    r, foto, anotada = amostra()
    with patch('interface_fotos.carregar_detector') as carregar:
        carregar.return_value.analisar.return_value = (r, foto, anotada)
        app = iniciar()
        app.file_uploader[0].upload('foto.jpg', foto, 'image/jpeg').run()
        app.text_input(key='foto_nome').set_value('Canal')
        app.number_input(key='foto_lat').set_value(-22.)
        app.number_input(key='foto_lon').set_value(-43.)
        app.button_group(key='foto_nivel').set_value('Pouco')
        app.checkbox(key='foto_confirmacao').check()
        app.checkbox(key='foto_publicacao').check()
        submit(app)
        assert not app.exception and len(listar_fotos()) == 1
        app.button(key='outra_foto').click().run()
        app.file_uploader[0].upload('mesma_renomeada.jpg', foto, 'image/jpeg').run()
        assert not app.checkbox(key='foto_confirmacao').value
        app.button_group(key='foto_nivel').set_value('Muito poluído')
        app.checkbox(key='foto_confirmacao').check()
        app.checkbox(key='foto_publicacao').check()
        submit(app)
        assert not app.exception and len(listar_fotos()) == 1
        assert any('já foi registrada' in w.value for w in app.warning)
        assert listar_fotos()[0]['nivel_informado'] == 'Pouco'


def test_rascunho_preservado_ao_navegar_sem_reexecutar_modelo():
    r, foto, anotada = amostra()
    with patch('interface_fotos.carregar_detector') as carregar:
        carregar.return_value.analisar.return_value = (r, foto, anotada)
        app = iniciar()
        app.file_uploader[0].upload('foto.jpg', foto, 'image/jpeg').run()
        app.switch_page('app_pages/inicio.py').run()
        app.switch_page('app_pages/registrar.py').run()
        assert not app.exception and app.metric[0].value == '2'
        assert carregar.return_value.analisar.call_count == 1
