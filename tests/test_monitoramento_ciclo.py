from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest

from corpos_hidricos import cadastrar_corpo
from monitoramento import (cadastrar_trecho, iniciar_sessao, encerrar_sessao, sessao_autorizada,
                           revisar_sessao, listar_entidades, metricas_sessao, lacunas)
from relatos import salvar_foto, revisar_foto, obter_foto, listar_fotos
from ciclo import hash_chave, consultar_recibo, historico_eventos, mudar_etapa, feedback
from evolucao import registrar_acao, comparar_acao, indicadores
from test_fotos import amostra

APP = str(Path(__file__).resolve().parents[1]/'app.py')
AGORA = datetime(2026, 9, 27, 18, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def banco(tmp_path, monkeypatch):
    monkeypatch.setenv('AQUASENTINEL_DB', str(tmp_path/'monitor.sqlite3'))
    sys.modules.pop('localizacao', None)


def trecho():
    c = cadastrar_corpo('Corpo de teste', 'Equipe')
    return cadastrar_trecho('Trecho A', c['id'], -22., -43., 100., 'Equipe')


def foto(sessao=None, chave=None, dias=0, nivel='Moderado'):
    r, imagem, anotada = amostra()
    r.update(registrado_em=(AGORA-timedelta(days=dias)).isoformat(),
             consentimento_publicacao=True, recibo_hash=hash_chave('recibo-teste'), nivel_informado=nivel)
    # Identidade diferente para fotos sintéticas de testes de cronologia.
    r['image_hash'] = r['id']
    return salvar_foto(r, imagem, anotada, sessao, chave)[0]


def test_sessao_recebe_fotos_calcula_taxas_e_impede_novas_apos_fim():
    t = trecho()
    s, chave = iniciar_sessao(t['id'], True, AGORA-timedelta(minutes=10))
    r = foto(s['id'], chave)
    assert r['modo'] == 'estruturado' and r['trecho_id'] == t['id']
    fim = encerrar_sessao(s['id'], chave, 100, True, False, AGORA)
    assert fim['quantidade_fotos'] == 1 and fim['duracao_min'] == 10
    assert metricas_sessao(fim, listar_fotos())['itens_m'] is None
    revisar_foto(r['id'], 'validado', 'Equipe', t['waterbody_id'])
    revisar_sessao(s['id'], 'validado', 'Equipe')
    m = metricas_sessao(sessao_autorizada(s['id'], chave), listar_fotos())
    assert m['itens_m'] == .02 and m['itens_100m'] == 2 and m['itens_min'] == .2
    with pytest.raises(ValueError, match='encerrada'):
        foto(s['id'], chave)
    with pytest.raises(ValueError):
        encerrar_sessao(s['id'], chave, 100, True, False, AGORA)


def test_recibos_privados_e_limites_de_sessao():
    t = trecho()
    with pytest.raises(ValueError):
        iniciar_sessao(t['id'], False)
    s, chave = iniciar_sessao(t['id'], True, AGORA-timedelta(minutes=5))
    assert chave not in str(listar_entidades('sessao'))
    with pytest.raises(ValueError, match='inválido'):
        sessao_autorizada(s['id'], 'errado')
    with pytest.raises(ValueError):
        foto(s['id'], 'errado')
    with pytest.raises(ValueError):
        encerrar_sessao(s['id'], chave, 0, True, True, AGORA)
    with pytest.raises(ValueError):
        encerrar_sessao(s['id'], chave, 100, True, False, AGORA)
    assert not listar_fotos()


def test_zero_explicito_e_diferente_de_sem_dado():
    t = trecho()
    sem = lacunas([t], [], [], AGORA)[0]
    assert sem['classe'] == 'Não temos dado' and sem['ultima_dias'] is None
    s, chave = iniciar_sessao(t['id'], True, AGORA-timedelta(minutes=5))
    fim = encerrar_sessao(s['id'], chave, 100, True, True, AGORA)
    assert metricas_sessao(fim, [])['itens_m'] is None
    revisar_sessao(s['id'], 'validado', 'Equipe')
    sessoes = listar_entidades('sessao')
    assert metricas_sessao(sessoes[0], [])['itens_m'] == 0
    cobertura = lacunas([t], [], sessoes, AGORA)[0]
    assert cobertura['estado'] == 'Observado: nenhum resíduo visto'
    assert cobertura['dias_30'] == 1 and cobertura['classe'] == 'Pouco observado'
    assert indicadores([], AGORA, sessoes)['Corpos hídricos monitorados'] == 1


def test_sem_cobertura_ou_foto_pendente_nao_inventa_taxa():
    t = trecho()
    s, chave = iniciar_sessao(t['id'], True, AGORA-timedelta(minutes=5))
    r = foto(s['id'], chave)
    with pytest.raises(ValueError, match='conflita'):
        encerrar_sessao(s['id'], chave, 100, True, True, AGORA)
    encerrar_sessao(s['id'], chave, 100, False, False, AGORA)
    revisar_foto(r['id'], 'validado', 'Equipe', t['waterbody_id'])
    revisar_sessao(s['id'], 'validado', 'Equipe')
    assert not metricas_sessao(listar_entidades('sessao')[0], listar_fotos())['completa']


def test_lacunas_contam_dias_e_mostram_42_dias():
    t = trecho()
    r = foto(dias=42, nivel='Sem resíduos')
    revisar_foto(r['id'], 'validado', 'Equipe', t['waterbody_id'])
    l = lacunas([t], listar_fotos(), [], AGORA)[0]
    assert l['ultima_dias'] == 42 and l['classe'] == 'Sem observação recente'
    assert l['chamada'] == 'Este trecho precisa de nova observação.'
    rs = []
    for i in range(4):
        rs.append({**obter_foto(r['id'])[0], 'id':str(i), 'registrado_em':(AGORA-timedelta(days=i)).isoformat()})
    assert lacunas([t], rs*3, [], AGORA)[0]['dias_30'] == 4
    assert lacunas([t], rs, [], AGORA)[0]['classe'] == 'Muito observado'


def test_trecho_nao_aceita_corpo_divergente_ou_coordenadas_ausentes():
    from monitoramento import pertence_trecho
    t = trecho()
    assert not pertence_trecho({'trecho_id': t['id'], 'waterbody_id': 'outro',
                               'waterbody_confirmado': True}, t)
    assert not pertence_trecho({'waterbody_id': t['waterbody_id'],
                               'waterbody_confirmado': True}, t)


def test_ciclo_recibo_feedback_e_terceira_observacao():
    t = trecho()
    registros = []
    for d in (10, 5, 0):
        r = foto(dias=d)
        revisar_foto(r['id'], 'validado', 'Equipe', t['waterbody_id'])
        registros.append(obter_foto(r['id'])[0])
    r = registros[-1]
    assert 'validado' in feedback(r, registros)[0]
    assert 'terceira observação' in feedback(r, registros)[1]
    with pytest.raises(ValueError, match='inválido'):
        consultar_recibo(r['id'], 'errado')
    assert consultar_recibo(r['id'], 'recibo-teste')['id'] == r['id']
    assert [e['etapa'] for e in historico_eventos(r)][:2] == ['recebida', 'aguardando revisão']
    mudar_etapa(r['id'], 'encaminhada', 'Equipe', 'Encaminhada para avaliação.')
    mudar_etapa(r['id'], 'ação realizada', 'Equipe', 'Limpeza registrada.')
    mudar_etapa(r['id'], 'acompanhamento', 'Equipe', 'Nova observação agendada.')
    mudar_etapa(r['id'], 'resolvida', 'Equipe', 'Equipe confirmou conclusão.')
    assert obter_foto(r['id'])[0]['etapa'] == 'resolvida'
    with pytest.raises(ValueError):
        mudar_etapa(r['id'], 'recebida', 'Equipe', 'Não pode retroceder assim')
    pendente = foto()
    with pytest.raises(ValueError):
        mudar_etapa(pendente['id'], 'resolvida', 'Equipe', 'Ainda não revisado')


def test_comparacao_acao_mesmo_local_e_lados_ausentes():
    t = trecho()
    a, b = foto(dias=20, nivel='Muito poluído'), foto(dias=2, nivel='Sem resíduos')
    revisar_foto(a['id'], 'validado', 'Equipe', t['waterbody_id'])
    revisar_foto(b['id'], 'validado', 'Equipe', t['waterbody_id'])
    acao = registrar_acao(a['id'], 'Limpeza', AGORA-timedelta(days=10), 'Retirada de resíduos', 'Equipe')
    comparacao = comparar_acao(acao, listar_fotos())
    assert comparacao['antes']['registro']['id'] == a['id']
    assert comparacao['depois']['registro']['id'] == b['id']
    assert comparacao['depois']['wps'] == 0
    assert comparar_acao(acao, [obter_foto(a['id'])[0]])['depois'] is None


def test_paginas_novas_e_sessao_na_interface():
    trecho()
    app = AppTest.from_file(APP, default_timeout=20).run()
    for pagina in ('transparencia','lacunas','acompanhamento','monitoramento'):
        app.switch_page(f'app_pages/{pagina}.py').run()
        assert not app.exception
    next(c for c in app.checkbox if 'Autorizo' in c.label).check()
    next(b for b in app.button if b.label == 'Iniciar sessão').click().run()
    assert not app.exception and app.session_state['monitor_id']
    app.switch_page('app_pages/registrar.py').run()
    assert not app.exception and app.selectbox(key='foto-modo').value == 'Monitoramento estruturado'
