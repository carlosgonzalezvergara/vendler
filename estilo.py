"""Estilo visual común de la suite Vendler.

Todos los módulos (vendler.py, aktionsart_es.py, aktionsart_en.py, ls.py e
info.py) toman de aquí colores, tipografías y CSS, de modo que cualquier
ajuste visual se hace en un solo lugar.

Principios:
- Un solo color de acento, el azul marino del logo, para la estructura
  lógica, las acciones principales y los títulos del panel.
- El verde del logo se reserva para los resultados: el rasgo que arroja cada
  prueba del detector y el aktionsart final.
- Toda la interfaz usa tipografía sin serifas; la notación formal se
  distingue por tamaño, color y fondo, no por familia tipográfica.
- Las preguntas se presentan como texto; las cajas de color quedan para
  advertencias y errores.

El color de los botones principales, casillas y botones de opción se define
en .streamlit/config.toml (primaryColor), que debe coincidir con MARINO.
"""

import streamlit as st

# --- Paleta (derivada del logo) ---
MARINO = "#1A2B3E"          # acento principal (logo)
MARINO_MEDIO = "#2F5379"     # variante clara: rótulos, botones secundarios
MARINO_TINTE = "#E7EDF4"    # fondo de la estructura lógica y del panel
VERDE = "#4DAF81"           # verde del logo: resultados
VERDE_OSCURO = "#1F6344"    # texto de resultados (contraste suficiente sobre el tinte)
VERDE_TINTE = "#E6F5ED"     # fondo de resultados
TEXTO_SECUNDARIO = "#5B6573"
BORDE = "#D5DEE8"

# --- Tipografía de la notación formal ---
# Sin serifas, como el resto de la interfaz; se distingue por tamaño y color.
FUENTE_NOTACION = '"Source Sans 3", "Source Sans Pro", "Helvetica Neue", Arial, sans-serif'

