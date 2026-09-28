from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from corpos_hidricos import cadastrar_corpo, listar_corpos
from relatos import (criar_registro, salvar_foto, obter_foto, listar_fotos, revisar_foto,
                     indexar_fotos_antigas, vincular_corpo, resolver_similaridade, conexao)
from visao import preparar_imagem
from test_fotos import amostra
from test_aquaverify import imagem, bytes_imagem

APP = str(Path(__file__).resolve().parents[1] / 'app.py')


@pytest.fixture(autouse=True)
def banco(tmp_path, monkeypatch):
    monkeypatch.setenv('AQUASENTINEL_DB', str(tmp_path/'evidencia.sqlite3'))
    sys.modules.pop('localizacao', None)


def salvar(im=None):
    analise, _, _ = amostra()
    foto = bytes_imagem(im if im is not None else imagem())
    analise.update(image_hash=preparar_imagem(foto)[1], dimensoes_originais=list((im or imagem()).size))
    r = criar_registro(analise, 'Descrição livre', -22., -43., 'Moderado')
    r['consentimento_publicacao'] = True
    return salvar_foto(r, foto, foto)[0]


def test_catalogo_ids_estaveis_sem_duplicar_e_vinculo_auditado():
    primeiro = cadastrar_corpo('Canal do Fundão · Rio', 'Equipe')
    assert primeiro['id'] == 'WB-BG-001'
    assert cadastrar_corpo(' CANAL DO FUNDAO · RIO ', 'Equipe') == primeiro
    assert cadastrar_corpo('Outro canal', 'Equipe')['id'] == 'WB-BG-002'
    assert len(listar_corpos()) == 2
    r = salvar()
    vincular_corpo(r['id'], primeiro['id'], 'Equipe')
    salvo = obter_foto(r['id'])[0]
    assert salvo['waterbody_confirmado'] and salvo['waterbody_id'] == primeiro['id']
    assert salvo['historico_vinculos'][0]['responsavel'] == 'Equipe'
    assert salvo['revisao'] == 'nao_revisado'
    with pytest.raises(ValueError):
        vincular_corpo(r['id'], 'WB-BG-999', 'Equipe')


def test_similaridade_revisao_e_sha_exato():
    a = salvar()
    b = salvar(imagem().resize((400, 300)))
    assert b['similaridade']['quantidade'] == 1
    assert b['similaridade']['candidatas'][0]['id'] == a['id']
    assert len(listar_fotos()) == 2
    repetida = salvar()
    assert repetida['id'] == a['id'] and len(listar_fotos()) == 2
    with pytest.raises(ValueError):
        resolver_similaridade(b['id'], 'independente', 'Equipe', '')
    resolver_similaridade(b['id'], 'reutilizada', 'Equipe', 'Mesma foto redimensionada')
    assert obter_foto(b['id'])[0]['similaridade_decisao'] == 'reutilizada'


def test_indexacao_legada_preserva_revisao_e_dados():
    a, b = salvar(), salvar(imagem().crop((80, 60, 720, 540)))
    revisar_foto(a['id'], 'validado', 'Equipe')
    with conexao() as con:
        r = obter_foto(a['id'])[0]
        r.pop('phash')
        r.pop('similaridade')
        con.execute('UPDATE relatos_foto SET conteudo=? WHERE id=?', (json.dumps(r), a['id']))
    assert indexar_fotos_antigas() == 1
    assert obter_foto(a['id'])[0]['revisao'] == 'validado'
    assert obter_foto(b['id'])[0]['similaridade']['quantidade'] == 1
    assert indexar_fotos_antigas() == 0


def test_envios_concorrentes_comparam_um_ao_outro():
    # Inicializa o esquema antes de disparar as transações concorrentes.
    listar_fotos()
    with ThreadPoolExecutor(max_workers=2) as executor:
        a = executor.submit(salvar, imagem())
        b = executor.submit(salvar, imagem().resize((400, 300)))
        resultados = [a.result(), b.result()]
    assert sorted(r['similaridade']['quantidade'] for r in resultados) == [0, 1]


def test_revisao_confirma_codigo_e_atualiza_aquaverify():
    r = salvar()
    corpo = cadastrar_corpo('Rio de teste', 'Equipe')
    revisado = revisar_foto(r['id'], 'validado', 'Equipe', corpo['id'])
    assert revisado['waterbody_confirmado']
    assert revisado['aquaverify']['indice'] == r['aquaverify']['indice'] + 15


def test_interface_catalogo_protegido_e_cadastro(monkeypatch):
    monkeypatch.setenv('AQUASENTINEL_REVIEW_PASSWORD', 'senha-teste')
    app = AppTest.from_file(APP, default_timeout=20).run()
    app.switch_page('app_pages/mapa.py').run()
    assert not app.exception
    assert not any(b.label == 'Cadastrar corpo hídrico' for b in app.button)
    app.text_input(key='senha_revisao').set_value('senha-teste').run()
    app.text_input(key='equipe-responsavel').set_value('Equipe')
    app.text_input(key='cadastro-corpo').set_value('Canal novo')
    next(b for b in app.button if b.label == 'Cadastrar corpo hídrico').click().run()
    assert not app.exception
    assert listar_corpos()[0]['id'] == 'WB-BG-001'
    app.switch_page('app_pages/registrar.py').run()
    assert not app.exception
    assert 'WB-BG-001' in str(app.selectbox(key='foto-waterbody').options)
