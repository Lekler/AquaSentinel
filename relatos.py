"""Fotos e metadados salvos atomicamente no mesmo banco usado pelo ARI."""
from datetime import datetime, timezone
from contextlib import contextmanager
import json
from uuid import uuid4
from historico import conectar, marcador
from motor import numero

NIVEIS = ['Sem resíduos', 'Pouco', 'Moderado', 'Muito poluído', 'Bloqueando']


@contextmanager
def conexao():
    con = conectar()
    tipo_blob = 'BYTEA' if marcador() == '%s' else 'BLOB'
    con.execute(f'''CREATE TABLE IF NOT EXISTS relatos_foto (
        id TEXT PRIMARY KEY, image_hash TEXT NOT NULL UNIQUE,
        conteudo TEXT NOT NULL, foto {tipo_blob} NOT NULL, anotada {tipo_blob} NOT NULL)''')
    con.execute('CREATE TABLE IF NOT EXISTS aqua_entidades (id TEXT PRIMARY KEY, tipo TEXT NOT NULL, conteudo TEXT NOT NULL)')
    con.execute('CREATE TABLE IF NOT EXISTS aqua_eventos (id TEXT PRIMARY KEY, registro_id TEXT NOT NULL, conteudo TEXT NOT NULL)')
    con.execute('CREATE INDEX IF NOT EXISTS aqua_eventos_registro ON aqua_eventos (registro_id)')
    con.commit()
    try:
        with con:
            yield con
    finally:
        con.close()


def criar_registro(analise, nome, latitude, longitude, nivel, observacoes='', origem='upload'):
    from versoes import APP, METODOLOGIA, WPS, CS, AQUAVERIFY
    if not isinstance(nome, str) or not nome.strip() or len(nome.strip()) > 100:
        raise ValueError('Informe o nome do local (até 100 caracteres).')
    if latitude is None or longitude is None:
        raise ValueError('Informe a latitude e a longitude ou use sua localização.')
    numero(latitude, -90, 90)
    numero(longitude, -180, 180)
    if nivel not in NIVEIS or len(observacoes) > 500:
        raise ValueError('Confira o nível e as observações (até 500 caracteres).')
    return {**analise, 'id': str(uuid4()), 'registrado_em': datetime.now(timezone.utc).isoformat(),
            'nome': nome.strip(), 'latitude': latitude, 'longitude': longitude,
            'nivel_informado': nivel, 'observacoes': observacoes.strip(), 'origem_foto': origem,
            'origem_localizacao': 'informada_pelo_usuario', 'revisao': 'nao_revisado',
            'consentimento_publicacao': False, 'modo': 'oportunistico',
            'versao_app': APP, 'versao_metodologia': METODOLOGIA, 'etapa': 'aguardando revisão',
            'versoes_indices': {'wps': WPS, 'cs': CS, 'aquaverify': AQUAVERIFY}}


def salvar_foto(registro, foto, anotada, sessao_id=None, sessao_chave=None):
    from similaridade import assinatura, comparar
    from visao import preparar_imagem
    from aquaverify import avaliar
    _, _, dimensoes = preparar_imagem(foto)
    registro = {**registro, 'imagem_valida': True, 'phash': assinatura(foto)}
    registro.setdefault('dimensoes', list(dimensoes))
    with conexao() as con:
        p = marcador()
        # Serializa a comparação e inserção: envios concorrentes também se enxergam.
        if p == '%s':
            con.execute('SELECT pg_advisory_xact_lock(73401921)')
        else:
            con.execute('BEGIN IMMEDIATE')
        if sessao_id:
            from monitoramento import sessao_autorizada
            sessao = sessao_autorizada(sessao_id, sessao_chave, con=con)
            if sessao['status'] != 'em andamento':
                raise ValueError('A sessão já foi encerrada. Inicie outra sessão ou use registro oportunístico.')
            registro.update(modo='estruturado', sessao_id=sessao_id, trecho_id=sessao['trecho_id'],
                            waterbody_id=sessao['waterbody_id'], waterbody_nome=sessao['waterbody_nome'],
                            waterbody_confirmado=False)
        anteriores = [json.loads(row[0]) for row in con.execute('SELECT conteudo FROM relatos_foto')]
        registro['similaridade'] = comparar(registro, anteriores)
        registro['aquaverify'] = avaliar(registro)
        from dados_abertos import registrar_indices
        registrar_indices(registro, anteriores)
        cursor = con.execute(f'INSERT INTO relatos_foto (id, image_hash, conteudo, foto, anotada) VALUES ({p}, {p}, {p}, {p}, {p}) ON CONFLICT DO NOTHING',
            (registro['id'], registro['image_hash'], json.dumps(registro, ensure_ascii=False, allow_nan=False),
             foto, anotada))
        if cursor.rowcount == 1:
            from ciclo import registrar_evento
            registrar_evento(con, registro['id'], 'recebida', 'Sistema', data=registro['registrado_em'])
            registrar_evento(con, registro['id'], 'aguardando revisão', 'Sistema')
        row = con.execute(f'SELECT conteudo FROM relatos_foto WHERE image_hash={p}',
                          (registro['image_hash'],)).fetchone()
        if row is None:
            raise ValueError('Identificador já utilizado por outra fotografia.')
        return json.loads(row[0]), cursor.rowcount == 1


