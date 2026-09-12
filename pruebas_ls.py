"""Pruebas automáticas del asistente de estructuras lógicas (ls.py).

Cada caso describe una cláusula, el aktionsart elegido, los argumentos y las
respuestas que daría un usuario. La prueba recorre el programa como lo haría
esa persona y compara la estructura lógica obtenida con la esperada.

Se comprueba la estructura ANTES de la traducción al inglés, por dos razones:
es la que depende solo del código, y la traducción exige conexión a internet.

Uso:
    python3 pruebas_ls.py              # todos los casos
    python3 pruebas_ls.py maratón      # solo los casos cuyo nombre contenga eso
    python3 pruebas_ls.py 0 8          # solo los casos de las posiciones 0 a 7

Cada caso arranca su propia copia del programa y tarda unos segundos, así que
la batería completa demora algunos minutos; los casos se reparten entre los
núcleos disponibles.

Al terminar informa cuántos casos pasaron y detalla cada fallo. Devuelve 0 si
todo pasó y 1 si hubo algún fallo, para poder usarlo en un flujo automático.

Requiere: pip install streamlit  (usa streamlit.testing, incluido).
"""

import json
import logging
import os
import re
import subprocess
import sys

from streamlit.testing.v1 import AppTest

# Streamlit avisa de que no hay ScriptRunContext cada vez que se ejecuta una
# aplicación fuera del servidor. Aquí es lo normal y el aviso solo estorba.
for _nombre in ('streamlit', 'streamlit.runtime.scriptrunner_utils.script_run_context'):
    _registro = logging.getLogger(_nombre)
    _registro.setLevel(logging.ERROR)
    _registro.propagate = False
    _registro.handlers = [logging.NullHandler()]

TIEMPO_LIMITE = 60  # segundos por caso

# Casos en paralelo. Cada uno arranca su propia copia del programa, así que
# conviene no pasar del número de núcleos disponibles.
PROCESOS = min(8, max(2, os.cpu_count() or 2))

# Pasos en los que se detiene el recorrido: ya hay una estructura que comparar
# (o el programa avisó de un error de análisis).
PASOS_FINALES = ('resultado', 'preguntar_operadores', 'final', 'error_oi')


# --------------------------------------------------------------------------
# Acciones que puede contener un caso
# --------------------------------------------------------------------------

def boton(etiqueta):
    """Pulsa el botón con esa etiqueta exacta (por ejemplo 'Sí')."""
    return ('boton', etiqueta)


def texto(*valores):
    """Rellena los campos de texto del formulario actual y lo envía."""
    return ('texto', valores)


def opcion(etiqueta):
    """Elige esa opción en el grupo de opciones actual (por ejemplo 'Adjetivo/atributo')."""
    return ('opcion', etiqueta)


def elegir(etiqueta):
    """Elige esa opción y envía el formulario (menús de clase semántica, etc.)."""
    return ('elegir', etiqueta)


def marcar(*etiquetas):
    """Marca las casillas indicadas y envía el formulario."""
    return ('marcar', etiquetas)


# --------------------------------------------------------------------------
# Motor
# --------------------------------------------------------------------------

def sin_html(texto_html):
    return re.sub(r'<[^>]+>', '', texto_html or '').replace('&lt;', '⟨').replace('&gt;', '⟩')


def pantalla(at):
    """Resumen de la pantalla actual, para los mensajes de error."""
    preguntas = [sin_html(m.value) for m in at.markdown
                 if '¿' in m.value or 'Escribe' in m.value or 'Selecciona' in m.value]
    return {
        'paso': at.session_state.ls_paso,
        'pregunta': preguntas[-1][:120] if preguntas else '',
        'botones': [b.label for b in at.button],
        'envios': [b.label for b in at.button if b.proto.is_form_submitter]
        if at.button else [],
        'campos': [t.label for t in at.text_input],
    }


def iniciar(caso):
    """Arranca el asistente y llega hasta el primer paso de análisis."""
    at = AppTest.from_file('ls.py', default_timeout=TIEMPO_LIMITE)
    at.run()  # el propio programa inicializa su estado

    # Pantalla de inicio: aktionsart y cláusula
    at.radio('akt_radio').set_value(caso['akt'])
    at.text_input[0].input(caso['clausula'])
    pulsar(at, 'Comenzar')

    # Pantalla de argumentos: casillas, tipo de expresión y valores
    for casilla, opciones, campo, valor in (('chk_sujeto', 'radio_sujeto', 'input_sujeto', caso.get('sujeto')),
                                            ('chk_cd', 'radio_cd', 'input_cd', caso.get('cd')),
                                            ('chk_ci', 'radio_ci', 'input_ci', caso.get('ci'))):
        if valor:
            at.checkbox(casilla).check().run()
            at.radio(opciones).set_value('constituyente').run()
            at.text_input(campo).input(valor).run()
    at.button(key='btn_args_siguiente').click().run()
    return at


