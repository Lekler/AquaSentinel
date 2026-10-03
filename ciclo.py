"""Eventos de acompanhamento auditáveis e consulta pelo recibo do remetente."""
from datetime import datetime, timezone
from hashlib import sha256
import hmac
import json
from uuid import uuid4
from historico import marcador

ETAPAS = ['recebida', 'aguardando revisão', 'validada', 'recorrente', 'encaminhada',
          'ação realizada', 'acompanhamento', 'resolvida', 'rejeitada']
TRANSICOES = {
    'validada': {'recorrente', 'encaminhada', 'ação realizada', 'acompanhamento', 'resolvida'},
    'recorrente': {'encaminhada', 'ação realizada', 'acompanhamento', 'resolvida'},
    'encaminhada': {'ação realizada', 'acompanhamento', 'resolvida'},
    'ação realizada': {'acompanhamento', 'resolvida'},
    'acompanhamento': {'recorrente', 'encaminhada', 'ação realizada', 'resolvida'},
    'resolvida': {'acompanhamento', 'recorrente'},
}


# Sem 0/O, 1/I/L: códigos fáceis de ler, digitar e copiar no celular.
ALFABETO_CODIGO = '23456789ABCDEFGHJKMNPQRSTUVWXYZ'


def gerar_codigo(tamanho=12):
    import secrets
    return ''.join(secrets.choice(ALFABETO_CODIGO) for _ in range(tamanho))


def variantes_codigo(chave):
    """Formas aceitas de um código colado: texto exato (recibos antigos) e sem espaços/hífens."""
    bruto = (chave or '').strip()
    if ':' in bruto:  # Linha copiada do recibo, ex.: "Código de acompanhamento: ABC…"
        bruto = bruto.rsplit(':', 1)[1].strip()
    limpo = ''.join(c for c in bruto if c.isalnum()).upper()
    return [v for v in dict.fromkeys([bruto, limpo]) if v]


def hash_chave(chave):
    return sha256(chave.encode('utf-8')).hexdigest()


def registrar_evento(con, registro_id, etapa, responsavel, nota='', data=None):
    p = marcador()
    evento = {'id': str(uuid4()), 'registro_id': registro_id, 'etapa': etapa,
              'responsavel': responsavel[:100], 'nota': nota[:1000],
              'data': data or datetime.now(timezone.utc).isoformat()}
    con.execute(f'INSERT INTO aqua_eventos (id,registro_id,conteudo) VALUES ({p},{p},{p})',
                (evento['id'], registro_id, json.dumps(evento, ensure_ascii=False)))


def historico_eventos(registro):
    from relatos import conexao
    with conexao() as con:
        eventos = [json.loads(row[0]) for row in con.execute(
            f'SELECT conteudo FROM aqua_eventos WHERE registro_id={marcador()}', (registro['id'],))]
    if not any(e['etapa'] == 'recebida' for e in eventos):
        eventos.insert(0, {'etapa': 'recebida', 'data': registro['registrado_em'], 'responsavel': 'Sistema',
                    'nota': 'Histórico legado reconstruído a partir dos metadados disponíveis.'})
    if len(eventos) == 1:
        eventos.append({'etapa': {'validado': 'validada', 'rejeitado': 'rejeitada'}.get(registro.get('revisao'), 'aguardando revisão'),
                        'data': registro.get('validado_em') or registro['registrado_em'],
                        'responsavel': registro.get('revisor') or 'Sistema', 'nota': 'Estado legado registrado.'})
    return sorted(eventos, key=lambda e: (e['data'], ETAPAS.index(e['etapa'])))


def mudar_etapa(ident, etapa, responsavel, nota):
    from relatos import conexao
    if not responsavel.strip() or not nota.strip():
        raise ValueError('Informe responsável e justificativa pública da atualização.')
    with conexao() as con:
        p = marcador()
        row = con.execute(f'SELECT conteudo FROM relatos_foto WHERE id={p}', (ident,)).fetchone()
        if row is None:
            raise ValueError('Registro não encontrado.')
        r = json.loads(row[0])
        atual = r.get('etapa') or ('validada' if r.get('revisao') == 'validado' else 'aguardando revisão')
        if r.get('revisao') != 'validado' or etapa not in TRANSICOES.get(atual, set()):
            raise ValueError('Transição não permitida. Valide o relato antes de acompanhá-lo.')
        r['etapa'] = etapa
        novo = json.dumps(r, ensure_ascii=False, allow_nan=False)
        cursor = con.execute(f'UPDATE relatos_foto SET conteudo={p} WHERE id={p} AND conteudo={p}', (novo, ident, row[0]))
        if cursor.rowcount != 1:
            raise ValueError('Registro atualizado por outra pessoa. Recarregue antes de tentar novamente.')
        registrar_evento(con, ident, etapa, responsavel.strip(), nota.strip())


def feedback(registro, todos):
    from observacao import agrupar_locais, filtrar_periodo, data_registro
    mensagens = []
    if registro.get('revisao') == 'validado':
        mensagens.append('Seu registro foi validado.')
        grupo = next((g for g in agrupar_locais(todos)
                      if any(r['id'] == registro['id'] for r in g['registros'])), None)
        if grupo:
            anteriores = filtrar_periodo(grupo['registros'], 30, data_registro(registro))
            anteriores = [r for r in anteriores if (data_registro(r), r['id']) <= (data_registro(registro), registro['id'])]
            n = len(anteriores)
            ordinal = {1: 'primeira', 2: 'segunda', 3: 'terceira'}.get(n, f'{n}ª')
            mensagens.append(f'Seu registro foi a {ordinal} observação deste local nos últimos 30 dias na data do envio, '
                             'considerando os registros atualmente validados.')
    elif registro.get('revisao') == 'rejeitado':
        mensagens.append('Seu registro foi revisado e não foi validado para publicação.')
    else:
        mensagens.append('Seu registro foi recebido e está aguardando revisão.')
    return mensagens


def consultar_recibo(ident, chave):
    """Consulta pelo código de acompanhamento; o ID é opcional (recibos antigos o incluíam)."""
    from relatos import obter_foto, listar_fotos
    erro = ValueError('Código de acompanhamento inválido. Confira e tente novamente.')
    hashes = [hash_chave(v) for v in variantes_codigo(chave)]
    if not hashes:
        raise erro
    ident = (ident or '').strip()
    if ident:
        try:
            candidatos = [obter_foto(ident)[0]]
        except ValueError:
            raise erro from None
    else:
        candidatos = listar_fotos()
    for r in candidatos:
        if r.get('recibo_hash') and any(hmac.compare_digest(r['recibo_hash'], h) for h in hashes):
            return r
    raise erro
