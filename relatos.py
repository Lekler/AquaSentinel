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
    con.commit()
    try:
        with con:
            yield con
    finally:
        con.close()


def criar_registro(analise, nome, latitude, longitude, nivel, observacoes='', origem='upload'):
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
            'consentimento_publicacao': False}


def salvar_foto(registro, foto, anotada):
    with conexao() as con:
        p = marcador()
        cursor = con.execute(f'INSERT INTO relatos_foto (id, image_hash, conteudo, foto, anotada) VALUES ({p}, {p}, {p}, {p}, {p}) ON CONFLICT DO NOTHING',
            (registro['id'], registro['image_hash'], json.dumps(registro, ensure_ascii=False, allow_nan=False),
             foto, anotada))
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


def revisar_foto(identificador, decisao, revisor):
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
                        validado_em=datetime.now(timezone.utc).isoformat())
        con.execute(f'UPDATE relatos_foto SET conteudo={p} WHERE id={p}',
                    (json.dumps(registro, ensure_ascii=False, allow_nan=False), identificador))
    return registro


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
