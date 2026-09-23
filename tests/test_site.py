from pathlib import Path
from io import BytesIO

from streamlit.testing.v1 import AppTest
from PIL import Image

from relatos import criar_relato, revisar, salvar


def test_site_abre_sem_banco_externo(tmp_path, monkeypatch):
    monkeypatch.delenv("AQUASENTINEL_DATABASE_URL", raising=False)
    monkeypatch.delenv("AQUASENTINEL_ALLOW_LOCAL_DB", raising=False)
    monkeypatch.setenv("AQUASENTINEL_DB", str(tmp_path / "relatos.sqlite3"))
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=15).run()
    assert not app.exception
    assert len(app.tabs) == 2
    assert app.warning


def test_site_mostra_relato_revisado_no_mapa(tmp_path, monkeypatch):
    monkeypatch.delenv("AQUASENTINEL_DATABASE_URL", raising=False)
    monkeypatch.setenv("AQUASENTINEL_DB", str(tmp_path / "relatos.sqlite3"))
    monkeypatch.setenv("AQUASENTINEL_ALLOW_LOCAL_DB", "1")
    foto = BytesIO()
    Image.new("RGB", (32, 32), "blue").save(foto, "JPEG")
    relato = criar_relato("Canal do Fundão", -22.86, -43.23, "Alto", "Pessoa", "Garrafas", foto.getvalue())
    salvar(relato)
    revisar(relato["id"], "validado", "Revisora")
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=15).run()
    assert not app.exception
    assert any("Canal do Fundão" in expander.label for expander in app.expander)
    assert any(metric.value == "1" for metric in app.metric)
