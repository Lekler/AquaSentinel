"""AquaSentinela — registro cívico de focos de resíduos em canais."""

import base64
import hmac
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from relatos import CORES, RelatoInvalido, banco_compartilhado, criar_relato, listar, revisar, salvar

st.set_page_config(page_title="AquaSentinela · focos de lixo", page_icon="💧", layout="wide", initial_sidebar_state="collapsed")
ASSETS = Path(__file__).parent / "Imagens"

st.markdown("""<style>
.block-container{max-width:1120px;padding-top:1.3rem;padding-bottom:4rem}
div[data-testid="stAppViewContainer"]{background:#f7fbfc}
h1,h2,h3{color:#123b54;letter-spacing:-.035em}
.hero{background:linear-gradient(120deg,#dffafa,#e7f2ff);border:1px solid #c9ebee;
border-radius:20px;padding:1.3rem 1.6rem;margin:1rem 0 1.5rem}
.hero strong{font-size:1.65rem;color:#123b54}.hero p{color:#31546a;margin:.4rem 0 0}
.kicker{font-size:.8rem;letter-spacing:.12em;text-transform:uppercase;color:#087f8c;font-weight:700}
@media(max-width:700px){.block-container{padding-top:.7rem}.hero{padding:1rem}.hero strong{font-size:1.3rem}}
</style>""", unsafe_allow_html=True)

logo = ASSETS / "Logo.png"
if logo.exists():
    st.image(str(logo), width=300)
else:
    st.title("💧 AquaSentinela")
st.markdown("""<div class="hero"><div class="kicker">MVP · Baía de Guanabara</div>
<strong>Mostre onde o lixo se acumula.</strong>
<p>Envie uma foto e indique o local. A equipe revisa cada relato antes que ele apareça no mapa de focos.</p></div>""", unsafe_allow_html=True)

try:
    registros = listar()
except Exception:
    st.error("Não foi possível abrir o banco de relatos. Confira a configuração de armazenamento.")
    st.stop()

envios_ativos = banco_compartilhado() or os.environ.get("AQUASENTINEL_ALLOW_LOCAL_DB") == "1"
if not envios_ativos:
    st.warning("Envios desativados até configurar um banco compartilhado. Para testar só neste computador, habilite o banco local conforme o README.")

enviar, mapa = st.tabs(["📷 Enviar relato", "🗺️ Mapa de focos"])

with enviar:
    st.subheader("Registrar um ponto com resíduos")
    st.caption("No celular, use a câmera ou selecione uma foto. Informe a posição no mapa; localização automática está em desenvolvimento.")
    modo = st.radio("Foto", ["Enviar arquivo", "Tirar foto"], horizontal=True)
    if modo == "Tirar foto":
        imagem = st.camera_input("Abra a câmera", key="camera")
    else:
        imagem = st.file_uploader("Escolha uma foto", type=["jpg", "jpeg", "png"], key="arquivo")
    if imagem:
        st.image(imagem, caption="Foto do relato", width=420)
    with st.form("novo_relato", clear_on_submit=True):
        nome = st.text_input("Canal ou ponto de referência", placeholder="Ex.: Canal do Fundão", max_chars=100)
        a, b = st.columns(2)
        latitude = a.number_input("Latitude", min_value=-90.0, max_value=90.0, value=-22.8667, format="%.6f")
        longitude = b.number_input("Longitude", min_value=-180.0, max_value=180.0, value=-43.2317, format="%.6f")
        st.caption("Exemplo inicial: região do Canal do Fundão. Confira e altere as coordenadas antes de enviar.")
        classe = st.select_slider("Acúmulo observado", options=["Baixo", "Moderado", "Alto"], value="Moderado")
        origem = st.selectbox("Quem está enviando?", ["Pessoa", "Equipe/órgão (declarado)"])
        observacao = st.text_area("Observações", max_chars=500, placeholder="Descreva o lixo e um ponto de referência próximo.")
        st.caption("A origem institucional é uma declaração do remetente; ainda não há verificação de identidade. A classificação é manual e provisória.")
        publicar = st.form_submit_button("Enviar para revisão", type="primary", use_container_width=True, disabled=not envios_ativos)
    if publicar:
        try:
            if imagem is None:
                raise RelatoInvalido("Tire ou selecione uma foto antes de enviar.")
            relato = criar_relato(nome, latitude, longitude, classe, origem, observacao, imagem.getvalue())
            salvar(relato)
            st.success(f"Relato recebido para revisão. Código: {relato['id'][:8]}")
        except RelatoInvalido as exc:
            st.error(str(exc))
        except Exception:
            st.error("Não foi possível salvar o relato. Tente novamente ou informe a equipe.")

