import streamlit as st
import spacy
from dataclasses import dataclass
from enum import Enum
from typing import Optional

# --- 1. CLASES Y ENUMS ---

class Aktionsart(Enum):
    ESTADO = "estado"
    ESTADO_CAUSATIVO = "estado causativo"
    LOGRO = "logro"
    LOGRO_CAUSATIVO = "logro causativo"
    SEMELFACTIVO = "semelfactivo"
    SEMELFACTIVO_CAUSATIVO = "semelfactivo causativo"
    REALIZACION_ACTIVA = "realización activa"
    REALIZACION_ACTIVA_CAUSATIVA = "realización activa causativa"
    REALIZACION = "realización"
    REALIZACION_CAUSATIVA = "realización causativa"
    ACTIVIDAD = "actividad"
    ACTIVIDAD_CAUSATIVA = "actividad causativa"
    PROCESO = "proceso"
    PROCESO_CAUSATIVO = "proceso causativo"

@dataclass
class RasgosPred:
    causativo: Optional[bool] = None
    estativo: Optional[bool] = None
    puntual: Optional[bool] = None
    telico: Optional[bool] = None
    dinamico: Optional[bool] = None

@dataclass
class DatosClause:
    gerundio: str = ""
    participio: str = ""
    infinitivo: str = ""
    sujeto: str = ""
    complementos: str = ""
    persona_numero: str = "3s"

# --- 2. DICCIONARIOS Y AUXILIARES ---

IRREGULARES = {
    "abrir": {"pp": "abierto"}, "cubrir": {"pp": "cubierto"},
    "decir": {"ger": "diciendo", "pp": "dicho"}, "escribir": {"pp": "escrito"},
    "hacer": {"pp": "hecho"}, "freír": {"pp": "frito"},
    "imprimir": {"pp": "impreso"}, "morir": {"ger": "muriendo", "pp": "muerto"},
    "poner": {"pp": "puesto"}, "proveer": {"pp": "provisto"},
    "romper": {"pp": "roto"}, "satisfacer": {"pp": "satisfecho"},
    "soltar": {"pp": "suelto"}, "ver": {"pp": "visto"},
    "volver": {"pp": "vuelto"}, "ir": {"ger": "yendo", "pp": "ido"},
    "ser": {"ger": "siendo", "pp": "sido"}, "pudrir": {"pp": "podrido"},
    "leer": {"ger": "leyendo", "pp": "leído"}, "traer": {"ger": "trayendo", "pp": "traído"},
    "caer": {"ger": "cayendo", "pp": "caído"}, "oír": {"ger": "oyendo", "pp": "oído"},
    "pedir": {"ger": "pidiendo"}, "sentir": {"ger": "sintiendo"},
    "mentir": {"ger": "mintiendo"}, "seguír": {"ger": "siguiendo"},
    "conseguír": {"ger": "consiguiendo"}, "perseguir": {"ger": "persiguiendo"},
    "servir": {"ger": "sirviendo"}, "vestir": {"ger": "vistiendo"},
    "repetir": {"ger": "repitiendo"}, "elegir": {"ger": "elegiendo"},
    "corregir": {"ger": "corrigiendo"}, "reír": {"ger": "riendo"},
    "sonreír": {"ger": "sonriendo"}, "venir": {"ger": "viniendo"},
    "competir": {"ger": "compitiendo"}, "medir": {"ger": "midiendo"},
    "despedir": {"ger": "despidiendo"}, "impedir": {"ger": "impidiendo"},
    "dormir": {"ger": "durmiendo"}, "poder": {"ger": "pudiendo"}
}

ESTAR_PRETERITO = {'1s': "estuve", '2s': "estuviste", '3s': "estuvo", '1p': "estuvimos", '2p': "estuvieron", '3p': "estuvieron"}
ESTAR = {'1s': "estoy", '2s': "estás", '3s': "está", '1p': "estamos", '2p': "están", '3p': "están"}
ESTAR_SUBJUNTIVO = {'1s': "estuviera", '2s': "estuvieras", '3s': "estuviera", '1p': "estuviéramos", '2p': "estuvieran", '3p': "estuvieran"}
HABER = {'1s': "he", '2s': "has", '3s': "ha", '1p': "hemos", '2p': "han", '3p': "han"}
DEJAR = {'1s': "dejara", '2s': "dejaras", '3s': "dejara", '1p': "dejáramos", '2p': "dejaran", '3p': "dejaran"}

