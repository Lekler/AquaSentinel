import streamlit as st
from registro_visual import cabecalho, rodape

cabecalho('Como funciona', 'Da observação segura ao acompanhamento de ações.', False,
          'How it works', 'From safe observation to action follow-up.', '/como-funciona')
etapas = [
    ('Foto', 'Tire uma foto de um ponto seguro ou envie JPG, PNG ou WEBP de até 12 MB.'),
    ('IA', 'Confira os objetos detectados, a quantidade e a confiança. A IA pode errar.'),
    ('Localização', 'Use GPS ou ajuste o ponto manualmente. Confira o local e o nível observado.'),
    ('Evidência', 'AquaVerify avalia a qualidade documental. Hash e similaridade ajudam a localizar imagens repetidas.'),
    ('Revisão', 'Autorize a publicação e envie. A equipe avalia o registro, a localização e possíveis duplicidades.'),
    ('Mapa', 'Registros validados e autorizados aparecem no mapa. Condição e cobertura têm representações separadas.'),
    ('Histórico', 'Consulte dias observados, níveis anteriores, fotografias e a página do local.'),
    ('Hotspot', 'A recorrência, o tempo, o WPS e a qualidade sustentam uma classificação experimental de persistência.'),
    ('Ação', 'A equipe registra ações e acompanha novas observações. Compare antes e depois sem presumir causalidade.')]
st.html('<div class="fluxo-etapas" aria-label="Fluxo do registro">' +
        ''.join(f'<span>{i+1}. {titulo}</span>' for i, (titulo, _) in enumerate(etapas)) + '</div>')
for i, (titulo, descricao) in enumerate(etapas, 1):
    with st.container(border=True):
        st.subheader(f'{i:02d} · {titulo}')
        st.write(descricao)
st.info('Guarde o recibo privado após enviar. Ele permite acompanhar e exportar seu registro, mesmo antes da publicação.')
with st.container(horizontal=True):
    st.page_link('app_pages/registrar.py', label='Registrar uma observação', icon=':material/photo_camera:')
    st.page_link('app_pages/monitoramento.py', label='Iniciar monitoramento estruturado', icon=':material/timer:')
rodape()
