"""Catálogo interno persistente; códigos não são identificadores oficiais."""
from contextlib import contextmanager
from datetime import datetime, timezone
import unicodedata
from historico import conectar, marcador


def normalizar(nome):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFKD', nome.casefold())
                           if not unicodedata.combining(c)).split())


@contextmanager
def conexao_catalogo():
    con = conectar()
    sequencia = 'SERIAL PRIMARY KEY' if marcador() == '%s' else 'INTEGER PRIMARY KEY AUTOINCREMENT'
    con.execute(f'''CREATE TABLE IF NOT EXISTS corpos_hidricos (
        numero {sequencia}, nome TEXT NOT NULL, nome_chave TEXT NOT NULL UNIQUE,
        criado_em TEXT NOT NULL, criado_por TEXT NOT NULL)''')
    con.commit()
    try:
        with con:
            yield con
    finally:
        con.close()


def listar_corpos():
    with conexao_catalogo() as con:
        return [{'id': f'WB-BG-{n:03d}', 'nome': nome}
                for n, nome in con.execute('SELECT numero, nome FROM corpos_hidricos ORDER BY numero')]


def cadastrar_corpo(nome, revisor):
    if not nome.strip() or len(nome.strip()) > 100 or not revisor.strip():
        raise ValueError('Informe nome do corpo hídrico (até 100 caracteres) e responsável.')
    with conexao_catalogo() as con:
        p = marcador()
        if p == '%s':
            con.execute('SELECT pg_advisory_xact_lock(73401922)')
        else:
            con.execute('BEGIN IMMEDIATE')
        existente = con.execute(f'SELECT numero,nome FROM corpos_hidricos WHERE nome_chave={p}',
                                 (normalizar(nome),)).fetchone()
        if existente:
            return {'id': f'WB-BG-{existente[0]:03d}', 'nome': existente[1]}
        con.execute(f'''INSERT INTO corpos_hidricos (nome,nome_chave,criado_em,criado_por)
            VALUES ({p},{p},{p},{p}) ON CONFLICT (nome_chave) DO NOTHING''',
            (nome.strip(), normalizar(nome), datetime.now(timezone.utc).isoformat(), revisor.strip()[:100]))
        n, nome = con.execute(f'SELECT numero,nome FROM corpos_hidricos WHERE nome_chave={p}',
                              (normalizar(nome),)).fetchone()
    return {'id': f'WB-BG-{n:03d}', 'nome': nome}


def obter_corpo(ident):
    corpo = next((c for c in listar_corpos() if c['id'] == ident), None)
    if corpo is None:
        raise ValueError('Selecione um corpo hídrico cadastrado.')
    return corpo
