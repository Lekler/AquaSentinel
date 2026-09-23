from io import BytesIO
import base64

from PIL import Image
import pytest

from relatos import RelatoInvalido, criar_relato, listar, revisar, salvar


@pytest.fixture(autouse=True)
def banco_local(tmp_path, monkeypatch):
    monkeypatch.delenv("AQUASENTINEL_DATABASE_URL", raising=False)
    monkeypatch.setenv("AQUASENTINEL_DB", str(tmp_path / "relatos.sqlite3"))


def foto():
    buffer = BytesIO()
    Image.new("RGB", (32, 32), "#21aabb").save(buffer, "PNG")
    return buffer.getvalue()


def test_fluxo_envio_revisao_e_mapa():
    relato = criar_relato("Canal do Fundão", -22.8667, -43.2317, "Alto", "Pessoa", "Garrafas", foto())
    assert relato["status_validacao"] == "pendente"
    assert relato["pontuacao_provisoria"] == 100
    assert base64.b64decode(relato["foto_jpeg_base64"])[:3] == b"\xff\xd8\xff"
    assert salvar(relato)
    assert not salvar(relato)
    assert len(listar()) == 1
    revisar(relato["id"], "validado", "Revisora")
    assert listar()[0]["status_validacao"] == "validado"
    with pytest.raises(RelatoInvalido):
        revisar(relato["id"], "rejeitado", "Outra pessoa")


def test_dados_invalidos_nao_criam_relato():
    with pytest.raises(RelatoInvalido):
        criar_relato("", -22, -43, "Alto", "Pessoa", "", foto())
    with pytest.raises(RelatoInvalido):
        criar_relato("Canal", float("nan"), -43, "Alto", "Pessoa", "", foto())
    with pytest.raises(RelatoInvalido):
        criar_relato("Canal", -22, -43, "Alto", "Pessoa", "", b"invalid image")
    assert listar() == []