PERSONAS_DICT = {
    "1s": "Primera persona singular",
    "2s": "Segunda persona singular",
    "3s": "Tercera persona singular",
    "1p": "Primera persona plural",
    "2p": "Segunda persona plural",
    "3p": "Tercera persona plural"
}

@st.cache_resource
def load_nlp():
    try: return spacy.load("es_core_news_sm")
    except: return None

nlp = load_nlp()

def analizar_automaticamente(oracion, datos):
    if not nlp: return False, "", ""
    doc = nlp(oracion)
    verbo_token = next((t for t in doc if t.dep_ == "ROOT" and t.pos_ in ["VERB", "AUX"]), None)
    if not verbo_token:
        verbo_token = next((t for t in doc if t.pos_ in ["VERB", "AUX"]), None)
    if not verbo_token: return False, "", ""
    
    idx = verbo_token.i
    cliticos = [doc[i].text.lower() for i in range(idx-1, max(idx-5, -1), -1) if doc[i].pos_ == "PRON" and doc[i].text.lower() in ["me", "te", "se", "nos", "os", "le", "les", "lo", "los", "la", "las"]]
    cliticos.reverse()
    lema_limpio = verbo_token.lemma_.lower()
    texto_verbo = verbo_token.text.lower()
    
    PRETERITOS_FUERTES = {"estuv": "estar", "tuv": "tener", "anduv": "andar", "pud": "poder", "pus": "poner", "sup": "saber", "hic": "hacer", "hiz": "hacer", "quis": "querer", "vin": "venir", "dij": "decir", "traj": "traer"}
    for raiz, inf_real in PRETERITOS_FUERTES.items():
        if texto_verbo.startswith(raiz):
            lema_limpio = inf_real
            break
            
    suffix = "".join(cliticos)
    datos.infinitivo = lema_limpio + suffix
    ger, part = IRREGULARES.get(lema_limpio, {}).get("ger", ""), IRREGULARES.get(lema_limpio, {}).get("pp", "")
    
    if not ger:
        if lema_limpio.endswith("uir") and not lema_limpio.endswith(("guir", "quir", "güir")): ger = lema_limpio[:-2] + "yendo"
        elif lema_limpio.endswith("ar"): ger = lema_limpio[:-2] + "ando"
        elif lema_limpio.endswith(("er", "ir")): ger = lema_limpio[:-2] + "iendo"
    if not part:
        if lema_limpio.endswith("ar"): part = lema_limpio[:-2] + "ado"
        elif lema_limpio.endswith(("er", "ir")): part = lema_limpio[:-2] + "ido"
        
    datos.gerundio, datos.participio = ger, part
    
    if texto_verbo.endswith(("é", "í")): datos.persona_numero = "1s"
    elif texto_verbo.endswith(("aste", "iste", "as", "es")): datos.persona_numero = "2s"
    elif texto_verbo.endswith("ó"): datos.persona_numero = "3s"
    else:
        morph = verbo_token.morph.to_dict()
        p, n = morph.get("Person", "3"), morph.get("Number", "Sing")
        datos.persona_numero = {("1", "Sing"): "1s", ("2", "Sing"): "2s", ("3", "Sing"): "3s", ("1", "Plur"): "1p", ("2", "Plur"): "2p", ("3", "Plur"): "3p"}.get((p, n), "3s")
        
    datos.sujeto = doc[:idx].text.strip()
    datos.complementos = doc[idx+1:].text.strip()
    return True, verbo_token.text, lema_limpio

