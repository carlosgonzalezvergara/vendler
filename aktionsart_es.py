import streamlit as st
import html
import estilo
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
    "abrir": {"pp": "abierto"},
    "cubrir": {"pp": "cubierto"},
    "decir": {"ger": "diciendo", "pp": "dicho"},
    "descubrir": {"pp": "descubierto"},
    "escribir": {"pp": "escrito"},
    "hacer": {"pp": "hecho"},
    "freír": {"pp": "frito"},
    "imprimir": {"pp": "impreso"},
    "morir": {"ger": "muriendo", "pp": "muerto"},
    "poner": {"pp": "puesto"},
    "proveer": {"pp": "provisto"},
    "romper": {"pp": "roto"},
    "satisfacer": {"pp": "satisfecho"},
    "soltar": {"pp": "suelto"},
    "ver": {"pp": "visto"},
    "volver": {"pp": "vuelto"},
    "ir": {"ger": "yendo", "pp": "ido"},
    "ser": {"ger": "siendo", "pp": "sido"},
    "pudrir": {"pp": "podrido"},
    "leer": {"ger": "leyendo", "pp": "leído"},
    "traer": {"ger": "trayendo", "pp": "traído"},
    "caer": {"ger": "cayendo", "pp": "caído"},
    "oír": {"ger": "oyendo", "pp": "oído"},

    # Derivados con participio irregular.
    "encubrir": {"pp": "encubierto"},
    "recubrir": {"pp": "recubierto"},
    "describir": {"pp": "descrito"},
    "inscribir": {"pp": "inscrito"},
    "prescribir": {"pp": "prescrito"},
    "proscribir": {"pp": "proscrito"},
    "suscribir": {"pp": "suscrito"},
    "transcribir": {"pp": "transcrito"},
    "deshacer": {"pp": "deshecho"},
    "rehacer": {"pp": "rehecho"},
    "componer": {"pp": "compuesto"},
    "descomponer": {"pp": "descompuesto"},
    "disponer": {"pp": "dispuesto"},
    "exponer": {"pp": "expuesto"},
    "imponer": {"pp": "impuesto"},
    "oponer": {"pp": "opuesto"},
    "proponer": {"pp": "propuesto"},
    "reponer": {"pp": "repuesto"},
    "suponer": {"pp": "supuesto"},
    "absolver": {"pp": "absuelto"},
    "disolver": {"pp": "disuelto"},
    "resolver": {"pp": "resuelto"},
    "devolver": {"pp": "devuelto"},
    "envolver": {"pp": "envuelto"},
    "revolver": {"pp": "revuelto"},
    "prever": {"pp": "previsto"},
    "entrever": {"pp": "entrevisto"},
    "pedir": {"ger": "pidiendo"},
    "sentir": {"ger": "sintiendo"},
    "mentir": {"ger": "mintiendo"},
    "seguir": {"ger": "siguiendo"},
    "conseguir": {"ger": "consiguiendo"},
    "perseguir": {"ger": "persiguiendo"},
    "servir": {"ger": "sirviendo"},
    "vestir": {"ger": "vistiendo"},
    "repetir": {"ger": "repitiendo"},
    "elegir": {"ger": "eligiendo"},
    "corregir": {"ger": "corrigiendo"},
    "reír": {"ger": "riendo"},
    "sonreír": {"ger": "sonriendo"},
    "venir": {"ger": "viniendo"},
    "competir": {"ger": "compitiendo"},
    "medir": {"ger": "midiendo"},
    "despedir": {"ger": "despidiendo"},
    "impedir": {"ger": "impidiendo"},
    "dormir": {"ger": "durmiendo"},
    "poder": {"ger": "pudiendo"}
}

ESTAR_PRETERITO = {
    '1s': "estuve",
    '2s': "estuviste",
    '3s': "estuvo",
    '1p': "estuvimos",
    '2p': "estuvieron",
    '3p': "estuvieron"
}

ESTAR = {
    '1s': "estoy",
    '2s': "estás",
    '3s': "está",
    '1p': "estamos",
    '2p': "están",
    '3p': "están"
}

ESTAR_SUBJUNTIVO = {
    '1s': "estuviera",
    '2s': "estuvieras",
    '3s': "estuviera",
    '1p': "estuviéramos",
    '2p': "estuvieran",
    '3p': "estuvieran"
}

HABER = {
    '1s': "he",
    '2s': "has",
    '3s': "ha",
    '1p': "hemos",
    '2p': "han",
    '3p': "han"
}

DEJAR = {
    '1s': "dejara",
    '2s': "dejaras",
    '3s': "dejara",
    '1p': "dejáramos",
    '2p': "dejaran",
    '3p': "dejaran"
}

# Ponerse en pretérito perfecto simple
PONERSE_PRETERITO = {
    '1s': "me puse",
    '2s': "te pusiste",
    '3s': "se puso",
    '1p': "nos pusimos",
    '2p': "se pusieron",
    '3p': "se pusieron"
}

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
    try:
        return spacy.load("es_core_news_sm")
    except OSError:
        return None


nlp = load_nlp()

def mayuscula_inicial(texto):
    if not texto:
        return texto
    return texto[0].upper() + texto[1:]

