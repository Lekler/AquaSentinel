from datetime import datetime, timezone

from observacao import (agrupar_locais, filtrar_periodo, resumo_local,
                        CORES_NIVEIS, PERIODOS)

AGORA = datetime(2026, 9, 27, 18, tzinfo=timezone.utc)


def registro(ident, data='2026-09-27T15:00:00+00:00', **extras):
    return {'id': ident, 'nome': 'Canal do Fundão', 'latitude': -22.83,
            'longitude': -43.24, 'registrado_em': data, 'image_hash': ident,
            'nivel_informado': 'Moderado', 'confianca_media': 90, 'total': 2,
            'por_classe': {'Garrafa plástica': 2}, 'revisao': 'validado',
            'consentimento_publicacao': True, **extras}


def test_dias_distintos_nao_sao_uploads_e_usam_brasilia():
    rs = [registro('a', '2026-09-26T23:00:00-03:00'),
          registro('b', '2026-09-27T02:30:00+00:00'),
          registro('c', '2026-09-27T04:00:00+00:00', nivel_informado='Sem resíduos')]
    resumo = resumo_local(rs, AGORA)
    assert resumo['total'] == 3 and resumo['dias'] == 2
    assert resumo['dias_residuos'] == 1 and resumo['recente']['id'] == 'c'
    assert resumo['objetos'] == 6 and resumo['classes'] == [('Garrafa plástica', 6)]


def test_periodos_incluem_hoje_limite_local_e_excluem_futuro():
    for dias in [7, 15, 30, 90]:
        from datetime import timedelta
        inicio = datetime(2026, 9, 27, 3, tzinfo=timezone.utc) - timedelta(days=dias-1)
        rs = [registro('dentro', inicio.isoformat()),
              registro('fora', (inicio-timedelta(seconds=1)).isoformat()),
              registro('futuro', '2027-01-01T00:00:00Z')]
        assert [r['id'] for r in filtrar_periodo(rs, dias, AGORA)] == ['dentro']
    assert PERIODOS['Todo o período'] is None
    assert len(filtrar_periodo(rs, None, AGORA)) == 2


def test_grupos_normalizam_nomes_e_nao_encadeiam_pontos_distantes():
    rs = [registro('a', latitude=0, longitude=0),
          registro('b', nome=' CANAL DO FUNDAO ', latitude=0, longitude=.0015),
          registro('c', latitude=0, longitude=.003),
          registro('d', nome='Outro rio', latitude=0, longitude=0)]
    grupos = agrupar_locais(list(reversed(rs)))
    assert [[r['id'] for r in g['registros']] for g in grupos] == [['a', 'b'], ['c'], ['d']]
    assert [g['id'] for g in grupos] == [g['id'] for g in agrupar_locais(rs)]


def test_privacidade_e_coordenadas_invalidas():
    rs = [registro('publico'), registro('pendente', revisao='nao_revisado'),
          registro('privado', consentimento_publicacao=False),
          registro('invalido', latitude=float('nan')),
          registro('sem_data', registrado_em='invalida')]
    grupos = agrupar_locais(rs)
    assert len(grupos) == 1 and len(grupos[0]['registros']) == 1
    assert grupos[0]['registros'][0]['id'] == 'publico'


def test_nivel_recente_nao_e_o_mais_grave_e_bloqueando_preto():
    rs = [registro('a', '2026-09-05T12:00:00Z', nivel_informado='Bloqueando'),
          registro('b', '2026-09-21T12:00:00Z', nivel_informado='Pouco')]
    assert resumo_local(rs, AGORA)['recente']['nivel_informado'] == 'Pouco'
    assert resumo_local(rs, AGORA)['dias_desde_ultima'] == 6
    assert CORES_NIVEIS['Bloqueando'] == '#000000'


def test_data_legada_sem_fuso_e_interpretada_como_utc():
    r = registro('a', '2026-09-27T02:00:00')
    assert resumo_local([r], AGORA)['ultima'].day == 26
