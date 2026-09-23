"""Relatos do MVP de resíduos, com SQLite local ou PostgreSQL compartilhado."""

from __future__ import annotations

import base64
from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
import json
from math import isfinite
import os
from pathlib import Path
import sqlite3
from uuid import uuid4

from PIL import Image, ImageOps, UnidentifiedImageError

CORES = {"Baixo": "#1BAF78", "Moderado": "#F4B740", "Alto": "#F26A4B"}
PONTOS_PROVISORIOS = {"Baixo": 25, "Moderado": 60, "Alto": 100}
LIMITE_UPLOAD = 10 * 1024 * 1024


class RelatoInvalido(ValueError):
    pass


def banco_compartilhado() -> bool:
    return bool(os.environ.get("AQUASENTINEL_DATABASE_URL", "").strip())


def _conectar():
    url = os.environ.get("AQUASENTINEL_DATABASE_URL", "").strip()
    if url:
        import psycopg

        opcoes = {"connect_timeout": 8, "sslmode": "require"}
        senha = os.environ.get("AQUASENTINEL_DATABASE_PASSWORD", "")
        if senha:
            opcoes["password"] = senha
        con = psycopg.connect(url, **opcoes)
        con.execute("CREATE TABLE IF NOT EXISTS relatos (id TEXT PRIMARY KEY, conteudo TEXT NOT NULL)")
    else:
        caminho = Path(os.environ.get("AQUASENTINEL_DB", "dados/relatos.sqlite3"))
        caminho.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(caminho, timeout=10)
        con.execute("CREATE TABLE IF NOT EXISTS relatos (id TEXT PRIMARY KEY, conteudo TEXT NOT NULL)")
    con.commit()
    return con


def preparar_foto(conteudo: bytes) -> tuple[str, str]:
    """Reduz tamanho e remove EXIF antes de guardar ou mostrar a imagem."""
    if not conteudo or len(conteudo) > LIMITE_UPLOAD:
        raise RelatoInvalido("Envie uma foto de até 10 MB.")
    try:
        with Image.open(BytesIO(conteudo)) as imagem:
            imagem = ImageOps.exif_transpose(imagem)
            imagem.thumbnail((1200, 1200))
            saida = BytesIO()
            imagem.convert("RGB").save(saida, format="JPEG", quality=75, optimize=True)
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise RelatoInvalido("Não foi possível ler a foto. Use JPG, PNG ou HEIC convertido para JPG.") from exc
    foto = saida.getvalue()
    return base64.b64encode(foto).decode("ascii"), sha256(foto).hexdigest()


def criar_relato(nome, latitude, longitude, classe, origem, observacao, foto: bytes):
    nome = nome.strip() if isinstance(nome, str) else ""
    if not nome or len(nome) > 100:
        raise RelatoInvalido("Informe um nome do canal ou local com até 100 caracteres.")
    try:
        latitude, longitude = float(latitude), float(longitude)
    except (TypeError, ValueError) as exc:
        raise RelatoInvalido("Latitude e longitude devem ser numéricas.") from exc
    if not (isfinite(latitude) and isfinite(longitude) and -90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise RelatoInvalido("Confira as coordenadas do local.")
    if classe not in PONTOS_PROVISORIOS:
        raise RelatoInvalido("Classe de acúmulo inválida.")
    if origem not in ("Pessoa", "Equipe/órgão (declarado)"):
        raise RelatoInvalido("Origem do relato inválida.")
    if len(observacao) > 500:
        raise RelatoInvalido("A descrição deve ter até 500 caracteres.")
    imagem, hash_foto = preparar_foto(foto)
    return {
        "id": str(uuid4()),
        "registrado_em": datetime.now(timezone.utc).isoformat(),
        "nome": nome,
        "latitude": latitude,
        "longitude": longitude,
        "classe_residuos": classe,
        "pontuacao_provisoria": PONTOS_PROVISORIOS[classe],
        "metodologia": "triagem-visual-provisoria-1",
        "origem_declarada": origem,
        "observacao": observacao.strip(),
        "foto_jpeg_base64": imagem,
        "foto_sha256": hash_foto,
        "status_validacao": "pendente",
        "revisor": None,
        "validado_em": None,
    }


def listar():
    with _conectar() as con:
        registros = [json.loads(row[0]) for row in con.execute("SELECT conteudo FROM relatos")]
    return sorted(registros, key=lambda item: item["registrado_em"], reverse=True)


def salvar(relato):
    with _conectar() as con:
        marcador = "%s" if banco_compartilhado() else "?"
        cursor = con.execute(
            f"INSERT INTO relatos (id, conteudo) VALUES ({marcador}, {marcador}) ON CONFLICT (id) DO NOTHING",
            (relato["id"], json.dumps(relato, ensure_ascii=False, allow_nan=False)),
        )
        return cursor.rowcount == 1


def revisar(identificador, decisao, revisor):
    if decisao not in ("validado", "rejeitado"):
        raise RelatoInvalido("Escolha validar ou rejeitar o relato.")
    if not revisor or not revisor.strip():
        raise RelatoInvalido("Informe o nome de quem revisou.")
    with _conectar() as con:
        marcador = "%s" if banco_compartilhado() else "?"
        row = con.execute(f"SELECT conteudo FROM relatos WHERE id={marcador}", (identificador,)).fetchone()
        if row is None:
            raise RelatoInvalido("Relato não encontrado.")
        registro = json.loads(row[0])
        if registro["status_validacao"] != "pendente":
            raise RelatoInvalido("Este relato já foi revisado.")
        registro["status_validacao"] = decisao
        registro["revisor"] = revisor.strip()[:100]
        registro["validado_em"] = datetime.now(timezone.utc).isoformat()
        con.execute(
            f"UPDATE relatos SET conteudo={marcador} WHERE id={marcador}",
            (json.dumps(registro, ensure_ascii=False, allow_nan=False), identificador),
        )
    return registro
