from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_site_abre_sem_banco_externo(tmp_path, monkeypatch):
    monkeypatch.delenv("AQUASENTINEL_DATABASE_URL", raising=False)
    monkeypatch.delenv("AQUASENTINEL_ALLOW_LOCAL_DB", raising=False)
    monkeypatch.setenv("AQUASENTINEL_DB", str(tmp_path / "relatos.sqlite3"))
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=15).run()
    assert not app.exception
    assert len(app.tabs) == 2
    assert app.warning
