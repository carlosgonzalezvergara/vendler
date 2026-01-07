import streamlit as st
import aktionsart_es
import aktionsart_en
import ls
import info

# Configuración de la página (Sin barra lateral)
st.set_page_config(
    page_title="Vendler - RRG Suite", 
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 1. GESTIÓN DE ESTADO ---

if 'lang' not in st.session_state:
    st.session_state.lang = 'EN'

if 'seccion' not in st.session_state:
    st.session_state.seccion = 'home'

# --- 2. FUNCIONES DE CONTROL (Callbacks) ---

def cambiar_seccion(nueva_seccion):
    # Limpiar variables del módulo de destino para empezar desde cero
    if nueva_seccion == 'akt':
        # Variables de aktionsart_es
        for key in ['akt_paso', 'historial', 'rasgos', 'datos', 'oracion_original', 
                    'oracion_actual', 'clausula_limpia', 'variante_no_causativa', 'reformulacion']:
            if key in st.session_state:
                del st.session_state[key]
        # Variables de aktionsart_en
        for key in ['akt_step', 'history', 'features', 'data', 'original_clause', 
                    'current_clause', 'clean_clause', 'non_causative_variant', 'paraphrase']:
            if key in st.session_state:
                del st.session_state[key]
    elif nueva_seccion == 'ls':
        # Variables de ls_gen_es
        for key in list(st.session_state.keys()):
            if key.startswith('ls_'):
                del st.session_state[key]
    
    st.session_state.seccion = nueva_seccion

def cambiar_idioma():
    st.session_state.lang = 'ES' if st.session_state.lang == 'EN' else 'EN'

# --- 3. DICCIONARIO DE TEXTOS ---
textos = {
    'ES': {
        'titulo': "Vendler",
        'subtitulo': "Asistente para la detección de aktionsart y formalización de estructuras lógicas en RRG",
        'presentacion': """
        **Vendler** es una herramienta computacional desarrollada en Python pensada con el propósito de asistir en la detección del aktionsart (aspecto léxico) de predicados en español y en la formalización de sus estructuras lógicas dentro del marco teórico de la Gramática de Papel y Referencia (*Role and Reference Grammar*, RRG).

        El programa está diseñado para facilitar tanto la investigación lingüística como la enseñanza avanzada de gramática y semántica. Así, implementa en forma interactiva las principales pruebas diagnósticas de compatibilidad morfosintáctica del español que permiten determinar la clase aspectual de un predicado y generar su correspondiente representación lógica.

        El sistema produce como resultado una clasificación aspectual y una estructura lógica formalizada, siguiendo las reflexiones y la notación propuestas por Van Valin y LaPolla (1997), Van Valin (2005) y Van Valin (2023).

        **Nota sobre funcionalidades:** Esta versión en español permite tanto la identificación del aktionsart como la generación asistida de la estructura lógica (LS). La versión en inglés, sin embargo, actualmente solo incluye el asistente para la detección de aktionsart.
        """,
        'btn_akt': "Detector de aktionsart",
        'btn_ls': "Estructuras lógicas",
        'btn_info': "Información",
        'btn_volver': "Volver al menú de inicio",
        'desc_akt': "Pruebas diagnósticas interactivas para determinar la clase aspectual.",
        'desc_ls': "Generación formal de la estructura lógica (LS) en español.",
        'desc_info': "Créditos, bibliografía y contacto institucional.",
        'lang_label': "Switch to English"
    },
    'EN': {
        'titulo': "Vendler",
        'subtitulo': "Assistant for aktionsart detection and logical structure formalization in RRG",
        'presentacion': """
        **Vendler** is a computational tool developed in Python designed to assist in the detection of the *Aktionsart* (lexical aspect) of predicates and in the formalization of their logical structures within the theoretical framework of Role and Reference Grammar (RRG).

        The program is designed to facilitate both linguistic research and advanced teaching of grammar and semantics. It interactively implements the main morphosyntactic compatibility diagnostics that allow for determining the aspectual class of a predicate and generating its corresponding logical representation.

        The system produces an aspectual classification and a formalized logical structure as a result, following the reflections and notation proposed by Van Valin and LaPolla (1997), Van Valin (2005), and Van Valin (2023).

        **Note on features:** Please note that the English version currently only includes the assistant for aktionsart detection. The formalization of logical structures (LS) is available exclusively in the Spanish version of this program.
        """,
        'btn_akt': "Aktionsart Detector",
        'btn_ls': None, 
        'btn_info': "Information",
        'btn_volver': "Back to Home",
        'desc_akt': "Interactive diagnostic tests to determine the aspectual class.",
        'desc_ls': None,
        'desc_info': "Credits, bibliography, and institutional contact info.",
        'lang_label': "Cambiar a español",
        'footer': "Carlos González Vergara | cgonzalv@uc.cl"
    }
}

L = textos[st.session_state.lang]

# --- 4. CABECERA Y BOTÓN DE IDIOMA ---

col_tit, col_btn = st.columns([0.7, 0.3])
with col_tit:
    st.image("vendler.png", width=300)
    st.caption(L['subtitulo'])
with col_btn:
    st.button(L['lang_label'], on_click=cambiar_idioma, key="lang_btn", use_container_width=True)

# Botón para volver si NO estamos en el home
if st.session_state.seccion != 'home':
    st.button(L['btn_volver'], on_click=cambiar_seccion, args=('home',), key="back_home_btn")

st.divider()

# --- 5. RENDERIZADO DE CONTENIDO ---

if st.session_state.seccion == 'home':
    st.markdown(L['presentacion'])
    st.divider()
    
    # Menú visual con botones grandesa
    if st.session_state.lang == 'ES':
        c1, c2, c3 = st.columns(3)
        with c1:
            st.button(L['btn_akt'], key="go_akt_es", use_container_width=True, on_click=cambiar_seccion, args=('akt',))
            st.caption(L['desc_akt'])
        with c2:
            st.button(L['btn_ls'], key="go_ls_es", use_container_width=True, on_click=cambiar_seccion, args=('ls',))
            st.caption(L['desc_ls'])
        with c3:
            st.button(L['btn_info'], key="go_info_es", use_container_width=True, on_click=cambiar_seccion, args=('info',))
            st.caption(L['desc_info'])
    else:
        c1, c2 = st.columns(2)
        with c1:
            st.button(L['btn_akt'], key="go_akt_en", use_container_width=True, on_click=cambiar_seccion, args=('akt',))
            st.caption(L['desc_akt'])
        with c2:
            st.button(L['btn_info'], key="go_info_en", use_container_width=True, on_click=cambiar_seccion, args=('info',))
            st.caption(L['desc_info'])

    st.divider()
    st.caption("by Carlos González Vergara (__cgonzalv@uc.cl__)")

    # Lógica para cargar y mostrar el icono de Creative Commons
    try:
        with open("cc_icon.png", "rb") as f:
            import base64
            img_data = base64.b64encode(f.read()).decode()
        st.markdown(
            f'<a href="https://creativecommons.org/licenses/by-nc-nd/4.0/" target="_blank">'
            f'<img src="data:image/png;base64,{img_data}" alt="CC BY-NC-ND 4.0" width="88"></a>',
            unsafe_allow_html=True,
        )
    except Exception:
        st.markdown("[CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/)")

elif st.session_state.seccion == 'akt':
    if st.session_state.lang == 'ES':
        aktionsart_es.mostrar_detector_es()
    else:
        aktionsart_en.mostrar_detector_en()

elif st.session_state.seccion == 'ls':
    ls.mostrar_asistente_ls()

elif st.session_state.seccion == 'info':
    info.mostrar_info()

# Ocultar la barra lateral por CSS para mayor limpieza
st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            display: none;
        }
    </style>
    """, unsafe_allow_html=True)