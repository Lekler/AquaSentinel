"""Catálogo interno persistente; códigos não são identificadores oficiais."""
from contextlib import contextmanager
from datetime import datetime, timezone
import unicodedata
from historico import conectar, marcador

TIPOS = ('Não informado', 'Rio', 'Canal', 'Lagoa', 'Baía', 'Lago', 'Córrego', 'Outro')


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
    con.execute('''CREATE TABLE IF NOT EXISTS corpos_detalhes (
        numero INTEGER PRIMARY KEY, tipo TEXT NOT NULL, observacao TEXT NOT NULL,
        atualizado_em TEXT NOT NULL, atualizado_por TEXT NOT NULL)''')
    con.commit()
    try:
        with con:
            yield con
    finally:
        con.close()


def listar_corpos():
    with conexao_catalogo() as con:
        return [{'id': f'WB-BG-{n:03d}', 'nome': nome, 'tipo': tipo or 'Não informado',
                 'observacao': obs or ''}
                for n, nome, tipo, obs in con.execute('''SELECT c.numero,c.nome,d.tipo,d.observacao
                    FROM corpos_hidricos c LEFT JOIN corpos_detalhes d ON d.numero=c.numero ORDER BY c.numero''')]


def cadastrar_corpo(nome, revisor, tipo='Não informado', observacao=''):
    if tipo not in TIPOS or len(observacao) > 500:
        raise ValueError('Confira o tipo e a observação de até 500 caracteres.')
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
        con.execute(f'''INSERT INTO corpos_detalhes (numero,tipo,observacao,atualizado_em,atualizado_por)
            VALUES ({p},{p},{p},{p},{p}) ON CONFLICT (numero) DO NOTHING''',
            (n, tipo, observacao.strip(), datetime.now(timezone.utc).isoformat(), revisor.strip()[:100]))
    return {'id': f'WB-BG-{n:03d}', 'nome': nome}


def atualizar_corpo(ident, nome, revisor, tipo='Não informado', observacao=''):
    import re
    if not re.fullmatch(r'WB-BG-\d{3,}', ident or ''):
        raise ValueError('Selecione um corpo hídrico cadastrado.')
    if not nome.strip() or len(nome.strip()) > 100 or not revisor.strip():
        raise ValueError('Informe nome do corpo hídrico (até 100 caracteres) e responsável.')
    if tipo not in TIPOS or len(observacao) > 500:
        raise ValueError('Confira o tipo e a observação de até 500 caracteres.')
    numero = int(ident.rsplit('-', 1)[1])
    with conexao_catalogo() as con:
        p = marcador()
        if p == '%s':
            con.execute('SELECT pg_advisory_xact_lock(73401922)')
        else:
            con.execute('BEGIN IMMEDIATE')
        if not con.execute(f'SELECT numero FROM corpos_hidricos WHERE numero={p}', (numero,)).fetchone():
            raise ValueError('Selecione um corpo hídrico cadastrado.')
        if con.execute(f'SELECT numero FROM corpos_hidricos WHERE nome_chave={p} AND numero<>{p}',
                       (normalizar(nome), numero)).fetchone():
            raise ValueError('Já existe um corpo hídrico com esse nome. Selecione o cadastro existente.')
        con.execute(f'UPDATE corpos_hidricos SET nome={p},nome_chave={p} WHERE numero={p}',
                    (nome.strip(), normalizar(nome), numero))
        con.execute(f'''INSERT INTO corpos_detalhes (numero,tipo,observacao,atualizado_em,atualizado_por)
            VALUES ({p},{p},{p},{p},{p}) ON CONFLICT (numero) DO UPDATE SET
            tipo=excluded.tipo,observacao=excluded.observacao,atualizado_em=excluded.atualizado_em,
            atualizado_por=excluded.atualizado_por''',
            (numero, tipo, observacao.strip(), datetime.now(timezone.utc).isoformat(), revisor.strip()[:100]))
    return obter_corpo(ident)


def obter_corpo(ident):
    corpo = next((c for c in listar_corpos() if c['id'] == ident), None)
    if corpo is None:
        raise ValueError('Selecione um corpo hídrico cadastrado.')
    return corpo
