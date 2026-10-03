from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
from corpos_hidricos import cadastrar_corpo, atualizar_corpo, listar_corpos, obter_corpo
from relatos import salvar_foto, listar_fotos
from test_fotos import amostra

APP = str(Path(__file__).resolve().parents[1]/'app.py')


@pytest.fixture(autouse=True)
def banco(tmp_path, monkeypatch):
    monkeypatch.setenv('AQUASENTINEL_DB', str(tmp_path/'ux.sqlite3'))
    monkeypatch.setenv('AQUASENTINEL_REVIEW_PASSWORD', 'teste-ux')


def login(app, senha='teste-ux'):
    app.text_input(key='senha_revisao').set_value(senha)
    next(b for b in app.button if b.label in ('Entrar', 'Sign in')).click().run()
    assert not app.exception


def test_login_revisao_imagem_unica_saida_e_expiracao(monkeypatch):
    r, foto, anotada = amostra()
    salvar_foto(r, foto, anotada)
    app = AppTest.from_file(APP, default_timeout=30).run()
    app.switch_page('app_pages/mapa.py').run()
    app.button_group(key='mapa-conjunto').set_value('Ocorrências da comunidade').run()
    assert not any(b.label=='Validar relato' for b in app.button)
    login(app, 'incorreta')
    assert app.error and not any(b.label=='Validar relato' for b in app.button)
    login(app)
    assert any(b.label=='Validar relato' for b in app.button)
    images = app.get('imgs') or app.get('image')
    assert len(images)==1
    labels=[s.value for s in app.subheader]
    assert labels.index('Evidência') < labels.index('Análise da IA') < labels.index('Localização') < labels.index('Decisão do revisor')
    app.button(key='equipe-sair').click().run()
    assert not app.exception
    assert not any(b.label=='Validar relato' for b in app.button)
    assert not (app.get('imgs') or app.get('image'))
    login(app)
    app.session_state['equipe_auth'] = {**app.session_state['equipe_auth'], 'expira': 0}
    app.run()
    assert not any(b.label=='Validar relato' for b in app.button)
    login(app)
    monkeypatch.setenv('AQUASENTINEL_REVIEW_PASSWORD', 'rotacionada')
    app.run()
    assert not any(b.label=='Validar relato' for b in app.button)


def test_equipe_valida_registro_e_confirma_corpo():
    r, foto, anotada = amostra()
    salvar_foto(r, foto, anotada)
    c = cadastrar_corpo('Canal Teste', 'Equipe', 'Canal', 'Trecho teste')
    app = AppTest.from_file(APP, default_timeout=30).run()
    app.switch_page('app_pages/mapa.py').run()
    login(app)
    app.text_input(key='equipe-responsavel').set_value('Equipe')
    app.selectbox(key=f"revisao-corpo-{r['id']}").select(c['id'])
    next(b for b in app.button if b.label=='Validar relato').click().run()
    assert not app.exception
    salvo=listar_fotos()[0]
    assert salvo['revisao']=='validado'
    assert salvo['waterbody_id']==c['id'] and salvo['waterbody_confirmado']
    app.selectbox(key='revisao-fila').select('Todos os registros').run()
    assert not app.exception
    assert app.selectbox(key='revisao-relato').value==r['id']
    assert any(e.label=='Ver detalhes técnicos' for e in app.expander)


def test_editar_corpo_preserva_id_e_rejeita_duplicado():
    a=cadastrar_corpo('Canal Antigo', 'Equipe', 'Canal', 'Nota')
    b=cadastrar_corpo('Rio Azul', 'Equipe', 'Rio')
    editado=atualizar_corpo(a['id'], 'Canal do Cunha', 'Revisora', 'Canal', 'Rio de Janeiro')
    assert editado['id']==a['id'] and editado['observacao']=='Rio de Janeiro'
    assert obter_corpo(a['id'])['nome']=='Canal do Cunha'
    with pytest.raises(ValueError,match='Já existe'):
        atualizar_corpo(a['id'],' RIO AZUL ', 'Equipe')
    assert len(listar_corpos())==2
    assert cadastrar_corpo('canal do cunha','Equipe')['id']==a['id']
    assert obter_corpo(b['id'])['nome']=='Rio Azul'


def test_publico_nao_recebe_detalhes_tecnicos():
    from unittest.mock import patch
    import sys
    sys.modules.pop('localizacao',None)
    r,f,a=amostra()
    with patch('interface_fotos.carregar_detector') as detector:
        detector.return_value.analisar.return_value=(r,f,a)
        app=AppTest.from_file(APP,default_timeout=30).run()
        app.switch_page('app_pages/registrar.py').run()
        app.file_uploader[0].upload('foto.jpg',f,'image/jpeg').run()
        assert not app.exception
        labels=[m.label for m in app.metric]
        assert labels==['Itens identificados','Confiança da IA']
        assert not any('técnic' in e.label or 'critério' in e.label for e in app.expander)
