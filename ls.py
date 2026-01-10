# -*- coding: utf-8 -*-
"""
Logical Structure Generator (ES version) - Streamlit
Versión con panel informativo lateral
"""
import streamlit as st
import typing
import re
from dataclasses import dataclass, field
from typing import Optional, List, Tuple

try:
    from deep_translator import GoogleTranslator
    TRADUCTOR_DISPONIBLE = True
except ImportError:
    TRADUCTOR_DISPONIBLE = False

# Caché para no consultar a Google repetidamente por la misma palabra
CACHE_TRADUCCION = {}

# --- DICCIONARIO DE CORRECCIONES MANUALES ---
CORRECCIONES = {
    "pintada": "painted", "pintado": "painted",
    "comida": "eaten", "comido": "eaten",
    "bebida": "drunk", "bebido": "drunk",
    "parada": "stopped", "parado": "stopped",
    "herida": "wounded", "herido": "wounded",
    "llamada": "called", "llamado": "called",
    "vista": "seen", "visto": "seen",
    "hecha": "made", "hecho": "made",
    "vuelta": "returned", "vuelto": "returned",
    "puesta": "put", "puesto": "put",
    "escrito": "written", "escrita": "written",
    "abierto": "open", "abierta": "open", 
    "rota": "broken", "roto": "broken",
    "muerto": "dead", "muerta": "dead", 
    "dicho": "said", "dicha": "said",
    "alto": "tall", "alta": "tall", "altos": "tall", "altas": "tall",
    "chico": "little", "chica": "little", "chicos": "little", "chicas": "little",
    "asesinado": "dead", "asesinada": "dead", "asesinados": "dead", "asesinadas": "dead",
}

# --- DICCIONARIO DE PARTICIPIOS IRREGULARES ---
PARTICIPIOS_IRREGULARES = {
    "abrir": "abierto", "cubrir": "cubierto", "decir": "dicho",
    "escribir": "escrito", "hacer": "hecho", "freír": "frito",
    "imprimir": "impreso", "morir": "muerto", "poner": "puesto",
    "proveer": "provisto", "romper": "roto", "satisfacer": "satisfecho",
    "soltar": "suelto", "ver": "visto", "volver": "vuelto",
    "ir": "ido", "ser": "sido", "pudrir": "podrido",
    "leer": "leído", "traer": "traído", "caer": "caído", "oír": "oído",
    # Derivados comunes
    "descubrir": "descubierto", "encubrir": "encubierto", "recubrir": "recubierto",
    "describir": "descrito", "inscribir": "inscrito", "prescribir": "prescrito",
    "proscribir": "proscrito", "suscribir": "suscrito", "transcribir": "transcrito",
    "deshacer": "deshecho", "rehacer": "rehecho",
    "componer": "compuesto", "descomponer": "descompuesto", "disponer": "dispuesto",
    "exponer": "expuesto", "imponer": "impuesto", "oponer": "opuesto",
    "proponer": "propuesto", "reponer": "repuesto", "suponer": "supuesto",
    "absolver": "absuelto", "disolver": "disuelto", "resolver": "resuelto",
    "devolver": "devuelto", "envolver": "envuelto", "revolver": "revuelto",
    "prever": "previsto", "entrever": "entrevisto",
}

# --- LISTA DE PROTECCIÓN: Palabras clave de RRG que NO deben traducirse ---
RRG_KEYWORDS = {
    "do", "cause", "become", "ingr", "proc", "seml", "fin", "exist", 
    "be", "be-loc", "know", "have", "feel", "see", "hear", "smell", "taste", 
    "covering.path.distance", "weather", "if", "evid", "sta", "tns", "mod", 
    "asp", "not", "purp", "being.created", "being.consumed", "consumed",
    "have.as.part", "have.as.kin", "have.enough.with", "express", "hit",
    "move.away.from.reference.point", "move.up.from.reference.point", 
    "move.down.from.reference.point", "not"
}

# --- 1. CLASES Y ESTRUCTURAS ---

@dataclass
class Operador:
    codigo: str
    descripcion: str
    requiere_valor: bool
    ejemplos: str

OPERADORES = [
    Operador('IF', 'Fuerza ilocutiva', True, "DECL, INT, IMP"),
    Operador('EVID', 'Evidencialidad', True, "VIS, INF, HEARSAY"),
    Operador('STA', 'Estatus', True, "REALIS, PSBL, NEG"),
    Operador('TNS', 'Tiempo', True, "PAST, PRES, FUT"),
    Operador('NEG.INT +', 'Negación interna', False, ""),
    Operador('MOD', 'Modalidad deóntica', True, "OBLIG, PERMIS"),
    Operador('EVQ', 'Cuantificación eventiva', True, "DISTR"),
    Operador('DIR.CORE', 'Direccionalidad de centro', True, "HACIA.HABLANTE, DESDE.HABLANTE"),
    Operador('DIR.NUC', 'Direccionalidad nuclear', True, "ARRIBA, AFUERA"),
    Operador('ASP', 'Aspecto', True, "PFV, PERF, PROG"),
    Operador('NEG.NUC +', 'Negación nuclear', False, "")
]

# Diccionario para obtener descripción completa de operadores
OPERADORES_DESC = {op.codigo: op.descripcion for op in OPERADORES}

AKTIONSART_OPCIONES = {
    "estado": "estado",
    "estado causativo": "estado causativo",
    "logro": "logro",
    "logro causativo": "logro causativo",
    "realización": "realización",
    "realización causativa": "realización causativa",
    "semelfactivo": "semelfactivo",
    "semelfactivo causativo": "semelfactivo causativo",
    "proceso": "proceso",
    "proceso causativo": "proceso causativo",
    "actividad": "actividad",
    "actividad causativa": "actividad causativa",
    "realización activa": "realización activa",
    "realización activa causativa": "realización activa causativa"
}

MODIFICADORES_AKT = {
    "logro": "INGR",
    "realización": "BECOME",
    "proceso": "PROC",
    "semelfactivo": "SEML",
    "logro causativo": "INGR",
    "realización causativa": "BECOME",
    "proceso causativo": "PROC",
    "semelfactivo causativo": "SEML"
}

# --- 2. DICCIONARIOS DE VERBOS ---

VERBOS_MOVIMIENTO = {
    "move.away.from.reference.point": [
        "ir", "irse", "salir", "partir", "marchar", "escapar", "huir",
        "largarse", "migrar", "retirarse", "alejarse", "ausentarse",
        "desaparecer", "desvanecerse", "desplazarse", "evadirse", "esfumarse",
        "fugarse", "trasladarse", "mudarse", "perderse", "marcharse", "venir",
        "arrancar", "arrancarse", "cambiarse", "saltar"
    ],
    "move.up.from.reference.point": [
        "subir", "subirse", "ascender", "escalar", "trepar", "elevarse", "remontar"
    ],
    "move.down.from.reference.point": [
        "bajar", "bajarse", "caer", "caerse", "descender"
    ]
}

VERBOS_METEOROLOGICOS = [
    "llover", "nevar", "granizar", "tronar", "relampaguear", "diluviar",
    "lloviznar", "escampar", "helar", "deshelar", "ventear", "anochecer",
    "amanecer", "atardecer", "oscurecer", "aclarar", "nublar", "despejar",
    "chispear", "orbayar", "orvallar", "chaparrear", "gotear", "garuar",
    "chirimirear", "temblar", "nortear", "terremotear"
]

VERBOS_TRANSFERENCIA = {
    "sacar": [
        "sacar", "retirar", "tomar", "agarrar", "coger", "quitar", "apartar",
        "desalojar", "separar", "desplazar", "exiliar", "remover", "descolgar",
        "extraer", "rescatar", "liberar", "arrancar", "sustraer", "arrebatar",
        "despojar", "confiscar", "desposeer", "usurpar", "desapropiar",
        "decomisar", "expropiar", "robar", "hurtar", "birlar", "enajenar",
        "pedir", "solicitar", "demandar", "exigir", "comprar", "cobrar",
        "exigir", "facturar", "reclamar", "perceptuar", "expulsar", "desalojar",
        "lanzar", "arrojar", "eliminar", "desterrar", "extraditar", "ahuyentar",
        "desarraigar", "destituir", "desprender", "erradicar", "vaciar", "drenar",
        "salvar"
    ],
    "dar_poner": [
        "acercar", "acreditar", "adicionar", "adscribir", "agregar", "alcanzar",
        "añadir", "aplicar", "arrimar", "asignar", "atribuir", "cargar", "ceder", "colocar",
        "conceder", "conferir", "consignar", "cubrir", "dar", "delegar", "desparramar",
        "destinar", "distribuir", "donar", "dotar", "echar", "encomendar", "endilgar",
        "entregar", "enviar", "esparcir", "estipular", "expandir", "extender",
        "facilitar", "fijar", "imputar", "incorporar", "instituir", "legar", "llevar",
        "mandar", "nombrar", "obsequiar", "ofrecer", "otorgar", "pasar", "poner",
        "prescribir", "prestar", "proporcionar", "reconocer", "repartir", "señalar",
        "suministrar", "traer", "transferir", "trasferir", "traspasar", "untar",
        "vender", "verter", "vertir"
    ]
}

VERBOS_DICCION = {
    "preguntar": [
        "averiguar", "consultar", "cuestionar", "demandar", "indagar",
        "inquirir", "interpelar", "interrogar", "pedir", "preguntar",
        "recabar", "requerir", "sondear"
    ],
    "conversar": [
        "charlar", "chismear", "chismorrear", "comentar", "conferenciar",
        "conferir", "conversar", "cotillear", "cotorrear", "cuchichear",
        "departir", "dialogar", "discutir", "gritar", "gritarse",
        "hablar", "interlocutar", "parlar", "parlotear", "platicar", "tratar"
    ],
    "agradecer": {
        "adular": "adulación", "advertir": "advertencia", "agradecer": "agradecimiento",
        "alardear": "alarde", "amenazar": "amenaza", "brindar": "brindis",
        "criticar": "crítica", "disculpar": "disculpa", "elogiar": "elogio",
        "encomiar": "encomio", "exhortar": "exhortación", "felicitar": "felicitación",
        "halagar": "halago", "implorar": "imploración", "insultar": "insulto",
        "jurar": "juramento", "lamentar": "lamento", "lisonjear": "lisonja",
        "pedir": "petición", "perdonar": "perdón", "protestar": "protesta",
        "regañar": "regaño", "replicar": "réplica", "rogar": "ruego",
        "saludar": "saludo", "suplicar": "súplica"
    },
    "bendecir": {
        "aconsejar": "consejo", "argumentar": "argumento", "bendecir": "bendición",
        "debatir": "debate", "maldecir": "maldición", "mentir": "mentira",
        "prometer": "promesa"
    }
}

VERBOS_TRI_NEG = {
    "desatribuir": [
        "desatribuir", "desasignar", "quitar", "retirar", "denegar",
        "rechazar", "rehusar", "desconocer", "ignorar", "negar", "revocar",
        "desacreditar", "desautorizar", "invalidar", "desadscribir",
        "desvincular", "separar"
    ],
    "ocultar": [
        "ocultar", "esconder", "encubrir", "disimular", "camuflar", "velar",
        "callar", "silenciar", "omitir", "reservar", "retener", "hurtar",
        "guardar", "escamotear", "suprimir", "enmascarar", "tapar"
    ]
}

VERBOS_POSESION = {
    "tener": [
        "acoger", "albergar", "alojar", "contener", "conservar", "custodiar",
        "cuidar", "demostrar", "denotar", "desplegar", "evidenciar", "exhibir",
        "gestionar", "guardar", "hospedar", "incluir", "lucir", "manifestar",
        "mantener", "mostrar", "ofrecer", "ostentar", "portar", "poseer",
        "presentar", "proteger", "reflejar", "resguardar", "revelar",
        "sostener", "soportar", "tener", "vigilar"
    ],
    "obtener": [
        "obtener", "conseguir", "lograr", "adquirir", "alcanzar", "recibir",
        "ganar", "captar", "capturar", "atrapar"
    ],
    "perder": ["perder", "extraviar", "traspapelar", "egraviar"]
}

VERBOS_EXISTENCIA = [
    "conservada", "conservado", "conservadas", "conservados",
    "existida", "existido", "existidas", "existidos",
    "habida", "habido", "habidas", "habidos",
    "perdurada", "perdurado", "perduradas", "perdurados",
    "permanecida", "permanecido", "permanecidas", "permanecidos",
    "persistida", "persistido", "persistidas", "persistidos",
    "quedada", "quedado", "quedadas", "quedados",
    "resistida", "resistido", "resistidas", "resistidos",
    "restada", "restado", "restadas", "restados",
    "sida", "sido", "sidas", "sidos",
    "sobrevivida", "sobrevivido", "sobrevividas", "sobrevividos",
    "subsistida", "subsistido", "subsistidas", "subsistidos"
]

VERBOS_PERCEPCION = {
    "ver": "see", "observar": "see", "mirar": "see", "contemplar": "see",
    "vislumbrar": "see", "divisar": "see", "atisbar": "see", "escudriñar": "see",
    "distinguir": "see", "enfocar": "see", "ojear": "see", "cachar": "see",
    "otear": "see", "escanear": "see", "acechar": "see",
    "oír": "hear", "escuchar": "hear", "atender": "hear", "auscultar": "hear",
    "tocar": "feel", "palpar": "feel", "rozar": "feel", "acariciar": "feel",
    "manosear": "feel",
    "probar": "taste", "saborear": "taste", "degustar": "taste", "paladear": "taste",
    "catar": "taste", "gustar": "taste",
    "oler": "smell", "aspirar": "smell", "olisquear": "smell", "olfatear": "smell",
    "husmear": "smell", "inhalar": "smell", "olorosar": "smell"
}

VERBOS_PERCEPCION_IMPERSONAL = {
    "saber": "taste", "sabido": "taste", "sabida": "taste", "sabidos": "taste", "sabidas": "taste",
    "oler": "smell", "olido": "smell", "olida": "smell", "olidos": "smell", "olidas": "smell",
    "sonar": "hear", "sonado": "hear", "sonada": "hear", "sonados": "hear", "sonadas": "hear",
    "ver": "see", "verse": "see", "visto": "see", "vista": "see", "vistos": "see", "vistas": "see",
    "sentir": "feel", "sentirse": "feel", "sentido": "feel", "sentida": "feel", "sentidos": "feel", "sentidas": "feel"
}

# --- 3. FUNCIONES AUXILIARES ---

def buscar_verbo(verbo, diccionario):
    for categoria, verbos in diccionario.items():
        if verbo in verbos:
            return categoria
    return None

def normalizar_arg(arg: str) -> str:
    return 'Ø' if arg in ('0', '') else arg

def extraer_mr(ls: str) -> tuple:
    """Extrae el marcador [MR0] o [MR1] de la estructura lógica.
    Retorna (ls_sin_mr, mr) donde mr es el marcador o cadena vacía."""
    match = re.search(r'\s*\[MR[01]\]\s*$', ls)
    if match:
        mr = match.group().strip()
        ls_sin_mr = ls[:match.start()].strip()
        return (ls_sin_mr, mr)
    return (ls, "")

def insertar_mr(ls: str, mr: str) -> str:
    """Inserta el marcador MR al final de la estructura lógica."""
    if mr:
        return f"{ls} {mr}"
    return ls

def traducir_ls_a_ingles(ls_string: str, usar_html: bool = True) -> str:
    """
    Traduce constantes al inglés y las pone en NEGRITA.
    Incluye un diccionario de correcciones ampliado para evitar ambigüedades 
    donde el traductor confunde participios con sustantivos.
    """
    if not ls_string:
        return ls_string

    # Tags para formato
    if usar_html:
        NEGRITA_INICIO = "<b>"
        NEGRITA_FIN = "</b>"
    else:
        NEGRITA_INICIO = ""
        NEGRITA_FIN = ""
    
    if TRADUCTOR_DISPONIBLE:
        translator = GoogleTranslator(source='es', target='en')
    else:
        translator = None

    def reemplazar_match(match):
        constante = match.group(1) 
        
        # Variable para guardar la palabra final
        palabra_final = constante
        constante_lower = constante.lower()

        # 1. Si está en la lista de palabras reservadas RRG, no tocar
        if constante_lower in RRG_KEYWORDS:
            pass
            
        # 2. Si está en nuestro DICCIONARIO DE CORRECCIONES, usar esa versión
        elif constante_lower in CORRECCIONES:
            palabra_final = CORRECCIONES[constante_lower]
            
        # 3. Si no, intentar traducción normal
        elif translator:
            texto_limpio = constante.replace(".", " ")
            if texto_limpio in CACHE_TRADUCCION:
                palabra_final = CACHE_TRADUCCION[texto_limpio]
            else:
                try:
                    traduccion = translator.translate(texto_limpio)
                    if traduccion:
                        palabra_final = traduccion.lower().strip().replace(" ", ".")
                        CACHE_TRADUCCION[texto_limpio] = palabra_final
                except Exception:
                    pass 

        return f"{NEGRITA_INICIO}{palabra_final}'{NEGRITA_FIN}"

    patron = r"\b([a-zA-Zñáéíóúü\._Ø0-9\-]+)'"
    ls_traducida = re.sub(patron, reemplazar_match, ls_string)
    return ls_traducida

def infinitivo_a_participio(infinitivo: str) -> str:
    """Convierte un infinitivo español a su forma de participio."""
    infinitivo = infinitivo.lower().strip()
    
    # Quitar pronombres enclíticos (se, me, te, nos, os)
    pronombres = ("se", "me", "te", "nos", "os")
    for pron in pronombres:
        if infinitivo.endswith(pron):
            infinitivo = infinitivo[:-len(pron)]
            break

    # Buscar en irregulares
    if infinitivo in PARTICIPIOS_IRREGULARES:
        return PARTICIPIOS_IRREGULARES[infinitivo]
    
    # Reglas regulares (adaptado de aktionsart_es.py)
    if infinitivo.endswith("ar"):
        return infinitivo[:-2] + "ado"
    elif infinitivo.endswith(("er", "ir")):
        return infinitivo[:-2] + "ido"
    
    # Si no reconoce el patrón, devolver tal cual
    return infinitivo

