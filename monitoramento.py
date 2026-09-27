"""Trechos planejados, sessões com recibo e métricas separadas dos envios avulsos."""
from datetime import datetime, timezone
import hmac
import json
import secrets
from uuid import uuid4

from ciclo import hash_chave
from historico import marcador, distancia_m
from motor import numero
from observacao import publicos, data_registro, FUSO
from relatos import conexao


def listar_entidades(tipo):
    with conexao() as con:
        return [json.loads(row[0]) for row in con.execute(
            f'SELECT conteudo FROM aqua_entidades WHERE tipo={marcador()}', (tipo,))]


def inserir(con, tipo, dado):
    p = marcador()
    con.execute(f'INSERT INTO aqua_entidades (id,tipo,conteudo) VALUES ({p},{p},{p})',
                (dado['id'], tipo, json.dumps(dado, ensure_ascii=False, allow_nan=False)))


def obter(con, ident, tipo):
    p = marcador()
    row = con.execute(f'SELECT conteudo FROM aqua_entidades WHERE id={p} AND tipo={p}', (ident, tipo)).fetchone()
    if row is None:
        raise ValueError('Registro não encontrado.')
    return json.loads(row[0])


def atualizar(con, tipo, dado):
    p = marcador()
    con.execute(f'UPDATE aqua_entidades SET conteudo={p} WHERE id={p} AND tipo={p}',
                (json.dumps(dado, ensure_ascii=False, allow_nan=False), dado['id'], tipo))


def bloquear(con):
    con.execute('SELECT pg_advisory_xact_lock(73401921)' if marcador() == '%s' else 'BEGIN IMMEDIATE')


def cadastrar_trecho(nome, corpo_id, latitude, longitude, extensao_m, responsavel):
    from corpos_hidricos import obter_corpo
    if not nome.strip() or len(nome) > 100 or not responsavel.strip():
        raise ValueError('Informe nome do trecho e responsável.')
    numero(latitude, -90, 90); numero(longitude, -180, 180); numero(extensao_m, .1, 100000)
    corpo = obter_corpo(corpo_id)
    trecho = {'id': 'TR-' + uuid4().hex[:12], 'nome': nome.strip(),
              'waterbody_id': corpo_id, 'waterbody_nome': corpo['nome'],
              'latitude': latitude, 'longitude': longitude, 'extensao_m': extensao_m,
              'criado_em': datetime.now(timezone.utc).isoformat(), 'responsavel': responsavel.strip()[:100]}
    with conexao() as con:
        inserir(con, 'trecho', trecho)
    return trecho


def iniciar_sessao(trecho_id, consentimento, agora=None):
    from versoes import MONITORAMENTO
    if consentimento is not True:
        raise ValueError('Autorize a publicação dos dados da sessão após revisão.')
    chave = secrets.token_urlsafe(24)
    with conexao() as con:
        trecho = obter(con, trecho_id, 'trecho')
        sessao = {'id': str(uuid4()), 'trecho_id': trecho_id, 'trecho_nome': trecho['nome'],
                  'waterbody_id': trecho['waterbody_id'], 'waterbody_nome': trecho['waterbody_nome'],
                  'inicio': (agora or datetime.now(timezone.utc)).isoformat(), 'fim': None,
                  'chave_hash': hash_chave(chave), 'status': 'em andamento', 'revisao': 'nao_revisado',
                  'consentimento_publicacao': True, 'versao': MONITORAMENTO}
        inserir(con, 'sessao', sessao)
    return sessao, chave


def sessao_autorizada(ident, chave, con=None):
    if con is None:
        with conexao() as propria:
            return sessao_autorizada(ident, chave, propria)
    try:
        sessao = obter(con, ident, 'sessao')
    except ValueError:
        raise ValueError('ID ou código da sessão inválido.') from None
    if not chave or not hmac.compare_digest(sessao['chave_hash'], hash_chave(chave)):
        raise ValueError('ID ou código da sessão inválido.')
    return sessao


