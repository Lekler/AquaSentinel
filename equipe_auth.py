"""Session-only team authentication; invalidated by expiry or password rotation."""
import hashlib
import hmac
import os
import time
from interface_idioma import st
from i18n import texto


def autenticado():
    senha = os.environ.get('AQUASENTINEL_REVIEW_PASSWORD', '')
    sessao = st.session_state.get('equipe_auth') or {}
    ok = bool(senha) and time.time() < sessao.get('expira', 0) and hmac.compare_digest(
        sessao.get('assinatura', ''), hashlib.sha256(senha.encode()).hexdigest())
    if not ok:
        st.session_state.pop('equipe_auth', None)
    return ok


def entrada():
    if autenticado():
        if st.button(texto('Sair da área da equipe', 'Sign out of team area'), key='equipe-sair'):
            st.session_state.pop('equipe_auth', None)
            st.rerun()
        return True
    with st.form('equipe-login', clear_on_submit=True):
        senha = st.text_input(texto('Senha', 'Password'), type='password', key='senha_revisao')
        entrar = st.form_submit_button(texto('Entrar', 'Sign in'))
    if entrar:
        with st.spinner(texto('Entrando…', 'Signing in…')):
            configurada = os.environ.get('AQUASENTINEL_REVIEW_PASSWORD', '')
            if configurada and hmac.compare_digest(senha.encode(), configurada.encode()):
                st.session_state['equipe_auth'] = {
                    'assinatura': hashlib.sha256(configurada.encode()).hexdigest(),
                    'expira': time.time() + 3600,
                }
                st.rerun()
            st.error(texto('Não foi possível entrar. Confira a senha com a equipe.', 'Unable to sign in. Check the password with the team.'))
    return False