# FUNCIONES PARA EXPORTAR O COPIAR LS FINAL

def limpiar_html_ls(ls_html: str) -> str:
    """Convierte la estructura lógica con HTML a texto plano."""
    texto = ls_html
    # Reemplazar entidades HTML por ángulos Unicode
    texto = texto.replace('&lt;', '⟨')
    texto = texto.replace('&gt;', '⟩')
    # Eliminar tags HTML
    texto = re.sub(r'<[^>]+>', '', texto)
    return texto

def convertir_ls_a_latex(ls_html: str) -> str:
    """Convierte la estructura lógica con HTML a formato LaTeX (modo matemático)."""
    texto = ls_html
    
    # 1. Convertir negritas (constantes predicativas)
    texto = re.sub(r'<b>([^<]+)</b>', r'\\mathbf{\1}', texto)
    
    # 2. Convertir apertura de operador: &lt;<sub>XX</sub> → \langle_{\text{XX}}\;
    texto = re.sub(r'&lt;<sub>([^<]+)</sub>', r'\\langle_{\\text{\1}}\\;', texto)
    
    # 3. Convertir itálicas (valores de operadores) con espacio después
    texto = re.sub(r'<i>([^<]+)</i>', r'\\textit{\1}\\;', texto)
    
    # 4. Convertir cierre de ángulos con espacio antes
    texto = texto.replace('&gt;', r'\rangle')
    
    # 5. Convertir símbolo vacío
    texto = texto.replace('Ø', r'\varnothing')
    
    # 6. Convertir palabras clave de RRG a texto con espacios
    keywords = ['CAUSE', 'INGR', 'BECOME', 'PROC', 'SEML', 'PURP', 'FIN', 'NOT']
    for kw in keywords:
        texto = re.sub(rf'(?<![a-zA-Z]){kw}(?![a-zA-Z\'])', f'\\;\\\\text{{{kw}}}\\;', texto)
    
    # 7. Formatear [MR0] y [MR1]
    texto = re.sub(r'\[MR([01])\]', r'\\;[\\text{MR\1}]', texto)
    
    # 8. Formatear argumentos entre paréntesis (palabras que empiezan con mayúscula)
    def formatear_argumento(match):
        arg = match.group(1)
        if arg[0].isupper() and arg not in keywords:
            return f'\\text{{{arg}}}'
        return arg
    
    texto = re.sub(r'\b([A-Z][a-zá-úñ]*)\b(?![}\'])', formatear_argumento, texto)
    
    # 9. Añadir espacio después de comas
    texto = texto.replace(',', ', ')
    
    # 10. Envolver todo en modo matemático
    texto = f'${texto}$'
    return texto

def generar_imagen_ls(ls_html: str) -> bytes:
    """Genera una imagen PNG de la estructura lógica con formato."""
    import matplotlib.pyplot as plt
    from io import BytesIO
    
    # Convertir HTML a formato matplotlib mathtext
    texto = ls_html
    texto = texto.replace('&lt;', '⟨')
    texto = texto.replace('&gt;', '⟩')
    texto = re.sub(r'<sub>([^<]+)</sub>', r'$_{\\mathrm{\1}}$', texto)
    texto = re.sub(r'<i>([^<]+)</i>', r'$\\mathit{\1}$', texto)
    texto = re.sub(r'<b>([^<]+)</b>', r'$\\mathbf{\1}$', texto)
    
    # Calcular ancho según longitud
    ancho = max(len(ls_html) * 0.08, 10)
    
    fig, ax = plt.subplots(figsize=(ancho, 1.5))
    ax.axis('off')
    
    ax.text(0.5, 0.5, texto,
            fontsize=14,
            ha='center',
            va='center',
            transform=ax.transAxes)
    
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=150,
                facecolor='white', edgecolor='none', pad_inches=0.3)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()

def extraer_predicados_de_ls(ls_html: str) -> list:
    """Extrae los predicados (en negrita) de la estructura lógica, excluyendo palabras reservadas de RRG."""
    patron = r"<b>([^<]+)'</b>"
    matches = re.findall(patron, ls_html)
    # Eliminar duplicados manteniendo orden, excluyendo palabras reservadas
    vistos = set()
    unicos = []
    for m in matches:
        m_lower = m.lower()
        # Verificar que no sea palabra reservada (comparar también sin puntos)
        m_base = m_lower.split('.')[0]
        if m not in vistos and m_lower not in RRG_KEYWORDS and m_base not in RRG_KEYWORDS:
            vistos.add(m)
            unicos.append(m)
    return unicos

def reemplazar_predicado_en_ls(ls_html: str, pred_viejo: str, pred_nuevo: str) -> str:
    """Reemplaza un predicado por otro en la estructura lógica."""
    # Reemplazar <b>pred_viejo'</b> por <b>pred_nuevo'</b>
    patron = f"<b>{re.escape(pred_viejo)}'</b>"
    reemplazo = f"<b>{pred_nuevo}'</b>"
    return re.sub(patron, reemplazo, ls_html)

# --- 4. FUNCIONES DE GENERACIÓN DE ESTRUCTURAS LÓGICAS ---

def generar_estructura_no_causativa(x, y, locus, pred, operador, AKT):
    if y != "Ø" and locus == "Ø":
        return f"{operador + ' ' if operador else ''}{pred}' ({x}, {y})"
    elif y == "Ø" and locus != "Ø":
        return f"{operador + ' ' if operador else ''}{pred}' ({x}, {locus})"
    elif y == "Ø" and locus == "Ø":
        return f"{operador + ' ' if operador else ''}{pred}' ({x})"
    return None

def generar_estructura_causativa(x, y, pred, operador):
    if y == "Ø":
        return None
    return f"[do' ({x}, Ø)] CAUSE [{operador + ' ' if operador else ''}{pred}' ({y})]"

def generar_estructura_actividad(x, y, locus, pred, operador):
    if y != "Ø" and locus == "Ø":
        return f"{operador + ' ' if operador else ''}do' ({x}, [{pred}' ({x}, {y})])"
    elif y == "Ø" and locus != "Ø":
        return f"{operador + ' ' if operador else ''}do' ({x}, [{pred}' ({x}, {locus})])"
    elif y == "Ø" and locus == "Ø":
        return f"{operador + ' ' if operador else ''}do' ({x}, [{pred}' ({x})])"
    return None

def generar_estructura_actividad_causativa(x, y, pred, operador):
    if y == "Ø":
        return None
    return f"[do' ({x}, Ø)] CAUSE [{operador + ' ' if operador else ''}do' ({y}, [{pred}' ({y})])]"

def aplicar_DO(x, estructura_logica):
    if estructura_logica is None:
        return None
    ls_sin_mr, mr = extraer_mr(estructura_logica)
    resultado = f"DO ({ls_sin_mr})"
    return insertar_mr(resultado, mr)

def aplicar_anticausativa(estructura_logica):
    ls_sin_mr, mr = extraer_mr(estructura_logica)
    resultado = f"[do' (Ø, Ø)] CAUSE [{ls_sin_mr}]"
    return insertar_mr(resultado, mr)

def añadir_operadores_a_ls(estructura_logica: str, operadores_seleccionados: List[Tuple[str, Optional[str]]]) -> str:
    """Añade operadores a la estructura lógica con formato RRG (operador en subíndice, valor en itálica)."""
    if not operadores_seleccionados:
        return estructura_logica
    
    # Extraer MR si existe
    ls_sin_mr, mr = extraer_mr(estructura_logica)
    # Construir el resultado base: MR queda dentro del corchete externo pero fuera de la LS
    if mr:
        resultado = f"[{ls_sin_mr}]{mr}"
    else:
        resultado = f"[{ls_sin_mr}]"
    
    for codigo, valor in reversed(operadores_seleccionados):
        # Separar el símbolo + si existe en el código (para NEG.INT + y NEG.NUC +)
        if codigo.endswith(' +'):
            codigo_base = codigo[:-2]
            sufijo_codigo = " <i>+</i>"
        else:
            codigo_base = codigo
            sufijo_codigo = ""
        
        # Separar el símbolo + si existe en el valor (para STA NEG +)
        if valor and valor.endswith(' +'):
            valor_base = valor[:-2]
            valor_formateado = f"<i>{valor_base}</i> <i>+</i>"
        elif valor:
            valor_formateado = f"<i>{valor}</i>"
        else:
            valor_formateado = ""
        
        if valor_formateado:
            resultado = f"&lt;<sub>{codigo_base}</sub>{sufijo_codigo} {valor_formateado} {resultado}&gt;"
        else:
            resultado = f"&lt;<sub>{codigo_base}</sub>{sufijo_codigo} {resultado}&gt;"
    
    return resultado

# --- 5. NAVEGACIÓN STREAMLIT ---

def crear_callback_ir_a(paso, **kwargs):
    """Crea un callback para navegar a un paso específico, opcionalmente asignando valores."""
    def callback():
        # Asignar valores adicionales al session_state
        for key, value in kwargs.items():
            st.session_state[key] = value
        # Navegar
        st.session_state.ls_paso = paso
    return callback

def ir_a(paso):
    """Navega a un paso (usar solo dentro de forms o al inicio)."""
    st.session_state.ls_paso = paso
    st.rerun()

def ir_a_intencionalidad():
    """Navega al paso intencionalidad guardando la estructura pre-DO."""
    st.session_state.ls_estructura_pre_do = st.session_state.ls_estructura
    st.session_state.ls_paso = 'intencionalidad'
    st.rerun()

def reiniciar_analisis():
    """Limpia todo el rastro del análisis de LS y resetea el paso inicial."""
    # 1. Identificar todas las llaves de LS
    keys_to_delete = [k for k in list(st.session_state.keys()) if k.startswith('ls_')]
    
    # 2. Eliminarlas del estado de sesión
    for key in keys_to_delete:
        del st.session_state[key]
    
    # 3. Asegurar que la dinamicidad heredada se limpie
    st.session_state.ls_es_dinamico = None

def botones_navegacion():
    st.write("---")
    st.button("Iniciar nuevo análisis", use_container_width=True, key=f"nav_reset_{st.session_state.ls_paso}", on_click=reiniciar_analisis)

def lista_elegante(items: list):
    html_items = ""
    for item in items:
        html_items += f'<div style="display: flex; align-items: flex-start; margin-bottom: 8px;"><div style="color: #4A90E2; margin-right: 10px; font-weight: bold;">•</div><div style="line-height: 1.4;">{item}</div></div>'
    st.markdown(f'<div style="margin-bottom: 15px;">{html_items}</div>', unsafe_allow_html=True)

# --- 6. PANEL INFORMATIVO LATERAL ---

