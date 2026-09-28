from hashlib import sha256
import logging
import secrets
from interface_idioma import st
from interface_fotos import carregar_detector, mostrar_analise, downloads
from localizacao import obter_localizacao, aplicar_posicao
from relatos import NIVEIS, criar_registro, salvar_foto, obter_foto
from registro_visual import cabecalho, titulo, fotos, rodape
from i18n import texto
from corpos_hidricos import listar_corpos, obter_corpo


def limpar_foto():
    for chave in ('rascunho_foto', 'erro_foto', 'assinatura_foto', 'foto_salva_id', 'pacote_foto',
                  'foto_confirmacao', 'foto_publicacao', 'foto_nivel', 'foto_obs', 'foto_duplicada', 'foto_para_repetir', 'foto_recibo', 'foto_posicao_salva', 'foto-sinais', 'foto-ambiente'):
        st.session_state.pop(chave, None)


def nova_foto():
    limpar_foto()
    st.session_state.foto_epoch = st.session_state.get('foto_epoch', 0) + 1


@st.dialog(texto('Tire uma foto do local', 'Take a photo of the location'), width='large')
def abrir_camera():
    captura = st.camera_input(texto('Enquadre os resíduos e tire a foto', 'Frame the waste and take a photo'), key=f"captura_{st.session_state.get('camera_epoch', 0)}", resolution='1080p')
    st.caption(texto('Permita o acesso à câmera. No celular, acesse o site por HTTPS.', 'Allow camera access. On mobile, open the site over HTTPS.'))
    if captura is not None:
        if st.button(texto('Usar esta foto', 'Use this photo'), type='primary'):
            limpar_foto()
            st.session_state.foto_epoch += 1
            st.session_state.captura_pendente = captura.getvalue()
            st.rerun()
        if st.button(texto('Tirar novamente', 'Take another photo')):
            st.session_state.camera_epoch = st.session_state.get('camera_epoch', 0) + 1
            st.rerun(scope='fragment')
    if st.button(texto('Voltar sem trocar a foto', 'Go back without changing the photo')):
        st.rerun()


cabecalho(titulo_ingles='Report an occurrence', descricao_ingles='One photo helps care for our waters.')
st.warning('Observe com segurança: não entre na água, não toque em resíduos, não se aproxime de margem '
           'instável e não arrisque sua segurança para tirar uma foto.', icon=':material/health_and_safety:')
modo_registro = st.selectbox('Modo do registro', ['Oportunístico', 'Monitoramento estruturado'],
    index=1 if st.session_state.get('monitor_id') else 0, key='foto-modo')
sessao_ativa = None
if modo_registro == 'Monitoramento estruturado':
    from monitoramento import sessao_autorizada
    try:
        sessao_ativa = sessao_autorizada(st.session_state.get('monitor_id'), st.session_state.get('monitor_chave'))
        if sessao_ativa['status'] != 'em andamento':
            raise ValueError('A sessão já foi encerrada.')
        st.info(f"Sessão: {sessao_ativa['trecho_nome']} · {sessao_ativa['waterbody_id']}")
    except ValueError:
        st.warning('Inicie ou retome uma sessão em Monitoramento estruturado antes de salvar neste modo.')
        st.page_link('app_pages/monitoramento.py', label='Iniciar / retomar sessão')
        sessao_ativa = None
st.session_state.setdefault('foto_epoch', 0)
esquerda, direita = st.columns(2, gap='small')
with esquerda, st.container(key='photo-card'):
    titulo('1', texto('Adicione uma foto', 'Add a photo'), texto('Registre o lixo ou resíduo no rio, canal ou na Baía.', 'Report waste or debris in a river, canal or the bay.'))
    imagens = st.empty()
    progresso_foto = st.empty()
    with st.container(key='photo-actions'):
        camera, upload = st.columns(2)
        if camera.button(texto('Abrir câmera', 'Open camera'), icon=':material/photo_camera:', type='primary', width='stretch'):
            st.session_state.camera_epoch = st.session_state.get('camera_epoch', 0) + 1
            abrir_camera()
        with upload.popover(texto('Enviar foto', 'Upload photo'), icon=':material/upload:', width='stretch'):
            arquivo = st.file_uploader(texto('Envie uma foto do local', 'Upload a photo of the location'), type=['jpg','jpeg','png','webp'],
                max_upload_size=12, key=f'upload_{st.session_state.foto_epoch}', on_change=limpar_foto)
    st.caption(texto('JPG, PNG ou WEBP · Até 12 MB. A análise aparece ao lado da sua foto.', 'JPG, PNG or WEBP · Up to 12 MB. The analysis appears beside your photo.'))