def listar_fotos():
    with conexao() as con:
        registros = [json.loads(row[0]) for row in con.execute('SELECT conteudo FROM relatos_foto')]
    return sorted(registros, key=lambda r: r.get('registrado_em', ''), reverse=True)


def obter_foto(identificador):
    with conexao() as con:
        row = con.execute(f'SELECT conteudo, foto, anotada FROM relatos_foto WHERE id={marcador()}', (identificador,)).fetchone()
        if row is None:
            raise ValueError('Registro não encontrado.')
        return json.loads(row[0]), bytes(row[1]), bytes(row[2])


def revisar_foto(identificador, decisao, revisor, waterbody_id=None,
                 similaridade_decisao=None, justificativa=''):
    if decisao not in ('validado', 'rejeitado') or not revisor or not revisor.strip():
        raise ValueError('Informe uma decisão e o nome do revisor.')
    with conexao() as con:
        p = marcador()
        row = con.execute(f'SELECT conteudo FROM relatos_foto WHERE id={p}', (identificador,)).fetchone()
        if row is None:
            raise ValueError('Registro não encontrado.')
        registro = json.loads(row[0])
        if registro.get('revisao', 'nao_revisado') != 'nao_revisado':
            raise ValueError('Este relato já foi revisado.')
        registro.update(revisao=decisao, revisor=revisor.strip()[:100],
                        validado_em=datetime.now(timezone.utc).isoformat(),
                        etapa='validada' if decisao == 'validado' else 'rejeitada')
        if waterbody_id:
            from corpos_hidricos import obter_corpo
            corpo = obter_corpo(waterbody_id)
            registro.update(waterbody_id=corpo['id'], waterbody_nome=corpo['nome'], waterbody_confirmado=True)
        if similaridade_decisao:
            if similaridade_decisao not in ('independente', 'reutilizada') or not justificativa.strip():
                raise ValueError('Justifique a decisão de similaridade.')
            registro.update(similaridade_decisao=similaridade_decisao,
                            similaridade_justificativa=justificativa.strip()[:500])
        from aquaverify import avaliar
        registro['aquaverify'] = avaliar(registro)
        from dados_abertos import registrar_indices
        anteriores = [json.loads(row[0]) for row in con.execute('SELECT conteudo FROM relatos_foto')]
        registrar_indices(registro, [r for r in anteriores if r['id'] != registro['id']] + [registro])
        con.execute(f'UPDATE relatos_foto SET conteudo={p} WHERE id={p}',
                    (json.dumps(registro, ensure_ascii=False, allow_nan=False), identificador))
        from ciclo import registrar_evento
        registrar_evento(con, identificador, registro['etapa'], revisor.strip())
    return registro


