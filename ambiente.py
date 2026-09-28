"""Contexto ambiental declarado, sem inferência clínica ou efeito nos índices."""
SINAIS = ['Animal próximo ao resíduo', 'Vegetação', 'Fauna aquática', 'Aves',
          'Espuma', 'Mancha superficial', 'Possível descarga/efluente', 'Outro sinal ambiental']
SIMBOLOS = {'Sem resíduos': '○', 'Pouco': '●', 'Moderado': '▲', 'Muito poluído': '◆', 'Bloqueando': '■'}


def validar_contexto(sinais, detalhe=''):
    if not isinstance(sinais, list) or any(s not in SINAIS for s in sinais) or len(detalhe) > 500:
        raise ValueError('Confira as observações ambientais e o limite de 500 caracteres.')
    return {'sinais': list(dict.fromkeys(sinais)), 'detalhe': detalhe.strip(),
            'tipo': 'observacao_ambiental_declarada', 'versao': 'one-health-context-v1'}


def mostrar_contexto(registro):
    from interface_idioma import st
    contexto = registro.get('contexto_ambiental') or {}
    sinais = contexto.get('sinais', [])
    with st.expander('One Health · observações ambientais'):
        a, b, c = st.columns(3)
        a.markdown('**Ambiente**')
        a.write(', '.join(s for s in sinais if s not in SINAIS[:4]) or 'Não informado')
        b.markdown('**Fauna / ecossistema**')
        b.write(', '.join(s for s in sinais if s in SINAIS[:4]) or 'Não informado')
        c.markdown('**Dimensão humana**')
        c.write('Participação e cuidado seguro com o território. Não são coletados sintomas ou diagnósticos.')
        if contexto.get('detalhe'):
            st.text(contexto['detalhe'])
        st.caption('Sinais declarados por quem observou, sem confirmação de causa, contaminação ou doença. '
                   'Campo vazio significa não informado. Estes sinais não alteram os índices.')
