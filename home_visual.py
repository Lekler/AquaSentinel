"""Home de marca com os PNGs do usuário. ViewBoxes não modificam os originais."""
import base64
from functools import lru_cache
from html import escape
from pathlib import Path
from i18n import alternador_html, em_ingles, idioma_query, texto

RAIZ = Path(__file__).resolve().parent
ASSETS = RAIZ / 'assets' / 'home'
ENQUADRAMENTOS = {
    'Logo.png': (125, 150, 1930, 435), 'mão e fundo.png': (20, 88, 1400, 921),
    'F1.png': (174, 313, 906, 688), 'F2.png': (148, 255, 958, 771),
    'F3.png': (190, 252, 875, 806), 'F4.png': (114, 172, 1023, 928),
    'F1.1.png': (187, 239, 880, 888), 'F2.2.png': (132, 150, 990, 980),
    'F3.3.png': (181, 395, 892, 531), 'F4.4.png': (135, 227, 985, 848),
    'g.png': (0, 458, 2172, 207),
}


@lru_cache(maxsize=16)
def imagem(nome, classe='', descricao=''):
    x, y, w, h = ENQUADRAMENTOS[nome]
    dimensoes = ((2172, 724) if nome in ('Logo.png', 'g.png') else
                 (1448, 1086) if nome == 'mão e fundo.png' else (1254, 1254))
    url = 'data:image/png;base64,' + base64.b64encode((ASSETS / nome).read_bytes()).decode('ascii')
    proporcao = 'none' if nome == 'g.png' else 'xMidYMid meet'
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {w} {h}" '
           f'preserveAspectRatio="{proporcao}"><image width="{dimensoes[0]}" '
           f'height="{dimensoes[1]}" href="{url}"/></svg>')
    # st.html permite img, mas seu sanitizador remove SVG inline.
    src = 'data:image/svg+xml;base64,' + base64.b64encode(svg.encode()).decode('ascii')
    return f'<img class="asset {classe}" src="{src}" alt="{escape(descricao, quote=True)}" draggable="false">'


CAMERA = '''<svg viewBox="0 0 48 44" aria-hidden="true"><path fill="currentColor" d="M17 3h14l4 6h7a5 5 0 0 1 5 5v24a5 5 0 0 1-5 5H6a5 5 0 0 1-5-5V14a5 5 0 0 1 5-5h7z"/><circle cx="24" cy="25" r="11" fill="#009ec0"/><circle cx="24" cy="25" r="6.8" fill="currentColor"/><circle cx="39" cy="15" r="2" fill="#009ec0"/></svg>'''
CAMERA_REGISTRO = CAMERA.replace('#009ec0', '#ffffff')
MAPA = '''<svg viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="3" stroke-linejoin="round" aria-hidden="true"><path d="m3 8 11-4 12 5 11-4v28l-11 4-12-5-11 4z"/><path d="M14 4v28M26 9v28"/></svg>'''
SETA = '''<svg class="seta" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 16h21m-8-8 8 8-8 8"/></svg>'''
ONDA = '''<svg class="traco-onda" viewBox="0 0 72 16" fill="none" aria-hidden="true"><path d="M3 8C24-5 45 22 69 8" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/></svg>'''


def icone(svg, cor, classe=''):
    svg = svg.replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" ', 1).replace('currentColor', cor)
    src = 'data:image/svg+xml;base64,' + base64.b64encode(svg.encode()).decode('ascii')
    return f'<img class="{classe}" src="{src}" alt="" aria-hidden="true">'


