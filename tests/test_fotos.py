from copy import deepcopy
from io import BytesIO
import zipfile
from PIL import Image
from openpyxl import load_workbook
import pytest
from visao import preparar_imagem, resumir, jpeg, LIMITES
from relatos import criar_registro, salvar_foto, listar_fotos, obter_foto
from exportacao import gerar_excel, gerar_pacote


def caixa(bbox=(0, 0, 40, 40), confidence=.9, classe='plastic_bottle'):
    return {'bbox': list(bbox), 'confidence': confidence, 'class_id': 2, 'class_name': classe}


def amostra():
    foto = jpeg(Image.new('RGB', (100, 80), 'white'))
    _, digest, _ = preparar_imagem(foto)
    analise = resumir([caixa(), caixa((50, 10, 80, 50), .7)], 100, 80)
    analise.update(image_hash=digest, model_hash='a'*64, analisado_em='2026-09-19T12:00:00+00:00',
                   parametros=LIMITES, classes_modelo=['plastic_bottle'])
    registro = criar_registro(analise, 'Canal teste', -22., -43., 'Moderado')
    return registro, foto, foto


@pytest.fixture(autouse=True)
def banco(tmp_path, monkeypatch):
    monkeypatch.setenv('AQUASENTINEL_DB', str(tmp_path / 'fotos.sqlite3'))


def test_deduplicacao_entre_classes_preserva_objetos_separados():
    resultado = resumir([caixa(), caixa((1, 1, 41, 41), .8, 'plastic_bag'),
                         caixa((60, 0, 99, 40), .6)], 100, 80)
    assert resultado['total'] == 2
    assert resultado['deteccoes_modelo'] == 3
    assert resultado['duplicadas_removidas'] == 1
    assert resultado['confianca_media'] == 75
    assert [d['item_id'] for d in resultado['itens']] == ['MAR-0001', 'MAR-0002']


@pytest.mark.parametrize('confidence,status', [(.5999,'baixa_confianca'),(.60,'revisao_recomendada'),
                                              (.7999,'revisao_recomendada'),(.80,'deteccao_consistente')])
def test_triagem_nao_declara_autenticidade(confidence, status):
    r = resumir([caixa(confidence=confidence)], 100, 100)
    assert r['triagem'] == status
    assert r['autenticidade'] == 'nao_verificada'


def test_sem_deteccao_nao_inventa_media():
    r = resumir([], 100, 100)
    assert r['total'] == 0 and r['confianca_media'] is None
    assert r['triagem'] == 'sem_deteccao'


def test_imagem_invalida_e_limites(monkeypatch):
    for dado in (b'', b'nao sou imagem'):
        with pytest.raises(ValueError):
            preparar_imagem(dado)
    monkeypatch.setattr('visao.MAX_PIXELS', 20)
    with pytest.raises(ValueError, match='megapixels'):
        preparar_imagem(jpeg(Image.new('RGB', (5, 5))))


def test_hash_ignora_metadados_e_redimensiona():
    from PIL.PngImagePlugin import PngInfo
    imagem = Image.new('RGB', (2000, 1000), 'blue')
    a, b = BytesIO(), BytesIO()
    imagem.save(a, format='PNG')
    meta = PngInfo(); meta.add_text('comentario', 'outra descrição')
    imagem.save(b, format='PNG', pnginfo=meta)
    processada, hash_a, tamanho = preparar_imagem(a.getvalue())
    assert preparar_imagem(b.getvalue())[1] == hash_a
    assert processada.size == (1920, 960) and tamanho == (2000, 1000)


def test_reenvio_mesma_foto_nao_duplica_nem_sobrescreve():
    r, foto, anotada = amostra()
    salvo, novo = salvar_foto(r, foto, anotada)
    assert novo
    outro = deepcopy(r); outro.update(id='outro', nome='outro local', latitude=40)
    repetido, novo = salvar_foto(outro, foto, anotada)
    assert not novo and repetido == salvo
    assert len(listar_fotos()) == 1
    assert obter_foto(r['id']) == (salvo, foto, anotada)
    assert all(salvo[k] == v for k, v in r.items())
    assert salvo['imagem_valida'] and salvo['phash']['versao']


@pytest.mark.parametrize('lat,lon', [(None,-43),(-22,None),(91,0),(0,-181),(float('nan'),0)])
def test_localizacao_invalida(lat,lon):
    r, _, _ = amostra()
    with pytest.raises(ValueError):
        criar_registro(r, 'Rio', lat, lon, 'Pouco')


def test_excel_valores_e_pacote_com_recortes():
    r, foto, anotada = amostra()
    r['nome'] = '=HYPERLINK("https://example.org")'
    wb = load_workbook(BytesIO(gerar_excel(r)))
    assert wb.sheetnames == ['Resumo', 'AquaVerify', 'Detecções']
    resumo = dict(wb['Resumo'].values)
    assert resumo['Itens identificados na foto'] == 2
    assert resumo['Confiança média (%)'] == 80
    assert resumo['Local'].startswith("'=")
    ws = wb['Detecções']
    assert ws.max_row == 3 and ws['C2'].value == 90 and ws['F2'].value is None
    assert ws['D2'].number_format == 'dd/mm/yyyy'
    with zipfile.ZipFile(BytesIO(gerar_pacote(r, foto, anotada))) as pacote:
        assert 'recortes/MAR-0001.jpg' in pacote.namelist()
        assert Image.open(BytesIO(pacote.read('recortes/MAR-0001.jpg'))).size == (40,40)
        assert load_workbook(BytesIO(pacote.read('deteccoes.xlsx')))['Detecções'].max_row == 3


def test_excel_vazio():
    r, _, _ = amostra()
    r.update(resumir([], 100, 80))
    wb = load_workbook(BytesIO(gerar_excel(r)))
    assert wb['Detecções'].max_row == 1
    assert dict(wb['Resumo'].values)['Confiança média (%)'] is None
