"""Ações documentadas e comparações descritivas, sem atribuir causalidade."""
from datetime import datetime, timezone
from uuid import uuid4
from observacao import agrupar_locais, publicos, filtrar_periodo, data_registro
from monitoramento import inserir
from relatos import conexao, obter_foto
from hotspots import avaliar_hotspot
from wps import pontuar

TIPOS_ACAO = ['Limpeza', 'Vistoria', 'Intervenção', 'Mobilização']


def registrar_acao(registro_id, tipo, data, descricao, responsavel):
    if tipo not in TIPOS_ACAO or not descricao.strip() or not responsavel.strip():
        raise ValueError('Informe ação, descrição pública e responsável.')
    if data.tzinfo is None or data > datetime.now(timezone.utc):
        raise ValueError('Use uma data de ação já realizada com fuso horário.')
    r, _, _ = obter_foto(registro_id)
    if r.get('revisao') != 'validado' or not r.get('waterbody_confirmado'):
        raise ValueError('A ação precisa de relato validado e corpo hídrico confirmado.')
    acao = {'id': str(uuid4()), 'registro_id': registro_id, 'tipo': tipo, 'data': data.isoformat(),
            'descricao': descricao.strip()[:1000], 'responsavel': responsavel.strip()[:100],
            'criado_em': datetime.now(timezone.utc).isoformat(), 'waterbody_id': r['waterbody_id']}
    with conexao() as con:
        inserir(con, 'acao', acao)
        from ciclo import registrar_evento
        # Documenta a ação; a etapa é atualizada separadamente pela equipe.
        registrar_evento(con, registro_id, r.get('etapa', 'validada'), responsavel,
                         f"Ação registrada: {tipo} · {descricao.strip()[:500]}")
    return acao


def comparar_acao(acao, registros):
    data = datetime.fromisoformat(acao['data'])
    grupo = next((g for g in agrupar_locais(registros)
                  if any(r['id'] == acao['registro_id'] for r in g['registros'])), None)
    rs = grupo['registros'] if grupo else []
    anteriores = [r for r in rs if data_registro(r) < data]
    posteriores = [r for r in rs if data_registro(r) > data]
    antes = max(anteriores, key=data_registro) if anteriores else None
    depois = min(posteriores, key=data_registro) if posteriores else None
    def lado(r):
        return {'registro': r, 'wps': pontuar(r, publicos(registros), data_registro(r))['wps']} if r else None
    return {'antes': lado(antes), 'depois': lado(depois)}


def indicadores(registros, agora=None, sessoes=()):
    revisados = publicos(registros)
    return {'Total de registros recebidos': len(registros),
            'Registros validados': sum(r.get('revisao') == 'validado' for r in registros),
            'Registros recebidos nos últimos 30 dias': len(filtrar_periodo(registros, 30, agora)),
            'Corpos hídricos monitorados': len({r['waterbody_id'] for r in revisados
                                               if r.get('waterbody_confirmado') and r.get('waterbody_id')}
                                              | {s['waterbody_id'] for s in sessoes if s.get('status') == 'encerrada'
                                                 and s.get('revisao') == 'validado' and s.get('consentimento_publicacao')}),
            'Hotspots persistentes': sum(avaliar_hotspot(g['registros'], agora)['persistente'] for g in agrupar_locais(revisados)),
            'Objetos detectados · registros públicos': sum(int(r.get('total') or 0) for r in revisados)}