def pulsar(at, etiqueta):
    """Pulsa un botón por su etiqueta, sea de formulario o no."""
    for b in at.button:
        if b.label == etiqueta:
            b.click().run()
            return
    raise AssertionError(f"no hay ningún botón «{etiqueta}»; hay {[b.label for b in at.button]}")


def aplicar(at, accion):
    tipo, dato = accion
    if tipo == 'boton':
        pulsar(at, dato)
    elif tipo == 'opcion':
        for r in at.radio:
            if dato in list(r.options):
                r.set_value(dato).run()
                return
        raise AssertionError(f"ninguna lista de opciones ofrece «{dato}»")
    elif tipo == 'elegir':
        aplicar(at, ('opcion', dato))
        envio = [b for b in at.button if b.proto.is_form_submitter]
        assert envio, "el formulario no tiene botón de envío"
        envio[0].click().run()
    elif tipo == 'texto':
        campos = at.text_input
        assert len(campos) >= len(dato), (
            f"se esperaban {len(dato)} campos y hay {len(campos)}: {[c.label for c in campos]}")
        for campo, valor in zip(campos, dato):
            campo.input(valor)
        envio = [b for b in at.button if b.proto.is_form_submitter]
        assert envio, "el formulario no tiene botón de envío"
        envio[0].click().run()
    elif tipo == 'marcar':
        for etiqueta in dato:
            marcadas = [c for c in at.checkbox if etiqueta in c.label]
            assert marcadas, f"no hay casilla «{etiqueta}»: {[c.label for c in at.checkbox]}"
            marcadas[0].check().run()
        envio = [b for b in at.button if b.proto.is_form_submitter]
        assert envio, "el formulario no tiene botón de envío"
        envio[0].click().run()
    else:
        raise AssertionError(f"acción desconocida: {tipo}")


def ejecutar(caso):
    """Recorre un caso. Devuelve (obtenido, at) o levanta AssertionError."""
    at = iniciar(caso)
    for i, accion in enumerate(caso['respuestas']):
        if at.session_state.ls_paso in PASOS_FINALES:
            raise AssertionError(
                f"el programa terminó antes de agotar las respuestas "
                f"(sobran {len(caso['respuestas']) - i}); pantalla: {pantalla(at)}")
        aplicar(at, accion)
    if at.session_state.ls_paso not in PASOS_FINALES:
        raise AssertionError(
            f"faltan respuestas: el programa sigue preguntando. Pantalla: {pantalla(at)}")
    if at.session_state.ls_paso == 'error_oi':
        return 'ERROR_DE_ANALISIS', at
    return sin_html(at.session_state.ls_estructura), at


def comprobar(caso):
    """Devuelve (nombre, ok, detalle)."""
    try:
        obtenido, at = ejecutar(caso)
    except AssertionError as e:
        return caso['nombre'], False, str(e)
    except Exception as e:  # fallo inesperado del programa
        return caso['nombre'], False, f"{type(e).__name__}: {e}"
    if at.exception:
        return caso['nombre'], False, f"excepción en la aplicación: {at.exception[0].value[:200]}"
    if obtenido != caso['esperado']:
        return caso['nombre'], False, f"esperado: {caso['esperado']}\n       obtenido: {obtenido}"
    return caso['nombre'], True, ''