def reconstruir_infinitivo_preterito(texto_verbo, lema_spacy):
    """
    Corrige el lema de spaCy cuando la morfología del pretérito
    permite recuperar el infinitivo con suficiente seguridad.

    Si no puede hacerlo con seguridad, conserva el lema de spaCy.
    """

    forma = texto_verbo.lower()
    lema = lema_spacy.lower()

    # ---------------------------------------------------------
    # 1. PRETÉRITOS FUERTES Y SUS DERIVADOS
    # ---------------------------------------------------------

    # Se analizan como familias:
    #
    # dije       -> decir
    # predije    -> predecir
    # contradije -> contradecir
    #
    # puse       -> poner
    # compuse    -> componer
    # propuse    -> proponer
    #
    # tuve       -> tener
    # mantuve    -> mantener
    # obtuve     -> obtener

    familias_fuertes = {
        "dij": "decir",
        "traj": "traer",
        "pus": "poner",
        "tuv": "tener",
        "vin": "venir",
        "anduv": "andar",
    }

    desinencias_fuertes = (
        "e",
        "iste",
        "o",
        "imos",
        "isteis",
        "ieron",
        "eron",
    )

    for raiz, infinitivo_base in familias_fuertes.items():
        for desinencia in desinencias_fuertes:
            terminacion = raiz + desinencia

            if forma.endswith(terminacion):
                prefijo = forma[:-len(terminacion)]
                return prefijo + infinitivo_base

    # ---------------------------------------------------------
    # 2. OTROS PRETÉRITOS FUERTES NO PRODUCTIVOS
    # ---------------------------------------------------------

    formas_fuertes = {
        "estuve": "estar",
        "estuviste": "estar",
        "estuvo": "estar",
        "estuvimos": "estar",
        "estuvisteis": "estar",
        "estuvieron": "estar",

        "pude": "poder",
        "pudiste": "poder",
        "pudo": "poder",
        "pudimos": "poder",
        "pudisteis": "poder",
        "pudieron": "poder",

        "supe": "saber",
        "supiste": "saber",
        "supo": "saber",
        "supimos": "saber",
        "supisteis": "saber",
        "supieron": "saber",

        "quise": "querer",
        "quisiste": "querer",
        "quiso": "querer",
        "quisimos": "querer",
        "quisisteis": "querer",
        "quisieron": "querer",

        "hice": "hacer",
        "hiciste": "hacer",
        "hizo": "hacer",
        "hicimos": "hacer",
        "hicisteis": "hacer",
        "hicieron": "hacer",

        "deshice": "deshacer",
        "deshiciste": "deshacer",
        "deshizo": "deshacer",
        "deshicimos": "deshacer",
        "deshicisteis": "deshacer",
        "deshicieron": "deshacer",

        "rehice": "rehacer",
        "rehiciste": "rehacer",
        "rehizo": "rehacer",
        "rehicimos": "rehacer",
        "rehicisteis": "rehacer",
        "rehicieron": "rehacer",
    }

    if forma in formas_fuertes:
        return formas_fuertes[forma]

    # ---------------------------------------------------------
    # 3. PRIMERA CONJUGACIÓN (-AR)
    # ---------------------------------------------------------

    if forma.endswith("asteis"):
        return forma[:-6] + "ar"

    if forma.endswith("aste"):
        return forma[:-4] + "ar"

    if forma.endswith("aron"):
        return forma[:-4] + "ar"

    # cantó -> cantar
    # pero no comió, vivió, construyó, cayó...
    if (
        forma.endswith("ó")
        and not forma.endswith(("ió", "yó"))
    ):
        return forma[:-1] + "ar"

    # Alternancias ortográficas:
    # busqué -> buscar
    # llegué -> llegar
    # empecé -> empezar
    # averigüé -> averiguar

    if forma.endswith("güé"):
        return forma[:-3] + "guar"

    if forma.endswith("qué"):
        return forma[:-3] + "car"

    if forma.endswith("gué"):
        return forma[:-3] + "gar"

    if forma.endswith("cé"):
        return forma[:-2] + "zar"

    # ---------------------------------------------------------
    # 4. VERBOS EN -UIR
    # ---------------------------------------------------------

    # construí -> construir
    # incluí -> incluir
    # huí -> huir

    if forma.endswith(("uí", "üí")):
        return forma[:-1] + "ir"

    # construiste -> construir
    # huiste -> huir

    if forma.endswith("uiste"):
        return forma[:-4] + "ir"

    # construyó -> construir
    # incluyó -> incluir
    # huyó -> huir

    if forma.endswith("uyó"):
        return forma[:-2] + "ir"

    if forma.endswith("uyeron"):
        return forma[:-5] + "ir"

    # ---------------------------------------------------------
    # 5. FAMILIA DE ABRIR
    # ---------------------------------------------------------

    # abrir y sus derivados son regulares en el pretérito,
    # pero spaCy puede fallar con formas aisladas:
    #
    # abrí       -> abrir
    # reabrí     -> reabrir
    # reabriste  -> reabrir

    formas_abrir = (
        ("abristeis", "abrir"),
        ("abrieron", "abrir"),
        ("abriste", "abrir"),
        ("abrimos", "abrir"),
        ("abrió", "abrir"),
        ("abrí", "abrir"),
    )

    for terminacion, infinitivo_base in formas_abrir:
        if forma.endswith(terminacion):
            prefijo = forma[:-len(terminacion)]
            return prefijo + infinitivo_base

    # ---------------------------------------------------------
    # 6. ALGUNOS VERBOS CON HIATO
    # ---------------------------------------------------------

    formas_especiales = {
        "oí": "oír",
        "desoí": "desoír",
        "leí": "leer",
        "releí": "releer",
        "caí": "caer",
        "recaí": "recaer",
        "reí": "reír",
        "sonreí": "sonreír",
    }

    if forma in formas_especiales:
        return formas_especiales[forma]

    # ---------------------------------------------------------
    # 7. SI spaCy YA DIO UN INFINITIVO PLAUSIBLE, SE CONSERVA
    # ---------------------------------------------------------

    if lema.endswith(("ar", "er", "ir", "ír")):
        return lema

    # Si no podemos recuperar con seguridad el infinitivo,
    # no inventamos uno.
    return ""


def construir_infinitivo_con_cliticos(lema, cliticos):
    """
    Añade los clíticos al infinitivo y conserva correctamente
    la posición del acento.

    Ejemplos:
        ver + lo         -> verlo
        caer + se        -> caerse
        oír + lo         -> oírlo
        dar + se + lo    -> dárselo
        decir + me + lo  -> decírmelo
        poner + se + la  -> ponérsela
    """

    if not cliticos:
        return lema

    sufijo = "".join(cliticos)

    # Con un solo clítico no cambia la acentuación gráfica
    # del infinitivo: verlo, decirme, caerse, oírlo.
    if len(cliticos) == 1:
        return lema + sufijo

    # Con dos o más clíticos, el acento prosódico sigue
    # recayendo donde lo hacía en el infinitivo. La palabra
    # resultante pasa normalmente a ser esdrújula.
    if lema.endswith("ar"):
        lema_acentuado = lema[:-2] + "ár"
    elif lema.endswith("er"):
        lema_acentuado = lema[:-2] + "ér"
    elif lema.endswith("ir"):
        lema_acentuado = lema[:-2] + "ír"
    else:
        # Para infinitivos que ya contienen una tilde,
        # como oír o reír, no modificamos la forma.
        lema_acentuado = lema

    return lema_acentuado + sufijo


def reemplazar_ultima_vocal(raiz, origen, destino):
    """
    Sustituye la última aparición de una vocal en la raíz.
    Ej.: sent -> sint; dorm -> durm.
    """
    i = raiz.rfind(origen)

    if i == -1:
        return raiz

    return raiz[:i] + destino + raiz[i + 1:]


