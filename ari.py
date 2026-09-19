"""ARI v2: componentes de 0–100, resultado normalizado de 0–1."""
from motor import DadosInvalidos, numero

CLASSES_RESIDUOS = {'Baixo': 25, 'Moderado': 60, 'Alto': 100}
NIVEIS_RIO = {'Vigilância': 0, 'Atenção': 25, 'Alerta': 50,
              'Alerta máximo': 75, 'Transbordamento': 100}
PESOS = {'W': .4, 'R': .25, 'L': .25, 'F': .1}
CORES = {'Baixo': '#228B45', 'Moderado': '#B38B00', 'Alto': '#D2691E', 'Crítico': '#C73545'}
ACOES = {'Baixo': 'Monitorar', 'Moderado': 'Intensificar monitoramento',
         'Alto': 'Avaliação prioritária', 'Crítico': 'Avaliação urgente recomendada'}


def pontuar_chuva_24h(mm):
    mm = numero(mm)
    if mm < 10: return 0
    if mm <= 30: return 25
    if mm <= 50: return 50
    if mm <= 80: return 75
    return 100


def pontuar_recorrencia(contagem):
    numero(contagem)
    if int(contagem) != contagem:
        raise DadosInvalidos('A contagem de registros deve ser inteira.')
    if contagem == 0: return 0
    if contagem == 1: return 25
    if contagem <= 3: return 50
    if contagem <= 5: return 75
    return 100


def triar_confianca(confianca, confirmacao_humana=False, revisor=''):
    c = numero(confianca, 0, 100)
    if not isinstance(confirmacao_humana, bool):
        raise DadosInvalidos('A confirmação humana deve ser booleana.')
    if c < 60: return 'excluido'
    if c >= 80: return 'aceito'
    if confirmacao_humana:
        if not isinstance(revisor, str) or not revisor.strip():
            raise DadosInvalidos('Identifique o responsável pela confirmação humana.')
        return 'confirmado_humano'
    return 'pendente'


def calcular_ari(classe_residuos, chuva_24h_mm, registros_anteriores,
                 nivel_rio=None, confianca=100, confirmacao_humana=False,
                 revisor='', nivel_oficial=False, fonte_nivel=''):
    if classe_residuos not in CLASSES_RESIDUOS:
        raise DadosInvalidos('Classe de resíduos inválida.')
    if nivel_rio is not None and nivel_rio not in NIVEIS_RIO:
        raise DadosInvalidos('Condição do rio inválida.')
    if not isinstance(nivel_oficial, bool):
        raise DadosInvalidos('A origem oficial deve ser booleana.')
    if nivel_oficial and (nivel_rio is None or not fonte_nivel.strip()):
        raise DadosInvalidos('Informe a condição do rio e a referência da fonte oficial.')
    status = triar_confianca(confianca, confirmacao_humana, revisor)
    urgente = nivel_rio == 'Transbordamento' and nivel_oficial
    componentes = {'W': CLASSES_RESIDUOS[classe_residuos],
                   'R': None if chuva_24h_mm is None else pontuar_chuva_24h(chuva_24h_mm),
                   'L': NIVEIS_RIO.get(nivel_rio), 'F': pontuar_recorrencia(registros_anteriores)}
    disponiveis = {k: v for k, v in componentes.items() if v is not None}
    cobertura = sum(PESOS[k] for k in disponiveis)
    pesos = {k: PESOS[k] / cobertura for k in disponiveis}
    calculavel = status in ('aceito', 'confirmado_humano') and componentes['R'] is not None
    score = sum(pesos[k] * v for k, v in disponiveis.items()) if calculavel else None
    nivel = None if score is None else ('Baixo' if score < 25 else 'Moderado' if score < 50 else 'Alto' if score < 75 else 'Crítico')
    return {'ari': None if score is None else round(score / 100, 6),
            'ari_score': None if score is None else round(score, 2),
            'ari_level': nivel, 'cor_hotspot': '#C73545' if urgente else CORES.get(nivel, '#7B8794'),
            'acao': 'Avaliação urgente recomendada' if urgente else ACOES.get(nivel, 'Aguardar validação ou previsão'),
            'avaliacao_urgente': urgente, 'motivo_urgencia': 'Transbordamento informado como oficial' if urgente else None,
            'status_validacao': status, 'componentes': componentes,
            'contribuicoes': {k: round(pesos[k] * v, 4) for k, v in disponiveis.items()} if calculavel else {},
            'pesos_efetivos': pesos, 'cobertura_pesos': round(cobertura, 2),
            'parcial': len(disponiveis) < 4, 'versao_metodologia': 'ari-2'}
