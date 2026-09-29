"""Rubrica transparente de qualidade documental, não probabilidade de verdade."""
import math

VERSAO = 'aquaverify-v1'
AVISO = ('AquaVerify avalia qualidade e completude da evidência. Não é probabilidade '
         'de a denúncia ser verdadeira, autenticação da foto ou medida de poluição.')


def numero(valor, padrao=0):
    try:
        valor = float(valor)
        return valor if math.isfinite(valor) else padrao
    except (ValueError, TypeError):
        return padrao


def avaliar(r):
    itens = []
    def item(nome, pontos, maximo, motivo):
        itens.append({'Critério': nome, 'Pontos': pontos, 'Máximo': maximo, 'Motivo': motivo})
    valida = r.get('imagem_valida') is True
    item('Imagem válida', 20 if valida else 0, 20,
         'Arquivo decodificado e validado' if valida else 'Validação indisponível neste registro legado')
    dims = r.get('dimensoes_originais') or r.get('dimensoes') or [0, 0]
    minimo = min(numero(x) for x in dims) if len(dims) == 2 else 0
    item('Resolução', 10 if minimo >= 480 else 5 if minimo >= 240 else 0, 10,
         f'Menor lado disponível: {minimo:.0f} px; 480+ recebe 10 pontos, 240–479 recebe 5')
    total = int(numero(r.get('total')))
    item('Presença de detecção', 10 if total > 0 else 0, 10,
         f'{total} objetos; ausência de detecção não invalida a observação')
    conf = max(0, min(100, numero(r.get('confianca_media'))))
    item('Confiança da IA', round(conf*.15, 1) if total else 0, 15,
         f'Média {conf:.1f}%; contribuição proporcional, não autenticidade')
    gps = r.get('gps') or {}
    gps_usado = (r.get('origem_localizacao') == 'geolocalizacao_navegador_confirmada'
                 and gps.get('latitude') == r.get('latitude') and gps.get('longitude') == r.get('longitude'))
    item('Localização', 10 if gps_usado else 3, 10,
         'GPS informado pelo navegador e confirmado' if gps_usado else 'Coordenadas manuais/ajustadas ou origem não disponível')
    precisao = numero(gps.get('accuracy'), -1)
    item('Precisão do GPS', (5 if 0 <= precisao <= 50 else 2 if 50 < precisao <= 200 else 0) if gps_usado else 0, 5,
         f'Precisão declarada: {precisao:.0f} m' if gps_usado and precisao >= 0 else 'Precisão de GPS indisponível')
    sim = r.get('similaridade') or {}
    pendente = bool(sim.get('quantidade')) and r.get('similaridade_decisao') != 'independente'
    indice_completo = sim.get('verificada') and sim.get('sem_indice', 0) == 0
    informativa = bool((r.get('phash') or {}).get('principal'))
    item('Duplicidade e similaridade', 10 if indice_completo and informativa and not pendente else 0, 10,
         'Sem correspondência pendente; SHA-256 e pHash consultados' if indice_completo and informativa and not pendente
         else 'Similaridade pendente, índice incompleto ou imagem pouco informativa; não comprova reutilização')
    item('Data/hora disponível', 5 if r.get('registrado_em') else 0, 5,
         ('Data de envio registrada pelo servidor; ' + (f"EXIF de captura disponível: {r['captura_exif']} (não autenticado)"
          if r.get('captura_exif') else 'data de captura indisponível')) if r.get('registrado_em')
         else 'Data de envio será registrada ao salvar')
    item('Revisão humana', 15 if r.get('revisao') == 'validado' else 0, 15,
         'Validado pela equipe' if r.get('revisao') == 'validado' else 'Pendente ou rejeitado; exige avaliação da equipe')
    score = round(sum(i['Pontos'] for i in itens), 1)
    return {'versao': VERSAO, 'indice': score,
            'faixa': 'alta' if score >= 75 else 'média' if score >= 45 else 'baixa', 'criterios': itens}


def explicar(r):
    total = int(numero(r.get('total')))
    conf = numero(r.get('confianca_media'))
    motivos = []
    if total == 0:
        motivos.append('Nenhum objeto reconhecido; isso não comprova ausência de resíduos.')
    elif conf < 60:
        motivos.append('Confiança média abaixo do limiar de 60%; revisão de baixa confiança.')
    elif conf < 80:
        motivos.append('Confiança intermediária (60% a menos de 80%); conferir as detecções.')
    if r.get('possivel_limite'):
        motivos.append('Limite de detecções atingido; a contagem pode estar incompleta.')
    removidas = int(numero(r.get('duplicadas_removidas')))
    if removidas:
        motivos.append(f'{removidas} caixas sobrepostas removidas por IoU > 0,55, mantendo a mais confiante; '
                       'essa deduplicação vale dentro da foto, não entre fotos.')
    if (r.get('similaridade') or {}).get('quantidade'):
        motivos.append('Imagem possivelmente semelhante a uma anterior; conferir reutilização ou falso positivo.')
    if (r.get('similaridade') or {}).get('sem_indice', 0):
        motivos.append('Há fotos antigas sem índice pHash; comparação histórica incompleta.')
    if not r.get('waterbody_confirmado'):
        motivos.append('Identificação do corpo hídrico ainda precisa de confirmação pela equipe.')
    if r.get('origem_localizacao') != 'geolocalizacao_navegador_confirmada':
        motivos.append('Localização manual/ajustada: conferir se corresponde ao local informado.')
    motivos.append('Todos os relatos exigem revisão humana antes da publicação, mesmo com confiança alta.')
    estado = 'Revisão humana concluída.' if r.get('revisao') == 'validado' else 'Relato encaminhado para revisão humana ao salvar.'
    contagem = 'Foi identificado 1 objeto' if total == 1 else f'Foram identificados {total} objetos'
    confianca = f'A confiança média foi de {conf:.1f}%.' if total else 'Não há confiança média sem detecções.'
    return f'{contagem}. {confianca} {estado}', motivos
