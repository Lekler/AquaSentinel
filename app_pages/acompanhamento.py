import streamlit as st
from ciclo import consultar_recibo, feedback
from acompanhamento_visual import rastreabilidade
from relatos import listar_fotos
from registro_visual import cabecalho, rodape

cabecalho('Acompanhar meu registro', 'Consulte o resultado e as etapas com seu recibo.', False,
          'Track my report', 'Check results and progress with your receipt.', '/acompanhamento')
with st.form('consultar-recibo'):
    ident = st.text_input('ID do registro')
    chave = st.text_input('Código privado de acompanhamento', type='password')
    consultar = st.form_submit_button('Consultar acompanhamento')
if consultar:
    try:
        r = consultar_recibo(ident, chave)
        for mensagem in feedback(r, listar_fotos()):
            st.info(mensagem)
        rastreabilidade(r)
        from ambiente import mostrar_contexto
        mostrar_contexto(r)
        st.page_link('app_pages/dados.py', label='Exportar meus registros com o recibo')
    except ValueError as exc:
        st.error(str(exc))
st.caption('O recibo é fornecido ao salvar um novo registro. Registros antigos sem código não podem ser '
           'consultados por este formulário; quando públicos, continuam acessíveis no mapa. Não há ranking de usuários.')
rodape()
