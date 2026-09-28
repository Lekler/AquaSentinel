import os
import re
from urllib.parse import urlparse
import streamlit as st
from registro_visual import cabecalho, rodape

cabecalho('Fale Conosco', 'Dúvidas, correções e colaboração com o projeto.', False,
          'Contact us', 'Questions, corrections and collaboration.', '/contato')
with st.container(border=True):
    st.subheader('Canais oficiais')
    email = os.getenv('AQUASENTINEL_CONTACT_EMAIL', '').strip()
    url = os.getenv('AQUASENTINEL_CONTACT_URL', '').strip()
    ativo = False
    if re.fullmatch(r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}', email):
        st.link_button('Enviar e-mail à equipe', 'mailto:' + email)
        ativo = True
    if urlparse(url).scheme == 'https' and urlparse(url).netloc:
        st.link_button('Abrir canal oficial do projeto', url)
        ativo = True
    if not ativo:
        st.info('Os canais de atendimento ainda estão sendo definidos pela equipe. '
                'Nenhum formulário de mensagem está ativo nesta página.')
    st.write('Ao pedir uma correção, informe o ID do registro e descreva o que precisa ser conferido. '
             'Não envie senhas nem o código privado do recibo em canais públicos.')
with st.container(border=True):
    st.subheader('Como colaborar')
    st.write('Você pode observar com segurança, participar de monitoramentos, contribuir com documentação '
             'ou propor parcerias de pesquisa e educação ambiental quando os canais estiverem disponíveis.')
    st.page_link('app_pages/como_funciona.py', label='Ver como participar')
rodape()