def encerrar_sessao(ident, chave, metros, cobertura_confirmada, sem_residuos, agora=None):
    numero(metros, .1, 100000)
    agora = agora or datetime.now(timezone.utc)
    with conexao() as con:
        bloquear(con)
        sessao = sessao_autorizada(ident, chave, con)
        if sessao['status'] != 'em andamento':
            raise ValueError('Sessão já encerrada.')
        minutos = (agora-datetime.fromisoformat(sessao['inicio'])).total_seconds()/60
        if minutos <= 0:
            raise ValueError('A duração precisa ser positiva.')
        fotos = [json.loads(row[0]) for row in con.execute('SELECT conteudo FROM relatos_foto')]
        fotos = [r for r in fotos if r.get('sessao_id') == ident]
        if not fotos and not sem_residuos:
            raise ValueError('Adicione fotos ou declare explicitamente que observou o trecho sem resíduos.')
        if sem_residuos and any(r.get('total', 0) > 0 or r.get('nivel_informado') != 'Sem resíduos' for r in fotos):
            raise ValueError('A declaração sem resíduos conflita com as fotos. Confira a sessão.')
        sessao.update(fim=agora.isoformat(), duracao_min=minutos, extensao_observada_m=metros,
                      cobertura_confirmada=bool(cobertura_confirmada), sem_residuos=bool(sem_residuos),
                      status='encerrada', quantidade_fotos=len(fotos))
        atualizar(con, 'sessao', sessao)
    return sessao


def revisar_sessao(ident, decisao, responsavel):
    if decisao not in ('validado', 'rejeitado') or not responsavel.strip():
        raise ValueError('Informe responsável e decisão.')
    with conexao() as con:
        bloquear(con)
        sessao = obter(con, ident, 'sessao')
        if sessao['status'] != 'encerrada' or sessao['revisao'] != 'nao_revisado':
            raise ValueError('A sessão deve estar encerrada e ainda não revisada.')
        sessao.update(revisao=decisao, revisor=responsavel.strip()[:100],
                      revisado_em=datetime.now(timezone.utc).isoformat())
        atualizar(con, 'sessao', sessao)


def metricas_sessao(sessao, registros):
    fotos = [r for r in registros if r.get('sessao_id') == sessao['id']]
    aceitas = [r for r in publicos(fotos) if r.get('waterbody_confirmado') is True
               and r.get('waterbody_id') == sessao['waterbody_id']
               and r.get('similaridade_decisao') != 'reutilizada'
               and (not (r.get('similaridade') or {}).get('quantidade') or r.get('similaridade_decisao') == 'independente')]
    total = sum(int(r.get('total') or 0) for r in aceitas)
    completa = (sessao.get('status') == 'encerrada' and sessao.get('revisao') == 'validado'
                and sessao.get('cobertura_confirmada') is True and len(aceitas) == len(fotos)
                and (bool(fotos) or sessao.get('sem_residuos') is True))
    metros, minutos = sessao.get('extensao_observada_m', 0), sessao.get('duracao_min', 0)
    completa = bool(completa and metros > 0 and minutos > 0)
    return {'fotos': len(fotos), 'fotos_validadas': len(aceitas), 'itens': total, 'completa': completa,
            'itens_m': total/metros if completa else None,
            'itens_100m': 100*total/metros if completa else None,
            'itens_min': total/minutos if completa else None}


def pertence_trecho(r, trecho):
    if r.get('waterbody_id') != trecho['waterbody_id'] or r.get('waterbody_confirmado') is not True:
        return False
    if r.get('trecho_id'):
        return r['trecho_id'] == trecho['id']
    try:
        return distancia_m(float(r['latitude']), float(r['longitude']), trecho['latitude'], trecho['longitude']) <= 200
    except (KeyError, TypeError, ValueError):
        return False


def lacunas(trechos, registros, sessoes, agora=None):
    agora = agora or datetime.now(timezone.utc)
    hoje = agora.astimezone(FUSO).date()
    saida = []
    for t in trechos:
        obs = [(data_registro(r), r.get('nivel_informado') == 'Sem resíduos') for r in publicos(registros)
               if pertence_trecho(r, t) and data_registro(r) and data_registro(r) <= agora]
        for s in sessoes:
            if (s.get('trecho_id') == t['id'] and s.get('status') == 'encerrada'
                    and s.get('revisao') == 'validado' and s.get('consentimento_publicacao')):
                data = datetime.fromisoformat(s['fim'])
                if data <= agora:
                    obs.append((data, s.get('sem_residuos') is True))
        obs.sort(key=lambda o: o[0])
        atraso = (hoje-obs[-1][0].astimezone(FUSO).date()).days if obs else None
        dias = len({d.astimezone(FUSO).date() for d, _ in obs if 0 <= (hoje-d.astimezone(FUSO).date()).days <= 29})
        classe = 'Não temos dado' if atraso is None else 'Sem observação recente' if atraso >= 30 else 'Muito observado' if dias >= 4 else 'Pouco observado'
        estado = 'Não temos dado' if not obs else 'Observado: nenhum resíduo visto' if obs[-1][1] else 'Há observação; consulte o nível registrado'
        saida.append({**t, 'classe': classe, 'dias_30': dias, 'ultima_dias': atraso, 'estado': estado,
                      'chamada': 'Este trecho precisa de nova observação.' if atraso is None or atraso >= 30 else ''})
    return saida