pendente = st.session_state.pop('captura_pendente', None)
origem = st.session_state.pop('origem_repetir', 'Abrir câmera') if pendente is not None else 'Enviar foto'
if pendente is not None:
    from io import BytesIO
    arquivo = BytesIO(pendente)

if arquivo is not None:
    conteudo = arquivo.getvalue()
    assinatura = sha256(conteudo).hexdigest()
    if assinatura != st.session_state.get('assinatura_foto'):
        limpar_foto()
        st.session_state.assinatura_foto = assinatura
        st.session_state.foto_para_repetir = (conteudo, origem)
        progresso = progresso_foto.progress(0, text=texto('Etapa 1 de 3 · Preparando sua foto…', 'Step 1 of 3 · Preparing your photo…'))
        try:
            # Valida o arquivo antes de carregar o modelo.
            from visao import preparar_imagem, jpeg
            previa, _, _ = preparar_imagem(conteudo)
            with imagens.container():
                fotos({'foto': jpeg(previa), 'anotada': None}, analisando=True)
            progresso.progress(33, text=texto('Etapa 2 de 3 · Carregando o modelo de IA…', 'Step 2 of 3 · Loading the AI model…'))
            detector = carregar_detector()
            progresso.progress(66, text=texto('Etapa 3 de 3 · Identificando resíduos na foto…', 'Step 3 of 3 · Identifying waste in the photo…'))
            analise, foto, anotada = detector.analisar(conteudo)
            from similaridade import assinatura, comparar, data_captura_exif
            from relatos import listar_fotos
            analise.update(imagem_valida=True, phash=assinatura(foto),
                           captura_exif=data_captura_exif(conteudo))
            analise['similaridade'] = comparar(analise, listar_fotos())
            st.session_state.rascunho_foto = {'analise': analise, 'foto': foto, 'anotada': anotada,
                                             'origem': 'camera' if origem == 'Abrir câmera' else 'upload'}
        except (ValueError, FileNotFoundError) as exc:
            st.session_state.erro_foto = str(exc)
        except Exception:
            logging.exception('Falha ao executar o modelo de detecção')
            st.session_state.erro_foto = texto('Não foi possível executar o modelo. Confira a instalação e tente novamente.', 'The model could not be run. Check the installation and try again.')
        finally:
            progresso_foto.empty()

if st.session_state.get('erro_foto'):
    st.error(st.session_state.erro_foto)
    if st.button(texto('Tentar a análise novamente', 'Try the analysis again')):
        conteudo, origem_anterior = st.session_state.foto_para_repetir
        st.session_state.captura_pendente = conteudo
        st.session_state.origem_repetir = origem_anterior
        st.session_state.pop('assinatura_foto', None)
        st.rerun()

rascunho = st.session_state.get('rascunho_foto')
with imagens.container():
    fotos(rascunho)
if rascunho:
    with esquerda:
        mostrar_analise(rascunho['analise'], rascunho['anotada'], exibir_imagem=False)
        st.button(texto('Usar outra foto', 'Use another photo'), on_click=nova_foto, key='outra_foto')

