from html import escape
from interface_idioma import st


def espaco_foto(titulo, legenda):
    st.html(f'<div class="foto-editorial" role="img" aria-label="Espaço reservado para foto: {escape(titulo)}">'
            f'<span aria-hidden="true">□</span><strong>{escape(titulo)}</strong><small>Foto a inserir</small></div>'
            f'<p class="galeria-legenda">{escape(legenda)}</p>')
