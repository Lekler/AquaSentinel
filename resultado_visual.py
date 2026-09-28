"""Cartões e tabela de evidências com valores reais e HTML escapado."""
from html import escape
from pathlib import Path
from interface_idioma import st
from aquaverify import avaliar, explicar, AVISO


def icone(tipo):
    caminhos = {
        'pin': '<path d="M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="2.5"/>',
        'shield': '<path d="m12 2 8 3v6c0 6-8 11-8 11S4 17 4 11V5Z"/><path d="m8 11 3 3 5-6"/>',
        'chart': '<path d="M4 20V10h3v10m4 0V4h3v16m4 0v-7h3v7"/>',
        'document': '<path d="M6 2h9l4 4v16H6Z"/><path d="M14 2v5h5M9 11h7M9 15h7M9 18h5"/>',
        'info': '<circle cx="12" cy="12" r="9"/><path d="M12 10v7M12 6v1"/>',
        'warning': '<circle cx="12" cy="12" r="9"/><path d="M12 6v8M12 17v1"/>',
    }
    return ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
            'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + caminhos[tipo] + '</svg>')


def estilo():
    st.html('<style>' + (Path(__file__).parent/'assets'/'resultado.css').read_text(encoding='utf-8') + '</style>')


def resumo_salvo(r):
    estilo()
    nivel = r.get('nivel_informado', 'Não informado')
    classes = {'Sem resíduos': 'sem', 'Pouco': 'pouco', 'Moderado': 'moderado',
               'Muito poluído': 'muito', 'Bloqueando': 'bloqueando'}
    st.html('<section class="resultado-local" aria-label="Resumo do registro salvo">'
            f'<div class="resultado-identidade">{icone("pin")}<div><h2>Local salvo: <span>{escape(r["nome"])}</span></h2>'
            f'<p>ID: {escape(r["id"])}</p></div></div>'
            f'<div class="resultado-coordenadas"><span class="resultado-icone">{icone("pin")}</span>'
            f'<div><span>Coordenadas salvas</span><p>{r["latitude"]:.6f}, {r["longitude"]:.6f}</p></div></div>'
            '<div class="resultado-nivel"><div><span>Nível informado</span>'
            f'<p><strong class="resultado-badge {classes.get(nivel, "sem")}">{escape(nivel)}</strong></p></div></div></section>')


def evidencia(registro):
    estilo()
    q = avaliar(registro)
    score = q['indice']
    linhas = []
    for c in q['criterios']:
        percentual = 100*c['Pontos']/c['Máximo'] if c['Máximo'] else 0
        cor = 'bom' if percentual >= 75 else 'medio' if percentual >= 45 else 'baixo'
        valor = f'{percentual:.1f}'.rstrip('0').rstrip('.')
        linhas.append(f'<tr><th scope="row">{escape(c["Critério"])}</th>'
                      f'<td>{c["Pontos"]:g}</td><td>{c["Máximo"]:g}</td>'
                      f'<td><div class="criterio-desempenho"><div class="resultado-trilho" aria-hidden="true">'
                      f'<span class="{cor}" style="width:{percentual:.3f}%"></span></div><span>{valor}%</span></div></td>'
                      f'<td>{escape(c["Motivo"])}</td></tr>')
    st.html('<section class="resultado-evidencia"><h2>AquaVerify / Qualidade da Evidência</h2>'
            f'<p class="resultado-subtitulo">{escape(AVISO)}</p>'
            '<div class="resultado-score">'
            f'<span class="resultado-icone grande">{icone("shield")}</span><div class="resultado-score-texto">'
            f'<strong>Qualidade da evidência {escape(q["faixa"])}</strong>'
            f'<p><b>{score:.1f}</b> / 100</p></div>'
            f'<div class="resultado-score-barra"><div role="progressbar" aria-label="Qualidade da evidência" '
            f'aria-valuemin="0" aria-valuemax="100" aria-valuenow="{score}" class="resultado-trilho">'
            f'<span style="width:{score}%"></span></div><b>{score:.1f}</b></div></div>'
            f'<div class="resultado-criterios"><h3>{icone("chart")}Detalhamento por critério</h3>'
            '<div class="resultado-tabela-scroll" tabindex="0" role="region" aria-label="Critérios AquaVerify">'
            '<table><caption class="resultado-sr">Critérios de qualidade da evidência, pontos e justificativas</caption>'
            '<thead><tr><th scope="col">Critério</th><th scope="col">Pontos</th><th scope="col">Máximo</th>'
            '<th scope="col">Desempenho</th><th scope="col">Motivo</th></tr></thead>'
            f'<tbody>{"".join(linhas)}</tbody></table></div></div>'
            f'<p class="resultado-rubrica">{icone("info")}Rubrica experimental v1: alta ≥ 75, média ≥ 45, baixa &lt; 45. '
            'Pesos e limiares não foram calibrados como probabilidade.</p></section>')
    texto, motivos = explicar(registro)
    partes = texto.split('. ', 1)
    resumo = '<strong>' + escape(partes[0]) + '.</strong> ' + escape(partes[1]) if len(partes) == 2 else escape(texto)
    itens = ''.join(f'<li>{icone("warning" if "limiar" in motivo or "Limite" in motivo else "pin" if "Localização" in motivo else "document")}<span>{escape(motivo)}</span></li>'
                    for motivo in motivos)
    st.html('<section class="resultado-explicacao" aria-label="Explicação da análise">'
            f'<div class="resultado-explicacao-topo"><span class="resultado-icone">{icone("document")}</span>'
            f'<p>{resumo}</p></div><ul>{itens}</ul></section>')
    if (registro.get('similaridade') or {}).get('quantidade'):
        st.warning('Esta imagem parece semelhante a uma anterior. A equipe deve verificar se é '
                   'uma nova observação, reutilização ou falso positivo. Isso não comprova fraude.')