with direita, st.container(key='location-card'):
    titulo('2', texto('Confirme sua localização', 'Confirm your location'), texto('Use o GPS e ajuste o ponto no mapa, se necessário.', 'Use GPS and adjust the point on the map if needed.'))
    posicao = obter_localizacao()
    if posicao:
        try:
            if aplicar_posicao(posicao):
                st.rerun()
        except (ValueError, TypeError, KeyError):
            st.warning('Localização inválida. Informe as coordenadas abaixo.')
    nome = st.text_input(texto('Nome do local, endereço ou ponto de referência', 'Location name, address or landmark'), max_chars=100,
                         placeholder='Ex.: Canal do Fundão, próximo à ponte', key='foto_nome', persist_state='session')
    catalogo = {c['id']: c for c in listar_corpos()}
    waterbody_id = st.selectbox('Corpo hídrico cadastrado', [None, *catalogo], key='foto-waterbody',
        disabled=bool(sessao_ativa),
        format_func=lambda i: f"{i} · {catalogo[i]['nome']}" if i else 'Não identificado — equipe fará a vinculação')
    st.caption(texto('Se souber, selecione o rio, canal ou baía. A equipe confirmará a escolha.', 'If known, select the river, canal or bay. The team will confirm your choice.'))
    with st.expander(texto('Ajustar coordenadas manualmente', 'Adjust coordinates manually')):
        col1, col2 = st.columns(2)
        lat = col1.number_input('Latitude', min_value=-90., max_value=90., value=None, format='%.6f',
                                key='foto_lat', persist_state='session')
        lon = col2.number_input('Longitude', min_value=-180., max_value=180., value=None, format='%.6f',
                                key='foto_lon', persist_state='session')

titulo('3', texto('Nível do local', 'Site level'), texto('Qual a quantidade de lixo ou resíduo no local?', 'How much waste or debris is at the location?'))
with st.form('enviar_foto'):
    niveis_exibicao = [texto(nivel, {'Sem resíduos': 'No visible waste', 'Pouco': 'Low', 'Moderado': 'Moderate', 'Muito poluído': 'Very polluted', 'Bloqueando': 'Blocking'}[nivel]) for nivel in NIVEIS]
    nivel_exibido = st.segmented_control(texto('Como está o local?', 'What is the site like?'), niveis_exibicao,
        key='foto_nivel', width='stretch')
    nivel = NIVEIS[niveis_exibicao.index(nivel_exibido)] if nivel_exibido else None
    st.caption(texto('Este nível é informado por você. A IA conta objetos visíveis; não determina se o canal está bloqueado.', 'You provide this level. AI counts visible objects; it does not determine whether the canal is blocked.'))
    with st.expander(texto('Informações opcionais', 'Optional information')):
        from ambiente import SINAIS, validar_contexto
        sinais = st.multiselect('One Health · sinais ambientais (opcional)', SINAIS, key='foto-sinais')
        detalhe_ambiental = st.text_area('Detalhe ambiental (opcional)', max_chars=500, key='foto-ambiente')
        observacoes = st.text_area(texto('Observações (opcional)', 'Notes (optional)'), max_chars=500, key='foto_obs',
                                  placeholder='Ex.: acúmulo próximo à margem, cheiro forte…')
    local_confirmado = st.checkbox(texto('Conferi a foto e a localização desta ocorrência.', 'I checked this report photo and location.'), key='foto_confirmacao')
    publicacao_autorizada = st.checkbox('Autorizo publicar a foto, o local e as coordenadas no mapa após revisão pela equipe.', key='foto_publicacao')
    enviar = st.form_submit_button(texto('Enviar ocorrência', 'Submit report'), type='primary', icon=':material/send:',
                                   disabled=not rascunho or bool(st.session_state.get('foto_salva_id')))