def construir_perif(tipo, datos):
    if tipo == 'gerundio_pret': v = ESTAR_PRETERITO.get(datos.persona_numero, "estuvo")
    elif tipo == 'gerundio_pres': v = ESTAR.get(datos.persona_numero, "está")
    elif tipo == 'gerundio_subj': v = ESTAR_SUBJUNTIVO.get(datos.persona_numero, "estuviera")
    elif tipo == 'participio': v = HABER.get(datos.persona_numero, "ha")
    elif tipo == 'infinitivo': return " ".join(p for p in [f"{DEJAR.get(datos.persona_numero, 'dejara')} de {datos.infinitivo}", datos.complementos] if p)
    aux = f"{v} {datos.gerundio}" if 'gerundio' in tipo else f"{v} {datos.participio}"
    return " ".join(p for p in [datos.sujeto, aux, datos.complementos] if p)

# --- NAVEGACIÓN ---
def ir_a(paso):
    st.session_state.historial.append(st.session_state.akt_paso)
    st.session_state.akt_paso = paso
    st.rerun()

def volver():
    if st.session_state.historial:
        paso_actual = st.session_state.akt_paso
        if paso_actual == 'limpieza':
            st.session_state.rasgos.causativo = None
            st.session_state.variante_no_causativa = ""
        elif paso_actual == 'estatividad':
            st.session_state.datos = DatosClause()
        elif paso_actual == 'puntualidad':
            st.session_state.rasgos.estativo = None
        elif paso_actual == 'telicidad':
            st.session_state.rasgos.puntual = None
        elif paso_actual == 'dinamicidad':
            st.session_state.rasgos.telico = None
        elif paso_actual == 'resultado':
            st.session_state.rasgos.dinamico = None
            
        st.session_state.akt_paso = st.session_state.historial.pop()
        st.rerun()

def reiniciar_analisis():
    for key in ['akt_paso', 'historial', 'rasgos', 'datos', 'oracion_original', 'oracion_actual', 'clausula_limpia', 'variante_no_causativa', 'reformulacion']:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

def botones_navegacion():
    st.write("---")
    c1, c2 = st.columns([1, 1])
    if c1.button("← Volver", use_container_width=True):
        volver()
    if c2.button("Iniciar nuevo análisis", use_container_width=True):
        reiniciar_analisis()

def lista_elegante(items: list):
    html_items = ""
    for item in items:
        html_items += f'<div style="display: flex; align-items: flex-start; margin-bottom: 8px;"><div style="color: #4A90E2; margin-right: 10px; font-weight: bold;">•</div><div style="line-height: 1.4;">{item}</div></div>'
    st.markdown(f'<div style="margin-bottom: 15px;">{html_items}</div>', unsafe_allow_html=True)

# --- 3. INTERFAZ ---