def ejecutar_en_paralelo(indices, procesos):
    """Ejecuta cada caso en su propio subproceso y devuelve sus resultados.

    Se usan subprocesos en vez de multiprocessing porque Streamlit sustituye
    el módulo principal al ejecutar la aplicación, y eso impide que los
    procesos creados por «spawn» (el método de macOS y Windows) reconstruyan
    este archivo.
    """
    resultados = {}
    pendientes = list(indices)
    en_marcha = {}
    carpeta = os.path.dirname(os.path.abspath(__file__)) or '.'
    while pendientes or en_marcha:
        while pendientes and len(en_marcha) < procesos:
            i = pendientes.pop(0)
            en_marcha[i] = subprocess.Popen(
                [sys.executable, os.path.abspath(__file__), '--caso', str(i)],
                cwd=carpeta, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        for i, proceso in list(en_marcha.items()):
            if proceso.poll() is None:
                continue
            salida = (proceso.stdout.read() or '').strip().splitlines()
            del en_marcha[i]
            linea = salida[-1] if salida else ''
            try:
                datos = json.loads(linea)
                resultados[i] = (datos['nombre'], datos['ok'], datos['detalle'])
            except (ValueError, KeyError):
                resultados[i] = (CASOS[i]['nombre'], False,
                                 f"el subproceso no devolvió un resultado legible: {linea[:200]}")
    return [resultados[i] for i in indices]


def main():
    argumentos = sys.argv[1:]
    if len(argumentos) == 2 and argumentos[0] == '--caso':
        # Modo hijo: comprueba un solo caso e informa en una línea JSON.
        nombre, ok, detalle = comprobar(CASOS[int(argumentos[1])])
        print(json.dumps({'nombre': nombre, 'ok': ok, 'detalle': detalle}))
        return 0
    if len(argumentos) == 2 and all(a.isdigit() for a in argumentos):
        desde, hasta = int(argumentos[0]), int(argumentos[1])
        filtro = f"casos {desde}-{hasta - 1}"
        casos = CASOS[desde:hasta]
    else:
        filtro = argumentos[0] if argumentos else ''
        casos = [c for c in CASOS if filtro.lower() in c['nombre'].lower()]
    if not casos and filtro:
        print(f"Ningún caso coincide con «{filtro}».")
        return 1
    fallos = []
    conocidos = []
    total = 0
    print(f"Recorriendo {len(casos)} cláusulas "
          f"(cada una tarda unos segundos; se ejecutan en paralelo):")
    procesos = min(PROCESOS, len(casos))
    if procesos > 1:
        indices = [CASOS.index(c) for c in casos]
        resultados = ejecutar_en_paralelo(indices, procesos)
    else:
        resultados = [comprobar(c) for c in casos]
    for caso, (nombre, ok, detalle) in zip(casos, resultados):
        if caso.get('pendiente'):
            # Error conocido del programa, todavía sin decidir cómo corregirlo:
            # se informa aparte y no cuenta como fallo de la batería.
            estado = 'CORREGIDO' if ok else 'pendiente'
            print(f"  {estado:9}  {nombre}")
            if not ok:
                conocidos.append((nombre, caso['pendiente']))
            continue
        total += 1
        print(f"  {'ok       ' if ok else 'FALLA    '}  {nombre}")
        if not ok:
            fallos.append((nombre, detalle))

    if not filtro:
        print("\nComprobaciones de notación y de las listas de verbos:")
        fallos_notacion = pruebas_de_notacion()
        print(f"  {'ok   ' if not fallos_notacion else 'FALLA'}  "
              f"notación clásica, plantillas y listas de verbos")
        fallos += [('notación y listas', d) for d in fallos_notacion]
        total += 1

    print(f"\n{total - len(fallos)} de {total} comprobaciones pasaron.")
    if fallos:
        print("\nFallos:")
        for nombre, detalle in fallos:
            print(f"\n- {nombre}\n       {detalle}")
    if conocidos:
        print("\nErrores conocidos, a la espera de decisión (no cuentan como fallo):")
        for nombre, motivo in conocidos:
            print(f"\n- {nombre}\n       {motivo}")
    return 1 if fallos else 0


# --------------------------------------------------------------------------
# Casos
# --------------------------------------------------------------------------

CASOS = [

    # ---- Clases aspectuales básicas ----
    dict(
        nombre="estado: Ana está enferma",
        clausula="Ana está enferma", akt="estado", sujeto="Ana",
        respuestas=[boton("No"), boton("No"), boton("No"), boton("No"),
                    opcion("Adjetivo/atributo"), texto("enfermo")],
        esperado="enfermo' (Ana)",
    ),
    dict(
        nombre="estado locativo: Ana está en Santiago",
        clausula="Ana está en Santiago", akt="estado", sujeto="Ana",
        respuestas=[boton("No"), boton("No"), boton("Sí"), texto("Santiago", "estar")],
        # El lugar va primero: be-LOC' (x, y) con x = Location, y = Theme
        # (Van Valin 2023, tabla de relaciones temáticas del apartado 1.4.3.1).
        esperado="be-LOC' (Santiago, Ana)",
    ),
    dict(
        nombre="actividad: Pepe corrió",
        clausula="Pepe corrió", akt="actividad", sujeto="Pepe",
        respuestas=[boton("No"), boton("No"), texto("correr"), boton("Sí")],
        esperado="DO (Pepe, [do' (Pepe, [correr' (Pepe)])])",
    ),
    dict(
        nombre="actividad no intencional: Pepe tembló",
        clausula="Pepe tembló", akt="actividad", sujeto="Pepe",
        respuestas=[boton("No"), boton("No"), texto("temblar"), boton("No")],
        esperado="do' (Pepe, [temblar' (Pepe)])",
    ),
    dict(
        # Parentesco más locativo: comprueba el orden lugar-entidad de be-LOC'
        # en una estructura con dos predicados.
        nombre="parentesco con locativo: Ana tiene un hermano en Santiago",
        clausula="Ana tiene un hermano en Santiago", akt="estado",
        sujeto="Ana", cd="un hermano",
        respuestas=[boton("No"), boton("Sí"), texto("Santiago", "tener"),
                    boton("No"), boton("Sí")],
        esperado="have.as.kin' (Ana, un hermano) ∧ be-LOC' (Santiago, un hermano)",
    ),
    dict(
        nombre="logro: Pepe llegó a Santiago",
        clausula="Pepe llegó a Santiago", akt="logro", sujeto="Pepe",
        respuestas=[boton("Sí"), boton("Sí"), texto("Santiago", "llegar"),
                    boton("Sí"), boton("2. Destino"), boton("Sí"), boton("No")],
        esperado="DO (Pepe, [INGR do' (Pepe, [be-LOC' (Santiago, Pepe)])])",
    ),
    dict(
        nombre="logro locativo de procedencia: Pepe salió de la casa",
        clausula="Pepe salió de la casa", akt="logro", sujeto="Pepe",
        respuestas=[boton("Sí"), boton("Sí"), texto("la casa", "salir"),
                    boton("Sí"), boton("1. Procedencia"), boton("Sí"), boton("No")],
        esperado="DO (Pepe, [INGR do' (Pepe, [NOT be-LOC' (la casa, Pepe)])])",
    ),
    dict(
        nombre="semelfactivo con anticausativa: Pepe se agachó",
        clausula="Pepe se agachó", akt="semelfactivo", sujeto="Pepe",
        respuestas=[boton("Sí"), boton("No"), boton("No"),
                    texto("agachar"), boton("Sí"), boton("Sí")],
        esperado="[do' (Ø, Ø)] CAUSE [DO (Pepe, [SEML do' (Pepe, [agachar' (Pepe)])])]",
    ),

    # ---- Realizaciones activas: las cuatro clases semánticas ----
    dict(
        nombre="realización activa de consumo: Pepe comió una manzana",
        clausula="Pepe comió una manzana", akt="realización activa",
        sujeto="Pepe", cd="una manzana",
        respuestas=[boton("No"), texto("comer"), elegir("Consumo"), boton("Sí")],
        esperado="DO (Pepe, [do' (Pepe, [comer' (Pepe, una manzana)]) ∧ PROC being.consumed' (una manzana) ∧ FIN consumed' (una manzana)])",
    ),
    dict(
        nombre="realización activa de creación: Pepe escribió un cuento",
        clausula="Pepe escribió un cuento", akt="realización activa",
        sujeto="Pepe", cd="un cuento",
        respuestas=[boton("No"), texto("escribir"), elegir("Creación"), boton("Sí")],
        esperado="DO (Pepe, [do' (Pepe, [escribir' (Pepe, un cuento)]) ∧ PROC being.created' (un cuento) ∧ FIN exist' (un cuento)])",
    ),
    dict(
        nombre="realización activa con destino: Pepe corrió hasta el parque",
        clausula="Pepe corrió hasta el parque", akt="realización activa", sujeto="Pepe",
        respuestas=[boton("Sí"), texto("el parque", "correr"), elegir("Desplazamiento"),
                    boton("2. Destino"), boton("Sí")],
        esperado="DO (Pepe, [do' (Pepe, [correr' (Pepe)]) ∧ PROC covering.path.distance' (Pepe) ∧ FIN be-LOC' (el parque, Pepe)])",
    ),
    dict(
        nombre="realización activa: transformarse en (con régimen)",
        clausula="Pepe se transformó en mi amigo", akt="realización activa", sujeto="Pepe",
        respuestas=[boton("No"), texto("transformarse"), elegir("Ninguno de estos"),
                    boton("Sí"), texto("en", "mi amigo"), boton("Sí")],
        esperado="DO (Pepe, [do' (Pepe, [transformarse.en' (Pepe, mi amigo)]) ∧ PROC being.transformado.en' (Pepe, mi amigo) ∧ FIN transformado.en' (Pepe, mi amigo)])",
    ),

    # ---- Correr una maratón: tema incremental frente a trayecto ----
    dict(
        nombre="maratón: recorrido completado (consumo)",
        clausula="Pepe corrió una maratón", akt="realización activa",
        sujeto="Pepe", cd="una maratón",
        respuestas=[boton("No"), texto("correr"), elegir("Desplazamiento"),
                    boton("Completa el recorrido"), boton("Sí")],
        esperado="DO (Pepe, [do' (Pepe, [correr' (Pepe, una maratón)]) ∧ PROC being.consumed' (una maratón) ∧ FIN consumed' (una maratón)])",
    ),
    dict(
        nombre="maratón: lugar atravesado (cruzar el río)",
        clausula="Pepe cruzó el río", akt="realización activa",
        sujeto="Pepe", cd="el río",
        respuestas=[boton("No"), texto("cruzar"), elegir("Desplazamiento"),
                    boton("Queda al otro lado"), boton("Sí")],
        esperado="DO (Pepe, [do' (Pepe, [cruzar' (Pepe)]) ∧ PROC covering.path.distance' (Pepe, el río) ∧ FIN be-at.far.side.of' (el río, Pepe)])",
    ),
    dict(
        nombre="venir: movimiento hacia el punto de referencia",
        clausula="Pepe vino hasta Santiago", akt="realización activa", sujeto="Pepe",
        respuestas=[boton("Sí"), texto("Santiago", "venir"), elegir("Desplazamiento"),
                    boton("2. Destino"), boton("Sí")],
        esperado="DO (Pepe, [do' (Pepe, [move.toward.reference.point' (Pepe)]) ∧ PROC covering.path.distance' (Pepe) ∧ FIN be-LOC' (Santiago, Pepe)])",
    ),

    # ---- Complemento indirecto ----
    dict(
        nombre="sacar con propósito: el ladrón le robó la billetera a Pepe",
        clausula="El ladrón le robó la billetera a Pepe", akt="logro causativo",
        sujeto="el ladrón", cd="la billetera", ci="Pepe",
        respuestas=[texto("Pepe perdió la billetera"), boton("No"), boton("No"),
                    texto("robar"), boton("Sí"), boton("Sí")],
        esperado="DO (el ladrón, [[do' (el ladrón, Ø)] CAUSE [INGR NOT have' (Pepe, la billetera)] PURP [have' (el ladrón, la billetera)]])",
    ),
    dict(
        nombre="sacar sin propósito: el juez le quitó el permiso a Pepe",
        clausula="El juez le quitó el permiso a Pepe", akt="logro causativo",
        sujeto="el juez", cd="el permiso", ci="Pepe",
        respuestas=[texto("Pepe perdió el permiso"), boton("No"), boton("No"),
                    texto("quitar"), boton("No"), boton("Sí")],
        esperado="DO (el juez, [[do' (el juez, Ø)] CAUSE [INGR NOT have' (Pepe, el permiso)]])",
    ),
    dict(
        nombre="transferencia: Pepe le dio un libro a Ana",
        clausula="Pepe le dio un libro a Ana", akt="logro causativo",
        sujeto="Pepe", cd="un libro", ci="Ana",
        respuestas=[texto("Ana tiene un libro"), boton("No"), boton("No"),
                    texto("dar"), boton("Sí")],
        esperado="DO (Pepe, [[do' (Pepe, Ø)] CAUSE [INGR have' (Ana, un libro)]])",
    ),
    dict(
        nombre="pedir un objeto material",
        clausula="Pepe le pidió dinero a Ana", akt="actividad",
        sujeto="Pepe", cd="dinero", ci="Ana",
        respuestas=[texto("pedir"), boton("Objeto material"), boton("Sí")],
        esperado="DO (Pepe, [[do' (Pepe, [express.something.to.Ana' (Pepe)])] PURP [[do' (Ana, Ø)] CAUSE [INGR have' (Pepe, dinero)]]])",
    ),
    dict(
        nombre="pedir una información",
        clausula="Pepe le pidió la hora a Ana", akt="actividad",
        sujeto="Pepe", cd="la hora", ci="Ana",
        respuestas=[texto("pedir"), boton("Información"), boton("Sí")],
        esperado="DO (Pepe, [[do' (Pepe, [express.something.to.Ana' (Pepe)])] PURP [do' (Ana, [express.something.to.Pepe' (Ana, la hora)])]])",
    ),
    dict(
        nombre="enseñar: realización causativa",
        clausula="Pepe le enseñó francés a Ana", akt="realización causativa",
        sujeto="Pepe", cd="francés", ci="Ana",
        respuestas=[boton("No"), texto("enseñar"), boton("No"), boton("No"),
                    boton("Sí"), boton("Sí")],
        esperado="DO (Pepe, [[do' (Pepe, Ø)] CAUSE [BECOME know' (Ana, francés)]])",
    ),
    dict(
        nombre="dativo posesivo: avisa de que no es un argumento",
        clausula="Pepe le rompió el brazo a Ana", akt="logro causativo",
        sujeto="Pepe", cd="el brazo", ci="Ana",
        respuestas=[texto("el brazo se rompió"), boton("No"), boton("No"),
                    texto("romper"), boton("No"), boton("No"), boton("No")],
        esperado="ERROR_DE_ANALISIS",
    ),
]


# --------------------------------------------------------------------------
# Comprobaciones que no recorren la interfaz
# --------------------------------------------------------------------------

def pruebas_de_notacion():
    """La notación clásica se deriva de la moderna en todas las plantillas."""
    import ls
    fallos = []
    equivalencias = [
        ("do' (Pepe, [comer' (Pepe, una manzana)]) ∧ PROC being.consumed' (una manzana)"
         " ∧ FIN consumed' (una manzana)",
         "do' (Pepe, [comer' (Pepe, una manzana)]) & INGR consumed' (una manzana)"),
        ("⟨TNS PAST [DO (Pepe, [do' (Pepe, [run' (Pepe)]) ∧ PROC covering.path.distance' (Pepe)"
         " ∧ FIN be-LOC' (el parque, Pepe)])]⟩",
         "⟨TNS PAST [DO (Pepe, [do' (Pepe, [run' (Pepe)]) & INGR be-LOC' (el parque, Pepe)])]⟩"),
        # Sin fase procesual, la estructura no cambia
        ("INGR broken' (el jarrón)", "INGR broken' (el jarrón)"),
    ]
    for moderna, clasica in equivalencias:
        obtenida = ls.a_notacion_clasica(moderna)
        if obtenida != clasica:
            fallos.append(f"notación clásica\n       esperado: {clasica}\n       obtenido: {obtenida}")

    # Todas las plantillas del programa deben poder convertirse
    import re as _re
    fuente = open('ls.py', encoding='utf-8').read()
    for plantilla in _re.findall(r'f"([^"\n]*∧ FIN [^"\n]*)"', fuente):
        muestra = _re.sub(r"\{operador \+ ' ' if operador else ''\}", "", plantilla)
        muestra = _re.sub(r"\{[^{}]+\}", "arg", muestra)
        convertida = ls.a_notacion_clasica(muestra)
        if 'PROC' in convertida or 'FIN' in convertida:
            fallos.append(f"plantilla sin convertir: {muestra}")

    # Las listas de verbos no deben tener solapamientos que oculten una plantilla
    for nombre_a, cat_a, nombre_b, cat_b in [
            ('VERBOS_PEDIR', None, 'VERBOS_TRANSFERENCIA', 'sacar'),
            ('VERBOS_PEDIR', None, 'VERBOS_DICCION', 'preguntar')]:
        lista_a = getattr(ls, nombre_a) if cat_a is None else getattr(ls, nombre_a)[cat_a]
        lista_b = getattr(ls, nombre_b) if cat_b is None else getattr(ls, nombre_b)[cat_b]
        comunes = sorted(set(lista_a) & set(lista_b))
        if comunes:
            fallos.append(f"{nombre_a} y {nombre_b}[{cat_b}] comparten: {comunes}")

    # Ningún verbo en dos categorías de movimiento a la vez
    from collections import Counter
    repetidos = [v for v, n in Counter(
        v for lista in ls.VERBOS_MOVIMIENTO.values() for v in lista).items() if n > 1]
    if repetidos:
        fallos.append(f"verbos en más de una categoría de movimiento: {repetidos}")
    return fallos


if __name__ == '__main__':
    sys.exit(main())