# Familias de verbos en -ir cuyo gerundio presenta e > i.
# Como usamos endswith(), una sola entrada cubre también sus derivados:
# sentir -> consentir, resentir, presentir...
# ferir -> preferir, referir, inferir, transferir...
GERUNDIO_E_I = (
    "pedir",
    "medir",
    "servir",
    "vestir",
    "sentir",
    "mentir",
    "seguir",
    "elegir",
    "regir",
    "petir",
    "ferir",
    "herir",
    "gerir",
    "vertir",
    "venir",
    "gemir",
    "querir",
    "henchir",
)


# Familias con o > u.
GERUNDIO_O_U = (
    "dormir",
    "morir",
)


# Irregularidades que se transmiten a verbos prefijados:
# caer -> recaer -> recayendo
# decir -> predecir -> prediciendo
# etc.
GERUNDIOS_HEREDADOS = {
    "caer": "cayendo",
    "decir": "diciendo",
    "leer": "leyendo",
    "oír": "oyendo",
    "traer": "trayendo",
}


def generar_gerundio(lema):
    lema = lema.lower()

    # 1. Excepción léxica ya registrada.
    ger_irregular = IRREGULARES.get(lema, {}).get("ger")

    if ger_irregular:
        return ger_irregular

    # 2. Irregularidades heredadas por prefijación.
    # recaer -> re + cayendo
    # predecir -> pre + diciendo
    # desoír -> des + oyendo
    for base, gerundio_base in GERUNDIOS_HEREDADOS.items():

        if lema.endswith(base):

            prefijo = lema[:-len(base)]

            return prefijo + gerundio_base

    # 3. Casos en -ñir / -ñer / -llir:
    # gruñir -> gruñendo
    # bullir -> bullendo
    # tañer -> tañendo
    #
    # Algunos en -ñir presentan además e > i:
    # ceñir -> ciñendo
    # teñir -> tiñendo
    # reñir -> riñendo
    if lema.endswith(("ceñir", "teñir", "reñir")):

        raiz = lema[:-2]
        raiz = reemplazar_ultima_vocal(
            raiz,
            "e",
            "i"
        )

        return raiz + "endo"

    if lema.endswith(("ñir", "ñer", "llir")):
        return lema[:-2] + "endo"

    # 4. Verbos en -ir con e > i.
    if lema.endswith(GERUNDIO_E_I):

        raiz = lema[:-2]

        raiz = reemplazar_ultima_vocal(
            raiz,
            "e",
            "i"
        )

        return raiz + "iendo"

    # 5. Verbos en -ir con o > u.
    if lema.endswith(GERUNDIO_O_U):

        raiz = lema[:-2]

        raiz = reemplazar_ultima_vocal(
            raiz,
            "o",
            "u"
        )

        return raiz + "iendo"

    # 6. Caso ortográfico especial:
    # argüir -> arguyendo
    if lema.endswith("güir"):
        return lema[:-4] + "guyendo"

    # 7. Primera conjugación.
    if lema.endswith("ar"):
        return lema[:-2] + "ando"

    # 8. Segunda y tercera conjugaciones.
    if lema.endswith(("er", "ir")):

        raiz = lema[:-2]

        # Vocal + -iendo -> -yendo:
        # creer -> creyendo
        # construir -> construyendo
        # huir -> huyendo
        #
        # Pero no distinguir -> *distinguyendo:
        # distinguir -> distinguiendo.
        if (
            raiz
            and raiz[-1] in "aeiouáéíóú"
            and not lema.endswith(("guir", "quir"))
        ):
            return raiz + "yendo"

        return raiz + "iendo"

    return ""

def generar_participio(lema):
    lema = lema.lower()

    # 1. Forma irregular registrada explícitamente.
    part_irregular = IRREGULARES.get(
        lema,
        {}
    ).get("pp")

    if part_irregular:
        return part_irregular

    # 2. Familias que heredan regularmente
    #    un participio irregular.
    PARTICIPIOS_HEREDADOS = {
        "abrir": "abierto",
        "cubrir": "cubierto",
        "scribir": "scrito",
        "hacer": "hecho",
        "poner": "puesto",
        "solver": "suelto",
        "volver": "vuelto",
    }

    for base, participio_base in PARTICIPIOS_HEREDADOS.items():
        if lema.endswith(base):
            prefijo = lema[:-len(base)]
            return prefijo + participio_base

    # 3. Familia de decir.
    #
    # predecir -> predicho
    # contradecir -> contradicho
    # desdecir -> desdicho
    #
    # bendecir y maldecir conservan aquí las formas regulares
    # usadas en los tiempos compuestos.
    if lema == "bendecir":
        return "bendecido"

    if lema == "maldecir":
        return "maldecido"

    if lema.endswith("decir"):
        prefijo = lema[:-len("decir")]
        return prefijo + "dicho"

    # 4. Participios regulares en -ar.
    if lema.endswith("ar"):
        return lema[:-2] + "ado"

    # 5. Participios regulares en -er / -ir.
    if lema.endswith(("er", "ir", "ér", "ír")):
        raiz = lema[:-2]

        # caer -> caído
        # leer -> leído
        # creer -> creído
        # oír -> oído
        #
        # Pero construir -> construido,
        # huir -> huido.
        if raiz and raiz[-1] in "aeoáéó":
            return raiz + "ído"

        return raiz + "ido"

    return ""


