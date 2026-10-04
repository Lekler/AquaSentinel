"""Ajustes do vídeo de 03/10: código único sem hífen, revisão em lote, localização e IA em blocos."""
from pathlib import Path
import sys

import pytest
from streamlit.testing.v1 import AppTest

from ciclo import ALFABETO_CODIGO, consultar_recibo, gerar_codigo, hash_chave
from relatos import listar_fotos, salvar_foto
from test_fotos import amostra
from visao import janelas, remover_contidas

APP = str(Path(__file__).resolve().parents[1] / 'app.py')


@pytest.fixture(autouse=True)
def banco(tmp_path, monkeypatch):
    monkeypatch.setenv('AQUASENTINEL_DB', str(tmp_path / 'video.sqlite3'))
    monkeypatch.setenv('AQUASENTINEL_REVIEW_PASSWORD', 'teste-video')
    sys.modules.pop('localizacao', None)


def salvar(codigo, imagem_hash=None):
    r, foto, anotada = amostra()
    r.update(recibo_hash=hash_chave(codigo), consentimento_publicacao=True)
    if imagem_hash:
        r['image_hash'] = imagem_hash
    return salvar_foto(r, foto, anotada)[0]


def test_codigos_sem_hifen_e_faceis_de_copiar():
    r, _, _ = amostra()
    for codigo in (gerar_codigo(12), r['id']):
        assert codigo.isalnum() and codigo.isupper() and set(codigo) <= set(ALFABETO_CODIGO)
    assert len(gerar_codigo(12)) == 12


def test_consulta_so_com_codigo_tolera_espacos_hifens_e_minusculas():
    codigo = gerar_codigo(12)
    r = salvar(codigo)
    for colado in (codigo, f'  {codigo.lower()} ', f'{codigo[:4]}-{codigo[4:8]} {codigo[8:]}',
                   f'Código de acompanhamento: {codigo}'):
        assert consultar_recibo('', colado)['id'] == r['id']
    assert consultar_recibo(r['id'], codigo)['id'] == r['id']
    with pytest.raises(ValueError):
        consultar_recibo('', 'ERRADO123456')
    with pytest.raises(ValueError):
        consultar_recibo('', '')


def test_recibo_antigo_continua_valido_sem_id():
    antigo = 'aB3-x_Y9antigo'
    r = salvar(antigo)
    assert consultar_recibo('', antigo)['id'] == r['id']


def test_pagina_acompanhamento_com_um_unico_campo():
    codigo = gerar_codigo(12)
    salvar(codigo)
    app = AppTest.from_file(APP, default_timeout=30).run()
    app.switch_page('app_pages/acompanhamento.py').run()
    app.text_input(key='acompanhamento-codigo').set_value(codigo.lower())
    next(b for b in app.button if b.label == 'Consultar acompanhamento').click().run()
    assert not app.exception and not app.error
    assert any('aguardando revisão' in i.value for i in app.info)


def test_revisao_em_lote_valida_todos_e_publica_no_mapa():
    for i in range(3):
        salvar(gerar_codigo(12), imagem_hash=f'{i:064d}')
    app = AppTest.from_file(APP, default_timeout=30).run()
    app.switch_page('app_pages/mapa.py').run()
    app.text_input(key='senha_revisao').set_value('teste-video')
    next(b for b in app.button if b.label == 'Entrar').click().run()
    app.button(key='lote-todos').click().run()
    assert app.error  # Exige responsável.
    app.text_input(key='equipe-responsavel').set_value('Equipe')
    app.button(key='lote-todos').click().run()
    assert not app.exception
    assert all(r['revisao'] == 'validado' for r in listar_fotos())
    assert any('3 registro(s) validado(s)' in s.value for s in app.success)
    assert app.get('deck_gl_json_chart')  # Mapa da comunidade + acervo continuam visíveis.


def test_localizacao_gps_nao_desmarca_confirmacao():
    from unittest.mock import patch
    app = AppTest.from_file(APP, default_timeout=20).run()
    app.switch_page('app_pages/registrar.py').run()
    # Valores de formulário só chegam ao servidor no envio; simula a caixa já marcada na sessão.
    app.session_state['foto_publicacao'] = True
    app.run()
    gps = {'latitude': -22.9, 'longitude': -43.1, 'accuracy': 8, 'timestamp': 1, 'source': 'gps'}
    with patch('localizacao.obter_localizacao', side_effect=[gps, None]):
        app.run()
    assert not app.exception
    assert app.session_state['foto_publicacao']
    assert app.checkbox(key='foto_publicacao').value
    assert any('Localização definida' in s.value for s in app.success)


def test_blocos_cobrem_a_foto_e_unem_recortes_parciais():
    assert janelas(640, 640, 960, .2) == []
    blocos = janelas(1920, 1440, 960, .2)
    assert max(b[2] for b in blocos) == 1920 and max(b[3] for b in blocos) == 1440
    assert all(b[2] - b[0] <= 960 and b[3] - b[1] <= 960 for b in blocos)
    inteira = {'bbox': [100, 100, 300, 300], 'confidence': .9}
    pedaco = {'bbox': [100, 100, 180, 300], 'confidence': .6}
    outra = {'bbox': [500, 500, 600, 600], 'confidence': .5}
    assert remover_contidas([pedaco, inteira, outra]) == [inteira, outra]
