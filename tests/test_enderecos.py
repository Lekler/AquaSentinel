from pathlib import Path
from unittest.mock import patch
import pytest
from streamlit.testing.v1 import AppTest
import enderecos

APP = str(Path(__file__).resolve().parents[1]/'app.py')


def feature(lat=-22.896, lon=-43.181, nome='Praça Mauá'):
    return {'geometry':{'coordinates':[lon,lat]},'properties':{'name':nome,'city':'Rio de Janeiro','countrycode':'BR'}}


@pytest.fixture(autouse=True)
def preparar(tmp_path, monkeypatch):
    monkeypatch.setenv('AQUASENTINEL_DB',str(tmp_path/'endereco.sqlite3'))
    monkeypatch.setenv('AQUASENTINEL_REVIEW_PASSWORD','teste-endereco')
    enderecos._buscar.clear()


def test_cep_resolve_endereco_antes_de_buscar_coordenadas_e_cache():
    with patch('enderecos._json',side_effect=[{'logradouro':'Praça Mauá','bairro':'Centro','localidade':'Rio de Janeiro','uf':'RJ'},
                                           {'features':[feature(),feature(),feature(float('nan'))]}]) as http:
        resultado=enderecos.buscar_endereco('20081-240')
        assert len(resultado)==1
        assert resultado[0]['latitude']==-22.896 and resultado[0]['longitude']==-43.181
        assert resultado[0]['source']=='address' and 'accuracy' not in resultado[0]
        assert '20081240' in http.call_args_list[0].args[0]
        assert http.call_args_list[1].args[1]['q']=='Praça Mauá, Centro, Rio de Janeiro, RJ'
        assert enderecos.buscar_endereco('20081-240')==resultado
        assert http.call_count==2


def test_validacao_nao_envia_cep_invalido_e_trata_cep_inexistente():
    with patch('enderecos._json') as http:
        with pytest.raises(ValueError,match='8 dígitos'):enderecos.buscar_endereco('12345')
        http.assert_not_called()
        http.return_value={'erro':True}
        with pytest.raises(ValueError,match='não encontrado'):enderecos.buscar_endereco('99999-999')
        assert http.call_count==1


def test_busca_vazia_e_resposta_invalida():
    with patch('enderecos._json',return_value={'features':[]}):
        assert enderecos.buscar_endereco('Um lugar, RJ')==[]
    with patch('enderecos._json',return_value={'error':'falha'}):
        with pytest.raises(ValueError,match='interpretar'):enderecos.buscar_endereco('Outro lugar, RJ')


def botao(app,label):
    return next(b for b in app.button if b.label==label)


def test_foto_busca_selecao_ajuste_manual_sem_sobrescrever_ponto():
    resultados=[{'latitude':-22.8,'longitude':-43.1,'label':'Praça A','source':'address','cep':False},
                {'latitude':-22.7,'longitude':-43.2,'label':'Praça B','source':'address','cep':False}]
    with patch('endereco_visual.buscar_endereco',return_value=resultados) as busca:
        app=AppTest.from_file(APP,default_timeout=30).run()
        app.switch_page('app_pages/registrar.py').run()
        assert not app.exception
        links=[n.label for n in app.get('page_link')]
        assert links[:4]==['Mapa e Registros','Monitoramento','Lacunas','Acompanhar']
        app.text_input(key='foto-endereco-busca').set_value('Praça A, Rio de Janeiro').run()
        busca.assert_not_called()
        botao(app,'Buscar endereço').click().run()
        assert not app.exception
        assert app.number_input(key='foto_lat').value==-22.8
        assert app.text_input(key='foto_nome').value=='Praça A'
        assert app.session_state['foto_gps'] is None
        app.selectbox(key='foto-endereco-selecionado').select(1).run()
        assert app.number_input(key='foto_lat').value==-22.7
        assert app.text_input(key='foto_nome').value=='Praça B'
        app.number_input(key='foto_lat').set_value(-22.6).run()
        assert app.number_input(key='foto_lat').value==-22.6
        assert busca.call_count==1
        assert any(e.label=='Ajustar coordenadas manualmente' for e in app.expander)


def test_trecho_busca_e_gps_sao_independentes_da_foto():
    resultado=[{'latitude':-22.8,'longitude':-43.1,'label':'Praça A','source':'address','cep':True}]
    with patch('endereco_visual.buscar_endereco',return_value=resultado):
        app=AppTest.from_file(APP,default_timeout=30).run()
        app.session_state['foto_lat']=-21.
        app.session_state['foto_lon']=-42.
        app.session_state['foto_salva_id']='outra-foto'
        app.switch_page('app_pages/mapa.py').run()
        app.text_input(key='senha_revisao').set_value('teste-endereco')
        botao(app,'Entrar').click().run()
        assert not app.exception
        app.text_input(key='trecho-endereco-busca').set_value('20081-240')
        botao(app,'Buscar endereço').click().run()
        assert not app.exception
        assert app.number_input(key='trecho-lat').value==-22.8
        assert app.session_state['foto_lat']==-21.
        gps={'latitude':-22.5,'longitude':-43.,'accuracy':10,'source':'gps'}
        with patch('localizacao.obter_localizacao',side_effect=[gps,None]):
            app.run()
        assert not app.exception
        assert app.number_input(key='trecho-lat').value==-22.5
        assert app.session_state['trecho-gps']['accuracy']==10


def test_falha_de_busca_preserva_ponto_atual():
    with patch('endereco_visual.buscar_endereco',side_effect=ValueError('Serviço indisponível')):
        app=AppTest.from_file(APP,default_timeout=30).run()
        app.switch_page('app_pages/registrar.py').run()
        app.number_input(key='foto_lat').set_value(-22.8)
        app.number_input(key='foto_lon').set_value(-43.1)
        app.text_input(key='foto-endereco-busca').set_value('Praça A, Rio')
        botao(app,'Buscar endereço').click().run()
        assert not app.exception and app.warning
        assert app.number_input(key='foto_lat').value==-22.8
