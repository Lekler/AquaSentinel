from interface_idioma import st
from home_visual import construir_home

st.html(construir_home(st.get_option('server.baseUrlPath')))
