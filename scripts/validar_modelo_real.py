"""Teste ponta a ponta com best.pt e foto local, em banco temporário."""
import argparse
from io import BytesIO
import json
import os
from pathlib import Path
import sys
import tempfile

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from streamlit.testing.v1 import AppTest
from openpyxl import load_workbook
from relatos import listar_fotos, obter_foto
from exportacao import gerar_excel, gerar_pacote


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('imagem', type=Path)
    parser.add_argument('--saida', type=Path, required=True)
    args = parser.parse_args()
    args.saida.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='aqua-validacao-') as pasta:
        os.environ['AQUASENTINEL_DB'] = str(Path(pasta) / 'teste.sqlite3')
        app = AppTest.from_file(str(RAIZ / 'app.py'), default_timeout=90).run()
        app.switch_page('app_pages/registrar.py').run()
        app.file_uploader[0].upload(args.imagem.name, args.imagem.read_bytes(), 'image/jpeg').run()
        assert not app.exception, app.exception
        assert 'rascunho_foto' in app.session_state
        app.text_input(key='foto_nome').set_value('TESTE TÉCNICO — frame de gravação local')
        app.number_input(key='foto_lat').set_value(-22.9068)
        app.number_input(key='foto_lon').set_value(-43.1729)
        app.button_group(key='foto_nivel').set_value('Moderado')
        app.checkbox(key='foto_confirmacao').check()
        next(b for b in app.button if b.label == 'Enviar ocorrência').click().run()
        assert not app.exception, app.exception
        registros = listar_fotos()
        assert len(registros) == 1
        registro, foto, anotada = obter_foto(registros[0]['id'])
        excel = gerar_excel(registro)
        wb = load_workbook(BytesIO(excel))
        assert wb['Detecções'].max_row == registro['total'] + 1
        app.switch_page('app_pages/mapa.py').run()
        assert not app.exception, app.exception
        app.button(key='mapa_abrir_ari').click().run()
        assert not app.exception and app.number_input[0].value == -22.9068
        (args.saida / 'resultado_real.xlsx').write_bytes(excel)
        (args.saida / 'anotada_real.jpg').write_bytes(anotada)
        (args.saida / 'evidencias_real.zip').write_bytes(gerar_pacote(registro, foto, anotada))
        (args.saida / 'resultado_real.json').write_text(json.dumps(registro, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps({k:registro[k] for k in ['total', 'deteccoes_modelo', 'duplicadas_removidas',
                                                  'confianca_media','triagem']}, ensure_ascii=False))
        print('OK: upload real, inferência, SQLite, Excel, mapa e vínculo ARI; banco de teste isolado.')


if __name__ == '__main__':
    main()