def vincular_corpo(identificador, waterbody_id, revisor):
    from corpos_hidricos import obter_corpo
    if not revisor.strip():
        raise ValueError('Informe o responsável pela vinculação.')
    corpo = obter_corpo(waterbody_id)
    with conexao() as con:
        p = marcador()
        row = con.execute(f'SELECT conteudo FROM relatos_foto WHERE id={p}', (identificador,)).fetchone()
        if row is None:
            raise ValueError('Registro não encontrado.')
        r = json.loads(row[0])
        r.setdefault('historico_vinculos', []).append({'anterior': r.get('waterbody_id'),
            'novo': waterbody_id, 'responsavel': revisor.strip()[:100],
            'data': datetime.now(timezone.utc).isoformat()})
        r.update(waterbody_id=corpo['id'], waterbody_nome=corpo['nome'], waterbody_confirmado=True)
        con.execute(f'UPDATE relatos_foto SET conteudo={p} WHERE id={p}',
                    (json.dumps(r, ensure_ascii=False, allow_nan=False), identificador))


def indexar_fotos_antigas(limite=100):
    """Índice incremental das fotos já armazenadas; não executa o detector novamente."""
    from similaridade import assinatura, comparar, VERSAO
    from visao import preparar_imagem
    from aquaverify import avaliar
    with conexao() as con:
        p = marcador()
        if p == '%s':
            con.execute('SELECT pg_advisory_xact_lock(73401921)')
        else:
            con.execute('BEGIN IMMEDIATE')
        registros = [json.loads(row[0]) for row in con.execute('SELECT conteudo FROM relatos_foto')]
        atualizados = 0
        for r in sorted(registros, key=lambda r: (r.get('registrado_em', ''), r['id'])):
            if (r.get('phash') or {}).get('versao') != VERSAO and atualizados < limite:
                foto = con.execute(f'SELECT foto FROM relatos_foto WHERE id={p}', (r['id'],)).fetchone()[0]
                _, _, dims = preparar_imagem(bytes(foto))
                r.update(phash=assinatura(bytes(foto)), imagem_valida=True)
                r.setdefault('dimensoes', list(dims))
                atualizados += 1
        # Somente fotos anteriores: evita marcar ambos os lados da mesma correspondência.
        anteriores = []
        for r in sorted(registros, key=lambda r: (r.get('registrado_em', ''), r['id'])):
            if r.get('phash'):
                sim = comparar(r, anteriores)
                antigos = {m['id'] for m in (r.get('similaridade') or {}).get('candidatas', [])}
                if {m['id'] for m in sim['candidatas']} - antigos:
                    r.pop('similaridade_decisao', None)
                r['similaridade'] = sim
                r['aquaverify'] = avaliar(r)
                con.execute(f'UPDATE relatos_foto SET conteudo={p} WHERE id={p}',
                            (json.dumps(r, ensure_ascii=False, allow_nan=False), r['id']))
            anteriores.append(r)
    return atualizados


def resolver_similaridade(identificador, decisao, revisor, justificativa):
    if decisao not in ('independente', 'reutilizada') or not revisor.strip() or not justificativa.strip():
        raise ValueError('Informe decisão, responsável e justificativa da similaridade.')
    from aquaverify import avaliar
    with conexao() as con:
        p = marcador()
        row = con.execute(f'SELECT conteudo FROM relatos_foto WHERE id={p}', (identificador,)).fetchone()
        if row is None:
            raise ValueError('Registro não encontrado.')
        r = json.loads(row[0])
        if not (r.get('similaridade') or {}).get('quantidade'):
            raise ValueError('Este registro não tem correspondência sinalizada.')
        r.setdefault('historico_similaridade', []).append({'decisao': decisao,
            'responsavel': revisor.strip()[:100], 'justificativa': justificativa.strip()[:500],
            'data': datetime.now(timezone.utc).isoformat()})
        r.update(similaridade_decisao=decisao, similaridade_justificativa=justificativa.strip()[:500])
        r['aquaverify'] = avaliar(r)
        con.execute(f'UPDATE relatos_foto SET conteudo={p} WHERE id={p}',
                    (json.dumps(r, ensure_ascii=False, allow_nan=False), identificador))


def excluir_fotos(identificadores):
    ids = tuple(dict.fromkeys(identificadores))
    if not ids:
        return 0
    with conexao() as con:
        placeholders = ','.join(marcador() for _ in ids)
        cursor = con.execute(f'DELETE FROM relatos_foto WHERE id IN ({placeholders})', ids)
        return cursor.rowcount


def excluir_todas_fotos():
    with conexao() as con:
        cursor = con.execute('DELETE FROM relatos_foto')
        return cursor.rowcount