def analizar_automaticamente(oracion, datos):
    if not nlp:
        return False, "", ""

    doc = nlp(oracion)

    # ---------------------------------------------------------
    # 1. IDENTIFICAR EL VERBO PRINCIPAL
    # ---------------------------------------------------------

    verbo_token = next(
        (
            t for t in doc
            if t.dep_ == "ROOT" and t.pos_ in ["VERB", "AUX"]
        ),
        None
    )

    if not verbo_token:
        verbo_token = next(
            (t for t in doc if t.pos_ in ["VERB", "AUX"]),
            None
        )

    if not verbo_token:
        # Con una entrada de una sola palabra, spaCy puede no
        # etiquetar correctamente una forma verbal aislada (p. ej., «oí»).
        # La aceptamos como candidata y dejamos que el usuario confirme
        # después el análisis morfológico.
        if len(doc) == 1:
            verbo_token = doc[0]
        else:
            return False, "", ""

    idx = verbo_token.i

    # ---------------------------------------------------------
    # 2. IDENTIFICAR CLÍTICOS PREVERBALES
    # ---------------------------------------------------------

    cliticos = [
        doc[i].text.lower()
        for i in range(idx - 1, max(idx - 5, -1), -1)
        if (
            doc[i].pos_ == "PRON"
            and doc[i].text.lower() in [
                "me", "te", "se", "nos", "os",
                "le", "les", "lo", "los", "la", "las"
            ]
        )
    ]

    cliticos.reverse()

    # ---------------------------------------------------------
    # 3. OBTENER EL LEMA
    # ---------------------------------------------------------

    lema_limpio = verbo_token.lemma_.lower()
    texto_verbo = verbo_token.text.lower()

    # ---------------------------------------------------------
    # 4. CORREGIR PRETÉRITOS FUERTES
    # ---------------------------------------------------------

    PRETERITOS_FUERTES = {
        "estuv": "estar",
        "tuv": "tener",
        "anduv": "andar",
        "pud": "poder",
        "pus": "poner",
        "sup": "saber",
        "hic": "hacer",
        "hiz": "hacer",
        "quis": "querer",
        "vin": "venir",
        "dij": "decir",
        "traj": "traer"
    }

    # Es necesario comprobar también la desinencia.
    # De lo contrario, por ejemplo, "pudrió"
    # podría confundirse con una forma de "poder".

    DESINENCIAS_PRET_FUERTE = (
        "e",
        "iste",
        "o",
        "imos",
        "isteis",
        "ieron",
        "eron"
    )

    for raiz, inf_real in PRETERITOS_FUERTES.items():
        if (
            texto_verbo.startswith(raiz)
            and texto_verbo[len(raiz):]
            in DESINENCIAS_PRET_FUERTE
        ):
            lema_limpio = inf_real
            break

    # ---------------------------------------------------------
    # 5. RECONSTRUIR EL INFINITIVO CUANDO SEA POSIBLE
    # ---------------------------------------------------------

    # Complementa la lematización de spaCy en formas del pretérito
    # que pueden analizarse con suficiente seguridad.
    lema_limpio = reconstruir_infinitivo_preterito(
        texto_verbo,
        lema_limpio
    )

    # Si no se pudo recuperar un infinitivo seguro, dejamos que
    # la interfaz pase a la corrección manual en vez de inventar
    # una forma morfológica.
    if not lema_limpio:
        return False, "", ""

    # ---------------------------------------------------------
    # 6. CONSTRUIR EL INFINITIVO CON CLÍTICOS
    # ---------------------------------------------------------

    datos.infinitivo = construir_infinitivo_con_cliticos(
        lema_limpio,
        cliticos
    )

    # ---------------------------------------------------------
    # 7. GENERAR EL GERUNDIO
    # ---------------------------------------------------------

    # La generación se delega ahora en generar_gerundio(),
    # que maneja tanto las formas regulares como familias
    # del tipo:
    #
    # preferir -> prefiriendo
    # sentir -> sintiendo
    # dormir -> durmiendo
    # recaer -> recayendo
    # construir -> construyendo

    ger = generar_gerundio(lema_limpio)

    # ---------------------------------------------------------
    # 8. GENERAR EL PARTICIPIO
    # ---------------------------------------------------------

    part = generar_participio(lema_limpio)

    datos.gerundio = ger
    datos.participio = part

    # ---------------------------------------------------------
    # 9. DETERMINAR PERSONA Y NÚMERO
    # ---------------------------------------------------------

    # Algunas formas del pretérito permiten reconocer
    # directamente la persona.

    if texto_verbo.endswith(("é", "í")):

        datos.persona_numero = "1s"

    elif texto_verbo.endswith(
        ("aste", "iste")
    ):

        datos.persona_numero = "2s"

    elif texto_verbo.endswith("ó"):

        datos.persona_numero = "3s"

    else:

        # En los demás casos utilizamos el análisis
        # morfológico de spaCy.

        morph = verbo_token.morph.to_dict()

        p = morph.get(
            "Person",
            "3"
        )

        n = morph.get(
            "Number",
            "Sing"
        )

        datos.persona_numero = {
            ("1", "Sing"): "1s",
            ("2", "Sing"): "2s",
            ("3", "Sing"): "3s",
            ("1", "Plur"): "1p",
            ("2", "Plur"): "2p",
            ("3", "Plur"): "3p"
        }.get(
            (p, n),
            "3s"
        )

    # ---------------------------------------------------------
    # 10. DIVIDIR LA CLÁUSULA EN SEGMENTOS
    # ---------------------------------------------------------

    datos.sujeto = doc[:idx].text.strip()

    datos.complementos = (
        doc[idx + 1:].text.strip()
    )

    # ---------------------------------------------------------
    # 11. DEVOLVER RESULTADOS
    # ---------------------------------------------------------

    return (
        True,
        verbo_token.text,
        lema_limpio
    )

def construir_perif(tipo, datos):
    if tipo == 'gerundio_pret':
        v = ESTAR_PRETERITO.get(
            datos.persona_numero,
            "estuvo"
        )

    elif tipo == 'gerundio_pres':
        v = ESTAR.get(
            datos.persona_numero,
            "está"
        )

    elif tipo == 'gerundio_subj':
        v = ESTAR_SUBJUNTIVO.get(
            datos.persona_numero,
            "estuviera"
        )

    elif tipo == 'participio':
        v = HABER.get(
            datos.persona_numero,
            "ha"
        )

    elif tipo == 'infinitivo':
        return " ".join(
            p for p in [
                f"{DEJAR.get(datos.persona_numero, 'dejara')} "
                f"de {datos.infinitivo}",
                datos.complementos
            ]
            if p
        )

    elif tipo == 'ponerse_a_infinitivo':

        # Los clíticos del predicado léxico ya están incorporados
        # en datos.infinitivo: equivocarme, verlo, caerse, etc.
        #
        # Se eliminan del segmento preverbal original y se añade
        # aparte el clítico propio de la perífrasis «ponerse a».
        #
        # Ejemplos:
        # Yo me equivoqué -> Yo me puse a equivocarme
        # Juan lo vio -> Juan se puso a verlo
        # Pedro corrió -> Pedro se puso a correr

        cliticos = {
            "me", "te", "se", "nos", "os",
            "le", "les", "lo", "los", "la", "las"
        }

        partes_sujeto = datos.sujeto.split()

        while (
            partes_sujeto
            and partes_sujeto[-1].lower() in cliticos
        ):
            partes_sujeto.pop()

        sujeto_sin_cliticos = " ".join(partes_sujeto)

        aux = (
            f"{PONERSE_PRETERITO.get(datos.persona_numero, 'se puso')} "
            f"a {datos.infinitivo}"
        )

        return " ".join(
            p for p in [
                sujeto_sin_cliticos,
                aux,
                datos.complementos
            ]
            if p
        )

    aux = (
        f"{v} {datos.gerundio}"
        if 'gerundio' in tipo
        else f"{v} {datos.participio}"
    )

    return " ".join(
        p for p in [
            datos.sujeto,
            aux,
            datos.complementos
        ]
        if p
    )