def mostrar_detector_es():
    st.markdown("""
        <style>
        div[data-testid="stElementContainer"] > div[style*="border: 1px solid"] {
            background-color: #fcfcfc;
            border: 1px solid #e0e0e0 !important;
            padding: 25px 25px 40px 25px;
            border-radius: 8px;
        }
        .header-analisis {
            color: #333333;
            font-size: 1.2em;
            font-weight: 600;
            border-bottom: 1px solid #eeeeee;
            margin-bottom: 20px;
            padding-bottom: 10px;
        }
        .rasgo-elegante {
            display: inline-block;
            background-color: #ffffff;
            color: #444444;
            padding: 4px 10px;
            border: 1px solid #cccccc;
            border-radius: 4px;
            margin: 3px;
            font-family: 'Courier New', Courier, monospace;
            font-weight: bold;
            font-size: 0.9em;
        }
        .tabla-analisis {
            width: 60%;
            margin-top: 10px;
            margin-bottom: 20px;
            border-collapse: collapse;
            font-size: 0.95em;
        }
        .tabla-analisis th {
            text-align: left;
            padding: 8px;
            border-bottom: 2px solid #e0e0e0;
            color: #666;
        }
        .tabla-analisis td {
            padding: 8px;
            border-bottom: 1px solid #eee;
        }
        </style>
    """, unsafe_allow_html=True)

    if 'akt_paso' not in st.session_state:
        st.session_state.akt_paso = 'inicio'
        st.session_state.historial = []
        st.session_state.rasgos = RasgosPred()
        st.session_state.datos = DatosClause()
        st.session_state.oracion_original = ""
        st.session_state.oracion_actual = ""
        st.session_state.clausula_limpia = ""
        st.session_state.variante_no_causativa = ""

    label_resultado = ""
    if st.session_state.akt_paso == 'resultado':
        res_r = st.session_state.rasgos
        if res_r.estativo: sub = "estado"
        elif res_r.puntual and res_r.telico: sub = "logro"
        elif res_r.puntual and not res_r.telico: sub = "semelfactivo"    
        elif not res_r.puntual and res_r.telico and res_r.dinamico: sub = "realización activa"
        elif not res_r.puntual and not res_r.telico and res_r.dinamico: sub = "actividad"
        elif not res_r.puntual and res_r.telico and not res_r.dinamico: sub = "realización"
        else: sub = "proceso"
        label_resultado = f"{sub} causativa" if res_r.causativo and sub in ["realización", "realización activa", "actividad"] else (f"{sub} causativo" if res_r.causativo else sub)

    col_izq, col_spacer, col_der = st.columns([0.6, 0.02, 0.38])

    with col_izq:
        if st.session_state.akt_paso == 'inicio':
            st.write("Este programa te ayudará a identificar el aktionsart del predicado principal en una cláusula.")
            st.write("Por favor, escribe una cláusula con el verbo que quieres probar conjugado en **pretérito** (ej.: *Pedro corrió hasta su casa*).")
            st.write("Si suena muy extraña, escríbela en **presente** (ej.: *María sabe inglés*).")
            with st.form(key="form_inicio_es"):
                oracion = st.text_input("Cláusula:")
                if st.form_submit_button("Comenzar el análisis"):
                    if oracion:
                        st.session_state.oracion_original = oracion
                        st.session_state.oracion_actual = oracion
                        ir_a('causatividad')

        elif st.session_state.akt_paso == 'causatividad':
            st.markdown("#### **Prueba de causatividad**")
            st.write(f"Intenta reformular *{st.session_state.oracion_actual}* siguiendo estos modelos:")
            lista_elegante([
                "El gato rompió el jarrón → El gato <b>hizo/causó que</b> el jarrón se rompiera",
                "Ana le dio un libro a Pepe → Ana <b>hizo/causó que</b> Pepe tuviera un libro"
            ])
            with st.form(key="form_caus_es"):
                reformula = st.text_input("Escribe tu reformulación:")
                c1, c2 = st.columns(2)
                if c1.form_submit_button("Siguiente"):
                    if not reformula.strip():
                        st.session_state.rasgos.causativo = False
                        ir_a('limpieza')
                    else:
                        st.session_state.reformulacion = reformula
                        ir_a('verificar_causa')
                if c2.form_submit_button("No es posible reformularla"):
                    st.session_state.rasgos.causativo = False
                    ir_a('limpieza')
            botones_navegacion()

        elif st.session_state.akt_paso == 'verificar_causa':
            st.write("Considera lo siguiente:")
            lista_elegante([
                f"<i>{st.session_state.reformulacion.capitalize()}</i> debe mantener el significado de <i>{st.session_state.oracion_actual}</i>.",
                f"<i>{st.session_state.reformulacion.capitalize()}</i> no debe añadir nuevos argumentos ni repetir otros ya existentes en <i>{st.session_state.oracion_actual}</i>.",
                "No debe tratarse de expresiones de consumo (<i>comer una manzana</i>) o creación (<i>escribir un cuento</i>)."
            ])
            st.write(f"¿*{st.session_state.reformulacion.capitalize()}* cumple con estos criterios?")
            c1, c2 = st.columns(2)
            if c1.button("Sí", use_container_width=True):
                ir_a('evento_basico')
            if c2.button("No", use_container_width=True):
                st.session_state.rasgos.causativo = False
                ir_a('limpieza')
            botones_navegacion()

        elif st.session_state.akt_paso == 'evento_basico':
            st.write("Escribe el evento o estado resultante sin la causa:")
            lista_elegante([
                "<i>El gato rompió el jarrón</i> → <i>el jarrón se rompió</i>",
                "<i>Ana le dio un libro a Pepe</i> → <i>Pepe tiene un libro</i>"
            ])
            with st.form(key="form_ev_bas_es"):
                ev = st.text_input("Escribe tu respuesta aquí:")
                c1, c2 = st.columns(2)
                if c1.form_submit_button("Siguiente", use_container_width=True):
                    if ev.strip():
                        st.session_state.rasgos.causativo = True
                        st.session_state.variante_no_causativa = ev
                        st.session_state.oracion_actual = ev
                        ir_a('limpieza')
                    else:
                        st.warning("Por favor, ingresa el evento o presiona 'No se me ocurre ninguno'")
                if c2.form_submit_button("No se me ocurre ninguno", use_container_width=True):
                    st.session_state.rasgos.causativo = False
                    ir_a('limpieza')
            botones_navegacion()

        elif st.session_state.akt_paso == 'limpieza':
            st.write(f"Esta es la cláusula a la que aplicaremos las pruebas: *{st.session_state.oracion_actual}*")
            st.write("Para que estas funcionen correctamente, la cláusula debe cumplir algunas condiciones formales. Asegúrate de que **no** tenga:")
            lista_elegante([
                "Expresiones de tiempo (ej: <i>ayer</i>, <i>siempre</i>, <i>el lunes</i>).",
                "Expresiones de modo (ej: <i>rápidamente</i>, <i>bien</i>, <i>mal</i>, <i>con calma</i>).",
                "Negaciones (ej: <i>no</i>, <i>tampoco</i>)."
            ])
            st.write("¿Tu cláusula contiene alguno de estos elementos?")
            c1, c2 = st.columns(2)
            if c1.button("Sí", use_container_width=True):
                ir_a('corregir_limpieza')
            if c2.button("No", use_container_width=True):
                st.session_state.clausula_limpia = st.session_state.oracion_actual
                ir_a('analisis_morph')
            botones_navegacion()

        elif st.session_state.akt_paso == 'corregir_limpieza':
            with st.form(key="form_limp_act_es"):
                nueva = st.text_input(f"Por favor, escribe *{st.session_state.oracion_actual}* de nuevo **sin** esos elementos (ej.: *Pedro corrió* en vez de *Pedro nunca corrió ayer*):")
                if st.form_submit_button("Actualizar"):
                    if nueva:
                        st.session_state.oracion_actual = nueva
                        st.session_state.clausula_limpia = nueva
                        ir_a('analisis_morph')
            botones_navegacion()

        elif st.session_state.akt_paso == 'analisis_morph':
            exito, v_vis, l_vis = analizar_automaticamente(st.session_state.oracion_actual, st.session_state.datos)
            if exito:
                st.write(f"Este es un análisis de algunos de los rasgos morfológicos y estructurales de **{st.session_state.oracion_actual}**")
                d = st.session_state.datos
                html_tabla = f"""
                <table class="tabla-analisis">
                    <tbody>
                        <tr><td><b>Verbo</b></td><td>{v_vis.lower()}</td></tr>
                        <tr><td><b>Infinitivo</b></td><td>{l_vis}</td></tr>
                        <tr><td><b>Gerundio</b></td><td>{d.gerundio}</td></tr>
                        <tr><td><b>Participio (masculino singular)</b></td><td>{d.participio}</td></tr>
                        <tr><td><b>Antes del verbo</b></td><td>{d.sujeto if d.sujeto else "no hay nada"}</td></tr>
                        <tr><td><b>Después del verbo</b></td><td>{d.complementos if d.complementos else "no hay nada"}</td></tr>
                    </tbody>
                </table>
                """
                st.markdown(html_tabla, unsafe_allow_html=True)
                st.write("¿Es correcto este análisis?")
                c1, c2 = st.columns(2)
                if c1.button("Sí", use_container_width=True): ir_a('estatividad')
                if c2.button("No", use_container_width=True): ir_a('manual_morph')
                botones_navegacion()
            else:
                ir_a('manual_morph')

        elif st.session_state.akt_paso == 'manual_morph':
            with st.form(key="form_m_save"):
                d = st.session_state.datos
                d.infinitivo = st.text_input(f"Escribe el **infinitivo** del verbo en *{st.session_state.oracion_actual}*, incluyendo los clíticos que haya:", d.infinitivo)
                d.gerundio = st.text_input(f"Escribe el **gerundio** del verbo en *{st.session_state.oracion_actual}*, sin clíticos:", d.gerundio)
                d.participio = st.text_input(f"Escribe el **participio** (masculino singular) del verbo en *{st.session_state.oracion_actual}*:", d.participio)
                d.sujeto = st.text_input(f"Escribe todo lo que hay **antes** del verbo en *{st.session_state.oracion_actual}*, incluyendo los clíticos, si los hay:", d.sujeto)
                d.complementos = st.text_input(f"Escribe todo lo que hay **después** del verbo en *{st.session_state.oracion_actual}*:", d.complementos)
                idx_actual = list(PERSONAS_DICT.keys()).index(d.persona_numero) if d.persona_numero in PERSONAS_DICT else 2
                d.persona_numero = st.selectbox(
                    "Selecciona la persona y número del verbo:", 
                    options=list(PERSONAS_DICT.keys()),
                    format_func=lambda x: PERSONAS_DICT[x],
                    index=idx_actual
                )
                if st.form_submit_button("Guardar"):
                    ir_a('estatividad')
            botones_navegacion()

        elif st.session_state.akt_paso == 'estatividad':
            st.markdown("#### **Prueba de estatividad**")
            st.write("Observa los siguientes diálogos:")
            
            cd1, cd2, cd3 = st.columns(3)
            with cd1:
                st.markdown(f"— ¿Qué pasó hace un rato?<br>— <i>{st.session_state.oracion_actual.capitalize()}</i>.", unsafe_allow_html=True)
            with cd2:
                st.markdown(f"— ¿Qué pasó ayer?<br>— <i>{st.session_state.oracion_actual.capitalize()}</i>.", unsafe_allow_html=True)
            with cd3:
                st.markdown(f"— ¿Qué pasó el mes pasado?<br>— <i>{st.session_state.oracion_actual.capitalize()}</i>.", unsafe_allow_html=True)
            
            st.write(f"¿Te parece que *{st.session_state.oracion_actual}* es una buena respuesta a, al menos, una de estas preguntas?")
            c1, c2 = st.columns(2)
            if c1.button("Sí", use_container_width=True):
                st.session_state.rasgos.estativo = False
                ir_a('puntualidad')
            if c2.button("No", use_container_width=True):
                st.session_state.rasgos.estativo = True
                ir_a('resultado')
            botones_navegacion()

        elif st.session_state.akt_paso == 'puntualidad':
            st.markdown("#### **Prueba de puntualidad**")
            p = construir_perif('gerundio_pret', st.session_state.datos)
            st.write("Observa estas expresiones:")
            lista_elegante([
                f"<i>{p.capitalize()} durante una hora.</i>",
                f"<i>{p.capitalize()} durante un mes.</i>"
            ])
            st.write("¿Es alguna de estas una expresión posible?<br>(Si la expresión tiene sentido iterativo o de inminencia, responde que **no**).", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            if c1.button("Sí", use_container_width=True):
                st.session_state.rasgos.puntual = False
                ir_a('telicidad')
            if c2.button("No", use_container_width=True):
                st.session_state.rasgos.puntual = True
                ir_a('telicidad')
            botones_navegacion()

        elif st.session_state.akt_paso == 'telicidad':
            st.markdown("#### **Prueba de telicidad**")
            p_ger = construir_perif('gerundio_subj', st.session_state.datos)
            p_inf = construir_perif('infinitivo', st.session_state.datos)
            p_par = construir_perif('participio', st.session_state.datos)
            st.write(f"Imagina que {p_ger} y de pronto {p_inf}.")
            st.write(f"¿Se podría decir que *{p_par}*?")
            c1, c2 = st.columns(2)
            if c1.button("Sí", use_container_width=True):
                st.session_state.rasgos.telico = False
                ir_a('dinamicidad')
            if c2.button("No", use_container_width=True):
                st.session_state.rasgos.telico = True
                ir_a('dinamicidad')
            botones_navegacion()

        elif st.session_state.akt_paso == 'dinamicidad':
            st.markdown("#### **Prueba de dinamicidad**")
            p = construir_perif('gerundio_pres', st.session_state.datos)
            st.write("Observa estas expresiones:")
            lista_elegante([
                f"<i>{p.capitalize()} enérgicamente</i>.",
                f"<i>{p.capitalize()} con fuerza</i>.",
                f"<i>{p.capitalize()} con ganas</i>."
            ])
            st.write("¿Te parecería natural decir algunas de estas expresiones?")
            c1, c2 = st.columns(2)
            if c1.button("Sí", use_container_width=True):
                st.session_state.rasgos.dinamico = True
                ir_a('resultado')
            if c2.button("No", use_container_width=True):
                st.session_state.rasgos.dinamico = False
                ir_a('resultado')
            botones_navegacion()

        elif st.session_state.akt_paso == 'resultado':
            st.markdown("### Análisis finalizado")
            st.write(f"El aktionsart de la cláusula **{st.session_state.oracion_original}** es **{label_resultado}**")
            
            # --- MODIFICACIÓN DE BOTONES (3 COLUMNAS) ---
            c1, c2, c3 = st.columns([1, 1, 1])
            if c1.button("Analizar otro predicado", use_container_width=True):
                reiniciar_analisis()
            if c2.button("← Volver a la última prueba", use_container_width=True):
                volver()
            if c3.button("Obtener Estructura Lógica", use_container_width=True):
                st.session_state.ls_akt = label_resultado.lower()
                st.session_state.ls_oracion = st.session_state.oracion_original
                st.session_state.seccion = 'ls'
                st.rerun()

    with col_der:
        with st.container(border=True):
            st.markdown('<div class="header-analisis">Estado del análisis</div>', unsafe_allow_html=True)
            if st.session_state.oracion_original:
                st.write("**Cláusula bajo análisis:**")
                st.info(st.session_state.oracion_original)
            if st.session_state.variante_no_causativa:
                st.write("**Variante no causativa:**")
                st.info(st.session_state.variante_no_causativa)
            if st.session_state.clausula_limpia:
                st.write("**Cláusula limpia:**")
                st.info(st.session_state.clausula_limpia)
            st.write("**Rasgos detectados:**")
            r = st.session_state.rasgos
            row_caus = ""
            if r.causativo is not None:
                row_caus = f'<div style="margin-bottom: 25px;"><span class="rasgo-elegante">[{"+" if r.causativo else "-"}causativo]</span></div>'
            row_otros = '<div style="margin-bottom: 15px;">'
            if r.estativo is not None: row_otros += f'<span class="rasgo-elegante">[{"+" if r.estativo else "-"}estativo]</span>'
            if r.puntual is not None: row_otros += f'<span class="rasgo-elegante">[{"+" if r.puntual else "-"}puntual]</span>'
            if r.telico is not None: row_otros += f'<span class="rasgo-elegante">[{"+" if r.telico else "-"}télico]</span>'
            if r.dinamico is not None: row_otros += f'<span class="rasgo-elegante">[{"+" if r.dinamico else "-"}dinámico]</span>'
            row_otros += "</div>"
            st.markdown(row_caus + row_otros, unsafe_allow_html=True)
            
            if st.session_state.akt_paso == 'resultado':
                st.markdown('<br><div class="header-analisis">Resultado</div>', unsafe_allow_html=True)
                st.success(f"**{label_resultado.upper()}**")

if __name__ == "__main__":
    mostrar_detector_es()