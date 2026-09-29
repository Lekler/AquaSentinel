from interface_idioma import st
from registro_visual import cabecalho, rodape

cabecalho('Como funciona', 'Da observação segura ao acompanhamento de ações.', False,
          'How it works', 'From safe observation to action follow-up.', '/como-funciona')
from home_visual import tutorial_ilustrado
st.html(tutorial_ilustrado())

etapas = [('Foto', 'Tire uma foto de um ponto seguro ou envie JPG, PNG ou WEBP de até 12 MB.'),
 ('IA', 'A inteligência artificial ajuda a identificar os resíduos visíveis na sua foto.'),
 ('Localização',
  'É só marcar o local no mapa, usando o GPS ou ajustando o ponto manualmente, conferir o endereço e '
  'pronto!'),
 ('Verificação',
  'O nosso sistema confere as informações registradas e compara a foto com as que já foram enviadas para '
  'evitar repetições.'),
 ('Revisão',
  'Confira os dados, autorize a publicação e envie seu registro. Pronto! Você acaba de dar uma mãozinha para '
  'cuidar das nossas águas.'),
 ('Explore o mapa',
  'Depois de verificados e autorizados, os registros aparecem no mapa. Você pode explorar onde há lixo '
  'observado e também quais áreas ainda precisam de mais registros.'),
 ('Histórico', 'Consulte dias observados, níveis anteriores, fotografias e a página do local.'),
 ('Pontos de atenção',
  'Quando os registros mostram lixo repetidamente em uma mesma região, o AquaSentinel pode destacá-lo como '
  'um ponto que merece atenção. Essa indicação considera quando e com que frequência as observações foram '
  'feitas.'),
 ('Acompanhe as ações!',
  'Depois de uma ação de limpeza, a equipe pode registrar o que foi feito e acompanhar novas fotos do local. '
  'Assim, todos conseguem ver o antes e o depois e observar como a área muda com o tempo.')]
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