# --- NAVEGACIÓN ---

def ir_a(paso, rasgo=None):
    # Si se ha determinado un rasgo, no se salta
    # directamente a la prueba siguiente: se
    # intercala una pantalla que lo anuncia y que
    # exige una confirmación explícita. El destino
    # real queda en espera.

    st.session_state.historial.append(
        st.session_state.akt_paso
    )

    if rasgo:
        st.session_state.rasgo_aviso = rasgo
        st.session_state.destino_tras_aviso = paso
        st.session_state.akt_paso = 'aviso_rasgo'

    else:
        st.session_state.akt_paso = paso

    st.rerun()


def continuar_tras_aviso():
    # No se apila 'aviso_rasgo' en el historial:
    # al volver desde la prueba siguiente se llega
    # directamente a la prueba anterior.

    st.session_state.akt_paso = (
        st.session_state.destino_tras_aviso
    )

    st.session_state.rasgo_aviso = None
    st.session_state.destino_tras_aviso = None

    st.rerun()


def volver():
    st.session_state.rasgo_aviso = None
    st.session_state.destino_tras_aviso = None

    if st.session_state.historial:

        destino = st.session_state.historial[-1]

        if destino in (
            'causatividad',
            'evento_independiente',
            'evento_basico'
        ):
            st.session_state.rasgos.causativo = None
            st.session_state.variante_no_causativa = ""
            st.session_state.oracion_actual = (
                st.session_state.oracion_original
            )

        elif destino in (
            'analisis_morph',
            'manual_morph'
        ):
            st.session_state.datos = DatosClause()

        elif destino == 'estatividad':
            st.session_state.rasgos.estativo = None

        elif destino == 'puntualidad':
            st.session_state.rasgos.puntual = None

        elif destino == 'telicidad':
            st.session_state.rasgos.telico = None

        elif destino == 'dinamicidad':
            st.session_state.rasgos.dinamico = None

        st.session_state.akt_paso = (
            st.session_state.historial.pop()
        )

        st.rerun()


def reiniciar_analisis():
    for key in [
        'akt_paso',
        'historial',
        'rasgos',
        'datos',
        'oracion_original',
        'oracion_actual',
        'clausula_limpia',
        'variante_no_causativa',
        'reformulacion',
        'rasgo_aviso',
        'destino_tras_aviso'
    ]:
        if key in st.session_state:
            del st.session_state[key]

    st.rerun()


def botones_navegacion():
    st.write("---")

    c1, c2 = st.columns([1, 1])

    if c1.button(
        "← Volver",
        use_container_width=True,
        key="nav_volver"
    ):
        volver()

    if c2.button(
        "Iniciar un nuevo análisis",
        use_container_width=True,
        key="nav_reset"
    ):
        reiniciar_analisis()


def lista_elegante(items: list):
    estilo.lista_elegante(items)


def chip_rasgo(etiqueta, destacado=False):
    clase = "rasgo-elegante"

    if destacado:
        clase += " rasgo-nuevo"

    return (
        f'<span class="{clase}">'
        f'{etiqueta}'
        f'</span>'
    )


# --- 3. INTERFAZ ---

