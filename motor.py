"""Regras puras de previsão e priorização, independentes da interface."""
from datetime import datetime, timezone
from math import ceil, isfinite
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class DadosInvalidos(ValueError):
    """Previsão incompleta ou incompatível com o cálculo."""


def numero(valor, minimo=0, maximo=float('inf')):
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise DadosInvalidos('Valor numérico ausente ou inválido.')
    if not isfinite(valor) or not minimo <= valor <= maximo:
        raise DadosInvalidos('Valor numérico fora da faixa permitida.')
    return float(valor)


def validar_entrada(nome, latitude, longitude, waste_score):
    if not isinstance(nome, str) or not nome.strip() or len(nome.strip()) > 100:
        raise DadosInvalidos('Informe um nome de canal com 1 a 100 caracteres.')
    numero(latitude, -90, 90)
    numero(longitude, -180, 180)
    numero(waste_score, 0, 100)


def classificar_chuva(mm):
    """Faixas contínuas: lacunas 5–5,1 e 25–25,1 entram na faixa superior."""
    mm = numero(mm)
    if mm < 0.2:
        return 0, 'Sem chuva significativa'
    if mm <= 5:
        return 25, 'Fraca'
    if mm <= 25:
        return 50, 'Moderada'
    if mm <= 50:
        return 75, 'Forte'
    return 100, 'Muito forte'


def calcular_prioridade(waste_score, rainfall_score):
    l = numero(waste_score, 0, 100) / 100
    r = numero(rainfall_score, 0, 100) / 100
    p = 100 * (0.6 * l + 0.2 * r + 0.2 * l * r)
    nivel = 'Baixa' if p < 25 else 'Média' if p < 50 else 'Alta' if p < 75 else 'Crítica'
    return round(p, 2), nivel


def analisar_previsao(dados, agora=None):
    """24 intervalos futuros completos; timestamps representam FIM de intervalo."""
    agora = agora or datetime.now(timezone.utc)
    if agora.tzinfo is None:
        raise DadosInvalidos('A data de referência precisa de fuso horário.')
    inicio = ceil(agora.timestamp() / 3600) * 3600
    try:
        zona = ZoneInfo(dados['timezone'])
        unidades = dados['hourly_units']
        if unidades['time'] != 'unixtime' or unidades['precipitation'] != 'mm' or unidades['precipitation_probability'] != '%':
            raise DadosInvalidos('Unidades inesperadas na resposta do Open-Meteo.')
        horas = dados['hourly']['time']
        chuva = dados['hourly']['precipitation']
        probabilidades = dados['hourly']['precipitation_probability']
        if not all(isinstance(v, list) for v in (horas, chuva, probabilidades)) or not len(horas) == len(chuva) == len(probabilidades):
            raise DadosInvalidos('Séries horárias com tamanhos incompatíveis.')
        tempos = [numero(t) for t in horas]
        if any(b - a != 3600 for a, b in zip(tempos, tempos[1:])):
            raise DadosInvalidos('Previsão com horas ausentes, duplicadas ou fora de ordem.')
        indices = [i for i, t in enumerate(tempos) if inicio < t <= inicio + 24 * 3600]
        if len(indices) != 24 or tempos[indices[0]] != inicio + 3600:
            raise DadosInvalidos('O Open-Meteo não retornou 24 horas futuras completas. Tente atualizar novamente.')
        valores = [numero(chuva[i]) for i in indices]
        probs = [None if probabilidades[i] is None else numero(probabilidades[i], 0, 100) for i in indices]
    except (KeyError, TypeError, ZoneInfoNotFoundError, OverflowError) as exc:
        raise DadosInvalidos('Resposta do Open-Meteo incompleta ou em formato inesperado.') from exc
    score, nivel = classificar_chuva(max(valores))
    def iso(t):
        return datetime.fromtimestamp(t, zona).isoformat()
    # Probabilidade parcial não é apresentada como pico conhecido das 24h.
    pico_prob = max(probs) if all(p is not None for p in probs) else None
    return {
        'max_1h_mm': max(valores),
        'acumulado_6h_mm': round(sum(valores[:6]), 3),
        'acumulado_24h_mm': round(sum(valores), 3),
        'precipitation_probability_peak': pico_prob,
        'rainfall_score': score,
        'level': nivel,
        'timezone': str(zona),
        'janela_inicio': iso(inicio),
        'janela_fim': iso(inicio + 24 * 3600),
        'calculado_em': agora.isoformat(),
        'horas': [
            {'inicio': iso(tempos[i] - 3600), 'fim': iso(tempos[i]),
             'precipitacao_mm': mm, 'probabilidade_pct': prob}
            for i, mm, prob in zip(indices, valores, probs)
        ],
    }