with mapa:
    validados = [r for r in registros if r["status_validacao"] == "validado"]
    pendentes = sum(r["status_validacao"] == "pendente" for r in registros)
    c1, c2 = st.columns(2)
    c1.metric("Pontos revisados", len(validados))
    c2.metric("Aguardando revisão", pendentes)
    st.caption("Verde: baixo · amarelo: moderado · coral: alto. A cor reflete a triagem visual provisória, sem medição de risco à saúde.")
    if validados:
        pontos = pd.DataFrame([{"latitude": r["latitude"], "longitude": r["longitude"],
                                "cor": CORES[r["classe_residuos"]], "local": r["nome"]} for r in validados])
        st.map(pontos, latitude="latitude", longitude="longitude", color="cor", size=45, use_container_width=True)
        for r in validados[:30]:
            with st.expander(f"{r['nome']} · {r['classe_residuos']} · {r['registrado_em'][:10]}"):
                a, b = st.columns([1, 2])
                with a:
                    st.image(base64.b64decode(r["foto_jpeg_base64"]), width=240)
                with b:
                    st.write(r["observacao"] or "Sem descrição adicional.")
                    st.caption(f"{r['latitude']:.5f}, {r['longitude']:.5f} · Revisado em {r['validado_em'][:16]}")
    else:
        st.info("O mapa ficará disponível quando a equipe validar o primeiro relato.")

senha_configurada = os.environ.get("AQUASENTINEL_REVIEW_PASSWORD", "")
with st.sidebar:
    st.header("Equipe de revisão")
    if not senha_configurada:
        st.caption("Revisão desativada. Configure a senha da equipe para validar relatos.")
    else:
        senha = st.text_input("Senha da equipe", type="password")
        autenticado = bool(senha) and hmac.compare_digest(senha, senha_configurada)
        if senha and not autenticado:
            st.error("Senha incorreta.")
        if autenticado:
            st.success("Área de revisão liberada")
            pendentes_revisao = [r for r in registros if r["status_validacao"] == "pendente"]
            if pendentes_revisao:
                escolhido = st.selectbox("Relato pendente", pendentes_revisao,
                                        format_func=lambda r: f"{r['nome']} · {r['id'][:8]}")
                st.image(base64.b64decode(escolhido["foto_jpeg_base64"]), width=240)
                st.write(escolhido["observacao"] or "Sem descrição")
                st.caption(f"Local declarado: {escolhido['latitude']:.5f}, {escolhido['longitude']:.5f}")
                revisor = st.text_input("Nome de quem revisou", max_chars=100)
                a, b = st.columns(2)
                decisao = "validado" if a.button("Validar") else "rejeitado" if b.button("Rejeitar") else None
                if decisao:
                    try:
                        revisar(escolhido["id"], decisao, revisor)
                        st.success("Revisão registrada. Atualize a página para ver o mapa.")
                    except RelatoInvalido as exc:
                        st.error(str(exc))
                    except Exception:
                        st.error("Não foi possível registrar a revisão.")
            else:
                st.caption("Nenhum relato aguardando revisão.")

st.divider()
st.caption("AquaSentinela · protótipo colaborativo. Artes: Alessandra Vaz dos Anjos Santos. Aplicativo inicial: Alexandre Rodrigues (Lekler). A pontuação W e o modelo de IA da equipe ainda serão integrados.")