def mostrar_detector_es():

    estilo.aplicar_estilo()

    if 'akt_paso' not in st.session_state:
        st.session_state.akt_paso = 'inicio'
        st.session_state.historial = []
        st.session_state.rasgos = RasgosPred()
        st.session_state.datos = DatosClause()
        st.session_state.oracion_original = ""
        st.session_state.oracion_actual = ""
        st.session_state.clausula_limpia = ""
        st.session_state.variante_no_causativa = ""
        st.session_state.reformulacion = ""
        st.session_state.rasgo_aviso = None
        st.session_state.destino_tras_aviso = None

    # Se consume aquí, de modo que el destello y el
    # aviso se produzcan una sola vez, justo después
    # de responder la prueba correspondiente.

    # Etiqueta del rasgo que se está anunciando en
    # la pantalla de confirmación. Sirve además para
    # destacarlo en el panel derecho.

    rasgo_aviso = st.session_state.get(
        'rasgo_aviso'
    )

    label_resultado = ""

    if st.session_state.akt_paso == 'resultado':

        res_r = st.session_state.rasgos

        if res_r.estativo:
            sub = "estado"

        elif res_r.puntual and res_r.telico:
            sub = "logro"

        elif res_r.puntual and not res_r.telico:
            sub = "semelfactivo"

        elif (
            not res_r.puntual
            and res_r.telico
            and res_r.dinamico
        ):
            sub = "realización activa"

        elif (
            not res_r.puntual
            and not res_r.telico
            and res_r.dinamico
        ):
            sub = "actividad"

        elif (
            not res_r.puntual
            and res_r.telico
            and not res_r.dinamico
        ):
            sub = "realización"

        else:
            sub = "proceso"

        if (
            res_r.causativo
            and sub in [
                "realización",
                "realización activa",
                "actividad"
            ]
        ):
            label_resultado = f"{sub} causativa"

        elif res_r.causativo:
            label_resultado = f"{sub} causativo"

        else:
            label_resultado = sub

    col_izq, col_spacer, col_der = st.columns(
        [0.6, 0.02, 0.38]
    )

    with col_izq:

        # --- CONFIRMACIÓN DE RASGO ---

        if (
            st.session_state.akt_paso
            == 'aviso_rasgo'
        ):

            st.write(
                "Resultado de la prueba:"
            )

            st.markdown(
                '<div class="aviso-confirmacion">'
                f'El predicado es {rasgo_aviso}'
                '</div>',
                unsafe_allow_html=True
            )

            c1, c2 = st.columns(2)

            if c1.button(
                "Continuar", type="primary",
                use_container_width=True
            ):
                continuar_tras_aviso()

            botones_navegacion()

        # --- INICIO ---

        elif st.session_state.akt_paso == 'inicio':

            st.write(
                "Este programa te ayudará a identificar "
                "el aktionsart del predicado principal "
                "en una cláusula."
            )

            st.write(
                "Por favor, escribe una cláusula con el "
                "verbo que quieres probar conjugado en "
                "**pretérito** "
                "(ej.: *Pedro corrió hasta su casa*)."
            )

            st.write(
                "Si suena muy extraña, o si en pretérito "
                "el verbo pasa a significar algo distinto "
                "de lo que quieres analizar, escríbela en "
                "**presente** "
                "(ej.: *María sabe inglés*, "
                "no *María supo la verdad*)."
            )

            with st.form(key="form_inicio_es"):

                oracion = st.text_input("Cláusula:")

                if st.form_submit_button(
                    "Comenzar el análisis", type="primary"
                ):
                    if oracion:

                        oracion_limpia = (
                            oracion.strip().rstrip('.')
                        )

                        st.session_state.oracion_original = (
                            oracion_limpia
                        )

                        st.session_state.oracion_actual = (
                            oracion_limpia
                        )

                        ir_a('causatividad')

        # --- CAUSATIVIDAD ---

        elif (
            st.session_state.akt_paso
            == 'causatividad'
        ):

            st.markdown(
                "#### Prueba de causatividad"
            )

            st.write(
                f"Intenta expresar solamente el evento resultante "
                f"de *{st.session_state.oracion_actual}*, "
                f"sin mencionar aquello que lo causa."
            )

            st.write(
                "Básate en estos ejemplos:"
            )

            lista_elegante([
                "<i>El gato rompió el jarrón</i> → "
                "<i>El jarrón se rompió</i>",

                "<i>El sicario mató a Juan</i> → "
                "<i>Juan murió</i>",

                "<i>Ana le dio un libro a Pepe</i> → "
                "<i>Pepe llegó a tener un libro</i>",

                "<i>El juez encarceló al ladrón</i> → "
                "<i>El ladrón llegó a estar encarcelado</i>"
            ])

            st.write(
                "Si lo que resulta no es un cambio de estado, sino un estado "
                "que se mantiene, escríbelo como estado (*El motor mantiene "
                "tibia la cabina* → *La cabina está tibia*)."
            )

            st.write(
                "**No escribas una pasiva** (*el jarrón fue roto*, *Juan fue "
                "asesinado*), porque esto mantiene al causante de forma "
                "implícita. Si no encuentras ninguna reformulación, presiona "
                "*No hay reformulación posible*."
            )

            with st.form(key="form_caus_es"):

                reformula = st.text_input(
                    "Escribe el evento o estado:"
                )

                c1, c2 = st.columns(2)

                if c1.form_submit_button(
                    "Siguiente", type="primary",
                    use_container_width=True
                ):

                    if not reformula.strip():

                        st.warning(
                            "Escribe el evento o estado, "
                            "o presiona "
                            "'No hay reformulación posible'."
                        )

                    else:

                        st.session_state.reformulacion = (
                            reformula
                        )

                        ir_a('evento_independiente')

                if c2.form_submit_button(
                    "No hay reformulación posible",
                    use_container_width=True
                ):

                    st.session_state.rasgos.causativo = False

                    ir_a(
                        'limpieza',
                        '[-causativo]'
                    )

            botones_navegacion()


        # --- INDEPENDENCIA DEL EVENTO RESULTANTE ---

        elif (
            st.session_state.akt_paso
            == 'evento_independiente'
        ):

            st.write(
                "Considera ahora la reformulación propuesta:"
            )

            st.markdown(
                f"*{mayuscula_inicial(st.session_state.reformulacion)}*"
            )

            st.write(
                "¿Puedes concebir que este evento ocurra, o que este estado "
                "llegue a darse por sí mismo? "
            )

            c1, c2 = st.columns(2)

            if c1.button(
                "Sí",
                use_container_width=True,
                key="evento_independiente_si"
            ):

                ir_a('evento_basico')

            if c2.button(
                "No",
                use_container_width=True,
                key="evento_independiente_no"
            ):

                st.session_state.rasgos.causativo = False

                ir_a(
                    'limpieza',
                    '[-causativo]'
                )

            botones_navegacion()

        # --- RELACIÓN CAUSAL ---

        elif (
            st.session_state.akt_paso
            == 'evento_basico'
        ):

            st.write(
                "Compara ahora las dos expresiones:"
            )

            st.markdown(
                f"(a) *{mayuscula_inicial(st.session_state.oracion_actual)}*\n\n"
                f"(b) *{mayuscula_inicial(st.session_state.reformulacion)}*"
            )

            st.write(
                "¿La expresión (a) introduce algún participante que "
                "no se encuentre en (b) y, además, implica "
                "que ese participante hizo que lo expresado en (b) "
                "ocurriera o llegara a darse?"
            )

            c1, c2 = st.columns(2)

            if c1.button(
                "Sí",
                use_container_width=True
            ):

                st.session_state.rasgos.causativo = True

                st.session_state.variante_no_causativa = (
                    st.session_state.reformulacion
                )

                st.session_state.oracion_actual = (
                    st.session_state.reformulacion
                )

                ir_a(
                    'limpieza',
                    '[+causativo]'
                )

            if c2.button(
                "No",
                use_container_width=True
            ):

                st.session_state.rasgos.causativo = False

                ir_a(
                    'limpieza',
                    '[-causativo]'
                )

            botones_navegacion()

        # --- LIMPIEZA ---

        elif (
            st.session_state.akt_paso
            == 'limpieza'
        ):

            st.write(
                f"Esta es la cláusula a la que "
                f"aplicaremos las pruebas: "
                f"*{st.session_state.oracion_actual}*"
            )

            st.write(
                "Para que estas funcionen correctamente, "
                "la cláusula debe cumplir algunas "
                "condiciones formales. Asegúrate de que "
                "**no** tenga:"
            )

            lista_elegante([
                "Expresiones de tiempo "
                "(ej: <i>ayer</i>, <i>siempre</i>, "
                "<i>el lunes</i>).",

                "Expresiones de modo "
                "(ej: <i>rápidamente</i>, "
                "<i>bien</i>, <i>mal</i>, "
                "<i>con calma</i>).",

                "Negaciones "
                "(ej: <i>no</i>, <i>tampoco</i>)."
            ])

            st.write(
                "¿Tu cláusula contiene alguno "
                "de estos elementos?"
            )

            c1, c2 = st.columns(2)

            if c1.button(
                "Sí",
                use_container_width=True
            ):
                ir_a('corregir_limpieza')

            if c2.button(
                "No",
                use_container_width=True
            ):

                st.session_state.clausula_limpia = (
                    st.session_state.oracion_actual
                )

                ir_a('analisis_morph')

            botones_navegacion()

        # --- CORREGIR LIMPIEZA ---

        elif (
            st.session_state.akt_paso
            == 'corregir_limpieza'
        ):

            with st.form(key="form_limp_act_es"):

                nueva = st.text_input(
                    f"Por favor, escribe "
                    f"*{st.session_state.oracion_actual}* "
                    f"de nuevo **sin** esos elementos "
                    f"(ej.: *Pedro corrió hasta su casa* "
                    f"en vez de *Pedro nunca corrió "
                    f"rápidamente hasta su casa ayer*):"
                )

                if st.form_submit_button(
                    "Actualizar", type="primary"
                ):

                    if nueva:

                        st.session_state.oracion_actual = (
                            nueva
                        )

                        st.session_state.clausula_limpia = (
                            nueva
                        )

                        ir_a('analisis_morph')

            botones_navegacion()

        # --- ANÁLISIS MORFOLÓGICO ---

        elif (
            st.session_state.akt_paso
            == 'analisis_morph'
        ):

            exito, v_vis, l_vis = (
                analizar_automaticamente(
                    st.session_state.oracion_actual,
                    st.session_state.datos
                )
            )

            if exito:

                st.write(
                    f"Este es un análisis de algunos de "
                    f"los rasgos morfológicos y "
                    f"estructurales de "
                    f"**{st.session_state.oracion_actual}**"
                )

                d = st.session_state.datos

                html_tabla = f"""
                <table class="tabla-analisis">
                    <tbody>
                        <tr>
                            <td><b>Verbo</b></td>
                            <td>{v_vis.lower()}</td>
                        </tr>
                        <tr>
                            <td><b>Infinitivo</b></td>
                            <td>{l_vis}</td>
                        </tr>
                        <tr>
                            <td><b>Gerundio</b></td>
                            <td>{d.gerundio}</td>
                        </tr>
                        <tr>
                            <td>
                                <b>
                                    Participio
                                    (masculino singular)
                                </b>
                            </td>
                            <td>{d.participio}</td>
                        </tr>
                        <tr>
                            <td><b>Antes del verbo</b></td>
                            <td>
                                {
                                    d.sujeto
                                    if d.sujeto
                                    else "no hay nada"
                                }
                            </td>
                        </tr>
                        <tr>
                            <td><b>Después del verbo</b></td>
                            <td>
                                {
                                    d.complementos
                                    if d.complementos
                                    else "no hay nada"
                                }
                            </td>
                        </tr>
                    </tbody>
                </table>
                """

                st.markdown(
                    html_tabla,
                    unsafe_allow_html=True
                )

                st.write(
                    "¿Es correcto este análisis?"
                )

                c1, c2 = st.columns(2)

                if c1.button(
                    "Sí",
                    use_container_width=True
                ):
                    ir_a('estatividad')

                if c2.button(
                    "No",
                    use_container_width=True
                ):
                    ir_a('manual_morph')

                botones_navegacion()

            else:

                ir_a('manual_morph')

        # --- CORRECCIÓN MANUAL ---

        elif (
            st.session_state.akt_paso
            == 'manual_morph'
        ):

            st.markdown(
                "Por favor, agrega o corrige "
                "la información que sea necesaria:"
            )

            with st.form(key="form_m_save"):

                d = st.session_state.datos

                d.infinitivo = st.text_input(
                    f"Escribe el **infinitivo** del verbo "
                    f"en *{st.session_state.oracion_actual}*, "
                    f"incluyendo los clíticos que haya:",
                    d.infinitivo
                )

                d.gerundio = st.text_input(
                    f"Escribe el **gerundio** del verbo "
                    f"en *{st.session_state.oracion_actual}*, "
                    f"sin clíticos:",
                    d.gerundio
                )

                d.participio = st.text_input(
                    f"Escribe el **participio** "
                    f"(masculino singular) del verbo en "
                    f"*{st.session_state.oracion_actual}*:",
                    d.participio
                )

                d.sujeto = st.text_input(
                    f"Escribe todo lo que hay "
                    f"**antes** del verbo en "
                    f"*{st.session_state.oracion_actual}*, "
                    f"incluyendo los clíticos, si los hay:",
                    d.sujeto
                )

                d.complementos = st.text_input(
                    f"Escribe todo lo que hay "
                    f"**después** del verbo en "
                    f"*{st.session_state.oracion_actual}*:",
                    d.complementos
                )

                idx_actual = (
                    list(PERSONAS_DICT.keys()).index(
                        d.persona_numero
                    )
                    if d.persona_numero in PERSONAS_DICT
                    else 2
                )

                d.persona_numero = st.selectbox(
                    "Selecciona la persona y "
                    "número del verbo:",
                    options=list(
                        PERSONAS_DICT.keys()
                    ),
                    format_func=lambda x: (
                        PERSONAS_DICT[x]
                    ),
                    index=idx_actual
                )

                if st.form_submit_button("Guardar", type="primary"):
                    ir_a('estatividad')

            botones_navegacion()

        # --- ESTATIVIDAD ---

        elif (
            st.session_state.akt_paso
            == 'estatividad'
        ):

            st.markdown(
                "#### Prueba de estatividad"
            )

            st.write(
                "Observa los siguientes diálogos:"
            )

            cd1, cd2, cd3 = st.columns(3)

            with cd1:
                st.markdown(
                    f"— ¿Qué pasó hace un rato?<br>"
                    f"— <i>"
                    f"{mayuscula_inicial(st.session_state.oracion_actual)}"
                    f"</i>.",
                    unsafe_allow_html=True
                )

            with cd2:
                st.markdown(
                    f"— ¿Qué pasó ayer?<br>"
                    f"— <i>"
                    f"{mayuscula_inicial(st.session_state.oracion_actual)}"
                    f"</i>.",
                    unsafe_allow_html=True
                )

            with cd3:
                st.markdown(
                    f"— ¿Qué pasó el mes pasado?<br>"
                    f"— <i>"
                    f"{mayuscula_inicial(st.session_state.oracion_actual)}"
                    f"</i>.",
                    unsafe_allow_html=True
                )

            st.write(
                f"¿Te parece que "
                f"*{st.session_state.oracion_actual}* "
                f"es una buena respuesta a, al menos, "
                f"una de estas preguntas?"
            )

            c1, c2 = st.columns(2)

            if c1.button(
                "Sí",
                use_container_width=True
            ):

                st.session_state.rasgos.estativo = False

                ir_a(
                    'puntualidad',
                    '[-estativo]'
                )

            if c2.button(
                "No",
                use_container_width=True
            ):

                st.session_state.rasgos.estativo = True

                ir_a(
                    'resultado',
                    '[+estativo]'
                )

            botones_navegacion()

        # --- PUNTUALIDAD ---

        elif (
            st.session_state.akt_paso
            == 'puntualidad'
        ):

            st.markdown(
                "#### Prueba de puntualidad"
            )

            p = construir_perif(
                'gerundio_pret',
                st.session_state.datos
            )

            st.write(
                "Observa estas expresiones:"
            )

            lista_elegante([
                f"<i>{mayuscula_inicial(p)} "
                f"durante una hora.</i>",

                f"<i>{mayuscula_inicial(p)} "
                f"durante un mes.</i>"
            ])

            st.write(
                "¿Es alguna de estas una expresión "
                "posible? **(Si la expresión tiene "
                "sentido iterativo o de inminencia, "
                "responde que no)**.",
                unsafe_allow_html=True
            )

            c1, c2 = st.columns(2)

            if c1.button(
                "Sí",
                use_container_width=True
            ):

                st.session_state.rasgos.puntual = False

                ir_a(
                    'telicidad',
                    '[-puntual]'
                )

            if c2.button(
                "No",
                use_container_width=True
            ):

                st.session_state.rasgos.puntual = True

                ir_a(
                    'telicidad',
                    '[+puntual]'
                )

            botones_navegacion()

        # --- TELICIDAD ---

        elif (
            st.session_state.akt_paso
            == 'telicidad'
        ):

            st.markdown(
                "#### Prueba de telicidad"
            )

            p_ger = construir_perif(
                'gerundio_subj',
                st.session_state.datos
            )

            p_inf = construir_perif(
                'infinitivo',
                st.session_state.datos
            )

            p_par = construir_perif(
                'participio',
                st.session_state.datos
            )

            st.write(
                f"Imagina que {p_ger} "
                f"y de pronto {p_inf}."
            )

            st.write(
                f"¿Se podría decir que "
                f"*{p_par}*?"
            )

            c1, c2 = st.columns(2)

            if c1.button(
                "Sí",
                use_container_width=True
            ):

                st.session_state.rasgos.telico = False

                ir_a(
                    'dinamicidad',
                    '[-télico]'
                )

            if c2.button(
                "No",
                use_container_width=True
            ):

                st.session_state.rasgos.telico = True

                ir_a(
                    'dinamicidad',
                    '[+télico]'
                )

            botones_navegacion()

        # --- DINAMICIDAD ---

        elif (
            st.session_state.akt_paso
            == 'dinamicidad'
        ):

            st.markdown(
                "#### Prueba de dinamicidad"
            )

            # NUEVO TEST:
            # compatibilidad con
            # «ponerse a + infinitivo»
            # en pretérito perfecto simple.

            p = construir_perif(
                'ponerse_a_infinitivo',
                st.session_state.datos
            )

            st.write(
                "Observa esta expresión:"
            )

            lista_elegante([
                f"<i>{mayuscula_inicial(p)}.</i>"
            ])

            st.write(
                "¿Te parece natural esta expresión?"
            )

            c1, c2 = st.columns(2)

            if c1.button(
                "Sí",
                use_container_width=True
            ):

                # Compatible con ponerse a + infinitivo
                # = [+dinámico]
                st.session_state.rasgos.dinamico = True

                ir_a(
                    'resultado',
                    '[+dinámico]'
                )

            if c2.button(
                "No",
                use_container_width=True
            ):

                # Incompatible con ponerse a + infinitivo
                # = [-dinámico]
                st.session_state.rasgos.dinamico = False

                ir_a(
                    'resultado',
                    '[-dinámico]'
                )

            botones_navegacion()

        # --- RESULTADO ---

        elif (
            st.session_state.akt_paso
            == 'resultado'
        ):

            st.markdown(
                "#### Análisis finalizado"
            )

            st.markdown(
                '<div class="aviso-resultado">'
                f'El aktionsart de la cláusula '
                f'<i>{st.session_state.oracion_original}</i> '
                f'es {label_resultado}'
                '</div>',
                unsafe_allow_html=True
            )

            c1, c2, c3 = st.columns(
                [1, 1, 1]
            )

            if c1.button(
                "Analizar otro predicado",
                use_container_width=True
            ):
                reiniciar_analisis()

            if c2.button(
                "← Volver a la última prueba",
                use_container_width=True
            ):
                volver()

            if c3.button(
                "Obtener estructura lógica", type="primary",
                use_container_width=True
            ):

                st.session_state.ls_akt = (
                    label_resultado.lower()
                )

                st.session_state.ls_oracion = (
                    st.session_state.oracion_original
                )

                st.session_state.ls_es_dinamico = (
                    st.session_state.rasgos.dinamico
                )

                st.session_state.seccion = 'ls'

                st.rerun()

    # --- PANEL DERECHO ---

    with col_der:

        with st.container():

            st.markdown(
                '<div class="header-analisis">'
                'Estado del análisis'
                '</div>',
                unsafe_allow_html=True
            )

            if st.session_state.oracion_original:

                estilo.mostrar_dato_panel("Cláusula bajo análisis", html.escape(st.session_state.oracion_original))

            if st.session_state.variante_no_causativa:

                estilo.mostrar_dato_panel("Variante no causativa", html.escape(st.session_state.variante_no_causativa))

            if st.session_state.clausula_limpia:

                estilo.mostrar_dato_panel("Cláusula limpia", html.escape(st.session_state.clausula_limpia))

            st.markdown('<div class=\"info-label\">Rasgos detectados</div>', unsafe_allow_html=True)

            r = st.session_state.rasgos

            row_caus = ""

            if r.causativo is not None:

                etq = (
                    f'[{"+" if r.causativo else "-"}'
                    f'causativo]'
                )

                row_caus = (
                    '<div style="margin-bottom: 25px;">'
                    + chip_rasgo(
                        etq,
                        etq == rasgo_aviso
                    )
                    + '</div>'
                )

            row_otros = (
                '<div style="margin-bottom: 15px;">'
            )

            if r.estativo is not None:

                etq = (
                    f'[{"+" if r.estativo else "-"}'
                    f'estativo]'
                )

                row_otros += chip_rasgo(
                    etq,
                    etq == rasgo_aviso
                )

            if r.puntual is not None:

                etq = (
                    f'[{"+" if r.puntual else "-"}'
                    f'puntual]'
                )

                row_otros += chip_rasgo(
                    etq,
                    etq == rasgo_aviso
                )

            if r.telico is not None:

                etq = (
                    f'[{"+" if r.telico else "-"}'
                    f'télico]'
                )

                row_otros += chip_rasgo(
                    etq,
                    etq == rasgo_aviso
                )

            if r.dinamico is not None:

                etq = (
                    f'[{"+" if r.dinamico else "-"}'
                    f'dinámico]'
                )

                row_otros += chip_rasgo(
                    etq,
                    etq == rasgo_aviso
                )

            row_otros += "</div>"

            st.markdown(
                row_caus + row_otros,
                unsafe_allow_html=True
            )

            if (
                st.session_state.akt_paso
                == 'resultado'
            ):

                estilo.mostrar_dato_panel("Resultado", label_resultado, "info-value-resultado")


if __name__ == "__main__":
    mostrar_detector_es()