if enviar:
    try:
        if not rascunho:
            raise ValueError('Adicione e analise uma foto antes de enviar.')
        if not local_confirmado:
            raise ValueError('Confirme a foto e a localização antes de enviar.')
        if not publicacao_autorizada:
            raise ValueError('Autorize a publicação no mapa para enviar o relato.')
        if modo_registro == 'Monitoramento estruturado' and not sessao_ativa:
            raise ValueError('Inicie uma sessão de monitoramento antes de salvar.')
        registro = criar_registro(rascunho['analise'], nome, lat, lon, nivel, observacoes, rascunho['origem'])
        from ciclo import hash_chave
        recibo = secrets.token_urlsafe(24)
        registro['recibo_hash'] = hash_chave(recibo)
        registro['consentimento_publicacao'] = True
        registro['contexto_ambiental'] = validar_contexto(sinais, detalhe_ambiental)
        if waterbody_id:
            corpo = obter_corpo(waterbody_id)
            registro.update(waterbody_id=corpo['id'], waterbody_nome=corpo['nome'], waterbody_confirmado=False)
        gps = st.session_state.get('foto_gps')
        if gps and lat == gps['latitude'] and lon == gps['longitude']:
            registro['origem_localizacao'] = 'geolocalizacao_navegador_confirmada'
            registro['gps'] = gps
        salvo, novo = salvar_foto(registro, rascunho['foto'], rascunho['anotada'],
            sessao_id=sessao_ativa['id'] if sessao_ativa else None,
            sessao_chave=st.session_state.get('monitor_chave') if sessao_ativa else None)
        if novo:
            st.session_state.foto_recibo = recibo
        st.session_state.foto_salva_id = salvo['id']
        st.session_state.foto_posicao_salva = {'latitude': salvo['latitude'], 'longitude': salvo['longitude']}
        st.session_state.foto_duplicada = not novo
        st.rerun()
    except (ValueError, OSError) as exc:
        st.error(f'Não foi possível salvar: {exc}')

if st.session_state.get('foto_salva_id'):
    try:
        salvo, foto, anotada = obter_foto(st.session_state.foto_salva_id)
        if st.session_state.get('foto_duplicada'):
            st.warning('Esta imagem já foi registrada. Mostramos o registro original; nada foi duplicado ou sobrescrito.')
        from resultado_visual import resumo_salvo
        resumo_salvo(salvo)
        if st.session_state.get('foto_recibo'):
            with st.container(border=True, key='resultado-recibo'):
                info, acao = st.columns([2.2, 1], vertical_alignment='center')
                with info:
                    st.subheader('Recibo de acompanhamento', icon=':material/receipt_long:')
                    st.caption('Guarde o recibo antes de enviar outra foto. O código permite consultar seu registro mesmo antes da publicação.')
                with acao:
                    st.download_button('Guardar recibo de acompanhamento',
                        f"ID: {salvo['id']}\nCódigo privado: {st.session_state.foto_recibo}\nConsulte em Acompanhar meu registro.\n",
                        file_name=f"recibo-{salvo['id'][:8]}.txt", mime='text/plain',
                        type='primary', icon=':material/receipt_long:', width='stretch')
        with st.container(border=True, key='resultado-acoes'):
            st.subheader('Outras ações', icon=':material/link:')
            st.page_link('app_pages/acompanhamento.py', label='Acompanhar meu registro', icon=':material/description:')
            st.page_link('app_pages/dados.py', label='Exportar meus dados em CSV, Excel, JSON ou GeoJSON', icon=':material/download:')
        from ciclo import feedback
        from relatos import listar_fotos
        with st.container(key='resultado-status'):
            for mensagem in feedback(salvo, listar_fotos()):
                st.info(f'**{mensagem}**', icon=':material/check_circle:')
        if salvo.get('modo') == 'estruturado':
            st.page_link('app_pages/monitoramento.py', label='Voltar à sessão para adicionar fotos ou encerrar')
        with st.container(border=True, key='resultado-downloads'):
            titulo_downloads, botoes_downloads = st.columns([1, 3], vertical_alignment='top')
            titulo_downloads.subheader('Downloads', icon=':material/download:')
            with botoes_downloads:
                downloads(salvo, foto, anotada, 'registro')
        if st.button(texto('Ir para o mapa', 'Go to the map'), key='foto_abrir_mapa', icon=':material/map:', type='primary'):
            st.switch_page('app_pages/mapa.py')
    except (ValueError, OSError) as exc:
        st.error(f'Não foi possível abrir o registro: {exc}')
st.caption(texto('Fotos e localização são guardadas no banco do projeto. O mapa carrega recursos externos.', 'Photos and location are stored in the project database. The map loads external resources.'))

rodape()
