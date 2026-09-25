"""Histórico local persistente. Um registro por ocorrência, sem duplicar reenvios."""
import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from math import asin, cos, radians, sin, sqrt
from pathlib import Path
from motor import DadosInvalidos, numero


def distancia_m(lat1, lon1, lat2, lon2):
    a, b = radians(lat1), radians(lat2)
    h = sin((b-a)/2)**2 + cos(a)*cos(b)*sin(radians(lon2-lon1)/2)**2
    return 6371000 * 2 * asin(sqrt(min(1, max(0, h))))


def conectar():
    url = os.environ.get('AQUASENTINEL_DATABASE_URL', '').strip()
    if url:
        import psycopg
        opcoes = {'connect_timeout': 8, 'sslmode': 'require'}
        senha = os.environ.get('AQUASENTINEL_DATABASE_PASSWORD', '')
        if senha:
            opcoes['password'] = senha
        con = psycopg.connect(url, **opcoes)
        con.execute('CREATE TABLE IF NOT EXISTS ocorrencias (id TEXT PRIMARY KEY, conteudo TEXT NOT NULL)')
        con.commit()
        return con
    caminho = Path(os.environ.get('AQUASENTINEL_DB', str(Path(__file__).resolve().parent / 'dados' / 'ocorrencias.sqlite3')))
    caminho.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(caminho, timeout=10)
    con.execute('CREATE TABLE IF NOT EXISTS ocorrencias (id TEXT PRIMARY KEY, conteudo TEXT NOT NULL)')
    con.commit()
    return con


def marcador():
    return '%s' if os.environ.get('AQUASENTINEL_DATABASE_URL', '').strip() else '?'


def listar():
    with conectar() as con:
        registros = [json.loads(row[0]) for row in con.execute('SELECT conteudo FROM ocorrencias')]
    return sorted(registros, key=lambda r: r.get('registrado_em', ''), reverse=True)


def salvar(registro):
    # INSERT OR IGNORE: reexibir, baixar ou clicar novamente não duplica um relato.
    with conectar() as con:
        p = marcador()
        cursor = con.execute(f'INSERT INTO ocorrencias (id, conteudo) VALUES ({p}, {p}) ON CONFLICT (id) DO NOTHING',
                             (registro['id'], json.dumps(registro, ensure_ascii=False, allow_nan=False)))
        return cursor.rowcount == 1


def excluir_registros(identificadores):
    ids = tuple(dict.fromkeys(identificadores))
    if not ids:
        return 0
    with conectar() as con:
        placeholders = ','.join(marcador() for _ in ids)
        cursor = con.execute(f'DELETE FROM ocorrencias WHERE id IN ({placeholders})', ids)
        return cursor.rowcount


def excluir_todos_registros():
    with conectar() as con:
        cursor = con.execute('DELETE FROM ocorrencias')
        return cursor.rowcount


def confirmar(identificador, revisor):
    if not revisor.strip():
        raise DadosInvalidos('Informe o responsável pela confirmação.')
    with conectar() as con:
        row = con.execute(f'SELECT conteudo FROM ocorrencias WHERE id={marcador()}', (identificador,)).fetchone()
        if row is None:
            raise DadosInvalidos('Ocorrência não encontrada.')
        registro = json.loads(row[0])
        if registro['status_validacao'] != 'pendente':
            raise DadosInvalidos('Somente ocorrências pendentes podem ser confirmadas.')
        registro.update(status_validacao='confirmado_humano', revisor=revisor.strip(),
                        validado_em=datetime.now(timezone.utc).isoformat())
        # O índice da consulta anterior não é recalculado com uma previsão antiga.
        p = marcador()
        con.execute(f'UPDATE ocorrencias SET conteudo={p} WHERE id={p}',
                    (json.dumps(registro, ensure_ascii=False, allow_nan=False), identificador))


def contar_proximos(registros, latitude, longitude, agora=None, raio_m=500, dias=30, excluir_id=None):
    numero(latitude, -90, 90); numero(longitude, -180, 180)
    numero(raio_m, 1, 10000); numero(dias, 1, 365)
    agora = agora or datetime.now(timezone.utc)
    if agora.tzinfo is None:
        raise DadosInvalidos('Data de referência sem fuso.')
    vistos = set()
    for r in registros:
        if r['id'] == excluir_id or r['status_validacao'] not in ('aceito', 'confirmado_humano'):
            continue
        data = datetime.fromisoformat(r['registrado_em'])
        validacao = datetime.fromisoformat(r.get('validado_em') or r['registrado_em'])
        if data.tzinfo is None or validacao.tzinfo is None:
            raise DadosInvalidos('Registro histórico sem fuso.')
        if agora - timedelta(days=dias) <= data < agora and validacao <= agora:
            if distancia_m(latitude, longitude, r['latitude'], r['longitude']) <= raio_m:
                vistos.add(r['id'])
    return len(vistos)