_CSS = f"""
<style>

/* --- Estructura lógica en el área principal --- */
.ls-resultado {{
    font-family: {FUENTE_NOTACION};
    font-size: 1.3rem;
    line-height: 1.5;
    color: {MARINO};
    padding: 14px 18px;
    background-color: {MARINO_TINTE};
    border-left: 4px solid {MARINO};
    border-radius: 2px;
    margin: 0 0 16px 0;
    overflow-wrap: anywhere;
}}

/* Rótulo de notación pegado al cuadro que le corresponde */
.ls-rotulo {{
    font-size: 0.8rem;
    color: {MARINO_MEDIO};
    margin: 0 0 3px 2px;
}}
.ls-resultado + .ls-rotulo {{
    margin-top: 4px;
}}

/* --- Panel lateral de datos (estructuras lógicas y detectores) --- */
.info-panel-title, .header-analisis {{
    font-size: 1.05rem;
    font-weight: 600;
    color: {MARINO};
    padding-bottom: 8px;
    margin-bottom: 14px;
    border-bottom: 2px solid {VERDE};
}}
.info-item {{
    margin-bottom: 14px;
}}
.info-label {{
    color: {MARINO_MEDIO};
    font-size: 0.8rem;
    font-weight: 600;
    margin-bottom: 2px;
}}
.info-value {{
    font-size: 0.95rem;
    line-height: 1.4;
}}
.info-value-ls {{
    font-family: {FUENTE_NOTACION};
    font-size: 1.02rem;
    line-height: 1.45;
    color: {MARINO};
    overflow-wrap: anywhere;
}}
.info-value-resultado {{
    color: {VERDE_OSCURO};
    font-weight: 700;
    font-size: 1.05rem;
}}
.notacion-rotulo {{
    font-family: inherit;
    font-size: 0.75rem;
    color: {MARINO_MEDIO};
    margin: 6px 0 1px 0;
}}

/* --- Rasgos del detector ([+dinámico], etc.) --- */
.rasgo-elegante {{
    display: inline-block;
    font-family: {FUENTE_NOTACION};
    font-size: 1rem;
    color: {MARINO};
    background-color: {MARINO_TINTE};
    padding: 2px 9px;
    border: 1px solid {BORDE};
    border-radius: 3px;
    margin: 3px;
}}
.rasgo-nuevo {{
    animation: destello-rasgo 2.4s ease-out 1;
}}
@keyframes destello-rasgo {{
    0%   {{ background-color: {VERDE_TINTE}; border-color: {VERDE}; color: {VERDE_OSCURO}; }}
    65%  {{ background-color: {VERDE_TINTE}; border-color: {VERDE}; color: {VERDE_OSCURO}; }}
    100% {{ background-color: {MARINO_TINTE}; border-color: {BORDE}; color: {MARINO}; }}
}}
@media (prefers-reduced-motion: reduce) {{
    .rasgo-nuevo {{
        animation: none;
        border-color: {VERDE} !important;
        background-color: {VERDE_TINTE} !important;
    }}
}}

/* --- Resultados del detector: rasgo de cada prueba y aktionsart final --- */
.aviso-confirmacion, .aviso-resultado {{
    background-color: {VERDE_TINTE};
    border-left: 4px solid {VERDE};
    color: {VERDE_OSCURO};
    padding: 26px 24px;
    border-radius: 2px;
    margin: 10px 0 25px 0;
    font-size: 1.35em;
    font-weight: 600;
    text-align: center;
    line-height: 1.35;
}}

/* --- Tabla de resumen del detector --- */
.tabla-analisis {{
    width: 60%;
    margin: 10px 0 20px 0;
    border-collapse: collapse;
    font-size: 0.95em;
}}
.tabla-analisis th {{
    text-align: left;
    padding: 8px;
    border-bottom: 2px solid {BORDE};
    color: {TEXTO_SECUNDARIO};
}}
.tabla-analisis td {{
    padding: 8px;
    border-bottom: 1px solid {BORDE};
}}

/* --- Botones de servicio: idioma, volver al inicio, reiniciar ---
   Son botones, no enlaces, pero en un azul más claro que el de las acciones
   principales, para que la jerarquía siga siendo clara.
   Streamlit asigna la clase st-key-<clave> al contenedor de cada widget con
   clave. Si una versión antigua no la asigna, estos botones simplemente
   conservan el aspecto normal. */
.st-key-back_home_btn button,
.st-key-lang_btn button,
.st-key-nav_volver button,
.st-key-nav_back button,
[class*="st-key-nav_reset"] button {{
    background-color: {MARINO_TINTE};
    border: 1px solid {MARINO_MEDIO};
    color: {MARINO_MEDIO};
    font-weight: 600;
}}
.st-key-back_home_btn button:hover,
.st-key-lang_btn button:hover,
.st-key-nav_volver button:hover,
.st-key-nav_back button:hover,
[class*="st-key-nav_reset"] button:hover {{
    background-color: {MARINO_MEDIO};
    border-color: {MARINO_MEDIO};
    color: #ffffff;
}}
.st-key-back_home_btn button:focus-visible,
.st-key-lang_btn button:focus-visible,
.st-key-nav_volver button:focus-visible,
.st-key-nav_back button:focus-visible,
[class*="st-key-nav_reset"] button:focus-visible {{
    outline: 2px solid {MARINO};
    outline-offset: 2px;
}}

/* --- Menú de la portada: los tres accesos, con borde de acento --- */
[class*="st-key-go_"] button {{
    border: 1px solid {MARINO_MEDIO};
    color: {MARINO};
    font-weight: 600;
}}
[class*="st-key-go_"] button:hover {{
    background-color: {MARINO_TINTE};
    border-color: {MARINO};
    color: {MARINO};
}}

/* --- Encabezados de sección del área principal --- */
h2, h3, h4 {{
    color: {MARINO};
}}

/* --- Aktionsart en el panel: es el resultado del detector, va en verde --- */
.info-value-akt {{
    color: {VERDE_OSCURO};
    font-weight: 700;
}}

/* --- Desplegables (nota teórica, exportación): título en el color de acento --- */
details summary, [data-testid="stExpander"] summary {{
    color: {MARINO};
    font-weight: 600;
}}

/* --- Separadores algo más presentes que el gris por omisión --- */
hr, [data-testid="stDivider"] hr {{
    border-color: {BORDE};
}}
</style>
"""


def aplicar_estilo() -> None:
    """Inyecta el CSS común. Puede llamarse más de una vez sin efectos."""
    st.markdown(_CSS, unsafe_allow_html=True)


def dato_panel(etiqueta: str, valor_html: str, clase: str = "info-value") -> str:
    """HTML de un dato del panel lateral: rótulo y valor."""
    return (
        f'<div class="info-item">'
        f'<div class="info-label">{etiqueta}</div>'
        f'<div class="{clase}">{valor_html}</div>'
        f'</div>'
    )


def mostrar_dato_panel(etiqueta: str, valor_html: str, clase: str = "info-value") -> None:
    st.markdown(dato_panel(etiqueta, valor_html, clase), unsafe_allow_html=True)


def lista_elegante(items: list) -> None:
    """Lista de ejemplos con viñetas en el color de acento."""
    html_items = "".join(
        f'<div style="display: flex; align-items: flex-start; margin-bottom: 8px;">'
        f'<div style="color: {MARINO}; margin-right: 10px; font-weight: bold;">•</div>'
        f'<div style="line-height: 1.4;">{item}</div></div>'
        for item in items
    )
    st.markdown(f'<div style="margin-bottom: 15px;">{html_items}</div>', unsafe_allow_html=True)