def mostrar_panel_info():
    """Muestra el panel informativo con los datos del análisis actual."""
    
    # Estilos del panel
    st.markdown("""
        <style>
        .info-panel {
            background-color: #f8f9fa;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
        }
        .info-panel-title {
            color: #333333;
            font-size: 1.1em;
            font-weight: 600;
            border-bottom: 2px solid #4A90E2;
            margin-bottom: 15px;
            padding-bottom: 8px;
        }
        .info-item {
            margin-bottom: 12px;
        }
        .info-label {
            color: #666666;
            font-size: 0.85em;
            font-weight: 600;
            margin-bottom: 3px;
        }
        .info-value {
            color: #333333;
            font-size: 0.95em;
            padding: 5px 8px;
            background-color: #ffffff;
            border-radius: 4px;
            border-left: 3px solid #4A90E2;
        }
        .info-value-ls {
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.85em;
            padding: 8px;
            background-color: #ffffff;
            border-radius: 4px;
            border-left: 3px solid #4A90E2;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }
        .info-value-akt {
            font-weight: 600;
            text-transform: uppercase;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="info-panel-title">Datos del análisis</div>', unsafe_allow_html=True)
    
    # 1. Cláusula bajo análisis
    if st.session_state.get('ls_oracion'):
        st.markdown(f'''
            <div class="info-item">
                <div class="info-label">Cláusula</div>
                <div class="info-value">{st.session_state.ls_oracion}</div>
            </div>
        ''', unsafe_allow_html=True)
    
    # 2. Aktionsart
    if st.session_state.get('ls_akt'):
        st.markdown(f'''
            <div class="info-item">
                <div class="info-label">Aktionsart</div>
                <div class="info-value info-value-akt">{st.session_state.ls_akt}</div>
            </div>
        ''', unsafe_allow_html=True)
    
    # 3. Sujeto
    x = st.session_state.get('ls_x')
    if x and x != 'Ø':
        st.markdown(f'''
            <div class="info-item">
                <div class="info-label">Sujeto</div>
                <div class="info-value">{x}</div>
            </div>
        ''', unsafe_allow_html=True)
    
    # 4. Complemento Directo
    y = st.session_state.get('ls_y')
    if y and y != 'Ø':
        st.markdown(f'''
            <div class="info-item">
                <div class="info-label">Complemento directo</div>
                <div class="info-value">{y}</div>
            </div>
        ''', unsafe_allow_html=True)
    
    # 5. Complemento Indirecto
    z = st.session_state.get('ls_z')
    if z and z != 'Ø':
        st.markdown(f'''
            <div class="info-item">
                <div class="info-label">Complemento indirecto</div>
                <div class="info-value">{z}</div>
            </div>
        ''', unsafe_allow_html=True)
    
    # 6. Complemento de régimen
    creg = st.session_state.get('ls_complemento_regimen')
    if creg and creg != 'Ø':
        st.markdown(f'''
            <div class="info-item">
                <div class="info-label">Complemento de régimen</div>
                <div class="info-value">{creg}</div>
            </div>
        ''', unsafe_allow_html=True)
    
    # 7. Argumento locativo
    locus = st.session_state.get('ls_locus')
    if locus and locus != 'Ø':
        st.markdown(f'''
            <div class="info-item">
                <div class="info-label">Información locativa</div>
                <div class="info-value">{locus}</div>
            </div>
        ''', unsafe_allow_html=True)
    
    # 8. Estructura lógica
    paso_actual = st.session_state.get('ls_paso', '')
    pasos_mostrar_el = ['resultado', 'seleccionar_operadores', 'final']
    ls_traducida = st.session_state.get('ls_estructura_traducida')
    if paso_actual in pasos_mostrar_el:
        ls_traducida = st.session_state.get('ls_estructura_traducida')
        if not ls_traducida:
            ls_estructura = st.session_state.get('ls_estructura')
            if ls_estructura:
                ls_traducida = traducir_ls_a_ingles(ls_estructura, usar_html=True)
        if ls_traducida:
            st.markdown(f'''
                <div class="info-item">
                    <div class="info-label">Estructura lógica</div>
                    <div class="info-value-ls">{ls_traducida}</div>
                </div>
            ''', unsafe_allow_html=True)
    
    # 9. Estructura lógica con capa de intencionalidad
    ls_con_do = st.session_state.get('ls_estructura_con_do')
    if ls_con_do:
        ls_con_do_trad = traducir_ls_a_ingles(ls_con_do, usar_html=True)
        st.markdown(f'''
            <div class="info-item">
                <div class="info-label">Estructura lógica con intencionalidad</div>
                <div class="info-value-ls">{ls_con_do_trad}</div>
            </div>
        ''', unsafe_allow_html=True)
    
    # 10. Operadores seleccionados
    ops_valores = st.session_state.get('ls_ops_valores')
    if ops_valores and len(ops_valores) > 0:
        ops_desc_list = []
        for codigo, valor in ops_valores:
            desc = OPERADORES_DESC.get(codigo, codigo)
            if valor:
                ops_desc_list.append(f"{desc}: {valor}")
            else:
                ops_desc_list.append(f"{desc}")
        ops_html = "<br>".join(ops_desc_list)
        st.markdown(f'''
            <div class="info-item">
                <div class="info-label">Operadores seleccionados</div>
                <div class="info-value">{ops_html}</div>
            </div>
        ''', unsafe_allow_html=True)
    
    # 11. Estructura lógica con operadores (solo si hay operadores seleccionados)
    ls_final = st.session_state.get('ls_estructura_final')
    ops_valores = st.session_state.get('ls_ops_valores')
    if ls_final and ops_valores and len(ops_valores) > 0:
        st.markdown(f'''
            <div class="info-item">
                <div class="info-label">Estructura lógica con operadores</div>
                <div class="info-value-ls">{ls_final}</div>
            </div>
        ''', unsafe_allow_html=True)

# --- 7. INTERFAZ PRINCIPAL ---

def mostrar_asistente_ls():
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
        .ls-resultado {
            font-family: 'Courier New', Courier, monospace;
            font-size: 1.1em;
            padding: 15px;
            background-color: #f8f9fa;
            border-left: 4px solid #4A90E2;
            margin: 10px 0;
            word-wrap: break-word;
        }
        .param-tag {
            display: inline-block;
            background-color: #e8f4f8;
            color: #2c5282;
            padding: 2px 8px;
            border-radius: 4px;
            margin: 2px;
            font-size: 0.9em;
        }
        </style>
    """, unsafe_allow_html=True)

    # Inicialización del estado
    if 'ls_paso' not in st.session_state:
        st.session_state.ls_paso = 'inicio'
        st.session_state.ls_oracion = st.session_state.get('ls_oracion', '')
        st.session_state.ls_akt = st.session_state.get('ls_akt', '')
        st.session_state.ls_x = ''
        st.session_state.ls_y = ''
        st.session_state.ls_z = ''
        st.session_state.ls_pred = ''
        st.session_state.ls_locus = 'Ø'
        st.session_state.ls_complemento_regimen = ''  # NUEVO
        st.session_state.ls_es_dinamico = st.session_state.get('ls_es_dinamico', None)
        st.session_state.ls_estructura = ''
        st.session_state.ls_estructura_pre_do = ''  # NUEVO: antes de DO
        st.session_state.ls_estructura_con_do = ''  # NUEVO: después de DO
        st.session_state.ls_operadores = []
        st.session_state.ls_preguntas_pendientes = []
        st.session_state.ls_respuestas = {}
        st.session_state.ls_es_verbo_reciproco = False

    # Layout con columnas: contenido principal (2) + panel info (1)
    col_main, col_spacer, col_info = st.columns([2, 0.1, 1])
    
    with col_info:
        mostrar_panel_info()
    
    with col_main:
        # --- PASO: INICIO ---
        if st.session_state.ls_paso == 'inicio':
            st.info("**Este módulo puede asistirte en la formalización de la estructura lógica básica de una cláusula.**")
            st.warning("Advertencia: el programa solo maneja cláusulas simples, con su estructura argumental típica, y puede dar resultados inexactos en construcciones que las alteran.")
            
            # Si viene del detector de aktionsart
            if st.session_state.ls_akt and st.session_state.ls_oracion:
                st.success(f"El aktionsart detectado para la cláusula **{st.session_state.ls_oracion}** fue **{st.session_state.ls_akt.upper()}**")
                
                col_cont, col_reset = st.columns(2)
                
                with col_cont:
                    st.button(
                        "Usar estos datos", 
                        use_container_width=True, 
                        on_click=crear_callback_ir_a('argumentos')
                    )
                
                with col_reset:
                    st.button(
                        "Iniciar un nuevo análisis", 
                        use_container_width=True, 
                        key="reset_desde_inicio",
                        on_click=reiniciar_analisis
                    )
            else:
                with st.form(key="form_inicio_ls"):
                    st.write("**Selecciona el aktionsart del predicado:**")
                    
                    # CSS para mostrar radio buttons en dos columnas
                    st.markdown("""
                        <style>
                        div[data-testid="stForm"] div[role="radiogroup"] {
                            display: grid;
                            grid-template-columns: 1fr 1fr;
                            gap: 0.3rem 8rem;
                            margin-bottom: 2rem;
                        }
                        div[data-testid="stForm"] div[role="radiogroup"] label {
                            padding: 0.2rem 0;
                        }
                        </style>
                    """, unsafe_allow_html=True)
                    
                    # Lista ordenada: primero no causativas, luego causativas
                    # Se mostrarán en dos columnas gracias al CSS grid
                    aktionsart_ordenados = [
                        "estado", "estado causativo",
                        "actividad", "actividad causativa",
                        "semelfactivo", "semelfactivo causativo",
                        "logro", "logro causativo",
                        "proceso", "proceso causativo",
                        "realización", "realización causativa",
                        "realización activa", "realización activa causativa"
                    ]
                    
                    akt = st.radio(
                        "Aktionsart",
                        options=aktionsart_ordenados,
                        format_func=lambda x: x.capitalize(),
                        key="akt_radio",
                        index=None,
                        label_visibility="collapsed"
                    )
                    
                    st.write("**Escribe la cláusula de la que quieres obtener su estructura lógica:**")

                    oracion = st.text_input(
                        "Cláusula", 
                        label_visibility="collapsed", 
                    )
                    
                    if st.form_submit_button("Comenzar"):
                        if oracion and akt:
                            st.session_state.ls_akt = akt
                            st.session_state.ls_oracion = oracion
                            ir_a('argumentos')
                        elif not akt:
                            st.warning("Por favor, selecciona un aktionsart.")
                        elif not oracion:
                            st.warning("Por favor, escribe la cláusula.")

        # --- PASO: ARGUMENTOS ---
        elif st.session_state.ls_paso == 'argumentos':
            st.markdown("#### **Identificación de argumentos**")
            st.info(f"Selecciona los argumentos presentes en la cláusula **{st.session_state.ls_oracion}** (sintácticos o morfológicos).")
            st.warning("Si hay argumentos sintácticos, privilegia estos.")
            
            # Inicializar estados si no existen
            if 'ls_arg_sujeto' not in st.session_state:
                st.session_state.ls_arg_sujeto = False
            if 'ls_arg_cd' not in st.session_state:
                st.session_state.ls_arg_cd = False
            if 'ls_arg_ci' not in st.session_state:
                st.session_state.ls_arg_ci = False
            if 'ls_tipo_sujeto' not in st.session_state:
                st.session_state.ls_tipo_sujeto = None
            if 'ls_tipo_cd' not in st.session_state:
                st.session_state.ls_tipo_cd = None
            if 'ls_tipo_ci' not in st.session_state:
                st.session_state.ls_tipo_ci = None
            
            # Opciones de rasgos
            RASGOS_OPCIONES = {
                "Primera persona singular": "1sg",
                "Segunda persona singular": "2sg",
                "Tercera persona singular": "3sg",
                "Primera persona plural": "1pl",
                "Segunda persona plural": "2pl",
                "Tercera persona plural": "3pl"
            }

            # --- SUJETO ---
            with st.container(border=True):
                st.session_state.ls_arg_sujeto = st.checkbox("Sujeto", value=st.session_state.ls_arg_sujeto, key="chk_sujeto")
            
                if st.session_state.ls_arg_sujeto:
                    st.session_state.ls_tipo_sujeto = st.radio(
                        "Tipo de expresión del sujeto",
                        options=["constituyente", "afijo"],
                        format_func=lambda x: "La información se expresa en un constituyente sintáctico" if x == "constituyente" else "La información se expresa únicamente en un afijo o clítico",
                        key="radio_sujeto",
                        index=0 if st.session_state.ls_tipo_sujeto == "constituyente" else (1 if st.session_state.ls_tipo_sujeto == "afijo" else None),
                        label_visibility="collapsed"
                    )
                
                    if st.session_state.ls_tipo_sujeto == "constituyente":
                        st.session_state.ls_x_input = st.text_input(
                            "Sujeto",
                            value=st.session_state.get('ls_x_input', ''),
                            placeholder="Escribe el sujeto",
                            key="input_sujeto",
                            label_visibility="collapsed"
                        )
                    elif st.session_state.ls_tipo_sujeto == "afijo":
                        st.write("Escoge los rasgos pertinentes:")
                        rasgos_sujeto = st.selectbox(
                            "Rasgos del sujeto",
                            options=list(RASGOS_OPCIONES.keys()),
                            key="select_sujeto",
                            label_visibility="collapsed"
                        )
                        st.session_state.ls_x_input = RASGOS_OPCIONES[rasgos_sujeto]
           
            # --- COMPLEMENTO DIRECTO ---
            with st.container(border=True): 
                st.session_state.ls_arg_cd = st.checkbox("Complemento directo", value=st.session_state.ls_arg_cd, key="chk_cd")
            
                if st.session_state.ls_arg_cd:
                    st.session_state.ls_tipo_cd = st.radio(
                        "Tipo de expresión del CD",
                        options=["constituyente", "afijo"],
                        format_func=lambda x: "La información se expresa en un constituyente sintáctico" if x == "constituyente" else "La información se expresa únicamente en un afijo o clítico",
                        key="radio_cd",
                        index=0 if st.session_state.ls_tipo_cd == "constituyente" else (1 if st.session_state.ls_tipo_cd == "afijo" else None),
                        label_visibility="collapsed"
                    )
                
                    if st.session_state.ls_tipo_cd == "constituyente":
                        st.session_state.ls_y_input = st.text_input(
                            "CD",
                            value=st.session_state.get('ls_y_input', ''),
                            placeholder="Escribe el complemento directo sin «a», si es pertinente",
                            key="input_cd",
                            label_visibility="collapsed"
                        )
                    elif st.session_state.ls_tipo_cd == "afijo":
                        st.write("Escoge los rasgos pertinentes:")
                        rasgos_cd = st.selectbox(
                            "Rasgos del CD",
                            options=list(RASGOS_OPCIONES.keys()),
                            key="select_cd",
                            label_visibility="collapsed"
                        )
                        st.session_state.ls_y_input = RASGOS_OPCIONES[rasgos_cd]
              
            # --- COMPLEMENTO INDIRECTO ---
            with st.container(border=True):
                st.session_state.ls_arg_ci = st.checkbox("Complemento indirecto", value=st.session_state.ls_arg_ci, key="chk_ci")
            
                if st.session_state.ls_arg_ci:
                    st.session_state.ls_tipo_ci = st.radio(
                        "Tipo de expresión del CI",
                        options=["constituyente", "afijo"],
                        format_func=lambda x: "La información se expresa en un constituyente sintáctico" if x == "constituyente" else "La información se expresa únicamente en un afijo o clítico",
                        key="radio_ci",
                        index=0 if st.session_state.ls_tipo_ci == "constituyente" else (1 if st.session_state.ls_tipo_ci == "afijo" else None),
                        label_visibility="collapsed"
                    )
                
                    if st.session_state.ls_tipo_ci == "constituyente":
                        st.session_state.ls_z_input = st.text_input(
                            "CI",
                            value=st.session_state.get('ls_z_input', ''),
                            placeholder="Escribe el complemento indirecto sin «a», si es pertinente",
                            key="input_ci",
                            label_visibility="collapsed"
                        )
                    elif st.session_state.ls_tipo_ci == "afijo":
                        st.write("Escoge los rasgos pertinentes:")
                        rasgos_ci = st.selectbox(
                            "Rasgos del CI",
                            options=list(RASGOS_OPCIONES.keys()),
                            key="select_ci",
                            label_visibility="collapsed"
                        )
                        st.session_state.ls_z_input = RASGOS_OPCIONES[rasgos_ci]
            
            # Botón para avanzar
            def _guardar_argumentos():
                # Sujeto
                if st.session_state.ls_arg_sujeto:
                    valor = st.session_state.get('ls_x_input', '').strip()
                    st.session_state.ls_x = valor if valor else 'Ø'
                else:
                    st.session_state.ls_x = 'Ø'
                
                # CD
                if st.session_state.ls_arg_cd:
                    valor = st.session_state.get('ls_y_input', '').strip()
                    st.session_state.ls_y = valor if valor else 'Ø'
                else:
                    st.session_state.ls_y = 'Ø'
                
                # CI
                if st.session_state.ls_arg_ci:
                    valor = st.session_state.get('ls_z_input', '').strip()
                    st.session_state.ls_z = valor if valor else 'Ø'
                else:
                    st.session_state.ls_z = 'Ø'
                
                st.session_state.ls_paso = 'dinamicidad'
            
            st.button("Siguiente", use_container_width=True, key="btn_args_siguiente", on_click=_guardar_argumentos)
            botones_navegacion()

        # --- PASO: DINAMICIDAD ---
        elif st.session_state.ls_paso == 'dinamicidad':
            if st.session_state.get('ls_es_dinamico') is not None:
                ir_a('caso_especial_check')
            
            st.markdown("#### **Verificación de dinamicidad**")
            oracion = st.session_state.ls_oracion
            AKT = st.session_state.ls_akt
            
            if AKT in ["actividad", "actividad causativa", "realización activa", "realización activa causativa"]:
                st.session_state.ls_es_dinamico = True
                ir_a('caso_especial_check')
            elif AKT in ["estado", "estado causativo", "realización causativa", "proceso causativo"]:
                st.session_state.ls_es_dinamico = False
                ir_a('caso_especial_check')
            elif AKT in ["logro", "semelfactivo"]:
                st.info(f"¿**{oracion[0].upper() + oracion[1:]}** es compatible con expresiones como *enérgicamente*, *con fuerza* o *con ganas*?")
                c1, c2 = st.columns(2)
                c1.button("Sí", use_container_width=True, key="din_si", on_click=crear_callback_ir_a('caso_especial_check', ls_es_dinamico=True))
                c2.button("No", use_container_width=True, key="din_no", on_click=crear_callback_ir_a('caso_especial_check', ls_es_dinamico=False))
            elif AKT in ["logro causativo", "semelfactivo causativo"]:
                with st.form(key="form_din_caus"):
                    st.info(f"Escribe el evento resultante de **{oracion}**, sin el segmento causativo (ej.:*el gato rompió el jarrón* → **el jarrón se rompió**):")
                    clausula_res = st.text_input("Resultado", label_visibility="collapsed")
                    if st.form_submit_button("Siguiente", use_container_width=True):
                        st.session_state.ls_clausula_resultante = clausula_res
                        ir_a('dinamicidad_confirm')
            else:
                st.session_state.ls_es_dinamico = False
                ir_a('caso_especial_check')
            botones_navegacion()

        elif st.session_state.ls_paso == 'dinamicidad_confirm':
            clausula = st.session_state.get('ls_clausula_resultante', '')
            st.info(f"¿Es **{clausula}** compatible con expresiones como *enérgicamente*, *con fuerza* o *con ganas*?")
            c1, c2 = st.columns(2)
            c1.button("Sí", use_container_width=True, key="din_conf_si", on_click=crear_callback_ir_a('caso_especial_check', ls_es_dinamico=True))
            c2.button("No", use_container_width=True, key="din_conf_no", on_click=crear_callback_ir_a('caso_especial_check', ls_es_dinamico=False))
            botones_navegacion()

        # --- PASO: PREDICADO ---
        elif st.session_state.ls_paso == 'predicado':
            st.markdown("#### **Identificación del predicado**")
            AKT = st.session_state.ls_akt
            es_dinamico = st.session_state.ls_es_dinamico
            y = st.session_state.ls_y
            
            # Determinar qué tipo de predicado pedir
            if AKT in ["actividad causativa", "realización activa causativa"] or (AKT in ["logro causativo", "semelfactivo causativo"] and es_dinamico):
                st.session_state.ls_pred = ""
                ir_a('predicados_especiales_check')
            elif (AKT in ["actividad", "realización activa"]) or (AKT in ["logro", "semelfactivo"] and es_dinamico) or (y != "Ø" and "causativ" not in AKT):
                with st.form(key="form_pred_inf"):
                    st.info("Escribe el **infinitivo** del verbo:")
                    pred = st.text_input("Infinitivo", label_visibility="collapsed")
                    if st.form_submit_button("Siguiente", use_container_width=True):
                        st.session_state.ls_pred = pred.lower().replace(" ", ".")
                        ir_a('predicados_especiales_check')
                botones_navegacion()
            else:
                with st.form(key="form_pred_part"):
                    st.info("Escribe el **infinitivo** del verbo (o el **adjetivo/atributo** si se trata de un verbo copulativo o seudocopulativo):")
                    pred = st.text_input("Predicado", label_visibility="collapsed")
                    tipo_pred = st.radio(
                        "Tipo de predicado",
                        options=["Verbo", "Adjetivo/atributo"],
                        index=None,
                        horizontal=True,
                        label_visibility="collapsed"
                    )
                    if st.form_submit_button("Siguiente", use_container_width=True):
                        if not tipo_pred:
                            st.warning("Por favor, indica si es un verbo o un adjetivo/atributo.")
                        elif not pred.strip():
                            st.warning("Por favor, escribe el predicado.")
                        else:
                            pred_limpio = pred.lower().replace(" ", ".")
                            if tipo_pred == "Adjetivo/atributo":
                                st.session_state.ls_pred = pred_limpio
                            elif pred_limpio.endswith(("ar", "er", "ir", "arse", "erse", "irse")):
                                st.session_state.ls_pred = infinitivo_a_participio(pred_limpio).replace(" ", ".")
                            else:
                                st.session_state.ls_pred = pred_limpio
                            ir_a('predicados_especiales_check')
                botones_navegacion()

        # --- PASO: VERIFICACIÓN DE CASOS ESPECIALES ---
        elif st.session_state.ls_paso == 'caso_especial_check':
            AKT = st.session_state.ls_akt
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            z = st.session_state.ls_z
            oracion = st.session_state.ls_oracion
            es_dinamico = st.session_state.ls_es_dinamico
            operador = MODIFICADORES_AKT.get(AKT, "")
            
            # Verificar verbos tipo "doler/gustar" y dativo experimentante
            if "causativ" not in AKT and AKT != "realización activa" and x != "Ø" and y == "Ø" and z != "Ø":
                st.session_state.ls_caso_actual = 'doler_gustar'
                ir_a('pregunta_filtro_se')
            # Verificar "hacer" meteorológico
            elif x == "Ø" and y != "Ø":
                st.session_state.ls_caso_actual = 'hacer_meteo'
                ir_a('pregunta_hacer_meteo')
            # Casos impersonales
            elif not es_dinamico and x == "Ø" and y == "Ø" and z != "Ø":
                ir_a('caso_impersonal')
            # Locativo-dativos
            elif "causativ" not in AKT and AKT != "estado" and x != "Ø" and y == "Ø" and z != "Ø":
                st.session_state.ls_caso_actual = 'locativo_dativo'
                ir_a('pregunta_locativo_dativo')
            # Casos especiales de estado
            elif AKT == "estado":
                ir_a('caso_estado')
            # Causativos con sensaciones (estado, logro, realización, proceso)
            elif AKT in ["estado causativo", "logro causativo", "realización causativa", "proceso causativo"]:
                ir_a('caso_causativo_sensacion_check')
            # Verbos con OI
            elif z != "Ø":
                ir_a('caso_oi')    
            # Otros casos
            else:
                ir_a('caso_locativo')

        # --- PREGUNTAS ESPECÍFICAS PARA CASOS ESPECIALES ---
        # --- PREGUNTA FILTRO SE (distingue dativo experimentante de doler/gustar) ---
        elif st.session_state.ls_paso == 'pregunta_filtro_se':
            oracion = st.session_state.ls_oracion
            st.info(f"""¿La oración **{oracion[0].upper() + oracion[1:]}** contiene la partícula **se** (como en *se me/te/le*)?

• Ejemplos con **se**: *Se me perdió el reloj*, *A Pepe se le olvidaron las llaves*  
• Ejemplos sin **se**: *Te duele la cabeza*, *A Ana le gustan los helados*""")
            c1, c2 = st.columns(2)
            c1.button("Sí, lleva SE", use_container_width=True, key="filtro_se_si", on_click=crear_callback_ir_a('pred_dativo_experimentante'))
            c2.button("No lleva SE", use_container_width=True, key="filtro_se_no", on_click=crear_callback_ir_a('pregunta_doler_gustar'))
            botones_navegacion()

        elif st.session_state.ls_paso == 'pred_dativo_experimentante':
            with st.form(key="form_pred_dat_exp"):
                st.info("Escribe el **infinitivo** del verbo:")
                pred = st.text_input("Infinitivo", label_visibility="collapsed")
                if st.form_submit_button("Generar estructura"):
                    st.session_state.ls_pred = pred.lower().replace(" ", ".")
                    ir_a('generar_dativo_experimentante')
            botones_navegacion()

        elif st.session_state.ls_paso == 'generar_dativo_experimentante':
            x = st.session_state.ls_x
            z = st.session_state.ls_z
            pred = st.session_state.ls_pred
            operador = MODIFICADORES_AKT.get(st.session_state.ls_akt, "")

            participio = infinitivo_a_participio(pred).replace(" ", ".")

            st.session_state.ls_participio_dat_exp = participio
            st.session_state.ls_operador_dat_exp = operador
            ir_a('anticausativa_dativo_experimentante')

        elif st.session_state.ls_paso == 'anticausativa_dativo_experimentante':
            x = st.session_state.ls_x
            z = st.session_state.ls_z
            participio = st.session_state.ls_participio_dat_exp
            operador = st.session_state.ls_operador_dat_exp

            st.info("¿El verbo de la cláusula tiene una contraparte causativa (ej.: *romperse* / *romper*)?")
            c1, c2 = st.columns(2)

            def _anti_dat_si():
                ls = f"[do' (Ø, Ø)] CAUSE [{operador + ' ' if operador else ''}{participio}' ({x})] ∧ affected' ({z})"
                st.session_state.ls_estructura = ls
                st.session_state.ls_paso = 'resultado'

            def _anti_dat_no():
                ls = f"{operador + ' ' if operador else ''}{participio}' ({x}) ∧ affected' ({z})"
                st.session_state.ls_estructura = ls
                st.session_state.ls_paso = 'resultado'

            c1.button("Sí", use_container_width=True, key="anti_dat_si", on_click=_anti_dat_si)
            c2.button("No", use_container_width=True, key="anti_dat_no", on_click=_anti_dat_no)
            botones_navegacion()

        elif st.session_state.ls_paso == 'pregunta_doler_gustar':
            x = st.session_state.ls_x
            z = st.session_state.ls_z
            st.info(f"¿**{x[0].upper() + x[1:]}** es una parte de **{z}**?")
            c1, c2 = st.columns(2)
            
            def _dg_si1():
                st.session_state.ls_respuestas['doler_gustar_parte'] = True
                st.session_state.ls_paso = 'pred_doler_gustar'
            
            def _dg_no1():
                st.session_state.ls_respuestas['doler_gustar_parte'] = False
                st.session_state.ls_paso = 'pregunta_doler_gustar_2'
            
            c1.button("Sí", use_container_width=True, key="dg_si1", on_click=_dg_si1)
            c2.button("No", use_container_width=True, key="dg_no1", on_click=_dg_no1)
            botones_navegacion()

        elif st.session_state.ls_paso == 'pregunta_doler_gustar_2':
            z = st.session_state.ls_z
            x = st.session_state.ls_x
            oracion = st.session_state.ls_oracion
            st.info(f"""¿**{oracion[0].upper() + oracion[1:]}** tiene una estructura parecida a alguno de estos ejemplos?

• *Me/te/le [verbo] {x}*  
• *A {z} me/te/le [verbo] {x}*""")
            c1, c2 = st.columns(2)
            
            def _dg2_si():
                st.session_state.ls_respuestas['doler_gustar_estructura'] = True
                st.session_state.ls_paso = 'pred_doler_gustar'
            
            def _dg2_no():
                # Si AKT != "estado", verificar locativo_dativo (como en CLI)
                AKT = st.session_state.ls_akt
                if AKT != "estado":
                    st.session_state.ls_paso = 'pregunta_locativo_dativo'
                else:
                    st.session_state.ls_paso = 'caso_locativo'
            
            c1.button("Sí", use_container_width=True, key="dg2_si", on_click=_dg2_si)
            c2.button("No", use_container_width=True, key="dg2_no", on_click=_dg2_no)
            botones_navegacion()

        elif st.session_state.ls_paso == 'pred_doler_gustar':
            with st.form(key="form_pred_dg"):
                st.info("Escribe el **infinitivo** del verbo:")
                pred = st.text_input("Infinitivo", label_visibility="collapsed")
                if st.form_submit_button("Generar estructura"):
                    st.session_state.ls_pred = pred.lower().replace(" ", ".")
                    ir_a('generar_doler_gustar')
            botones_navegacion()

        elif st.session_state.ls_paso == 'generar_doler_gustar':
            x = st.session_state.ls_x
            z = st.session_state.ls_z
            pred = st.session_state.ls_pred
            es_dinamico = st.session_state.ls_es_dinamico
            operador = MODIFICADORES_AKT.get(st.session_state.ls_akt, "")
            
            if st.session_state.ls_respuestas.get('doler_gustar_parte'):
                if es_dinamico:
                    ls = f"{operador + ' ' if operador else ''}do' ({x}, [{pred}' ({x})]) ∧ have.as.part' ({z}, {x})"
                else:
                    ls = f"{operador + ' ' if operador else ''}{pred}' ({x}) ∧ have.as.part' ({z}, {x})"
            else:
                if es_dinamico:
                    ls = f"{operador + ' ' if operador else ''}do' ({x}, [{pred}' ({x}, {z})]) [MR1]"
                else:
                    ls = f"{operador + ' ' if operador else ''}{pred}' ({x}, {z}) [MR1]"
            
            st.session_state.ls_estructura = ls
            ir_a_intencionalidad()

        elif st.session_state.ls_paso == 'pregunta_hacer_meteo':
            oracion = st.session_state.ls_oracion
            st.info(f"¿El verbo de **{oracion}** es *hacer*?")
            c1, c2 = st.columns(2)
            c1.button("Sí", use_container_width=True, key="hm_si", on_click=crear_callback_ir_a('pred_hacer_meteo'))
            c2.button("No", use_container_width=True, key="hm_no", on_click=crear_callback_ir_a('caso_locativo'))
            botones_navegacion()

        elif st.session_state.ls_paso == 'pred_hacer_meteo':
            with st.form(key="form_hacer_meteo"):
                st.info("Escribe la sensación en forma de adjetivo (ej.: *caluroso*):")
                pred = st.text_input("Sensación", label_visibility="collapsed")
                if st.form_submit_button("Generar estructura"):
                    pred = pred.lower().replace(" ", ".")
                    es_dinamico = st.session_state.ls_es_dinamico
                    operador = MODIFICADORES_AKT.get(st.session_state.ls_akt, "")
                    if es_dinamico:
                        ls = f"{operador + ' ' if operador else ''}do' (weather, [{pred}' (weather)])"
                    else:
                        ls = f"{operador + ' ' if operador else ''}{pred}' (weather)"
                    st.session_state.ls_estructura = ls
                    ir_a_intencionalidad()
            botones_navegacion()

        elif st.session_state.ls_paso == 'caso_impersonal':
            st.markdown("#### **Caso impersonal**")
            with st.form(key="form_impersonal"):
                st.info("Escribe el infinitivo del verbo:")
                verbo = st.text_input("Infinitivo", label_visibility="collapsed")
                if st.form_submit_button("Siguiente"):
                    verbo = verbo.lower().replace(" ", ".")
                    st.session_state.ls_verbo_impersonal = verbo
                    st.session_state.ls_pred = verbo  # Guardar para el panel
                    if verbo in ["ir", "irme", "irte", "irle", "irnos", "iros", "irles"]:
                        ir_a('impersonal_ir')
                    elif verbo in ["bastar", "sobrar"]:
                        ir_a('impersonal_bastar')
                    else:
                        ir_a('caso_locativo')
            botones_navegacion()

        elif st.session_state.ls_paso == 'impersonal_ir':
            with st.form(key="form_imp_ir"):
                st.info("Escribe el adverbio o equivalente (ej.: *bien*):")
                pred = st.text_input("adverbio", label_visibility="collapsed")
                if st.form_submit_button("Generar estructura"):
                    pred = pred.lower().replace(" ", ".")
                    z = st.session_state.ls_z
                    operador = MODIFICADORES_AKT.get(st.session_state.ls_akt, "")
                    ls = f"{operador + ' ' if operador else ''}{pred}' ({z}) [MR0]"
                    st.session_state.ls_estructura = ls
                    ir_a_intencionalidad()
            botones_navegacion()

        elif st.session_state.ls_paso == 'impersonal_bastar':
            with st.form(key="form_imp_bastar"):
                suplemento = st.text_input("Escribe la información del complemento sin preposición (ej.: *tu amistad*):")
                if st.form_submit_button("Generar estructura"):
                    z = st.session_state.ls_z
                    operador = MODIFICADORES_AKT.get(st.session_state.ls_akt, "")
                    st.session_state.ls_complemento_regimen = suplemento  # Guardar
                    ls = f"{operador + ' ' if operador else ''}have.enough.with' ({z}, {suplemento}) [MR0]"
                    st.session_state.ls_estructura = ls
                    ir_a_intencionalidad()
            botones_navegacion()

        elif st.session_state.ls_paso == 'pregunta_locativo_dativo':
            x = st.session_state.ls_x
            z = st.session_state.ls_z
            st.info(f"¿*{z[0].upper() + z[1:]}* señala el destino de un desplazamiento por parte de *{x}*?")
            c1, c2 = st.columns(2)
            c1.button("Sí", use_container_width=True, key="ld_si", on_click=crear_callback_ir_a('generar_locativo_dativo'))
            c2.button("No", use_container_width=True, key="ld_no", on_click=crear_callback_ir_a('caso_oi'))
            botones_navegacion()

        elif st.session_state.ls_paso == 'generar_locativo_dativo':
            AKT = st.session_state.ls_akt
            x = st.session_state.ls_x
            z = st.session_state.ls_z
            es_dinamico = st.session_state.ls_es_dinamico
            operador = MODIFICADORES_AKT.get(AKT, "")
            
            if AKT == "realización activa":
                with st.form(key="form_ld_ra"):
                    st.info("Escribe el **infinitivo** del verbo:")
                    pred = st.text_input("Infinitivo", label_visibility="collapsed")
                    if st.form_submit_button("Generar estructura"):
                        pred = pred.lower().replace(" ", ".")
                        st.session_state.ls_pred = pred
                        ls = f"do' ({x}, [{pred}' ({x})]) ∧ PROC covering.path.distance' ({x}) ∧ FIN be-LOC' ({z}, {x})"
                        st.session_state.ls_estructura = ls
                        ir_a_intencionalidad()
            else:
                if es_dinamico:
                    ls = f"{operador + ' ' if operador else ''}do' ({x}, [be-LOC' ({z}, {x})])"
                else:
                    ls = f"{operador + ' ' if operador else ''}be-LOC' ({z}, {x})"
                st.session_state.ls_estructura = ls
                ir_a_intencionalidad()
            botones_navegacion()

        # --- CASO OI (verbos con objeto indirecto) ---
        elif st.session_state.ls_paso == 'caso_oi':
            st.markdown("#### **Verbo con complemento indirecto**")
            AKT = st.session_state.ls_akt
            
            # Para realización activa, verificar si es verbo de dicción primero
            if AKT == "realización activa":
                with st.form(key="form_oi_pred_ra"):
                    st.info("Escribe el **infinitivo** del verbo:")
                    pred = st.text_input("Infinitivo", label_visibility="collapsed")
                    if st.form_submit_button("Siguiente"):
                        st.session_state.ls_pred = pred.lower().replace(" ", ".")
                        ir_a('pregunta_diccion_ra')
            # Para realización activa causativa (ej.: "Pepe le enseñó francés a Ana")
            elif AKT == "realización activa causativa":
                with st.form(key="form_oi_pred_rac"):
                    st.info("Escribe el **infinitivo** del verbo:")
                    pred = st.text_input("Infinitivo", label_visibility="collapsed")
                    if st.form_submit_button("Siguiente"):
                        st.session_state.ls_pred = pred.lower().replace(" ", ".")
                        ir_a('pregunta_ensenar_rac')
            else:
                with st.form(key="form_oi_pred"):
                    st.info("Escribe el **infinitivo** del verbo:")
                    pred = st.text_input("Infinitivo", label_visibility="collapsed")
                    if st.form_submit_button("Siguiente"):
                        st.session_state.ls_pred = pred.lower().replace(" ", ".")
                        ir_a('verificar_tipo_oi')
            botones_navegacion()

        # Pregunta enseñar/mostrar para realización activa causativa
        elif st.session_state.ls_paso == 'pregunta_ensenar_rac':
            pred = st.session_state.ls_pred
            st.info(f"¿Es **{pred}** un verbo como *enseñar* o *mostrar*?")
            c1, c2 = st.columns(2)
            
            def _ens_rac_si():
                x = st.session_state.ls_x
                y = st.session_state.ls_y
                z = st.session_state.ls_z
                pred = st.session_state.ls_pred
                ls = f"[do' ({x}, [{pred}' ({x}, {y})])] CAUSE [do' ({z}, [know' ({z}, {y})]) ∧ PROC being.created' ({y}) ∧ FIN exist' ({y})]"
                st.session_state.ls_estructura = ls
                st.session_state.ls_estructura_pre_do = st.session_state.ls_estructura
                st.session_state.ls_paso = 'intencionalidad'
            
            c1.button("Sí", use_container_width=True, key="ens_rac_si", on_click=_ens_rac_si)
            c2.button("No", use_container_width=True, key="ens_rac_no", on_click=crear_callback_ir_a('caso_locativo'))
            botones_navegacion()

        # Pregunta de dicción para realización activa
        elif st.session_state.ls_paso == 'pregunta_diccion_ra':
            pred = st.session_state.ls_pred
            st.info(f"¿Es **{pred}** un verbo de dicción?")
            c1, c2 = st.columns(2)
            c1.button("Sí", use_container_width=True, key="dicc_ra_si", on_click=crear_callback_ir_a('generar_diccion_ra'))
            c2.button("No", use_container_width=True, key="dicc_ra_no", on_click=crear_callback_ir_a('caso_locativo'))
            botones_navegacion()

        # Generación de dicción para realización activa (estructura especial con being.created)
        elif st.session_state.ls_paso == 'generar_diccion_ra':
            pred = st.session_state.ls_pred
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            z = st.session_state.ls_z
            
            y_clean = "something" if y in ["Ø", "0"] else y.replace(" ", ".")
            
            if pred in VERBOS_DICCION["preguntar"]:
                ls = f"[do' ({x}, [express.question' ({x}, pregunta)]) ∧ PROC being.created' (pregunta) ∧ FIN exist' (pregunta)] PURP [do' ({z}, [express.something' ({z}, {y})])]"
            elif pred in VERBOS_DICCION["agradecer"]:
                arg_inc = VERBOS_DICCION["agradecer"].get(pred, pred)
                ls = f"[do' ({x}, [express.{arg_inc}' ({x}, {y})]) ∧ PROC being.created' ({arg_inc}) ∧ FIN exist' ({arg_inc})] PURP [know' ({z}, {arg_inc} por {y})]"
            elif pred in VERBOS_DICCION["bendecir"]:
                arg_inc = VERBOS_DICCION["bendecir"].get(pred, pred)
                ls = f"[do' ({x}, [express.{arg_inc}' ({x}, {y})]) ∧ PROC being.created' ({arg_inc}) ∧ FIN exist' ({arg_inc})] PURP [know' ({z}, {arg_inc} de {y})]"
            else:
                ls = f"[do' ({x}, [express.something' ({x}, {y})]) ∧ PROC being.created' ({y}) ∧ FIN exist' ({y})] PURP [know' ({z}, {y})]"
            
            st.session_state.ls_estructura = ls
            ir_a_intencionalidad()

        elif st.session_state.ls_paso == 'verificar_tipo_oi':
            pred = st.session_state.ls_pred
            AKT = st.session_state.ls_akt
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            z = st.session_state.ls_z
            operador = MODIFICADORES_AKT.get(AKT, "")
            
            # Verificar transferencia
            if pred in VERBOS_TRANSFERENCIA["sacar"]:
                if pred == "arrancar" and "causativ" not in AKT:
                    ir_a('caso_locativo')
                else:
                    ls = f"[do' ({x}, Ø)] CAUSE [{operador + ' ' if operador else ''}NOT have' ({z}, {y})] PURP [have' ({x}, {y})]"
                    st.session_state.ls_estructura = ls
                    ir_a_intencionalidad()
            elif pred in VERBOS_TRANSFERENCIA["dar_poner"] or (pred == "pegar" and y != "Ø"):
                ls = f"[do' ({x}, Ø)] CAUSE [{operador + ' ' if operador else ''}have' ({z}, {y})]"
                st.session_state.ls_estructura = ls
                ir_a_intencionalidad()
            else:
                ir_a('pregunta_transferencia')

        elif st.session_state.ls_paso == 'pregunta_transferencia':
            pred = st.session_state.ls_pred
            st.info(f"¿El significado típico de **{pred}** es la transferencia de un objeto físico?")
            c1, c2 = st.columns(2)
            
            def _trans_si():
                x = st.session_state.ls_x
                y = st.session_state.ls_y
                z = st.session_state.ls_z
                operador = MODIFICADORES_AKT.get(st.session_state.ls_akt, "")
                ls = f"[do' ({x}, Ø)] CAUSE [{operador + ' ' if operador else ''}have' ({z}, {y})]"
                st.session_state.ls_estructura = ls
                st.session_state.ls_estructura_pre_do = st.session_state.ls_estructura
                st.session_state.ls_paso = 'intencionalidad'
            
            c1.button("Sí", use_container_width=True, key="trans_si", on_click=_trans_si)
            c2.button("No", use_container_width=True, key="trans_no", on_click=crear_callback_ir_a('pregunta_diccion'))
            botones_navegacion()

        elif st.session_state.ls_paso == 'pregunta_diccion':
            pred = st.session_state.ls_pred
            st.info(f"¿Es **{pred}** un verbo de dicción?")
            c1, c2 = st.columns(2)
            c1.button("Sí", use_container_width=True, key="dicc_si", on_click=crear_callback_ir_a('generar_diccion'))
            c2.button("No", use_container_width=True, key="dicc_no", on_click=crear_callback_ir_a('otros_verbos_oi'))
            botones_navegacion()

        elif st.session_state.ls_paso == 'generar_diccion':
            pred = st.session_state.ls_pred
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            z = st.session_state.ls_z
            operador = MODIFICADORES_AKT.get(st.session_state.ls_akt, "")
            
            y_clean = "something" if y in ["Ø", "0"] else y.replace(" ", ".")
            
            if pred in VERBOS_DICCION["preguntar"]:
                ls = f"[{operador + ' ' if operador else ''}do' ({x}, [express.question' ({x})])] PURP [do' ({z}, [express.{y_clean}' ({z}, {y})])]"
            elif pred in VERBOS_DICCION["agradecer"]:
                arg_inc = VERBOS_DICCION["agradecer"].get(pred, pred)
                ls = f"[{operador + ' ' if operador else ''}do' ({x}, [express.{arg_inc}' ({x}, {y})])] PURP [know' ({z}, {arg_inc} por {y})]"
            elif pred in VERBOS_DICCION["bendecir"]:
                arg_inc = VERBOS_DICCION["bendecir"].get(pred, pred)
                ls = f"[{operador + ' ' if operador else ''}do' ({x}, [express.{arg_inc}' ({x}, {y})])] PURP [know' ({z}, {arg_inc} de {y})]"
            else:
                ls = f"[{operador + ' ' if operador else ''}do' ({x}, [express.something' ({x}, {y})])] PURP [know' ({z}, {y})]"
            
            st.session_state.ls_estructura = ls
            ir_a_intencionalidad()

        elif st.session_state.ls_paso == 'otros_verbos_oi':
            pred = st.session_state.ls_pred
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            z = st.session_state.ls_z
            AKT = st.session_state.ls_akt
            operador = MODIFICADORES_AKT.get(AKT, "")
            
            if pred in VERBOS_TRI_NEG["desatribuir"]:
                ls = f"[do' ({x}, Ø)] CAUSE [{operador + ' ' if operador else ''}NOT have' ({z}, {y})]"
                st.session_state.ls_estructura = ls
                ir_a_intencionalidad()
            elif pred in VERBOS_TRI_NEG["ocultar"]:
                ls = f"[do' ({x}, Ø)] CAUSE [{operador + ' ' if operador else ''}NOT know' ({z}, {y})]"
                st.session_state.ls_estructura = ls
                ir_a_intencionalidad()
            else:
                ir_a('pregunta_ensenar')

        elif st.session_state.ls_paso == 'pregunta_ensenar':
            pred = st.session_state.ls_pred
            st.info(f"¿Es **{pred}** un verbo como *enseñar* o *mostrar*?")
            c1, c2 = st.columns(2)
            
            def _ens_si():
                x = st.session_state.ls_x
                y = st.session_state.ls_y
                z = st.session_state.ls_z
                operador = MODIFICADORES_AKT.get(st.session_state.ls_akt, "")
                ls = f"[do' ({x}, Ø)] CAUSE [{operador + ' ' if operador else ''}know' ({z}, {y})]"
                st.session_state.ls_estructura = ls
                st.session_state.ls_estructura_pre_do = st.session_state.ls_estructura
                st.session_state.ls_paso = 'intencionalidad'
            
            def _ens_no():
                if st.session_state.ls_pred in ["pegar", "pegarle"]:
                    x = st.session_state.ls_x
                    z = st.session_state.ls_z
                    operador = MODIFICADORES_AKT.get(st.session_state.ls_akt, "")
                    ls = f"{operador + ' ' if operador else ''}do' ({x}, [hit' ({x}, {z})]) [MR1]"
                    st.session_state.ls_estructura = ls
                    st.session_state.ls_estructura_pre_do = st.session_state.ls_estructura
                    st.session_state.ls_paso = 'intencionalidad'
                else:
                    st.session_state.ls_paso = 'error_oi'
            
            c1.button("Sí", use_container_width=True, key="ens_si", on_click=_ens_si)
            c2.button("No", use_container_width=True, key="ens_no", on_click=_ens_no)
            botones_navegacion()

        elif st.session_state.ls_paso == 'error_oi':
            pred = st.session_state.ls_pred
            z = st.session_state.ls_z

            st.error(
                "Error. No se puede generar una estructura lógica con estos datos.\n\n"
                f"Asegúrate de que **{z}** sea un argumento de **{pred}** y de que no se trate de un dativo ético o parte de una construcción aplicativa."
            )

            botones_navegacion()

        # --- CASOS ESPECIALES DE ESTADO ---
        elif st.session_state.ls_paso == 'caso_estado':
            st.markdown("#### **Caso especial: Estado**")
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            oracion = st.session_state.ls_oracion
            
            if y == "Ø":
                if x == "Ø":
                    st.info(f"¿**{oracion[0].upper() + oracion[1:]}** describe una sensación o fenómeno climático usando *estar* como verbo no auxiliar (ej.: *está nublado*)?")
                    c1, c2 = st.columns(2)
                    c1.button("Sí", use_container_width=True, key="est_clim_si", on_click=crear_callback_ir_a('estado_climatico'))
                    c2.button("No", use_container_width=True, key="est_clim_no", on_click=crear_callback_ir_a('caso_locativo'))
                else:
                    ir_a('pregunta_ser_esencial')
            else:
                ir_a('pregunta_sensacion_od')
            botones_navegacion()

        # --- ESTADO CAUSATIVO CON SENSACIONES ---
        elif st.session_state.ls_paso == 'caso_causativo_sensacion_check':
            AKT = st.session_state.ls_akt
            if AKT == "estado causativo":
                pregunta = "¿El estado es un tipo de sensación o sentimiento (ej.: *miedo*, *amor*, *frío*)?"
            else:
                pregunta = "¿El evento resultante involucra una sensación o sentimiento (ej.: *miedo*, *amor*, *frío*)?"
            st.info(pregunta)
            c1, c2 = st.columns(2)
            c1.button("Sí", use_container_width=True, key="caus_sens_si", on_click=crear_callback_ir_a('causativo_sensacion'))
            c2.button("No", use_container_width=True, key="caus_sens_no", on_click=crear_callback_ir_a('caso_locativo'))
            botones_navegacion()

        elif st.session_state.ls_paso == 'causativo_sensacion':
            AKT = st.session_state.ls_akt
            operador = MODIFICADORES_AKT.get(AKT, "")
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            z = st.session_state.ls_z
            
            # Determinar el experimentante: z si existe, sino y
            experimentante = z if z != "Ø" else y

            with st.form(key="form_caus_sens"):
                st.info("Escribe esa sensación o sentimiento (ej.: *miedo*, *amor*, *frío*):")
                pred = st.text_input("Sensación", label_visibility="collapsed")
                if st.form_submit_button("Generar estructura"):
                    pred = pred.lower().replace(" ", ".")
                    st.session_state.ls_pred = pred
                    if operador:
                        ls = f"[do' ({x}, Ø)] CAUSE [{operador} feel' ({experimentante}, [{pred}'])]"
                    else:
                        ls = f"[do' ({x}, Ø)] CAUSE [feel' ({experimentante}, [{pred}'])]"
                    st.session_state.ls_estructura = ls
                    ir_a_intencionalidad()
            botones_navegacion()

        elif st.session_state.ls_paso == 'estado_climatico':
            with st.form(key="form_est_clim"):
                st.info("Escribe la sensación o fenómeno climático (ej.: *frío*, *nublado*):")
                pred = st.text_input("Sensación", label_visibility="collapsed")
                if st.form_submit_button("Generar estructura"):
                    pred = pred.lower().replace(" ", ".")
                    st.session_state.ls_pred = pred
                    ls = f"{pred}' (weather)"
                    st.session_state.ls_estructura = ls
                    ir_a_intencionalidad()
            botones_navegacion()

        elif st.session_state.ls_paso == 'pregunta_ser_esencial':
            x = st.session_state.ls_x
            oracion = st.session_state.ls_oracion
            st.info(f"¿**{oracion[0].upper() + oracion[1:]}** expresa un atributo esencial del sujeto usando **ser** (ej.: *Ana es alta*)?")
            c1, c2 = st.columns(2)
            c1.button("Sí", use_container_width=True, key="ser_si", on_click=crear_callback_ir_a('estado_ser'))
            c2.button("No", use_container_width=True, key="ser_no", on_click=crear_callback_ir_a('pregunta_sensacion_estado'))
            botones_navegacion()

        elif st.session_state.ls_paso == 'estado_ser':
            with st.form(key="form_est_ser"):
                st.info("Escribe el atributo:")
                pred = st.text_input("Atributo", label_visibility="collapsed")
                if st.form_submit_button("Generar estructura"):
                    pred = pred.lower().replace(" ", ".")
                    st.session_state.ls_pred = pred
                    x = st.session_state.ls_x
                    ls = f"be' ({x}, [{pred}'])"
                    st.session_state.ls_estructura = ls
                    ir_a_intencionalidad()
            botones_navegacion()

        elif st.session_state.ls_paso == 'pregunta_sensacion_estado':
            st.info("¿El estado es un tipo de sensación o sentimiento (ej.: *frío* o *amor*)?")
            st.warning("(Si es un verbo de percepción sensorial, responde que no)")
            c1, c2 = st.columns(2)
            c1.button("Sí", use_container_width=True, key="sens_si", on_click=crear_callback_ir_a('estado_sensacion'))
            c2.button("No", use_container_width=True, key="sens_no", on_click=crear_callback_ir_a('caso_locativo'))
            botones_navegacion()

        elif st.session_state.ls_paso == 'estado_sensacion':
            with st.form(key="form_est_sens"):
                st.info("Escribe esa sensación o sentimiento (ej.: *frío* o *enamorado*):")
                pred = st.text_input("Sensación", label_visibility="collapsed")
                if st.form_submit_button("Generar estructura"):
                    pred = pred.lower().replace(" ", ".")
                    st.session_state.ls_pred = pred
                    x = st.session_state.ls_x
                    ls = f"feel' ({x}, [{pred}'])"
                    st.session_state.ls_estructura = ls
                    ir_a_intencionalidad()
            botones_navegacion()

        elif st.session_state.ls_paso == 'pregunta_sensacion_od':
            y = st.session_state.ls_y
            st.info(f"¿*{y[0].upper() + y[1:]}* expresa una sensación o sentimiento?")
            c1, c2 = st.columns(2)
            
            def _sens_od_si():
                y = st.session_state.ls_y
                y_clean = y.replace(" ", ".")
                x = st.session_state.ls_x
                ls = f"feel' ({x}, [{y_clean}'])"
                st.session_state.ls_estructura = ls
                st.session_state.ls_estructura_pre_do = st.session_state.ls_estructura
                st.session_state.ls_paso = 'intencionalidad'
            
            c1.button("Sí", use_container_width=True, key="sens_od_si", on_click=_sens_od_si)
            c2.button("No", use_container_width=True, key="sens_od_no", on_click=crear_callback_ir_a('caso_locativo'))
            botones_navegacion()

        # --- CASO LOCATIVO ---
        elif st.session_state.ls_paso == 'caso_locativo':
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            oracion = st.session_state.ls_oracion
            
            # Filtrar argumentos presentes (no Ø)
            args_presentes = [f"*{arg}*" for arg in [x, y] if arg != "Ø"]
            texto_participantes = " o ".join(args_presentes) if args_presentes else "los participantes"
            
            msg = (
                f"Considera la cláusula **{oracion}**.\n\n"
                f"¿Alguno de sus constituyentes argumentales (no periféricos) o el atributo (si es pertinente) indica la ubicación, el destino o el punto de partida de **{texto_participantes}**?"
            )

            st.info(msg)
            c1, c2 = st.columns(2)
            c1.button("Sí", use_container_width=True, key="loc_si", on_click=crear_callback_ir_a('obtener_locativo'))
            c2.button("No", use_container_width=True, key="loc_no", on_click=crear_callback_ir_a('info_mente'))
            botones_navegacion()

        elif st.session_state.ls_paso == 'obtener_locativo':
            with st.form(key="form_loc"):
                st.info("Escribe la información del lugar, sin preposición:")
                locus = st.text_input("Lugar", label_visibility="collapsed")
                st.info("Escribe el infinitivo del verbo:")
                pred = st.text_input("infinitivo", label_visibility="collapsed")
                if st.form_submit_button("Siguiente"):
                    st.session_state.ls_locus = locus
                    st.session_state.ls_pred = pred.lower().replace(" ", ".")
                    ir_a('procesar_locativo')
            botones_navegacion()

        elif st.session_state.ls_paso == 'procesar_locativo':
            pred = st.session_state.ls_pred
            locus = st.session_state.ls_locus
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            AKT = st.session_state.ls_akt
            operador = MODIFICADORES_AKT.get(AKT, "")
            es_dinamico = st.session_state.ls_es_dinamico
            
            # Verbo "haber" con locativo
            if pred == "haber":
                if y != "Ø":
                    ls = f"be-LOC' ({locus}, {y}) [MR1]"
                elif x != "Ø":
                    ls = f"be-LOC' ({locus}, {x}) [MR1]"
                else:
                    ls = f"be-LOC' ({locus}, Ø) [MR1]"
                st.session_state.ls_estructura = ls
                ir_a_intencionalidad()
            # Verbo "tener" con locativo
            elif pred in VERBOS_POSESION["tener"]:
                ir_a('pregunta_tener_locativo')
            # Verbo "olvidar" con locativo
            elif pred == "olvidar":
                ls = f"{operador + ' ' if operador else ''}NOT know' ({x}, {y}) ∧ be-LOC' ({locus}, {y})"
                st.session_state.ls_estructura = ls
                ir_a_intencionalidad()
            # Verbos tipo "sacar" con locativo
            elif pred in VERBOS_TRANSFERENCIA["sacar"] and not ((pred == "arrancar" or pred == "retirar") and "causativ" not in AKT):
                ls = f"[do' ({x}, Ø)] CAUSE [{operador + ' ' if operador else ''}NOT be-LOC' ({locus}, {y})]"
                st.session_state.ls_estructura = ls
                ir_a_intencionalidad()
            # Verbos de movimiento
            elif AKT in ("actividad", "logro", "realización", "proceso", "semelfactivo"):
                categoria_mov = buscar_verbo(pred, VERBOS_MOVIMIENTO)
                if categoria_mov:
                    ir_a('pregunta_lugar_tipo')
                else:
                    ir_a('pregunta_resultado_loc')
            # Verbos causativos con locativo
            elif AKT in ("logro causativo", "realización causativa", "proceso causativo", "semelfactivo causativo"):
                ir_a('pregunta_resultado_loc_caus')
            else:
                # Como en CLI: si AKT != "realización activa", cambiar pred a "be-LOC"
                if AKT != "realización activa":
                    st.session_state.ls_pred = "be-LOC"
                ir_a('generar_basico')

        elif st.session_state.ls_paso == 'pregunta_tener_locativo':
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            st.info(f"¿*{y[0].upper() + y[1:]}* está situado en alguna parte de **{x}**?")
            c1, c2 = st.columns(2)
            
            def _ten_loc_si():
                x = st.session_state.ls_x
                y = st.session_state.ls_y
                locus = st.session_state.ls_locus
                ls = f"have.as.part' ({x}, {y}) ∧ be-LOC' ({locus}, {y})"
                st.session_state.ls_estructura = ls
                st.session_state.ls_estructura_pre_do = st.session_state.ls_estructura
                st.session_state.ls_paso = 'intencionalidad'
            
            c1.button("Sí", use_container_width=True, key="ten_loc_si", on_click=_ten_loc_si)
            c2.button("No", use_container_width=True, key="ten_loc_no", on_click=crear_callback_ir_a('pregunta_parentesco_loc'))
            botones_navegacion()

        elif st.session_state.ls_paso == 'pregunta_parentesco_loc':
            y = st.session_state.ls_y
            pred = st.session_state.ls_pred
            
            # Solo preguntar por parentesco si el verbo es uno de estos
            if pred not in ["tener", "poseer", "ostentar", "lucir"]:
                # Ir directamente a generar estructura con pred normal
                x = st.session_state.ls_x
                locus = st.session_state.ls_locus
                ls = f"{pred}' ({x}, {y}) ∧ be-LOC' ({locus}, {y})"
                st.session_state.ls_estructura = ls
                ir_a_intencionalidad()
            else:
                st.info(f"¿*{y[0].upper() + y[1:]}* indica una relación de parentesco?")
                c1, c2 = st.columns(2)
                
                def _par_loc_si():
                    x = st.session_state.ls_x
                    y = st.session_state.ls_y
                    locus = st.session_state.ls_locus
                    ls = f"have.as.kin' ({x}, {y}) ∧ be-LOC' ({locus}, {y})"
                    st.session_state.ls_estructura = ls
                    st.session_state.ls_estructura_pre_do = st.session_state.ls_estructura
                st.session_state.ls_paso = 'intencionalidad'
                
                def _par_loc_no():
                    x = st.session_state.ls_x
                    y = st.session_state.ls_y
                    pred = st.session_state.ls_pred
                    locus = st.session_state.ls_locus
                    ls = f"{pred}' ({x}, {y}) ∧ be-LOC' ({locus}, {y})"
                    st.session_state.ls_estructura = ls
                    st.session_state.ls_estructura_pre_do = st.session_state.ls_estructura
                st.session_state.ls_paso = 'intencionalidad'
                
                c1.button("Sí", use_container_width=True, key="par_loc_si", on_click=_par_loc_si)
                c2.button("No", use_container_width=True, key="par_loc_no", on_click=_par_loc_no)
                botones_navegacion()

        elif st.session_state.ls_paso == 'pregunta_resultado_loc':
            x = st.session_state.ls_x
            locus = st.session_state.ls_locus
            st.info(f"¿Como resultado del evento, **{x}** dejó de estar o llegó a estar en **{locus}**?")
            c1, c2 = st.columns(2)
            c1.button("Sí", use_container_width=True, key="res_loc_si", on_click=crear_callback_ir_a('pregunta_lugar_tipo'))
            c2.button("No", use_container_width=True, key="res_loc_no", on_click=crear_callback_ir_a('generar_basico'))
            botones_navegacion()

        elif st.session_state.ls_paso == 'pregunta_lugar_tipo':
            locus = st.session_state.ls_locus
            st.info(f"¿*{locus[0].upper() + locus[1:]}* es la procedencia o el destino?")
            c1, c2 = st.columns(2)
            c1.button("1. Procedencia", use_container_width=True, key="proc", on_click=crear_callback_ir_a('generar_movimiento', ls_lugar_tipo="1"))
            c2.button("2. Destino", use_container_width=True, key="dest", on_click=crear_callback_ir_a('generar_movimiento', ls_lugar_tipo="2"))
            botones_navegacion()

        elif st.session_state.ls_paso == 'generar_movimiento':
            x = st.session_state.ls_x
            locus = st.session_state.ls_locus
            es_dinamico = st.session_state.ls_es_dinamico
            operador = MODIFICADORES_AKT.get(st.session_state.ls_akt, "")
            lugar_tipo = st.session_state.ls_lugar_tipo
            
            if es_dinamico:
                if lugar_tipo == "1":
                    ls = f"{operador + ' ' if operador else ''}do' ({x}, [NOT be-LOC' ({locus}, {x})])"
                else:
                    ls = f"{operador + ' ' if operador else ''}do' ({x}, [be-LOC' ({locus}, {x})])"
            else:
                if lugar_tipo == "1":
                    ls = f"{operador + ' ' if operador else ''}NOT be-LOC' ({locus}, {x})"
                else:
                    ls = f"{operador + ' ' if operador else ''}be-LOC' ({locus}, {x})"
            
            st.session_state.ls_estructura = ls
            ir_a_intencionalidad()

        elif st.session_state.ls_paso == 'pregunta_resultado_loc_caus':
            y = st.session_state.ls_y
            locus = st.session_state.ls_locus
            st.info(f"¿Como resultado del evento, **{y}** dej.ó de estar o llegó a estar en **{locus}**?")
            c1, c2 = st.columns(2)
            c1.button("Sí", use_container_width=True, key="res_loc_caus_si", on_click=crear_callback_ir_a('pregunta_lugar_tipo_caus'))
            c2.button("No", use_container_width=True, key="res_loc_caus_no", on_click=crear_callback_ir_a('generar_basico'))
            botones_navegacion()

        elif st.session_state.ls_paso == 'pregunta_lugar_tipo_caus':
            locus = st.session_state.ls_locus
            st.info(f"¿*{locus[0].upper() + locus[1:]}* es la procedencia o el destino?")
            c1, c2 = st.columns(2)
            c1.button("Procedencia", use_container_width=True, key="proc_caus", on_click=crear_callback_ir_a('generar_movimiento_caus', ls_lugar_tipo="1"))
            c2.button("Destino", use_container_width=True, key="dest_caus", on_click=crear_callback_ir_a('generar_movimiento_caus', ls_lugar_tipo="2"))
            botones_navegacion()

        elif st.session_state.ls_paso == 'generar_movimiento_caus':
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            locus = st.session_state.ls_locus
            es_dinamico = st.session_state.ls_es_dinamico
            operador = MODIFICADORES_AKT.get(st.session_state.ls_akt, "")
            lugar_tipo = st.session_state.ls_lugar_tipo
            
            if es_dinamico:
                if lugar_tipo == "1":
                    ls = f"[do' ({x}, Ø)] CAUSE [{operador + ' ' if operador else ''}do' ({y}, [NOT be-LOC' ({locus}, {y})])]"
                else:
                    ls = f"[do' ({x}, Ø)] CAUSE [{operador + ' ' if operador else ''}do' ({y}, [be-LOC' ({locus}, {y})])]"
            else:
                if lugar_tipo == "1":
                    ls = f"[do' ({x}, Ø)] CAUSE [{operador + ' ' if operador else ''}NOT be-LOC' ({locus}, {y})]"
                else:
                    ls = f"[do' ({x}, Ø)] CAUSE [{operador + ' ' if operador else ''}be-LOC' ({locus}, {y})]"
            
            st.session_state.ls_estructura = ls
            ir_a_intencionalidad()

        # --- INFORMACIÓN MENTAL ---
        elif st.session_state.ls_paso == 'info_mente':
            y = st.session_state.ls_y
            AKT = st.session_state.ls_akt
            
            if y == "Ø" or "causativ" in AKT or AKT == "realización activa" or AKT == "actividad":
                ir_a('complemento_regimen')
            else:
                x = st.session_state.ls_x
                oracion = st.session_state.ls_oracion
                st.info(f"¿**{oracion[0].upper() + oracion[1:]}** describe que **{x}** tiene en su mente o llega a tener en su mente lo expresado en **{y}**?")
                st.warning("(Si se trata de un verbo de dicción o de percepción sensorial, responde que no)")
                c1, c2 = st.columns(2)
                
                def _mente_si():
                    x = st.session_state.ls_x
                    y = st.session_state.ls_y
                    AKT = st.session_state.ls_akt
                    operador = MODIFICADORES_AKT.get(AKT, "")
                    ls = f"{operador + ' ' if operador else ''}know' ({x}, {y})"
                    st.session_state.ls_estructura = ls
                    st.session_state.ls_estructura_pre_do = st.session_state.ls_estructura
                st.session_state.ls_paso = 'intencionalidad'
                
                c1.button("Sí", use_container_width=True, key="mente_si", on_click=_mente_si)
                c2.button("No", use_container_width=True, key="mente_no", on_click=crear_callback_ir_a('complemento_regimen'))
            botones_navegacion()

        # --- COMPLEMENTO DE RÉGIMEN ---
        elif st.session_state.ls_paso == 'complemento_regimen':
            AKT = st.session_state.ls_akt
            y = st.session_state.ls_y
            oracion = st.session_state.ls_oracion
            
            if AKT in ["estado", "actividad", "proceso", "logro", "realización", "semelfactivo"] and y == "Ø":
                st.info(f"¿Alguno de los constituyentes de **{oracion}** es un complemento de régimen (ej.: *de defectos* en *la obra carece de defectos*)?")
                c1, c2 = st.columns(2)
                c1.button("Sí", use_container_width=True, key="cr_si", on_click=crear_callback_ir_a('obtener_complemento_regimen'))
                c2.button("No", use_container_width=True, key="cr_no", on_click=crear_callback_ir_a('predicado'))
            else:
                ir_a('predicado')
            botones_navegacion()

        elif st.session_state.ls_paso == 'obtener_complemento_regimen':
            with st.form(key="form_cr"):
                st.info("Escribe el infinitivo del verbo:")
                verbo = st.text_input("Infinitivo", label_visibility="collapsed")
                st.info("Escribe la información del complemento de régimen (sin preposición):")
                suplemento = st.text_input("Supl", label_visibility="collapsed")
                if st.form_submit_button("Generar estructura"):
                    pred = verbo.lower().replace(" ", ".")
                    st.session_state.ls_pred = pred
                    st.session_state.ls_complemento_regimen = suplemento  # GUARDAR
                    
                    # Filtro de seguridad para verbos recíprocos (como en el CLI)
                    verbo_aislado = pred.split(".")[0]
                    categoria = buscar_verbo(verbo_aislado, VERBOS_DICCION)
                    if categoria == "conversar":
                        # Abortar y dejar que lo maneje predicados_especiales
                        ir_a('predicados_especiales_check')
                    else:
                        x = st.session_state.ls_x
                        es_dinamico = st.session_state.ls_es_dinamico
                        operador = MODIFICADORES_AKT.get(st.session_state.ls_akt, "")
                        
                        if es_dinamico:
                            ls = f"{operador + ' ' if operador else ''}do' ({x}, [{pred}' ({x}, {suplemento})]) [MR1]"
                        else:
                            ls = f"{operador + ' ' if operador else ''}{pred}' ({x}, {suplemento}) [MR1]"
                        
                        st.session_state.ls_estructura = ls
                        ir_a_intencionalidad()
            botones_navegacion()

        # --- PREDICADOS ESPECIALES (NUEVO - equivalente a predicados_especiales del CLI) ---
        elif st.session_state.ls_paso == 'predicados_especiales_check':
            AKT = st.session_state.ls_akt
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            pred = st.session_state.ls_pred
            es_dinamico = st.session_state.ls_es_dinamico
            operador = MODIFICADORES_AKT.get(AKT, "")
            
            # Casos de percepción impersonal (algo huele mal)
            if pred in VERBOS_PERCEPCION_IMPERSONAL and not es_dinamico and y == "Ø":
                ir_a('percepcion_impersonal')
            # Verbos meteorológicos propios
            elif x == "Ø" and pred in VERBOS_METEOROLOGICOS:
                ls = f"{operador + ' ' if operador else ''}do' ([{pred}'])"
                st.session_state.ls_estructura = ls
                ir_a_intencionalidad()
            # Verbos de conversación recíproca
            elif pred in VERBOS_DICCION["conversar"]:
                ir_a('pregunta_interlocutor')
            # Verbos de olvido
            elif pred in ["olvidar", "desaprender"]:
                if es_dinamico:
                    ls = f"{operador + ' ' if operador else ''}do' ({x}, [NOT know' ({x}, {y})])"
                else:
                    ls = f"{operador + ' ' if operador else ''}NOT know' ({x}, {y})"
                st.session_state.ls_estructura = ls
                ir_a_intencionalidad()
            # Verbos de pérdida
            elif pred in VERBOS_POSESION["perder"]:
                if es_dinamico:
                    ls = f"{operador + ' ' if operador else ''}do' ({x}, [NOT have' ({x}, {y})])"
                else:
                    ls = f"{operador + ' ' if operador else ''}NOT have' ({x}, {y})"
                st.session_state.ls_estructura = ls
                ir_a_intencionalidad()
            # Verbos de obtención
            elif pred in VERBOS_POSESION["obtener"] and y != "Ø":
                if es_dinamico:
                    ls = f"{operador + ' ' if operador else ''}do' ({x}, [INGR have' ({x}, {y})])"
                else:
                    ls = f"{operador + ' ' if operador else ''}have' ({x}, {y})"
                st.session_state.ls_estructura = ls
                ir_a_intencionalidad()
            # Estados especiales
            elif AKT == "estado":
                # Verbos de desconocimiento
                if pred in ["ignorar", "desconocer"]:
                    ls = f"NOT know' ({x}, {y})"
                    st.session_state.ls_estructura = ls
                    ir_a_intencionalidad()
                # Verbos de existencia con sujeto
                elif pred in VERBOS_EXISTENCIA and y == "Ø":
                    ls = f"exist' ({x})"
                    st.session_state.ls_estructura = ls
                    ir_a_intencionalidad()
                # Verbos de existencia sin sujeto ("haber")
                elif pred == "haber":
                    ls = f"exist' ({y}) [MR0]"
                    st.session_state.ls_estructura = ls
                    ir_a_intencionalidad()
                # Posesión alienable, inalienable y de parentesco
                elif pred in VERBOS_POSESION["tener"] and y != "Ø":
                    ir_a('pregunta_posesion_parte')
                else:
                    ir_a('generar_basico')
            else:
                ir_a('generar_basico')

        # Percepción impersonal (algo huele mal)
        elif st.session_state.ls_paso == 'percepcion_impersonal':
            pred = st.session_state.ls_pred
            oracion = st.session_state.ls_oracion
            with st.form(key="form_perc_imp"):
                st.info(f"Escribe la cualidad percibida en **{oracion}** (ej.: *mal*, *raro*, *a chocolate*):")
                cualidad = st.text_input("Cualidad", label_visibility="collapsed")
                if st.form_submit_button("Generar estructura"):
                    cualidad = cualidad.lower().replace(" ", ".")
                    x = st.session_state.ls_x
                    operador = MODIFICADORES_AKT.get(st.session_state.ls_akt, "")
                    verbo_infinitivo = VERBOS_PERCEPCION_IMPERSONAL[pred]
                    ls = f"{operador + ' ' if operador else ''}{verbo_infinitivo}.{cualidad}' ({x})"
                    st.session_state.ls_estructura = ls
                    # No hay intencionalidad para estos casos
                    st.session_state.ls_es_verbo_reciproco = True  # Para saltar intencionalidad
                    ir_a('anticausativa')
            botones_navegacion()

        # Pregunta de interlocutor para verbos recíprocos
        elif st.session_state.ls_paso == 'pregunta_interlocutor':
            oracion = st.session_state.ls_oracion
            st.info(f"¿Hay un interlocutor en **{oracion}**?")
            c1, c2 = st.columns(2)
            c1.button("Sí", use_container_width=True, key="interloc_si", on_click=crear_callback_ir_a('obtener_interlocutor'))
            c2.button("No", use_container_width=True, key="interloc_no", on_click=crear_callback_ir_a('generar_basico'))
            botones_navegacion()

        elif st.session_state.ls_paso == 'obtener_interlocutor':
            with st.form(key="form_interlocutor"):
                st.info("Escribe quién es el interlocutor:")
                interlocutor = st.text_input("inter", label_visibility="collapsed")
                if st.form_submit_button("Siguiente"):
                    st.session_state.ls_interlocutor = interlocutor
                    ir_a('pregunta_intencionalidad_reciproca')
            botones_navegacion()

        elif st.session_state.ls_paso == 'pregunta_intencionalidad_reciproca':
            x = st.session_state.ls_x
            z = st.session_state.ls_interlocutor
            st.info(f"¿Tanto **{x}** como **{z}** actuaron de manera intencional en la conversación?")
            c1, c2 = st.columns(2)
            
            def _gen_reciproco(intencional):
                x = st.session_state.ls_x
                y = st.session_state.ls_y
                z = st.session_state.ls_interlocutor
                operador = MODIFICADORES_AKT.get(st.session_state.ls_akt, "")
                
                x_clean = x.replace(" ", ".")
                y_clean = y.replace(" ", ".")
                z_clean = z.replace(" ", ".")
                
                parte1 = f"[do' ({x}, [express.something.to.{z_clean}' ({x}, {y})])] PURP [{operador + ' ' if operador else ''}know' ({z}, {y})]"
                parte2 = f"[do' ({z}, [express.something.to.{x_clean}' ({z}, {y})])] PURP [{operador + ' ' if operador else ''}know' ({x}, {y})]"
                
                if intencional:
                    ls = f"DO ({parte1}) ∧ DO ({parte2})"
                else:
                    ls = f"{parte1} ∧ {parte2}"
                
                st.session_state.ls_estructura = ls
                st.session_state.ls_es_verbo_reciproco = True
                st.session_state.ls_paso = 'anticausativa'
            
            c1.button("Sí", use_container_width=True, key="rec_int_si", on_click=lambda: _gen_reciproco(True))
            c2.button("No", use_container_width=True, key="rec_int_no", on_click=lambda: _gen_reciproco(False))
            botones_navegacion()

        # Posesión: parte constituyente o parentesco
        elif st.session_state.ls_paso == 'pregunta_posesion_parte':
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            st.info(f"¿*{y[0].upper() + y[1:]}* es una parte constituyente de **{x}**?")
            c1, c2 = st.columns(2)
            
            def _pos_parte_si():
                x = st.session_state.ls_x
                y = st.session_state.ls_y
                ls = f"have.as.part' ({x}, {y})"
                st.session_state.ls_estructura = ls
                st.session_state.ls_estructura_pre_do = st.session_state.ls_estructura
                st.session_state.ls_paso = 'intencionalidad'
            
            c1.button("Sí", use_container_width=True, key="pos_parte_si", on_click=_pos_parte_si)
            c2.button("No", use_container_width=True, key="pos_parte_no", on_click=crear_callback_ir_a('pregunta_posesion_parentesco'))
            botones_navegacion()

        elif st.session_state.ls_paso == 'pregunta_posesion_parentesco':
            pred = st.session_state.ls_pred
            y = st.session_state.ls_y
            
            # Solo preguntar por parentesco si es uno de estos verbos específicos
            if pred in ["tener", "poseer", "ostentar", "lucir"]:
                st.info(f"¿*{y[0].upper() + y[1:]}* indica una relación de parentesco?")
                c1, c2 = st.columns(2)
                
                def _pos_kin_si():
                    x = st.session_state.ls_x
                    y = st.session_state.ls_y
                    ls = f"have.as.kin' ({x}, {y})"
                    st.session_state.ls_estructura = ls
                    st.session_state.ls_estructura_pre_do = st.session_state.ls_estructura
                st.session_state.ls_paso = 'intencionalidad'
                
                def _pos_kin_no():
                    x = st.session_state.ls_x
                    y = st.session_state.ls_y
                    ls = f"have' ({x}, {y})"
                    st.session_state.ls_estructura = ls
                    st.session_state.ls_estructura_pre_do = st.session_state.ls_estructura
                st.session_state.ls_paso = 'intencionalidad'
                
                c1.button("Sí", use_container_width=True, key="pos_kin_si", on_click=_pos_kin_si)
                c2.button("No", use_container_width=True, key="pos_kin_no", on_click=_pos_kin_no)
            else:
                x = st.session_state.ls_x
                ls = f"have' ({x}, {y})"
                st.session_state.ls_estructura = ls
                ir_a_intencionalidad()
            botones_navegacion()

        # --- GENERACIÓN BÁSICA ---
        elif st.session_state.ls_paso == 'generar_basico':
            AKT = st.session_state.ls_akt
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            z = st.session_state.ls_z
            pred = st.session_state.ls_pred
            locus = st.session_state.ls_locus
            es_dinamico = st.session_state.ls_es_dinamico
            operador = MODIFICADORES_AKT.get(AKT, "")
            
            ls = None
            
            if AKT in ["realización activa", "realización activa causativa"]:
                ir_a('realizacion_activa')
            elif es_dinamico and "causativ" in AKT:
                ir_a('actividad_causativa')
            elif AKT in ["estado causativo", "logro causativo", "realización causativa", "proceso causativo", "semelfactivo causativo"]:
                ls = generar_estructura_causativa(x, y, pred, operador)
                if ls:
                    st.session_state.ls_estructura = ls
                    ir_a_intencionalidad()
                else:
                    st.error("No fue posible generar una estructura lógica con estos parámetros.")
                    botones_navegacion()
            elif es_dinamico:
                # Para actividades: verificar percepción solo si y != "Ø" AND locus == "Ø" (como en CLI)
                if y != "Ø" and locus == "Ø":
                    ir_a('pregunta_percepcion')
                else:
                    ls = generar_estructura_actividad(x, y, locus, pred, operador)
                    if ls:
                        st.session_state.ls_estructura = ls
                        ir_a_intencionalidad()
                    else:
                        st.error("No fue posible generar una estructura lógica con estos parámetros.")
                        botones_navegacion()
            elif AKT in ["estado", "logro", "realización", "proceso", "semelfactivo"]:
                # Para no causativos: verificar percepción si AKT != "estado" AND y != "Ø" (como en CLI)
                if AKT != "estado" and y != "Ø":
                    ir_a('pregunta_percepcion')
                else:
                    ls = generar_estructura_no_causativa(x, y, locus, pred, operador, AKT)
                    if ls:
                        st.session_state.ls_estructura = ls
                        ir_a_intencionalidad()
                    else:
                        st.error("No fue posible generar una estructura lógica con estos parámetros.")
                        botones_navegacion()
            else:
                st.error("No fue posible generar una estructura lógica con estos parámetros.")
                botones_navegacion()

        # Pregunta de percepción sensorial (como en CLI)
        elif st.session_state.ls_paso == 'pregunta_percepcion':
            pred = st.session_state.ls_pred
            st.info(f"¿*{pred[0].upper() + pred[1:]}* indica un tipo de percepción sensorial?")
            c1, c2 = st.columns(2)
            
            def _perc_si():
                pred = st.session_state.ls_pred
                pred_lower = pred.lower()
                if pred_lower in VERBOS_PERCEPCION:
                    st.session_state.ls_pred = VERBOS_PERCEPCION[pred_lower]
                    st.session_state.ls_paso = 'generar_basico_final'
                else:
                    st.session_state.ls_paso = 'seleccionar_sentido'
            
            def _perc_no():
                st.session_state.ls_paso = 'generar_basico_final'
            
            c1.button("Sí", use_container_width=True, key="perc_si", on_click=_perc_si)
            c2.button("No", use_container_width=True, key="perc_no", on_click=_perc_no)
            botones_navegacion()

        elif st.session_state.ls_paso == 'seleccionar_sentido':
            st.markdown("#### **Sentido de la percepción**")
            
            with st.form(key="form_sentidos"):
                st.info("Indica el sentido involucrado en el acto de percepción:")
                
                sentidos_map = {
                    "Vista": "see",
                    "Oído": "hear",
                    "Olfato": "smell",
                    "Gusto": "taste",
                    "Tacto": "feel"
                }

                # Widget radial
                seleccion = st.radio(
                    "Sentido",
                    options=list(sentidos_map.keys()),
                    index=None, # Aparece sin selección previa
                    label_visibility="collapsed"
                )
                
                if st.form_submit_button("Confirmar sentido", use_container_width=True):
                    if seleccion:
                        # Asignamos la constante RRG correspondiente (see, hear, etc.)
                        st.session_state.ls_pred = sentidos_map[seleccion]
                        ir_a('generar_basico_final')
                    else:
                        st.warning("Por favor, selecciona una opción antes de continuar.")
            
            botones_navegacion()

        elif st.session_state.ls_paso == 'generar_basico_final':
            AKT = st.session_state.ls_akt
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            pred = st.session_state.ls_pred
            locus = st.session_state.ls_locus
            es_dinamico = st.session_state.ls_es_dinamico
            operador = MODIFICADORES_AKT.get(AKT, "")
            
            if es_dinamico:
                ls = generar_estructura_actividad(x, y, locus, pred, operador)
            else:
                ls = generar_estructura_no_causativa(x, y, locus, pred, operador, AKT)
            
            if ls:
                st.session_state.ls_estructura = ls
                ir_a_intencionalidad()
            else:
                st.error("No fue posible generar una estructura lógica con estos parámetros.")
                botones_navegacion()

        elif st.session_state.ls_paso == 'realizacion_activa':
            st.markdown("#### **Realización activa**")
    
            with st.form(key="form_realizacion_activa"):
                st.info("Selecciona la clase semántica que mejor se ajuste al verbo:")
        
                tipo_verbo = st.radio(
                    "Tipo de verbo",
                    options=["Creación", "Consumo", "Desplazamiento", "Ninguno de estos"],
                    index=None,
                    label_visibility="collapsed"
                )
        
                if st.form_submit_button("Siguiente", use_container_width=True):
                    if tipo_verbo == "Creación":
                        ir_a('ra_creacion')
                    elif tipo_verbo == "Consumo":
                        ir_a('ra_consumo')
                    elif tipo_verbo == "Desplazamiento":
                        ir_a('ra_desplazamiento')
                    elif tipo_verbo == "Ninguno de estos":
                        ir_a('ra_otros')
                    else:
                        st.warning("Por favor, selecciona una opción.")
            botones_navegacion()

        elif st.session_state.ls_paso == 'ra_creacion':
            AKT = st.session_state.ls_akt
            es_causativa = AKT == "realización activa causativa"
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            z = st.session_state.ls_z
            
            if es_causativa:
                with st.form(key="form_ra_creacion_caus"):
                    st.info(f"Escribe en infinitivo la actividad realizada por **{z}** (ej.: *escribir*):")
                    pred = st.text_input("infinitivo", label_visibility="collapsed")
                    if st.form_submit_button("Generar estructura"):
                        pred = pred.lower().replace(" ", ".")
                        st.session_state.ls_pred = pred
                        ls = f"[do' ({x}, Ø)] CAUSE [do' ({z}, [{pred}' ({z}, {y})]) ∧ PROC being.created' ({y}) ∧ FIN exist' ({y})]"
                        st.session_state.ls_estructura = ls
                        ir_a_intencionalidad()
            else:
                pred = st.session_state.ls_pred
                ls = f"do' ({x}, [{pred}' ({x}, {y})]) ∧ PROC being.created' ({y}) ∧ FIN exist' ({y})"
                st.session_state.ls_estructura = ls
                ir_a_intencionalidad()
            botones_navegacion()

        elif st.session_state.ls_paso == 'ra_consumo':
            AKT = st.session_state.ls_akt
            es_causativa = AKT == "realización activa causativa"
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            z = st.session_state.ls_z
            
            if es_causativa:
                with st.form(key="form_ra_consumo_caus"):
                    st.info("Escribe el infinitivo del verbo de la oración original (ej.: *alimentar*):")
                    verbo_original = st.text_input("infinitivo", label_visibility="collapsed")
                    if st.form_submit_button("Siguiente"):
                        st.session_state.ls_verbo_consumo = verbo_original.lower().replace(" ", ".")
                        st.session_state.ls_pred = verbo_original.lower().replace(" ", ".")
                        ir_a('ra_consumo_caus_2')
            else:
                pred = st.session_state.ls_pred
                ls = f"do' ({x}, [{pred}' ({x}, {y})]) ∧ PROC being.consumed' ({y}) ∧ FIN consumed' ({y})"
                st.session_state.ls_estructura = ls
                ir_a_intencionalidad()
            botones_navegacion()

        elif st.session_state.ls_paso == 'ra_consumo_caus_2':
            verbo = st.session_state.ls_verbo_consumo
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            z = st.session_state.ls_z
            
            if verbo in ["alimentar", "nutrir", "cebar", "hidratar", "saciar", "empachar"]:
                with st.form(key="form_ra_consumo_alim"):
                    st.info(f"Escribe en infinitivo la actividad realizada por **{y}** (ej.: *comer*):")
                    pred = st.text_input("infinitivo", label_visibility="collapsed")
                    st.info("Escribe el alimento que fue consumido (ej.: *una manzana*):")
                    alimento = st.text_input("alimento", label_visibility="collapsed")
                    if st.form_submit_button("Generar estructura"):
                        pred = pred.lower().replace(" ", ".")
                        alimento = alimento.lower().replace(" ", ".")
                        ls = f"[do' ({x}, Ø)] CAUSE [do' ({y}, [{pred}' ({y}, {alimento})]) ∧ PROC being.consumed' ({alimento}) ∧ FIN consumed' ({alimento})]"
                        st.session_state.ls_estructura = ls
                        ir_a_intencionalidad()
            else:
                with st.form(key="form_ra_consumo_otro"):
                    st.info(f"Escribe en infinitivo la actividad realizada por **{z}** (ej.: *comer*):")
                    pred = st.text_input("infinitivo", label_visibility="collapsed")
                    if st.form_submit_button("Generar estructura"):
                        pred = pred.lower().replace(" ", ".")
                        ls = f"[do' ({x}, Ø)] CAUSE [do' ({z}, [{pred}' ({z}, {y})]) ∧ PROC being.consumed' ({y}) ∧ FIN consumed' ({y})]"
                        st.session_state.ls_estructura = ls
                        ir_a_intencionalidad()
            botones_navegacion()

        elif st.session_state.ls_paso == 'ra_desplazamiento':
            AKT = st.session_state.ls_akt
            es_causativa = AKT == "realización activa causativa"
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            locus = st.session_state.ls_locus
            pred = st.session_state.ls_pred
            
            # Buscar categoría de movimiento
            categoria_mov = buscar_verbo(pred, VERBOS_MOVIMIENTO)
            if categoria_mov:
                pred = categoria_mov
                st.session_state.ls_pred = pred
            
            if (locus == "Ø" or (locus != "Ø" and y != "Ø")) and not es_causativa:
                ls = f"do' ({x}, [{pred}' ({x})]) ∧ PROC covering.path.distance' ({x}, {y}) ∧ FIN be-LOC' ({locus}, {x})"
                st.session_state.ls_estructura = ls
                ir_a_intencionalidad()
            else:
                ir_a('ra_despl_lugar')
            botones_navegacion()

        elif st.session_state.ls_paso == 'ra_despl_lugar':
            locus = st.session_state.ls_locus
            st.info(f"¿*{locus[0].upper() + locus[1:]}* es (1) la procedencia o (2) el destino?")
            c1, c2 = st.columns(2)
            c1.button("1. Procedencia", use_container_width=True, key="despl_proc", on_click=crear_callback_ir_a('ra_despl_generar', ls_fin_loc="NOT be-LOC'"))
            c2.button("2. Destino", use_container_width=True, key="despl_dest", on_click=crear_callback_ir_a('ra_despl_generar', ls_fin_loc="be-LOC'"))
            botones_navegacion()

        elif st.session_state.ls_paso == 'ra_despl_generar':
            AKT = st.session_state.ls_akt
            es_causativa = AKT == "realización activa causativa"
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            locus = st.session_state.ls_locus
            fin_loc = st.session_state.ls_fin_loc
            
            if es_causativa:
                with st.form(key="form_despl_caus"):
                    st.info(f"Escribe en infinitivo la actividad realizada por **{y}** (ej.: *correr*):")
                    pred = st.text_input("infinitivo", label_visibility="collapsed")
                    if st.form_submit_button("Generar estructura"):
                        pred = pred.lower().replace(" ", ".")
                        st.session_state.ls_pred = pred
                        ls = f"[do' ({x}, Ø)] CAUSE [do' ({y}, [{pred}' ({y})]) ∧ PROC covering.path.distance' ({y}) ∧ FIN {fin_loc} ({locus}, {y})]"
                        st.session_state.ls_estructura = ls
                        ir_a_intencionalidad()
            else:
                pred = st.session_state.ls_pred
                ls = f"do' ({x}, [{pred}' ({x})]) ∧ PROC covering.path.distance' ({x}) ∧ FIN {fin_loc} ({locus}, {x})"
                st.session_state.ls_estructura = ls
                ir_a_intencionalidad()
            botones_navegacion()

        elif st.session_state.ls_paso == 'ra_otros':
            AKT = st.session_state.ls_akt
            es_causativa = AKT == "realización activa causativa"
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            z = st.session_state.ls_z
            oracion = st.session_state.ls_oracion
            
            if es_causativa:
                if z != "Ø":
                    with st.form(key="form_ra_otros_z"):
                        st.info(f"Escribe en infinitivo la actividad realizada por **{z}** (ej.: *comer*):")
                        pred = st.text_input("infinitivo", label_visibility="collapsed")
                        if st.form_submit_button("Generar estructura"):
                            pred = pred.lower().replace(" ", ".")
                            participio = infinitivo_a_participio(pred).replace(" ", ".")
                            st.session_state.ls_pred = pred
                            ls = f"[do' ({x}, Ø)] CAUSE [do' ({z}, [{pred}' ({z}, {y})]) ∧ PROC {participio}' ({y}) ∧ FIN {participio}' ({y})]"
                            st.session_state.ls_estructura = ls
                            ir_a_intencionalidad()
                else:
                    ir_a('ra_otros_regimen')
            else:
                if y != "Ø":
                    pred = st.session_state.ls_pred
                    participio = infinitivo_a_participio(pred).replace(" ", ".")
                    ls = f"do' ({x}, [{pred}' ({x}, {y})]) ∧ PROC {participio}' ({y}) ∧ FIN {participio}' ({y})"
                    st.session_state.ls_estructura = ls
                    ir_a_intencionalidad()
                else:
                    ir_a('ra_otros_regimen_nc')
            botones_navegacion()

        elif st.session_state.ls_paso == 'ra_otros_regimen':
            oracion = st.session_state.ls_oracion
            st.info(f"¿Alguno de los constituyentes de **{oracion}** es un complemento de régimen (ej.: *en mi amigo* en *Ana transformó a Pepe en mi amigo*)?")
            c1, c2 = st.columns(2)
            c1.button("Sí", use_container_width=True, key="ra_reg_si", on_click=crear_callback_ir_a('ra_otros_regimen_form'))
            c2.button("No", use_container_width=True, key="ra_reg_no", on_click=crear_callback_ir_a('ra_otros_sin_regimen'))
            botones_navegacion()

        elif st.session_state.ls_paso == 'ra_otros_regimen_form':
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            with st.form(key="form_ra_reg"):
                st.info(f"Escribe en infinitivo la actividad realizada por **{y}** (ej.: *transformarse*):")
                pred = st.text_input("inf", label_visibility="collapsed")
                st.info("Escribe la preposición regida por el verbo (ej.: *en*):")
                prep = st.text_input("Prep", label_visibility="collapsed")
                st.info("Escribe la información del complemento de régimen (sin preposición) (ej.: *mi amigo*):")
                suplemento = st.text_input("Supl", label_visibility="collapsed")
                if st.form_submit_button("Generar estructura"):
                    pred = pred.lower().replace(" ", ".")
                    participio = infinitivo_a_participio(pred).replace(" ", ".")
                    prep = prep.lower().replace(" ", ".")
                    st.session_state.ls_pred = pred
                    st.session_state.ls_complemento_regimen = suplemento
                    ls = f"[do' ({x}, Ø)] CAUSE [do' ({y}, [{pred}.{prep}' ({y}, {suplemento})]) ∧ PROC {participio}.{prep}' ({y}, {suplemento}) ∧ FIN {participio}.{prep}' ({y}, {suplemento})]"
                    st.session_state.ls_estructura = ls
                    ir_a_intencionalidad()
            botones_navegacion()

        elif st.session_state.ls_paso == 'ra_otros_sin_regimen':
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            with st.form(key="form_ra_sin_reg"):
                st.info(f"Escribe en infinitivo la actividad realizada por **{y}** (ej.: *comer*):")
                pred = st.text_input("Inf", label_visibility="collapsed")
                if st.form_submit_button("Generar estructura"):
                    pred = pred.lower().replace(" ", ".")
                    participio = infinitivo_a_participio(pred).replace(" ", ".")
                    st.session_state.ls_pred = pred
                    ls = f"[do' ({x}, Ø)] CAUSE [do' ({y}, [{pred}' ({y})]) ∧ PROC {participio}' ({y}) ∧ FIN {participio}' ({y})]"
                    st.session_state.ls_estructura = ls
                    ir_a_intencionalidad()
            botones_navegacion()

        elif st.session_state.ls_paso == 'ra_otros_regimen_nc':
            oracion = st.session_state.ls_oracion
            st.info(f"¿Alguno de los constituyentes de **{oracion}** es un complemento de régimen (ej.: *en mi amigo* en *Pepe se transformó en mi amigo*)?")
            c1, c2 = st.columns(2)
            c1.button("Sí", use_container_width=True, key="ra_reg_nc_si", on_click=crear_callback_ir_a('ra_otros_regimen_nc_form'))
            c2.button("No", use_container_width=True, key="ra_reg_nc_no", on_click=crear_callback_ir_a('ra_otros_sin_regimen_nc'))
            botones_navegacion()

        elif st.session_state.ls_paso == 'ra_otros_regimen_nc_form':
            x = st.session_state.ls_x
            pred = st.session_state.ls_pred
            with st.form(key="form_ra_reg_nc"):
                st.info("Escribe la preposición regida por el verbo (ej.: *en*):")
                prep = st.text_input("Prep", label_visibility="collapsed")
                st.info("Escribe la información del complemento de régimen (sin preposición) (ej.: *mi amigo*):")
                suplemento = st.text_input("Supl", label_visibility="collapsed")
                if st.form_submit_button("Generar estructura"):
                    participio = infinitivo_a_participio(pred).replace(" ", ".")
                    prep = prep.lower().replace(" ", ".")
                    st.session_state.ls_complemento_regimen = suplemento
                    ls = f"do' ({x}, [{pred}.{prep}' ({x}, {suplemento})]) ∧ PROC {participio}.{prep}' ({x}, {suplemento}) ∧ FIN {participio}.{prep}' ({x}, {suplemento})"
                    st.session_state.ls_estructura = ls
                    ir_a_intencionalidad()
            botones_navegacion()

        elif st.session_state.ls_paso == 'ra_otros_sin_regimen_nc':
            x = st.session_state.ls_x
            pred = st.session_state.ls_pred
            participio = infinitivo_a_participio(pred).replace(" ", ".")
            ls = f"do' ({x}, [{pred}' ({x})]) ∧ PROC {participio}' ({x}) ∧ FIN {participio}' ({x})"
            st.session_state.ls_estructura = ls
            ir_a_intencionalidad()
            botones_navegacion()

        elif st.session_state.ls_paso == 'actividad_causativa':
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            operador = MODIFICADORES_AKT.get(st.session_state.ls_akt, "")
            
            with st.form(key="form_act_caus"):
                st.info(f"Escribe en infinitivo la actividad realizada por **{y}** (ej.: *comer*):")
                pred = st.text_input("Inf", label_visibility="collapsed")
                if st.form_submit_button("Generar estructura"):
                    pred = pred.lower().replace(" ", ".")
                    st.session_state.ls_pred = pred
                    ls = f"[do' ({x}, Ø)] CAUSE [{operador + ' ' if operador else ''}do' ({y}, [{pred}' ({y})])]"
                    st.session_state.ls_estructura = ls
                    ir_a_intencionalidad()
            botones_navegacion()

        # --- INTENCIONALIDAD ---
        elif st.session_state.ls_paso == 'intencionalidad':
            x = st.session_state.ls_x
            AKT = st.session_state.ls_akt
            es_dinamico = st.session_state.ls_es_dinamico
            oracion = st.session_state.ls_oracion
            es_verbo_reciproco = st.session_state.get('ls_es_verbo_reciproco', False)
            
            # No preguntar intencionalidad si es verbo recíproco (ya se manej.ó)
            if es_verbo_reciproco:
                ir_a('anticausativa')
            elif x != "Ø" and (es_dinamico or "causativ" in AKT):
                st.info(f"¿La acción de **{oracion}** fue efectuada intencionalmente por **{x}**?")
                c1, c2 = st.columns(2)
                
                def _int_si():
                    x = st.session_state.ls_x
                    estructura_con_do = aplicar_DO(x, st.session_state.ls_estructura)
                    st.session_state.ls_estructura = estructura_con_do
                    st.session_state.ls_estructura_con_do = estructura_con_do  # GUARDAR
                    st.session_state.ls_paso = 'anticausativa'
                
                def _int_no():
                    # No hay capa DO, limpiar variable
                    st.session_state.ls_estructura_con_do = ''
                    st.session_state.ls_paso = 'anticausativa'
                
                c1.button("Sí", use_container_width=True, key="int_si", on_click=_int_si)
                c2.button("No", use_container_width=True, key="int_no", on_click=_int_no)
            else:
                ir_a('anticausativa')
            botones_navegacion()

        # --- ANTICAUSATIVA ---
        elif st.session_state.ls_paso == 'anticausativa':
            AKT = st.session_state.ls_akt
            y = st.session_state.ls_y
            
            if AKT in ["realización", "logro", "proceso", "semelfactivo"] and y == "Ø":
                st.info("¿El verbo de la cláusula está construido con el clítico *se* y tiene una contraparte causativa (ej.: *romperse* / *romper*)?")
                c1, c2 = st.columns(2)
                
                def _anti_si():
                    st.session_state.ls_estructura = aplicar_anticausativa(st.session_state.ls_estructura)
                    # Solo actualizar ls_estructura_pre_do si no se aplicó DO
                    if not st.session_state.get('ls_estructura_con_do'):
                        st.session_state.ls_estructura_pre_do = st.session_state.ls_estructura
                    st.session_state.ls_paso = 'resultado'
                
                def _anti_no():
                    # Solo actualizar ls_estructura_pre_do si no se aplicó DO
                    if not st.session_state.get('ls_estructura_con_do'):
                        st.session_state.ls_estructura_pre_do = st.session_state.ls_estructura
                    st.session_state.ls_paso = 'resultado'
                
                c1.button("Sí", use_container_width=True, key="anti_si", on_click=_anti_si)
                c2.button("No", use_container_width=True, key="anti_no", on_click=_anti_no)
            else:
                # Solo actualizar ls_estructura_pre_do si no se aplicó DO
                if not st.session_state.get('ls_estructura_con_do'):
                    st.session_state.ls_estructura_pre_do = st.session_state.ls_estructura
                ir_a('resultado')
            botones_navegacion()

        # --- RESULTADO ---
        elif st.session_state.ls_paso == 'resultado':
            st.markdown("### Estructura lógica generada")
            
            # Aplicar traducción con negritas HTML
            ls_traducida = traducir_ls_a_ingles(st.session_state.ls_estructura, usar_html=True)
            st.session_state.ls_estructura_traducida = ls_traducida
            
            st.markdown(f'<div class="ls-resultado">{ls_traducida}</div>', unsafe_allow_html=True)
            
            # Extraer predicados modificables
            predicados = extraer_predicados_de_ls(ls_traducida)
            st.session_state.ls_predicados_extraidos = predicados
            
            st.write("---")
            
            # Informar sobre traducción automática y ofrecer corrección
            if predicados:
                st.warning("El programa traduce automáticamente los predicados del español al inglés, pero puede cometer errores en casos de ambigüedad léxica.")
                st.info("¿Quieres modificar alguno de los predicados?")
                
                c1, c2 = st.columns(2)
                c1.button("Sí, modificar predicados", use_container_width=True, key="mod_pred_si", on_click=crear_callback_ir_a('seleccionar_predicados'))
                c2.button("No, continuar", use_container_width=True, key="mod_pred_no", on_click=crear_callback_ir_a('preguntar_operadores'))
            else:
                ir_a('preguntar_operadores')
            
            st.write("---")
            st.button("Analizar otra cláusula", use_container_width=True, key="otra", on_click=reiniciar_analisis)

        # --- PREGUNTAR OPERADORES ---
        elif st.session_state.ls_paso == 'preguntar_operadores':
            st.markdown("### Estructura lógica generada")
            
            ls_traducida = st.session_state.ls_estructura_traducida
            st.markdown(f'<div class="ls-resultado">{ls_traducida}</div>', unsafe_allow_html=True)
            
            st.write("---")
            st.info("¿Quieres añadir operadores a la estructura lógica?")
            c1, c2 = st.columns(2)
            
            def _op_no():
                st.session_state.ls_estructura_final = st.session_state.ls_estructura_traducida
                st.session_state.ls_paso = 'final'
            
            c1.button("Sí, añadir operadores", use_container_width=True, key="op_si", on_click=crear_callback_ir_a('seleccionar_operadores'))
            c2.button("No, finalizar", use_container_width=True, key="op_no", on_click=_op_no)
            
            st.write("---")
            st.button("Analizar otra cláusula", use_container_width=True, key="otra_preop", on_click=reiniciar_analisis)

        # --- SELECCIONAR PREDICADOS A MODIFICAR ---
        elif st.session_state.ls_paso == 'seleccionar_predicados':
            st.markdown("### Corrección de predicados")
            
            ls_traducida = st.session_state.ls_estructura_traducida
            st.markdown(f'<div class="ls-resultado">{ls_traducida}</div>', unsafe_allow_html=True)
            
            st.write("---")
            
            predicados = st.session_state.ls_predicados_extraidos
            
            if len(predicados) == 1:
                # Solo un predicado: preguntar directamente
                pred = predicados[0]
                st.info(f"El predicado traducido es **{pred}**. ¿Quieres modificarlo?")
                
                with st.form(key="form_corregir_unico"):
                    nuevo_valor = st.text_input(
                        "Nuevo valor del predicado",
                        value=pred,
                        placeholder="Escribe el predicado corregido",
                        key="input_pred_unico"
                    )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("Guardar cambio", use_container_width=True):
                            if nuevo_valor.strip() and nuevo_valor.strip() != pred:
                                ls_corregida = reemplazar_predicado_en_ls(ls_traducida, pred, nuevo_valor.strip())
                                st.session_state.ls_estructura_traducida = ls_corregida
                            ir_a('preguntar_operadores')
                    with col2:
                        if st.form_submit_button("Cancelar", use_container_width=True):
                            ir_a('preguntar_operadores')
            else:
                # Múltiples predicados: mostrar lista con checkboxes
                st.info("Selecciona los predicados que quieres modificar:")
                
                # Inicializar estado para checkboxes
                if 'ls_preds_a_modificar' not in st.session_state:
                    st.session_state.ls_preds_a_modificar = []
                
                with st.container(border=True):
                    preds_seleccionados = []
                    for i, pred in enumerate(predicados):
                        if st.checkbox(f"**{pred}**", key=f"chk_pred_{i}"):
                            preds_seleccionados.append(pred)
                
                col1, col2 = st.columns(2)
                
                def _continuar_con_seleccion():
                    st.session_state.ls_preds_a_modificar = preds_seleccionados
                    if preds_seleccionados:
                        st.session_state.ls_pred_edit_index = 0
                        st.session_state.ls_paso = 'corregir_predicados'
                    else:
                        st.session_state.ls_paso = 'preguntar_operadores'
                
                col1.button("Continuar", use_container_width=True, key="btn_sel_preds", on_click=_continuar_con_seleccion)
                col2.button("Cancelar", use_container_width=True, key="btn_cancel_preds", on_click=crear_callback_ir_a('preguntar_operadores'))
            
            botones_navegacion()

        # --- CORREGIR PREDICADOS (uno por uno) ---
        elif st.session_state.ls_paso == 'corregir_predicados':
            st.markdown("### Corrección de predicados")
            
            ls_traducida = st.session_state.ls_estructura_traducida
            st.markdown(f'<div class="ls-resultado">{ls_traducida}</div>', unsafe_allow_html=True)
            
            st.write("---")
            
            preds_a_modificar = st.session_state.ls_preds_a_modificar
            indice = st.session_state.get('ls_pred_edit_index', 0)
            
            if indice < len(preds_a_modificar):
                pred_actual = preds_a_modificar[indice]
                total = len(preds_a_modificar)
                
                st.info(f"Predicado {indice + 1} de {total}: **{pred_actual}**")
                
                with st.form(key=f"form_corregir_{indice}"):
                    nuevo_valor = st.text_input(
                        "Escribe el predicado corregido",
                        value=pred_actual,
                        placeholder="Escribe el predicado corregido",
                        key=f"input_pred_{indice}",
                        label_visibility="collapsed"
                    )
                    
                    if st.form_submit_button("Guardar y continuar", use_container_width=True):
                        # Aplicar el cambio si es diferente
                        if nuevo_valor.strip() and nuevo_valor.strip() != pred_actual:
                            ls_corregida = reemplazar_predicado_en_ls(
                                st.session_state.ls_estructura_traducida, 
                                pred_actual, 
                                nuevo_valor.strip()
                            )
                            st.session_state.ls_estructura_traducida = ls_corregida
                        
                        # Avanzar al siguiente predicado o terminar
                        if indice + 1 < len(preds_a_modificar):
                            st.session_state.ls_pred_edit_index = indice + 1
                            st.rerun()
                        else:
                            ir_a('preguntar_operadores')
            else:
                ir_a('preguntar_operadores')
            
            botones_navegacion()

        # --- SELECCIÓN DE OPERADORES ---
        elif st.session_state.ls_paso == 'seleccionar_operadores':
            st.markdown("#### **Selección de operadores**")
            st.info("Marca los operadores que desees añadir e ingresa sus valores:")
    
            with st.form(key="form_ops"):
                ops_seleccionados = []
        
                # Operadores clausulares (índices 0-3)
                st.write("**Operadores clausulares:**")
                for i, op in enumerate(OPERADORES[:4]):
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        checked = st.checkbox(op.descripcion, key=f"op_check_{i}")
                    with col2:
                        if op.requiere_valor:
                            valor = st.text_input(
                                f"Valor para {op.codigo}",
                                placeholder=f"ej.: {op.ejemplos}",
                                key=f"op_val_{i}",
                                label_visibility="collapsed"
                            )
                        else:
                            valor = None
                    if checked:
                        ops_seleccionados.append((i, op.codigo, valor))
        
                # Operadores centrales (índices 4-7)
                st.write("**Operadores centrales:**")
                for i, op in enumerate(OPERADORES[4:8], start=4):
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        checked = st.checkbox(op.descripcion, key=f"op_check_{i}")
                    with col2:
                        if op.requiere_valor:
                            valor = st.text_input(
                                f"Valor para {op.codigo}",
                                placeholder=f"ej.: {op.ejemplos}",
                                key=f"op_val_{i}",
                                label_visibility="collapsed"
                            )
                        else:
                            valor = None
                    if checked:
                        ops_seleccionados.append((i, op.codigo, valor))
        
                # Operadores nucleares (índices 8-10)
                st.write("**Operadores nucleares:**")
                for i, op in enumerate(OPERADORES[8:], start=8):
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        checked = st.checkbox(op.descripcion, key=f"op_check_{i}")
                    with col2:
                        if op.requiere_valor:
                            valor = st.text_input(
                                f"Valor para {op.codigo}",
                                placeholder=f"ej.: {op.ejemplos}",
                                key=f"op_val_{i}",
                                label_visibility="collapsed"
                            )
                        else:
                            valor = None
                    if checked:
                        ops_seleccionados.append((i, op.codigo, valor))
        
                if st.form_submit_button("Siguiente", use_container_width=True):
                    if ops_seleccionados:
                        # Procesar los valores
                        ops_valores = []
                        for idx, codigo, valor in ops_seleccionados:
                            if valor:
                                valor = valor.upper()
                                if codigo == 'STA' and valor == 'NEG':
                                    valor = 'NEG +'
                            ops_valores.append((codigo, valor))
                
                        st.session_state.ls_ops_valores = ops_valores
                
                        # Aplicar operadores directamente
                        ls_base = st.session_state.get('ls_estructura_traducida', st.session_state.ls_estructura)
                        ls_con_ops = añadir_operadores_a_ls(ls_base, ops_valores)
                        st.session_state.ls_estructura_final = ls_con_ops
                    else:
                        # Sin operadores, usar estructura traducida como final
                        st.session_state.ls_estructura_final = st.session_state.get('ls_estructura_traducida', st.session_state.ls_estructura)
            
                    ir_a('final')
    
            botones_navegacion()

        # --- FINAL ---
        elif st.session_state.ls_paso == 'final':
            st.markdown("### Resultado final")
            
            ls_final = st.session_state.get('ls_estructura_final', st.session_state.ls_estructura)
            st.markdown(f'<div class="ls-resultado">{ls_final}</div>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True) 

            with st.expander("Copiar o descargar estructura lógica (texto plano, LaTex o imagen)"):
                ls_copiable = limpiar_html_ls(ls_final)
                ls_latex = convertir_ls_a_latex(ls_final)
                
                st.write("**Texto plano:**")
                st.code(ls_copiable, language=None)
                
                st.write("**LaTeX:**")
                st.code(ls_latex, language="latex")
                
                st.write("**Imagen:**")
                imagen_bytes = generar_imagen_ls(ls_final)
                st.download_button(
                    label="Descargar como PNG",
                    data=imagen_bytes,
                    file_name="estructura_logica.png",
                    mime="image/png"
                )

            st.write("---")
            c1, c2 = st.columns(2)
            c1.button("Analizar otra cláusula", use_container_width=True, key="otra_final", on_click=reiniciar_analisis)
            
            def _volver_a_aktionsart():
                # Limpiar variables de ls
                keys_to_delete = [k for k in list(st.session_state.keys()) if k.startswith('ls_')]
                for key in keys_to_delete:
                    del st.session_state[key]
                # Limpiar variables de aktionsart_es
                for key in ['akt_paso', 'historial', 'rasgos', 'datos', 'oracion_original', 'oracion_actual', 'clausula_limpia', 'variante_no_causativa', 'reformulacion']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.session_state.seccion = 'akt'
            
            c2.button("Ir al detector de aktionsart", use_container_width=True, key="volver_akt", on_click=_volver_a_aktionsart)

if __name__ == "__main__":
    mostrar_asistente_ls()