def construir_home(base_url=''):
    prefixo = '/' + base_url.strip('/') if base_url.strip('/') else ''
    registrar, mapa, ari = (escape(prefixo + '/' + p, quote=True) for p in ('registrar', 'mapa', 'avaliacao'))
    query = idioma_query()
    css = (RAIZ / 'assets' / 'home.css').read_text(encoding='utf-8')
    language_switch = alternador_html(prefixo or '/')
    label_sobre = texto('Sobre', 'About')
    label_como = texto('Como funciona', 'How it works')
    label_mapa = texto('Mapa', 'Map')
    label_duvidas = texto('Dúvidas', 'Questions')
    label_diferenca = texto('Faça a diferença', 'Make a difference')
    titulo_1 = texto('Viu lixo em um rio', 'Did you see waste')
    titulo_2 = texto('ou canal?', 'in a river or canal?')
    titulo_3 = texto('Mostre pra gente.', 'Show us.')
    descricao_hero = texto('Uma foto ajuda a identificar pontos que precisam de atenção<br class="desktop-break"> e contribui para proteger nossos rios e a Baía de Guanabara.', 'A photo helps identify places that need attention<br class="desktop-break"> and contributes to protecting our rivers and Guanabara Bay.')
    registrar_label = texto('Registrar ocorrência', 'Report an occurrence')
    ver_mapa_label = texto('Ver mapa', 'View map')
    simples = texto('É muito simples', 'It is very simple')
    simples_desc = texto('Em poucos passos, você registra e nos ajuda a cuidar das nossas águas.', 'In a few steps, you can report an issue and help care for our waters.')
    return f'''<style>{css}</style>
<div class="aqua-page"><div class="aqua-home {"english-home" if em_ingles() else ""}">
  <a class="skip-link" href="#como-funciona">{texto('Pular para como funciona', 'Skip to how it works')}</a>
  <header class="aqua-header">
    <a class="brand" href="{prefixo or '/'}" target="_self" aria-label="AquaSentinela — início">
      {imagem('Logo.png', 'brand-image', 'AquaSentinela. Rios mais limpos. Um futuro melhor.')}
    </a>
    <nav class="aqua-nav" aria-label="Navegação principal">
      <details class="nav-disclosure nav-about"><summary>{label_sobre}</summary>
        <div class="nav-panel"><strong>{texto('Mais olhos pelos nossos rios.', 'More eyes on our rivers.')}</strong>
        <p>{texto('O AquaSentinela reúne relatos com foto e localização para ajudar a identificar resíduos nos rios, canais e na Baía de Guanabara.', 'AquaSentinela brings together photo and location reports to help identify waste in rivers, canals and Guanabara Bay.')}</p>
        <p>{texto('A inteligência artificial identifica plásticos visíveis. A avaliação ambiental combina as informações do local com a previsão de chuva.', 'Artificial intelligence identifies visible plastics. Environmental assessment combines site information with the rain forecast.')}</p></div>
      </details>
      <a class="nav-how" href="#como-funciona">{label_como}</a>
      <a href="{mapa}{query}" target="_self">{label_mapa}</a>
      <details class="nav-disclosure nav-faq"><summary>{label_duvidas}</summary>
        <div class="nav-panel"><strong>{texto('Como posso participar?', 'How can I participate?')}</strong><p>{texto('Tire uma foto ou envie uma imagem, confira a localização e informe o nível de resíduos que você observou.', 'Take a photo or upload an image, check the location and report the waste level you observed.')}</p>
        <strong>{texto('A IA confirma se a foto é verdadeira?', 'Does AI confirm that the photo is authentic?')}</strong><p>{texto('Não. A confiança indica o reconhecimento dos objetos, sem comprovar a autenticidade da imagem.', 'No. Confidence indicates object recognition; it does not prove image authenticity.')}</p>
        <strong>{texto('Preciso permitir a localização?', 'Do I need to allow location access?')}</strong><p>{texto('Você pode usar a localização do navegador ou informar as coordenadas manualmente.', 'You can use browser location or enter coordinates manually.')}</p></div>
      </details>
      {language_switch}<details class="nav-disclosure nav-more"><summary aria-label="Mais opções"><span aria-hidden="true">•••</span></summary>
        <div class="nav-panel more-links"><a href="{registrar}{query}" target="_self">{texto('Registrar ocorrência', 'Report an occurrence')}</a>
        <a href="{mapa}{query}" target="_self">{texto('Mapa e registros', 'Map and reports')}</a>
        <a href="{ari}{query}" target="_self">{texto('Avaliação ambiental · ARI', 'Environmental assessment · ARI')}</a>
        <a class="mobile-only" href="#como-funciona">{label_como}</a>
        <details class="mobile-only mobile-info"><summary>{label_sobre}</summary><p>{texto('Fotos e localização ajudam a identificar resíduos nos rios, canais e na Baía de Guanabara.', 'Photos and location help identify waste in rivers, canals and Guanabara Bay.')}</p></details>
        <details class="mobile-only mobile-info"><summary>{label_duvidas}</summary><p>{texto('Você pode enviar uma foto ou usar a câmera, permitir o GPS ou informar coordenadas. A IA identifica plásticos; a confiança não comprova a autenticidade da foto.', 'You can upload a photo or use the camera, allow GPS or enter coordinates. AI identifies plastics; confidence does not prove image authenticity.')}</p></details></div>
      </details>
    </nav>
  </header>
  <main>
    <section class="aqua-hero" aria-labelledby="home-title">
      <div class="hero-visual">{imagem('mão e fundo.png', 'hero-image', 'Mão segurando um celular com uma fotografia de resíduos na Baía de Guanabara. Rios vivos, cidades melhores. Juntos por águas mais limpas para todos.')}</div>
      <div class="hero-copy">
        <div class="participation-badge">{imagem('F1.1.png', 'badge-leaf')}<span>{label_diferenca}</span></div>
        <h1 id="home-title"><span>{titulo_1}</span><span>{titulo_2}</span><span class="accent">{titulo_3}</span></h1>
        <p class="hero-description">{descricao_hero}</p>
        <div class="hero-actions">
          <a class="cta cta-primary" href="{registrar}{query}" target="_self"><span class="cta-icon">{icone(CAMERA, '#ffffff')}</span><span>{registrar_label}</span>{icone(SETA, '#ffffff', 'seta')}</a>
          <a class="cta cta-secondary" href="{mapa}{query}" target="_self"><span class="cta-icon">{icone(MAPA, '#10568d')}</span><span>{ver_mapa_label}</span>{icone(SETA, '#10568d', 'seta')}</a>
        </div>
      </div>
    </section>
    <section class="how-section" id="como-funciona" aria-labelledby="how-title">
      <h2 id="how-title">{simples}</h2>
      <p class="how-intro">{simples_desc}</p>
      <div class="step-grid">
        <article class="step-card"><span class="step-number" aria-label="Etapa 1">1</span>
          <div class="step-art">{imagem('F1.png', 'step-camera')}</div>
          <h3>{texto('Tire uma foto', 'Take a photo')}</h3><p>{texto('Registre o lixo ou resíduo<br>no rio, canal ou na baía.', 'Report waste or debris<br>in a river, canal or bay.')}</p>
        </article>
        <article class="step-card"><span class="step-number" aria-label="Etapa 2">2</span>
          <div class="step-art">{imagem('F2.png', 'step-location')}</div>
          <h3>{texto('Confirme a localização', 'Confirm the location')}</h3><p>{texto('O local é identificado<br>pelo seu celular.', 'The location is identified<br>by your phone.')}</p>
        </article>
        <article class="step-card level-card"><span class="step-number" aria-label="Etapa 3">3</span>
          <div class="step-art">{imagem('F3.png', 'step-level')}</div>
          <h3>{texto('Informe o nível', 'Report the level')}</h3><p>{texto('Diga o quanto de resíduo<br>há no local.', 'Tell us how much waste<br>is at the location.')}</p>
          <div class="level-badges" aria-label="{texto('Níveis de resíduos', 'Waste levels')}"><span class="low"><i></i>{texto('Pouco', 'Low')}</span><span class="medium"><i></i>{texto('Moderado', 'Moderate')}</span><span class="high"><i></i>{texto('Muito', 'High')}</span><span class="blocked"><i></i>{texto('Bloqueando', 'Blocking')}</span></div>
        </article>
        <article class="community-card">
          <div class="community-art">{imagem('F4.png', 'step-community')}</div>
          <p>{texto('Sua participação<br>fortalece um ambiente<br>mais saudável para as<br>pessoas e a vida marinha.', 'Your participation<br>supports a healthier environment<br>for people and marine life.')}</p>{icone(ONDA, '#4cc1d7', 'traco-onda')}
        </article>
      </div>
    </section>
    <section class="benefits" aria-label="{texto('Nossa contribuição', 'Our contribution')}">
      <div class="benefit">{imagem('F1.1.png', 'benefit-leaf')}<div><h3>{texto('Cidadãos engajados', 'Engaged citizens')}</h3><p>{texto('Mais olhos pelos nossos rios', 'More eyes on our rivers')}</p></div></div>
      <div class="benefit">{imagem('F2.2.png', 'benefit-target')}<div><h3>{texto('Ações mais rápidas', 'Faster action')}</h3><p>{texto('Informações que viram impacto', 'Information that drives impact')}</p></div></div>
      <div class="benefit">{imagem('F3.3.png', 'benefit-water')}<div><h3>{texto('Rios e Baía mais limpos', 'Cleaner rivers and bay')}</h3><p>{texto('Um futuro melhor pra todos', 'A better future for everyone')}</p></div></div>
      <div class="benefit">{imagem('F4.4.png', 'benefit-heart')}<div><h3>{texto('Tecnologia a serviço<br>do bem comum', 'Technology for<br>the common good')}</h3></div></div>
    </section>
  </main>
  <footer class="aqua-footer">{imagem('g.png', 'footer-waves')}
    <span class="footer-signature">{texto('Água limpa move vidas', 'Clean water moves lives')} {icone(ONDA, '#46b2cb', 'traco-onda')}</span>
  </footer>
</div></div>'''
