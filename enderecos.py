"""Explicit, cached address searches; no background/autocomplete requests."""
import math
import os
import re
import threading
import time
import requests
import streamlit as st

_lock = threading.Lock()
_ultima = 0.
AGENTE = 'AquaSentinela/1.0 (+https://github.com/Lekler/AquaSentinel)'


def _json(url, params=None):
    global _ultima
    with _lock:
        time.sleep(max(0., 1.1 - (time.monotonic() - _ultima)))
        _ultima = time.monotonic()
        try:
            r = requests.get(url, params=params, headers={'User-Agent': AGENTE}, timeout=(4, 10))
            r.raise_for_status()
            return r.json()
        except (requests.RequestException, ValueError) as exc:
            raise ValueError('Não foi possível buscar o endereço agora. Use o GPS ou marque o ponto no mapa.') from exc


def buscar_endereco(consulta):
    consulta = ' '.join(consulta.strip().split())
    if not 3 <= len(consulta) <= 180:
        raise ValueError('Informe um CEP de 8 dígitos ou um endereço com cidade e estado.')
    if re.fullmatch(r'[\d\s-]+', consulta) and not re.fullmatch(r'\d{5}-?\d{3}', consulta):
        raise ValueError('O CEP deve ter 8 dígitos.')
    endpoint = os.environ.get('AQUASENTINEL_PHOTON_URL', 'https://photon.komoot.io/api/').strip()
    return _buscar(consulta, endpoint)


@st.cache_data(ttl=86400, max_entries=512, show_spinner=False)
def _buscar(consulta, endpoint):
    cep = re.fullmatch(r'\d{5}-?\d{3}', consulta)
    endereco = consulta
    if cep:
        dados = _json(f'https://viacep.com.br/ws/{consulta.replace("-", "")}/json/')
        if not isinstance(dados, dict) or dados.get('erro') or not dados.get('localidade'):
            raise ValueError('CEP não encontrado. Confira os números ou tente o endereço completo.')
        endereco = ', '.join(dados[k] for k in ('logradouro', 'bairro', 'localidade', 'uf') if dados.get(k))
    retorno = _json(endpoint, {'q': endereco, 'countrycode': 'BR', 'limit': 5})
    if not isinstance(retorno, dict) or not isinstance(retorno.get('features'), list):
        raise ValueError('Não foi possível interpretar a busca. Use o GPS ou marque o ponto no mapa.')
    resultados = []
    vistos = set()
    for feature in retorno['features'][:5]:
        try:
            lon, lat = map(float, feature['geometry']['coordinates'][:2])
            p = feature['properties']
            if not math.isfinite(lat) or not math.isfinite(lon) or not (-90 <= lat <= 90 and -180 <= lon <= 180):
                continue
            if p.get('countrycode', 'BR').upper() != 'BR':
                continue
            partes = [str(p[k]) for k in ('name', 'housenumber', 'street', 'district', 'city', 'state', 'postcode') if p.get(k)]
            label = ', '.join(dict.fromkeys(partes)) or endereco
            chave = (round(lat, 6), round(lon, 6), label)
            if chave in vistos:continue
            vistos.add(chave)
            resultados.append({'latitude':lat, 'longitude':lon, 'label':label,
                               'source':'address', 'cep':bool(cep)})
        except (KeyError, TypeError, ValueError, AttributeError):
            continue
    return resultados
