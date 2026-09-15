"""Cliente Open-Meteo. Nenhuma credencial é necessária no endpoint público."""
from datetime import datetime, timezone
import requests
from motor import numero

ENDPOINT = 'https://api.open-meteo.com/v1/forecast'


class ErroPrevisao(RuntimeError):
    pass


def consultar_previsao(latitude, longitude):
    numero(latitude, -90, 90)
    numero(longitude, -180, 180)
    parametros = {
        'latitude': latitude, 'longitude': longitude,
        'hourly': 'precipitation,precipitation_probability',
        'timezone': 'auto', 'timeformat': 'unixtime',
        'precipitation_unit': 'mm', 'forecast_days': 3,
    }
    try:
        resposta = requests.get(ENDPOINT, params=parametros, timeout=(5, 20))
        resposta.raise_for_status()
        dados = resposta.json()
    except requests.Timeout as exc:
        raise ErroPrevisao('O Open-Meteo demorou a responder. Tente novamente em alguns instantes.') from exc
    except requests.HTTPError as exc:
        status = exc.response.status_code
        motivo = 'Limite de consultas atingido' if status == 429 else 'Serviço indisponível ou consulta rejeitada'
        raise ErroPrevisao(f'{motivo} (HTTP {status}). Tente novamente mais tarde.') from exc
    except ValueError as exc:
        raise ErroPrevisao('O Open-Meteo retornou uma resposta que não é JSON válido.') from exc
    except requests.RequestException as exc:
        raise ErroPrevisao('Não foi possível conectar ao Open-Meteo. Verifique sua conexão e tente novamente.') from exc
    if not isinstance(dados, dict) or dados.get('error'):
        raise ErroPrevisao('O Open-Meteo retornou um erro ou formato inesperado.')
    return {'dados': dados, 'consultado_em': datetime.now(timezone.utc).isoformat(), 'url': resposta.url}
