# -*- coding: utf-8 -*-
"""
Logical Structure Generator (EN version) - Streamlit
Based on the Spanish version, adapted for English
"""
import streamlit as st
import re
from dataclasses import dataclass
from typing import Optional, List, Tuple

# =============================================================================
# 1. RRG CORE COMPONENTS (Reused from Spanish version)
# =============================================================================

# --- RRG RESERVED KEYWORDS (unchanged) ---
RRG_KEYWORDS = {
    "do", "cause", "become", "ingr", "proc", "seml", "fin", "exist", 
    "be", "be-loc", "know", "have", "feel", "see", "hear", "smell", "taste", 
    "covering.path.distance", "weather", "if", "evid", "sta", "tns", "mod", 
    "asp", "not", "purp", "being.created", "being.consumed", "consumed",
    "have.as.part", "have.as.kin", "have.enough.with", "express", "hit",
    "move.away.from.reference.point", "move.up.from.reference.point", 
    "move.down.from.reference.point", "want", "use"
}

# --- OPERATORS (identical RRG system) ---
@dataclass
class Operator:
    code: str
    description: str
    requires_value: bool
    examples: str

OPERATORS = [
    Operator('IF', 'Illocutionary force', True, "DECL, INT, IMP"),
    Operator('EVID', 'Evidentiality', True, "VIS, INF, HEARSAY"),
    Operator('STA', 'Status', True, "REALIS, PSBL, NEG"),
    Operator('TNS', 'Tense', True, "PAST, PRES, FUT"),
    Operator('NEG.INT +', 'Internal negation', False, ""),
    Operator('MOD', 'Deontic modality', True, "OBLIG, PERMIS"),
    Operator('EVQ', 'Event quantification', True, "DISTR"),
    Operator('DIR.CORE', 'Core directional', True, "TOWARD.SPEAKER, AWAY.FROM.SPEAKER"),
    Operator('DIR.NUC', 'Nuclear directional', True, "UP, OUT"),
    Operator('ASP', 'Aspect', True, "PFV, PERF, PROG"),
    Operator('NEG.NUC +', 'Nuclear negation', False, "")
]

OPERATORS_DESC = {op.code: op.description for op in OPERATORS}

# --- AKTIONSART OPTIONS (identical) ---
AKTIONSART_OPTIONS = {
    "state": "state",
    "causative state": "causative state",
    "achievement": "achievement",
    "causative achievement": "causative achievement",
    "accomplishment": "accomplishment",
    "causative accomplishment": "causative accomplishment",
    "semelfactive": "semelfactive",
    "causative semelfactive": "causative semelfactive",
    "process": "process",
    "causative process": "causative process",
    "activity": "activity",
    "causative activity": "causative activity",
    "active accomplishment": "active accomplishment",
    "causative active accomplishment": "causative active accomplishment"
}

# --- AKTIONSART MODIFIERS (identical) ---
AKTIONSART_MODIFIERS = {
    "achievement": "INGR",
    "accomplishment": "BECOME",
    "process": "PROC",
    "semelfactive": "SEML",
    "causative achievement": "INGR",
    "causative accomplishment": "BECOME",
    "causative process": "PROC",
    "causative semelfactive": "SEML"
}

# =============================================================================
# 2. ENGLISH VERB LEXICON
# =============================================================================

# --- MOTION VERBS ---
VERBS_MOTION = {
    "move.away.from.reference.point": [
        "go", "leave", "depart", "exit", "flee", "escape", "migrate",
        "withdraw", "retreat", "disappear", "vanish", "move", "come"
    ],
    "move.up.from.reference.point": [
        "rise", "ascend", "climb", "scale", "soar", "elevate"
    ],
    "move.down.from.reference.point": [
        "descend", "fall", "drop", "sink", "lower", "plunge"
    ]
}

# --- WEATHER VERBS (impersonal with 'it') ---
VERBS_WEATHER = [
    "rain", "snow", "hail", "thunder", "drizzle", "pour",
    "freeze", "thaw", "clear", "cloud", "dawn", "dusk"
]

# --- TRANSFER VERBS ---
VERBS_TRANSFER = {
    "take": [
        "take", "remove", "grab", "seize", "snatch", "extract", "withdraw",
        "steal", "rob", "confiscate", "deprive", "strip", "buy", "purchase",
        "acquire", "obtain", "get", "receive", "accept", "collect"
    ],
    "give": [
        "give", "hand", "pass", "deliver", "offer", "grant", "award",
        "present", "donate", "contribute", "provide", "supply", "furnish",
        "sell", "lend", "loan", "send", "transfer", "assign", "allocate"
    ]
}

# --- SPEECH VERBS ---
VERBS_SPEECH = {
    "ask": [
        "ask", "question", "inquire", "query", "interrogate", "demand"
    ],
    "converse": [
        "talk", "speak", "chat", "converse", "discuss", "argue", "debate"
    ],
    "thank": {
        "thank": "thanks", "congratulate": "congratulations",
        "apologize": "apology", "greet": "greeting", "insult": "insult",
        "praise": "praise", "criticize": "criticism", "warn": "warning"
    },
    "promise": {
        "promise": "promise", "swear": "oath", "vow": "vow",
        "advise": "advice", "bless": "blessing", "curse": "curse"
    }
}

# --- NEGATION VERBS (triargumental) ---
VERBS_TRI_NEG = {
    "deny": [
        "deny", "refuse", "reject", "revoke", "withhold", "deprive"
    ],
    "hide": [
        "hide", "conceal", "cover", "mask", "obscure", "suppress"
    ]
}

# --- POSSESSION VERBS ---
VERBS_POSSESSION = {
    "have": [
        "have", "hold", "possess", "own", "keep", "maintain", "contain",
        "include", "carry", "bear", "display", "show", "exhibit"
    ],
    "obtain": [
        "obtain", "get", "acquire", "gain", "achieve", "attain", "receive"
    ],
    "lose": ["lose", "misplace", "forfeit"]
}

# --- PERCEPTION VERBS ---
VERBS_PERCEPTION = {
    "see": "see", "watch": "see", "observe": "see", "view": "see",
    "notice": "see", "spot": "see", "glimpse": "see", "witness": "see",
    "hear": "hear", "listen": "hear", "overhear": "hear",
    "feel": "feel", "touch": "feel", "sense": "feel",
    "taste": "taste", "sample": "taste",
    "smell": "smell", "sniff": "smell"
}

# --- IMPERSONAL PERCEPTION (English: "It sounds/looks/smells...") ---
VERBS_PERCEPTION_IMPERSONAL = {
    "taste": "taste", "smell": "smell", "sound": "hear",
    "look": "see", "feel": "feel"
}

# --- IRREGULAR PAST PARTICIPLES ---
IRREGULAR_PARTICIPLES = {
    "be": "been", "beat": "beaten", "become": "become", "begin": "begun",
    "bend": "bent", "bite": "bitten", "bleed": "bled", "blow": "blown",
    "break": "broken", "bring": "brought", "build": "built", "burn": "burnt",
    "buy": "bought", "catch": "caught", "choose": "chosen", "come": "come",
    "cost": "cost", "cut": "cut", "dig": "dug", "do": "done", "draw": "drawn",
    "dream": "dreamt", "drink": "drunk", "drive": "driven", "eat": "eaten",
    "fall": "fallen", "feed": "fed", "feel": "felt", "fight": "fought",
    "find": "found", "fly": "flown", "forbid": "forbidden", "forget": "forgotten",
    "forgive": "forgiven", "freeze": "frozen", "get": "got", "give": "given",
    "go": "gone", "grow": "grown", "hang": "hung", "have": "had", "hear": "heard",
    "hide": "hidden", "hit": "hit", "hold": "held", "hurt": "hurt", "keep": "kept",
    "know": "known", "lay": "laid", "lead": "led", "learn": "learnt",
    "leave": "left", "lend": "lent", "let": "let", "lie": "lain", "light": "lit",
    "lose": "lost", "make": "made", "mean": "meant", "meet": "met", "pay": "paid",
    "put": "put", "read": "read", "ride": "ridden", "ring": "rung", "rise": "risen",
    "run": "run", "say": "said", "see": "seen", "seek": "sought", "sell": "sold",
    "send": "sent", "set": "set", "shake": "shaken", "shine": "shone",
    "shoot": "shot", "show": "shown", "shrink": "shrunk", "shut": "shut",
    "sing": "sung", "sink": "sunk", "sit": "sat", "sleep": "slept",
    "slide": "slid", "speak": "spoken", "spend": "spent", "spin": "spun",
    "split": "split", "spread": "spread", "spring": "sprung", "stand": "stood",
    "steal": "stolen", "stick": "stuck", "sting": "stung", "stink": "stunk",
    "strike": "struck", "swear": "sworn", "sweep": "swept", "swim": "swum",
    "swing": "swung", "take": "taken", "teach": "taught", "tear": "torn",
    "tell": "told", "think": "thought", "throw": "thrown", "understand": "understood",
    "wake": "woken", "wear": "worn", "win": "won", "wind": "wound",
    "write": "written"
}

# =============================================================================
# 3. AUXILIARY FUNCTIONS
# =============================================================================

def find_verb(verb, dictionary):
    """Search for a verb in a categorized dictionary."""
    for category, verbs in dictionary.items():
        if verb in verbs:
            return category
    return None

def normalize_arg(arg: str) -> str:
    """Normalize empty arguments to Ø."""
    return 'Ø' if arg in ('0', '', None) else arg

def extract_mr(ls: str) -> tuple:
    """Extract the [MR0] or [MR1] marker from the logical structure."""
    match = re.search(r'\s*\[MR[01]\]\s*$', ls)
    if match:
        mr = match.group().strip()
        ls_without_mr = ls[:match.start()].strip()
        return (ls_without_mr, mr)
    return (ls, "")

def insert_mr(ls: str, mr: str) -> str:
    """Insert the MR marker at the end of the logical structure."""
    if mr:
        return f"{ls} {mr}"
    return ls

def infinitive_to_participle(infinitive: str) -> str:
    """Convert an English infinitive to its past participle form."""
    infinitive = infinitive.lower().strip()
    
    # Check irregular forms
    if infinitive in IRREGULAR_PARTICIPLES:
        return IRREGULAR_PARTICIPLES[infinitive]
    
    # Regular rules
    if infinitive.endswith('e'):
        return infinitive + 'd'
    elif infinitive.endswith('y') and len(infinitive) > 2 and infinitive[-2] not in 'aeiou':
        return infinitive[:-1] + 'ied'
    elif (len(infinitive) >= 3 and 
          infinitive[-1] not in 'aeiouwxy' and 
          infinitive[-2] in 'aeiou' and 
          infinitive[-3] not in 'aeiou'):
        return infinitive + infinitive[-1] + 'ed'
    else:
        return infinitive + 'ed'

# =============================================================================
# 4. EXPORT FUNCTIONS (Reused from Spanish version)
# =============================================================================

def clean_html_ls(ls_html: str) -> str:
    """Convert HTML-formatted logical structure to plain text."""
    text = ls_html
    text = text.replace('&lt;', '⟨')
    text = text.replace('&gt;', '⟩')
    text = re.sub(r'<[^>]+>', '', text)
    return text

def convert_ls_to_latex(ls_html: str) -> str:
    """Convert HTML-formatted logical structure to LaTeX (math mode)."""
    text = ls_html
    
    # Convert bold (predicative constants)
    text = re.sub(r'<b>([^<]+)</b>', r'\\mathbf{\1}', text)
    
    # Convert operator opening: &lt;<sub>XX</sub> → \langle_{\text{XX}}\;
    text = re.sub(r'&lt;<sub>([^<]+)</sub>', r'\\langle_{\\text{\1}}\\;', text)
    
    # Convert italics (operator values) with space after
    text = re.sub(r'<i>([^<]+)</i>', r'\\textit{\1}\\;', text)
    
    # Convert angle closing with space before
    text = text.replace('&gt;', r'\rangle')
    
    # Convert empty symbol
    text = text.replace('Ø', r'\varnothing')
    
    # Convert RRG keywords to text with spaces
    keywords = ['CAUSE', 'INGR', 'BECOME', 'PROC', 'SEML', 'PURP', 'FIN', 'NOT']
    for kw in keywords:
        text = re.sub(rf'(?<![a-zA-Z]){kw}(?![a-zA-Z\'])', f'\\;\\\\text{{{kw}}}\\;', text)
    
    # Format [MR0] and [MR1]
    text = re.sub(r'\[MR([01])\]', r'\\;[\\text{MR\1}]', text)
    
    # Format arguments in parentheses
    def format_argument(match):
        arg = match.group(1)
        if arg[0].isupper() and arg not in keywords:
            return f'\\text{{{arg}}}'
        return arg
    
    text = re.sub(r'\b([A-Z][a-z]*)\b(?![}\'])', format_argument, text)
    
    # Add space after commas
    text = text.replace(',', ', ')
    
    # Wrap in math mode
    text = f'${text}$'
    return text

def generate_ls_image(ls_html: str) -> bytes:
    """Generate a PNG image of the logical structure."""
    import matplotlib.pyplot as plt
    from io import BytesIO
    
    # Convert HTML to matplotlib mathtext format
    text = ls_html
    text = text.replace('&lt;', '⟨')
    text = text.replace('&gt;', '⟩')
    text = re.sub(r'<sub>([^<]+)</sub>', r'$_{\\mathrm{\1}}$', text)
    text = re.sub(r'<i>([^<]+)</i>', r'$\\mathit{\1}$', text)
    text = re.sub(r'<b>([^<]+)</b>', r'$\\mathbf{\1}$', text)
    
    # Calculate width based on length
    width = max(len(ls_html) * 0.08, 10)
    
    fig, ax = plt.subplots(figsize=(width, 1.5))
    ax.axis('off')
    
    ax.text(0.5, 0.5, text,
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

def extract_predicates_from_ls(ls_html: str) -> list:
    """Extract predicates (in bold) from the logical structure, excluding RRG keywords."""
    pattern = r"<b>([^<]+)'</b>"
    matches = re.findall(pattern, ls_html)
    seen = set()
    unique = []
    for m in matches:
        m_lower = m.lower()
        m_base = m_lower.split('.')[0]
        if m not in seen and m_lower not in RRG_KEYWORDS and m_base not in RRG_KEYWORDS:
            seen.add(m)
            unique.append(m)
    return unique

def replace_predicate_in_ls(ls_html: str, old_pred: str, new_pred: str) -> str:
    """Replace a predicate with another in the logical structure."""
    pattern = f"<b>{re.escape(old_pred)}'</b>"
    replacement = f"<b>{new_pred}'</b>"
    return re.sub(pattern, replacement, ls_html)

# =============================================================================
# 5. LOGICAL STRUCTURE GENERATION FUNCTIONS
# =============================================================================

def generate_non_causative_structure(x, y, locus, pred, modifier, AKT):
    """Generate LS for non-causative predicates (states, achievements, accomplishments, processes, semelfactives)."""
    mod_prefix = f"{modifier} " if modifier else ""
    
    if y != "Ø" and locus == "Ø":
        return f"{mod_prefix}<b>{pred}'</b> ({x}, {y})"
    elif y == "Ø" and locus != "Ø":
        return f"{mod_prefix}<b>{pred}'</b> ({x}, {locus})"
    elif y == "Ø" and locus == "Ø":
        return f"{mod_prefix}<b>{pred}'</b> ({x})"
    return None

def generate_causative_structure(x, y, pred, modifier):
    """Generate LS for causative predicates (non-activity)."""
    if y == "Ø":
        return None
    mod_prefix = f"{modifier} " if modifier else ""
    return f"[<b>do'</b> ({x}, Ø)] CAUSE [{mod_prefix}<b>{pred}'</b> ({y})]"

def generate_activity_structure(x, y, locus, pred, modifier):
    """Generate LS for activity predicates."""
    mod_prefix = f"{modifier} " if modifier else ""
    
    if y != "Ø" and locus == "Ø":
        return f"{mod_prefix}<b>do'</b> ({x}, [<b>{pred}'</b> ({x}, {y})])"
    elif y == "Ø" and locus != "Ø":
        return f"{mod_prefix}<b>do'</b> ({x}, [<b>{pred}'</b> ({x}, {locus})])"
    elif y == "Ø" and locus == "Ø":
        return f"{mod_prefix}<b>do'</b> ({x}, [<b>{pred}'</b> ({x})])"
    return None

def generate_causative_activity_structure(x, y, pred, modifier):
    """Generate LS for causative activity predicates."""
    if y == "Ø":
        return None
    mod_prefix = f"{modifier} " if modifier else ""
    return f"[<b>do'</b> ({x}, Ø)] CAUSE [{mod_prefix}<b>do'</b> ({y}, [<b>{pred}'</b> ({y})])]"

# --- ACTIVE ACCOMPLISHMENT STRUCTURES ---

def generate_active_accomplishment_creation(x, y, pred):
    """Generate LS for active accomplishment of creation type.
    Example: 'John wrote a letter' -> do'(John, [write'(John, letter)]) & PROC being.created'(letter) & FIN exist'(letter)
    """
    return f"<b>do'</b> ({x}, [<b>{pred}'</b> ({x}, {y})]) ∧ PROC <b>being.created'</b> ({y}) ∧ FIN <b>exist'</b> ({y})"

def generate_active_accomplishment_consumption(x, y, pred):
    """Generate LS for active accomplishment of consumption type.
    Example: 'John ate the pizza' -> do'(John, [eat'(John, pizza)]) & PROC being.consumed'(pizza) & FIN consumed'(pizza)
    """
    return f"<b>do'</b> ({x}, [<b>{pred}'</b> ({x}, {y})]) ∧ PROC <b>being.consumed'</b> ({y}) ∧ FIN <b>consumed'</b> ({y})"

def generate_active_accomplishment_motion(x, pred, locus, is_destination=True):
    """Generate LS for active accomplishment of motion type.
    Example: 'Peter ran to the store' -> do'(Peter, [run'(Peter)]) & PROC covering.path.distance'(Peter) & FIN be-LOC'(the.store, Peter)
    """
    if is_destination:
        fin_pred = f"<b>be-LOC'</b> ({locus}, {x})"
    else:
        fin_pred = f"NOT <b>be-LOC'</b> ({locus}, {x})"
    
    return f"<b>do'</b> ({x}, [<b>{pred}'</b> ({x})]) ∧ PROC <b>covering.path.distance'</b> ({x}) ∧ FIN {fin_pred}"

def generate_active_accomplishment_other(x, y, pred, result_pred):
    """Generate LS for active accomplishment with other result states.
    Example: 'John wiped the table clean' -> do'(John, [wipe'(John, table)]) & PROC clean'(table) & FIN clean'(table)
    """
    return f"<b>do'</b> ({x}, [<b>{pred}'</b> ({x}, {y})]) ∧ PROC <b>{result_pred}'</b> ({y}) ∧ FIN <b>{result_pred}'</b> ({y})"

def generate_causative_active_accomplishment_motion(x, y, pred, locus, is_destination=True):
    """Generate LS for causative active accomplishment of motion type.
    Example: 'John chased Mary to the park' -> [do'(John, Ø)] CAUSE [do'(Mary, [run'(Mary)]) & PROC covering.path.distance'(Mary) & FIN be-LOC'(park, Mary)]
    """
    if is_destination:
        fin_pred = f"<b>be-LOC'</b> ({locus}, {y})"
    else:
        fin_pred = f"NOT <b>be-LOC'</b> ({locus}, {y})"
    
    return f"[<b>do'</b> ({x}, Ø)] CAUSE [<b>do'</b> ({y}, [<b>{pred}'</b> ({y})]) ∧ PROC <b>covering.path.distance'</b> ({y}) ∧ FIN {fin_pred}]"

def generate_causative_active_accomplishment_creation(x, z, y, pred):
    """Generate LS for causative active accomplishment of creation type."""
    return f"[<b>do'</b> ({x}, Ø)] CAUSE [<b>do'</b> ({z}, [<b>{pred}'</b> ({z}, {y})]) ∧ PROC <b>being.created'</b> ({y}) ∧ FIN <b>exist'</b> ({y})]"

def generate_causative_active_accomplishment_consumption(x, z, y, pred):
    """Generate LS for causative active accomplishment of consumption type."""
    return f"[<b>do'</b> ({x}, Ø)] CAUSE [<b>do'</b> ({z}, [<b>{pred}'</b> ({z}, {y})]) ∧ PROC <b>being.consumed'</b> ({y}) ∧ FIN <b>consumed'</b> ({y})]"

def apply_DO(x, logical_structure):
    """Apply the DO operator for intentionality."""
    if logical_structure is None:
        return None
    ls_without_mr, mr = extract_mr(logical_structure)
    result = f"DO ({ls_without_mr})"
    return insert_mr(result, mr)

def apply_anticausative(logical_structure):
    """Apply anticausative transformation."""
    ls_without_mr, mr = extract_mr(logical_structure)
    result = f"[<b>do'</b> (Ø, Ø)] CAUSE [{ls_without_mr}]"
    return insert_mr(result, mr)

def add_operators_to_ls(logical_structure: str, selected_operators: List[Tuple[str, Optional[str]]]) -> str:
    """Add operators to the logical structure with RRG format."""
    if not selected_operators:
        return logical_structure
    
    ls_without_mr, mr = extract_mr(logical_structure)
    if mr:
        result = f"[{ls_without_mr}]{mr}"
    else:
        result = f"[{ls_without_mr}]"
    
    for code, value in reversed(selected_operators):
        if code.endswith(' +'):
            base_code = code[:-2]
            code_suffix = " <i>+</i>"
        else:
            base_code = code
            code_suffix = ""
        
        if value and value.endswith(' +'):
            base_value = value[:-2]
            formatted_value = f"<i>{base_value}</i> <i>+</i>"
        elif value:
            formatted_value = f"<i>{value}</i>"
        else:
            formatted_value = ""
        
        if formatted_value:
            result = f"&lt;<sub>{base_code}</sub>{code_suffix} {formatted_value} {result}&gt;"
        else:
            result = f"&lt;<sub>{base_code}</sub>{code_suffix} {result}&gt;"
    
    return result

# =============================================================================
# 6. STREAMLIT NAVIGATION
# =============================================================================

def create_goto_callback(step, **kwargs):
    """Create a callback to navigate to a specific step."""
    def callback():
        for key, value in kwargs.items():
            st.session_state[key] = value
        st.session_state.ls_step = step
    return callback

def goto(step):
    """Navigate to a step (use only within forms or at start)."""
    st.session_state.ls_step = step
    st.rerun()

def goto_intentionality():
    """Navigate to intentionality step, saving pre-DO structure."""
    st.session_state.ls_structure_pre_do = st.session_state.ls_structure
    st.session_state.ls_step = 'intentionality'
    st.rerun()

def reset_analysis():
    """Clear all LS analysis state and reset to initial step."""
    keys_to_delete = [k for k in list(st.session_state.keys()) if k.startswith('ls_')]
    for key in keys_to_delete:
        del st.session_state[key]
    st.session_state.ls_is_dynamic = None

def navigation_buttons():
    st.write("---")
    st.button("Start new analysis", use_container_width=True, 
              key=f"nav_reset_{st.session_state.ls_step}", on_click=reset_analysis)

# =============================================================================
# 7. INFO PANEL
# =============================================================================

def show_info_panel():
    """Display the information panel with current analysis data."""
    
    st.markdown("""
        <style>
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
        }
        .info-value-akt {
            font-weight: 600;
            text-transform: uppercase;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="info-panel-title">Analysis data</div>', unsafe_allow_html=True)
    
    # Clause
    if st.session_state.get('ls_clause'):
        st.markdown(f'''
            <div class="info-item">
                <div class="info-label">Clause</div>
                <div class="info-value">{st.session_state.ls_clause}</div>
            </div>
        ''', unsafe_allow_html=True)
    
    # Aktionsart
    if st.session_state.get('ls_akt'):
        st.markdown(f'''
            <div class="info-item">
                <div class="info-label">Aktionsart</div>
                <div class="info-value info-value-akt">{st.session_state.ls_akt}</div>
            </div>
        ''', unsafe_allow_html=True)
    
    # Subject
    x = st.session_state.get('ls_x')
    if x and x != 'Ø':
        st.markdown(f'''
            <div class="info-item">
                <div class="info-label">Subject</div>
                <div class="info-value">{x}</div>
            </div>
        ''', unsafe_allow_html=True)
    
    # Direct object
    y = st.session_state.get('ls_y')
    if y and y != 'Ø':
        st.markdown(f'''
            <div class="info-item">
                <div class="info-label">Direct object</div>
                <div class="info-value">{y}</div>
            </div>
        ''', unsafe_allow_html=True)
    
    # Indirect object
    z = st.session_state.get('ls_z')
    if z and z != 'Ø':
        st.markdown(f'''
            <div class="info-item">
                <div class="info-label">Indirect object</div>
                <div class="info-value">{z}</div>
            </div>
        ''', unsafe_allow_html=True)
    
    # Locative
    locus = st.session_state.get('ls_locus')
    if locus and locus != 'Ø':
        st.markdown(f'''
            <div class="info-item">
                <div class="info-label">Locative information</div>
                <div class="info-value">{locus}</div>
            </div>
        ''', unsafe_allow_html=True)
    
    # Logical structure
    current_step = st.session_state.get('ls_step', '')
    steps_show_ls = ['result', 'select_operators', 'final']
    if current_step in steps_show_ls:
        ls_structure = st.session_state.get('ls_structure')
        if ls_structure:
            st.markdown(f'''
                <div class="info-item">
                    <div class="info-label">Logical structure</div>
                    <div class="info-value-ls">{ls_structure}</div>
                </div>
            ''', unsafe_allow_html=True)

# =============================================================================
# 8. MAIN INTERFACE
# =============================================================================

def show_ls_assistant():
    st.markdown("""
        <style>
        .ls-result {
            font-family: 'Courier New', Courier, monospace;
            font-size: 1.1em;
            padding: 15px;
            background-color: #f8f9fa;
            border-left: 4px solid #4A90E2;
            margin: 10px 0;
            word-wrap: break-word;
        }
        </style>
    """, unsafe_allow_html=True)

    # Initialize state
    if 'ls_step' not in st.session_state:
        st.session_state.ls_step = 'start'
        st.session_state.ls_clause = ''
        st.session_state.ls_akt = ''
        st.session_state.ls_x = ''
        st.session_state.ls_y = ''
        st.session_state.ls_z = ''
        st.session_state.ls_pred = ''
        st.session_state.ls_locus = 'Ø'
        st.session_state.ls_is_dynamic = None
        st.session_state.ls_is_destination = True
        st.session_state.ls_location_type = ""
        st.session_state.ls_structure = ''
        st.session_state.ls_structure_pre_do = ''
        st.session_state.ls_structure_with_do = ''
        st.session_state.ls_operators = []
        st.session_state.ls_answers = {}

    # Layout: main content (2) + info panel (1)
    col_main, col_spacer, col_info = st.columns([2, 0.1, 1])
    
    with col_info:
        show_info_panel()
    
    with col_main:
        # --- STEP: START ---
        if st.session_state.ls_step == 'start':
            st.info("**This module helps you formalize the basic logical structure of an English clause.**")
            st.warning("Note: The program handles simple clauses with typical argument structure. Complex constructions may yield inaccurate results.")
            
            with st.form(key="form_start"):
                clause = st.text_input("Enter the clause to analyze:")
                akt = st.selectbox("Select the aktionsart:", 
                                   options=[""] + list(AKTIONSART_OPTIONS.keys()),
                                   format_func=lambda x: "-- Select --" if x == "" else x.upper())
                
                if st.form_submit_button("Continue", use_container_width=True):
                    if clause and akt:
                        st.session_state.ls_clause = clause
                        st.session_state.ls_akt = akt
                        # Set dynamicity based on aktionsart
                        static_types = ["state", "causative state"]
                        st.session_state.ls_is_dynamic = akt not in static_types
                        goto('arguments')
                    else:
                        st.error("Please enter a clause and select an aktionsart.")

        # --- STEP: ARGUMENTS ---
        elif st.session_state.ls_step == 'arguments':
            st.markdown("#### **Argument structure**")
            st.info("Enter the arguments of the clause. Leave blank for non-existent arguments.")
            
            with st.form(key="form_arguments"):
                x = st.text_input("Subject (x):", placeholder="e.g., John, the cat")
                y = st.text_input("Direct object (y):", placeholder="e.g., the book, her")
                z = st.text_input("Indirect object (z):", placeholder="e.g., Mary, to him")
                
                if st.form_submit_button("Continue", use_container_width=True):
                    st.session_state.ls_x = normalize_arg(x)
                    st.session_state.ls_y = normalize_arg(y)
                    st.session_state.ls_z = normalize_arg(z)
                    goto('route_case')
            
            navigation_buttons()

        # --- STEP: ROUTE CASE ---
        elif st.session_state.ls_step == 'route_case':
            AKT = st.session_state.ls_akt
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            z = st.session_state.ls_z
            
            # Weather verbs (impersonal)
            if x == "Ø" and y == "Ø" and z == "Ø":
                goto('weather_case')
            # State special cases
            elif AKT == "state":
                goto('state_case')
            # Causative with sensations
            elif AKT in ["causative state", "causative achievement", 
                        "causative accomplishment", "causative process"]:
                goto('causative_sensation_check')
            # Verbs with IO
            elif z != "Ø":
                goto('io_case')
            # Other cases
            else:
                goto('locative_case')

        # --- WEATHER CASE ---
        elif st.session_state.ls_step == 'weather_case':
            with st.form(key="form_weather"):
                st.info("Enter the weather predicate (e.g., *rain*, *snow*, *cold*):")
                pred = st.text_input("Predicate", label_visibility="collapsed")
                if st.form_submit_button("Generate structure"):
                    pred = pred.lower().replace(" ", ".")
                    st.session_state.ls_pred = pred
                    modifier = AKTIONSART_MODIFIERS.get(st.session_state.ls_akt, "")
                    mod_prefix = f"{modifier} " if modifier else ""
                    ls = f"{mod_prefix}<b>{pred}'</b> (weather)"
                    st.session_state.ls_structure = ls
                    goto_intentionality()
            navigation_buttons()

        # --- STATE CASE ---
        elif st.session_state.ls_step == 'state_case':
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            clause = st.session_state.ls_clause
            
            if y == "Ø":
                st.info(f"Does **{clause}** express an essential attribute using the verb 'be' (e.g., *John is tall*)?")
                c1, c2 = st.columns(2)
                c1.button("Yes", use_container_width=True, key="be_yes", 
                         on_click=create_goto_callback('state_be'))
                c2.button("No", use_container_width=True, key="be_no", 
                         on_click=create_goto_callback('state_sensation'))
            else:
                goto('state_sensation_od')
            navigation_buttons()

        elif st.session_state.ls_step == 'state_be':
            with st.form(key="form_state_be"):
                st.info("Enter the attribute:")
                pred = st.text_input("Attribute", label_visibility="collapsed")
                if st.form_submit_button("Generate structure"):
                    pred = pred.lower().replace(" ", ".")
                    st.session_state.ls_pred = pred
                    x = st.session_state.ls_x
                    ls = f"<b>be'</b> ({x}, [<b>{pred}'</b>])"
                    st.session_state.ls_structure = ls
                    goto_intentionality()
            navigation_buttons()

        elif st.session_state.ls_step == 'state_sensation':
            st.info("Is the state a type of sensation or feeling (e.g., *cold*, *love*, *fear*)?")
            c1, c2 = st.columns(2)
            c1.button("Yes", use_container_width=True, key="sens_yes", 
                     on_click=create_goto_callback('state_feel'))
            c2.button("No", use_container_width=True, key="sens_no", 
                     on_click=create_goto_callback('locative_case'))
            navigation_buttons()

        elif st.session_state.ls_step == 'state_feel':
            with st.form(key="form_state_feel"):
                st.info("Enter the sensation or feeling (e.g., *cold*, *in love*):")
                pred = st.text_input("Sensation", label_visibility="collapsed")
                if st.form_submit_button("Generate structure"):
                    pred = pred.lower().replace(" ", ".")
                    st.session_state.ls_pred = pred
                    x = st.session_state.ls_x
                    ls = f"<b>feel'</b> ({x}, [<b>{pred}'</b>])"
                    st.session_state.ls_structure = ls
                    goto_intentionality()
            navigation_buttons()

        elif st.session_state.ls_step == 'state_sensation_od':
            y = st.session_state.ls_y
            st.info(f"Does *{y}* express a sensation or feeling?")
            c1, c2 = st.columns(2)
            
            def _sens_od_yes():
                y = st.session_state.ls_y
                y_clean = y.replace(" ", ".")
                x = st.session_state.ls_x
                ls = f"<b>feel'</b> ({x}, [<b>{y_clean}'</b>])"
                st.session_state.ls_structure = ls
                st.session_state.ls_structure_pre_do = st.session_state.ls_structure
                st.session_state.ls_step = 'intentionality'
            
            c1.button("Yes", use_container_width=True, key="sens_od_yes", on_click=_sens_od_yes)
            c2.button("No", use_container_width=True, key="sens_od_no", 
                     on_click=create_goto_callback('locative_case'))
            navigation_buttons()

        # --- CAUSATIVE WITH SENSATION CHECK ---
        elif st.session_state.ls_step == 'causative_sensation_check':
            AKT = st.session_state.ls_akt
            if AKT == "causative state":
                question = "Is the state a type of sensation or feeling (e.g., *fear*, *love*, *cold*)?"
            else:
                question = "Does the resulting event involve a sensation or feeling (e.g., *fear*, *love*, *cold*)?"
            st.info(question)
            c1, c2 = st.columns(2)
            c1.button("Yes", use_container_width=True, key="caus_sens_yes", 
                     on_click=create_goto_callback('causative_sensation'))
            c2.button("No", use_container_width=True, key="caus_sens_no", 
                     on_click=create_goto_callback('locative_case'))
            navigation_buttons()

        elif st.session_state.ls_step == 'causative_sensation':
            AKT = st.session_state.ls_akt
            modifier = AKTIONSART_MODIFIERS.get(AKT, "")
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            z = st.session_state.ls_z
            
            experiencer = z if z != "Ø" else y

            with st.form(key="form_caus_sens"):
                st.info("Enter the sensation or feeling (e.g., *fear*, *love*, *cold*):")
                pred = st.text_input("Sensation", label_visibility="collapsed")
                if st.form_submit_button("Generate structure"):
                    pred = pred.lower().replace(" ", ".")
                    st.session_state.ls_pred = pred
                    mod_prefix = f"{modifier} " if modifier else ""
                    ls = f"[<b>do'</b> ({x}, Ø)] CAUSE [{mod_prefix}<b>feel'</b> ({experiencer}, [<b>{pred}'</b>])]"
                    st.session_state.ls_structure = ls
                    goto_intentionality()
            navigation_buttons()

        # --- IO CASE ---
        elif st.session_state.ls_step == 'io_case':
            with st.form(key="form_io_pred"):
                st.info("Enter the verb infinitive:")
                pred = st.text_input("Infinitive", label_visibility="collapsed")
                if st.form_submit_button("Continue"):
                    st.session_state.ls_pred = pred.lower().replace(" ", ".")
                    goto('verify_io_type')
            navigation_buttons()

        elif st.session_state.ls_step == 'verify_io_type':
            pred = st.session_state.ls_pred
            AKT = st.session_state.ls_akt
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            z = st.session_state.ls_z
            modifier = AKTIONSART_MODIFIERS.get(AKT, "")
            mod_prefix = f"{modifier} " if modifier else ""
            
            # Check transfer verbs
            if pred in VERBS_TRANSFER["take"]:
                ls = f"[<b>do'</b> ({x}, Ø)] CAUSE [{mod_prefix}NOT <b>have'</b> ({z}, {y})] PURP [<b>have'</b> ({x}, {y})]"
                st.session_state.ls_structure = ls
                goto_intentionality()
            elif pred in VERBS_TRANSFER["give"]:
                ls = f"[<b>do'</b> ({x}, Ø)] CAUSE [{mod_prefix}<b>have'</b> ({z}, {y})]"
                st.session_state.ls_structure = ls
                goto_intentionality()
            else:
                goto('transfer_question')

        elif st.session_state.ls_step == 'transfer_question':
            pred = st.session_state.ls_pred
            st.info(f"Is the typical meaning of **{pred}** the physical transfer of an object?")
            c1, c2 = st.columns(2)
            
            def _trans_yes():
                x = st.session_state.ls_x
                y = st.session_state.ls_y
                z = st.session_state.ls_z
                modifier = AKTIONSART_MODIFIERS.get(st.session_state.ls_akt, "")
                mod_prefix = f"{modifier} " if modifier else ""
                ls = f"[<b>do'</b> ({x}, Ø)] CAUSE [{mod_prefix}<b>have'</b> ({z}, {y})]"
                st.session_state.ls_structure = ls
                st.session_state.ls_structure_pre_do = st.session_state.ls_structure
                st.session_state.ls_step = 'intentionality'
            
            c1.button("Yes", use_container_width=True, key="trans_yes", on_click=_trans_yes)
            c2.button("No", use_container_width=True, key="trans_no", 
                     on_click=create_goto_callback('speech_question'))
            navigation_buttons()

        elif st.session_state.ls_step == 'speech_question':
            pred = st.session_state.ls_pred
            st.info(f"Is **{pred}** a speech verb (e.g., tell, say, ask)?")
            c1, c2 = st.columns(2)
            c1.button("Yes", use_container_width=True, key="speech_yes", 
                     on_click=create_goto_callback('generate_speech'))
            c2.button("No", use_container_width=True, key="speech_no", 
                     on_click=create_goto_callback('teach_question'))
            navigation_buttons()

        elif st.session_state.ls_step == 'generate_speech':
            pred = st.session_state.ls_pred
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            z = st.session_state.ls_z
            modifier = AKTIONSART_MODIFIERS.get(st.session_state.ls_akt, "")
            mod_prefix = f"{modifier} " if modifier else ""
            
            y_clean = "something" if y in ["Ø", "0"] else y.replace(" ", ".")
            
            if pred in VERBS_SPEECH["ask"]:
                ls = f"[{mod_prefix}<b>do'</b> ({x}, [<b>express.question'</b> ({x})])] PURP [<b>do'</b> ({z}, [<b>express.{y_clean}'</b> ({z}, {y})])]"
            elif pred in VERBS_SPEECH["thank"]:
                arg_inc = VERBS_SPEECH["thank"].get(pred, pred)
                ls = f"[{mod_prefix}<b>do'</b> ({x}, [<b>express.{arg_inc}'</b> ({x}, {y})])] PURP [<b>know'</b> ({z}, {arg_inc} for {y})]"
            elif pred in VERBS_SPEECH["promise"]:
                arg_inc = VERBS_SPEECH["promise"].get(pred, pred)
                ls = f"[{mod_prefix}<b>do'</b> ({x}, [<b>express.{arg_inc}'</b> ({x}, {y})])] PURP [<b>know'</b> ({z}, {arg_inc} about {y})]"
            else:
                ls = f"[{mod_prefix}<b>do'</b> ({x}, [<b>express.something'</b> ({x}, {y})])] PURP [<b>know'</b> ({z}, {y})]"
            
            st.session_state.ls_structure = ls
            goto_intentionality()

        elif st.session_state.ls_step == 'teach_question':
            pred = st.session_state.ls_pred
            st.info(f"Is **{pred}** a verb like *teach*, *show*, or *demonstrate*?")
            c1, c2 = st.columns(2)
            
            def _teach_yes():
                x = st.session_state.ls_x
                y = st.session_state.ls_y
                z = st.session_state.ls_z
                modifier = AKTIONSART_MODIFIERS.get(st.session_state.ls_akt, "")
                mod_prefix = f"{modifier} " if modifier else ""
                ls = f"[<b>do'</b> ({x}, Ø)] CAUSE [{mod_prefix}<b>know'</b> ({z}, {y})]"
                st.session_state.ls_structure = ls
                st.session_state.ls_structure_pre_do = st.session_state.ls_structure
                st.session_state.ls_step = 'intentionality'
            
            def _teach_no():
                x = st.session_state.ls_x
                z = st.session_state.ls_z
                modifier = AKTIONSART_MODIFIERS.get(st.session_state.ls_akt, "")
                mod_prefix = f"{modifier} " if modifier else ""
                # Default triargumental structure
                ls = f"{mod_prefix}<b>do'</b> ({x}, [<b>{st.session_state.ls_pred}'</b> ({x}, {z})]) [MR1]"
                st.session_state.ls_structure = ls
                st.session_state.ls_structure_pre_do = st.session_state.ls_structure
                st.session_state.ls_step = 'intentionality'
            
            c1.button("Yes", use_container_width=True, key="teach_yes", on_click=_teach_yes)
            c2.button("No", use_container_width=True, key="teach_no", on_click=_teach_no)
            navigation_buttons()

        # --- LOCATIVE CASE ---
        elif st.session_state.ls_step == 'locative_case':
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            clause = st.session_state.ls_clause
            
            args_present = [f"*{arg}*" for arg in [x, y] if arg != "Ø"]
            participants_text = " or ".join(args_present) if args_present else "the participants"
            
            msg = (
                f"Consider the clause **{clause}**.\n\n"
                f"Does any of its core arguments (not peripheral) indicate the location, destination, or source of **{participants_text}**?"
            )

            st.info(msg)
            c1, c2 = st.columns(2)
            c1.button("Yes", use_container_width=True, key="loc_yes", 
                     on_click=create_goto_callback('get_locative'))
            c2.button("No", use_container_width=True, key="loc_no", 
                     on_click=create_goto_callback('mental_info'))
            navigation_buttons()

        elif st.session_state.ls_step == 'get_locative':
            with st.form(key="form_loc"):
                st.info("Enter the location information (without preposition):")
                locus = st.text_input("Location", label_visibility="collapsed")
                st.info("Enter the verb infinitive:")
                pred = st.text_input("Infinitive", label_visibility="collapsed")
                if st.form_submit_button("Continue"):
                    st.session_state.ls_locus = locus
                    st.session_state.ls_pred = pred.lower().replace(" ", ".")
                    goto('process_locative')
            navigation_buttons()

        elif st.session_state.ls_step == 'process_locative':
            pred = st.session_state.ls_pred
            AKT = st.session_state.ls_akt
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            locus = st.session_state.ls_locus
            is_dynamic = st.session_state.ls_is_dynamic
            modifier = AKTIONSART_MODIFIERS.get(AKT, "")
            mod_prefix = f"{modifier} " if modifier else ""
            
            # ACTIVE ACCOMPLISHMENTS with locative -> go to motion flow
            if AKT in ["active accomplishment", "causative active accomplishment"]:
                goto('aa_motion_direction')
            # Check motion verbs for other aktionsarts
            else:
                motion_type = None
                for m_type, verbs in VERBS_MOTION.items():
                    if pred in verbs:
                        motion_type = m_type
                        break
                
                if motion_type:
                    if "causativ" in AKT:
                        ls = f"[<b>do'</b> ({x}, Ø)] CAUSE [{mod_prefix}<b>do'</b> ({y}, [<b>{motion_type}'</b> ({y})])]"
                    else:
                        ls = f"{mod_prefix}<b>do'</b> ({x}, [<b>{motion_type}'</b> ({x})])"
                    st.session_state.ls_structure = ls
                    goto_intentionality()
                elif "causativ" in AKT:
                    goto('location_type_question_caus')
                else:
                    goto('location_type_question')

        elif st.session_state.ls_step == 'location_type_question':
            locus = st.session_state.ls_locus
            st.info(f"Is *{locus}* the source or the destination?")
            c1, c2 = st.columns(2)
            c1.button("Source", use_container_width=True, key="source", 
                     on_click=create_goto_callback('generate_motion', ls_location_type="1"))
            c2.button("Destination", use_container_width=True, key="dest", 
                     on_click=create_goto_callback('generate_motion', ls_location_type="2"))
            navigation_buttons()

        elif st.session_state.ls_step == 'generate_motion':
            x = st.session_state.ls_x
            locus = st.session_state.ls_locus
            is_dynamic = st.session_state.ls_is_dynamic
            modifier = AKTIONSART_MODIFIERS.get(st.session_state.ls_akt, "")
            mod_prefix = f"{modifier} " if modifier else ""
            location_type = st.session_state.ls_location_type
            
            if is_dynamic:
                if location_type == "1":
                    ls = f"{mod_prefix}<b>do'</b> ({x}, [NOT <b>be-LOC'</b> ({locus}, {x})])"
                else:
                    ls = f"{mod_prefix}<b>do'</b> ({x}, [<b>be-LOC'</b> ({locus}, {x})])"
            else:
                if location_type == "1":
                    ls = f"{mod_prefix}NOT <b>be-LOC'</b> ({locus}, {x})"
                else:
                    ls = f"{mod_prefix}<b>be-LOC'</b> ({locus}, {x})"
            
            st.session_state.ls_structure = ls
            goto_intentionality()

        elif st.session_state.ls_step == 'location_type_question_caus':
            locus = st.session_state.ls_locus
            st.info(f"Is *{locus}* the source or the destination?")
            c1, c2 = st.columns(2)
            c1.button("Source", use_container_width=True, key="source_caus", 
                     on_click=create_goto_callback('generate_motion_caus', ls_location_type="1"))
            c2.button("Destination", use_container_width=True, key="dest_caus", 
                     on_click=create_goto_callback('generate_motion_caus', ls_location_type="2"))
            navigation_buttons()

        elif st.session_state.ls_step == 'generate_motion_caus':
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            locus = st.session_state.ls_locus
            is_dynamic = st.session_state.ls_is_dynamic
            modifier = AKTIONSART_MODIFIERS.get(st.session_state.ls_akt, "")
            mod_prefix = f"{modifier} " if modifier else ""
            location_type = st.session_state.ls_location_type
            
            if is_dynamic:
                if location_type == "1":
                    ls = f"[<b>do'</b> ({x}, Ø)] CAUSE [{mod_prefix}<b>do'</b> ({y}, [NOT <b>be-LOC'</b> ({locus}, {y})])]"
                else:
                    ls = f"[<b>do'</b> ({x}, Ø)] CAUSE [{mod_prefix}<b>do'</b> ({y}, [<b>be-LOC'</b> ({locus}, {y})])]"
            else:
                if location_type == "1":
                    ls = f"[<b>do'</b> ({x}, Ø)] CAUSE [{mod_prefix}NOT <b>be-LOC'</b> ({locus}, {y})]"
                else:
                    ls = f"[<b>do'</b> ({x}, Ø)] CAUSE [{mod_prefix}<b>be-LOC'</b> ({locus}, {y})]"
            
            st.session_state.ls_structure = ls
            goto_intentionality()

        # --- MENTAL INFORMATION ---
        elif st.session_state.ls_step == 'mental_info':
            y = st.session_state.ls_y
            AKT = st.session_state.ls_akt
            
            if y == "Ø" or "causativ" in AKT or AKT in ["active accomplishment", "activity"]:
                goto('predicate')
            else:
                x = st.session_state.ls_x
                clause = st.session_state.ls_clause
                st.info(f"Does **{clause}** describe that **{x}** has or comes to have **{y}** in their mind?")
                st.warning("(If it's a speech or sensory perception verb, answer No)")
                c1, c2 = st.columns(2)
                
                def _mental_yes():
                    x = st.session_state.ls_x
                    y = st.session_state.ls_y
                    AKT = st.session_state.ls_akt
                    modifier = AKTIONSART_MODIFIERS.get(AKT, "")
                    mod_prefix = f"{modifier} " if modifier else ""
                    ls = f"{mod_prefix}<b>know'</b> ({x}, {y})"
                    st.session_state.ls_structure = ls
                    st.session_state.ls_structure_pre_do = st.session_state.ls_structure
                    st.session_state.ls_step = 'intentionality'
                
                c1.button("Yes", use_container_width=True, key="mental_yes", on_click=_mental_yes)
                c2.button("No", use_container_width=True, key="mental_no", 
                         on_click=create_goto_callback('predicate'))
            navigation_buttons()

        # --- PREDICATE INPUT ---
        elif st.session_state.ls_step == 'predicate':
            with st.form(key="form_predicate"):
                st.info("Enter the verb infinitive:")
                pred = st.text_input("Infinitive", label_visibility="collapsed")
                if st.form_submit_button("Generate structure"):
                    st.session_state.ls_pred = pred.lower().replace(" ", ".")
                    goto('special_predicates_check')
            navigation_buttons()

        elif st.session_state.ls_step == 'special_predicates_check':
            pred = st.session_state.ls_pred
            AKT = st.session_state.ls_akt
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            locus = st.session_state.ls_locus
            is_dynamic = st.session_state.ls_is_dynamic
            modifier = AKTIONSART_MODIFIERS.get(AKT, "")
            mod_prefix = f"{modifier} " if modifier else ""
            
            # Check perception verbs
            if pred in VERBS_PERCEPTION:
                perception_type = VERBS_PERCEPTION[pred]
                if y != "Ø":
                    ls = f"<b>{perception_type}'</b> ({x}, {y})"
                else:
                    ls = f"<b>{perception_type}'</b> ({x})"
                st.session_state.ls_structure = ls
                goto_intentionality()
            # Check possession verbs
            elif pred in VERBS_POSSESSION["have"]:
                ls = f"<b>have'</b> ({x}, {y})"
                st.session_state.ls_structure = ls
                goto_intentionality()
            elif pred in VERBS_POSSESSION["obtain"]:
                ls = f"{mod_prefix}<b>have'</b> ({x}, {y})"
                st.session_state.ls_structure = ls
                goto_intentionality()
            elif pred in VERBS_POSSESSION["lose"]:
                ls = f"{mod_prefix}NOT <b>have'</b> ({x}, {y})"
                st.session_state.ls_structure = ls
                goto_intentionality()
            else:
                goto('generate_basic')

        elif st.session_state.ls_step == 'generate_basic':
            pred = st.session_state.ls_pred
            AKT = st.session_state.ls_akt
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            locus = st.session_state.ls_locus
            is_dynamic = st.session_state.ls_is_dynamic
            modifier = AKTIONSART_MODIFIERS.get(AKT, "")
            
            # ACTIVE ACCOMPLISHMENTS require special handling with conjunctions
            if AKT in ["active accomplishment", "causative active accomplishment"]:
                goto('active_accomplishment_type')
            elif "causativ" in AKT:
                if AKT == "causative activity":
                    ls = generate_causative_activity_structure(x, y, pred, modifier)
                else:
                    ls = generate_causative_structure(x, y, pred, modifier)
                if ls:
                    st.session_state.ls_structure = ls
                    goto_intentionality()
                else:
                    st.error("Could not generate a logical structure with the provided data.")
                    navigation_buttons()
            elif AKT == "activity":
                ls = generate_activity_structure(x, y, locus, pred, modifier)
                if ls:
                    st.session_state.ls_structure = ls
                    goto_intentionality()
                else:
                    st.error("Could not generate a logical structure with the provided data.")
                    navigation_buttons()
            else:
                ls = generate_non_causative_structure(x, y, locus, pred, modifier, AKT)
                if ls:
                    st.session_state.ls_structure = ls
                    goto_intentionality()
                else:
                    st.error("Could not generate a logical structure with the provided data.")
                    navigation_buttons()

        # --- ACTIVE ACCOMPLISHMENT TYPE SELECTION ---
        elif st.session_state.ls_step == 'active_accomplishment_type':
            st.markdown("#### **Active Accomplishment**")
            
            with st.form(key="form_aa_type"):
                st.info("Select the semantic class that best fits the verb:")
                
                verb_type = st.radio(
                    "Verb type",
                    options=["Creation (write, build, paint...)", 
                             "Consumption (eat, drink, read...)", 
                             "Motion/Displacement (run to, walk to, drive to...)", 
                             "Other"],
                    index=None,
                    label_visibility="collapsed"
                )
                
                if st.form_submit_button("Continue", use_container_width=True):
                    if verb_type and "Creation" in verb_type:
                        goto('aa_creation')
                    elif verb_type and "Consumption" in verb_type:
                        goto('aa_consumption')
                    elif verb_type and "Motion" in verb_type:
                        goto('aa_motion')
                    elif verb_type and "Other" in verb_type:
                        goto('aa_other')
                    else:
                        st.warning("Please select an option.")
            navigation_buttons()

        # --- ACTIVE ACCOMPLISHMENT: CREATION ---
        elif st.session_state.ls_step == 'aa_creation':
            AKT = st.session_state.ls_akt
            is_causative = AKT == "causative active accomplishment"
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            z = st.session_state.ls_z
            pred = st.session_state.ls_pred
            
            if is_causative:
                with st.form(key="form_aa_creation_caus"):
                    st.info(f"Enter the activity performed by **{z}** (e.g., *write*, *build*):")
                    activity_pred = st.text_input("Activity", label_visibility="collapsed")
                    if st.form_submit_button("Generate structure"):
                        activity_pred = activity_pred.lower().replace(" ", ".")
                        ls = generate_causative_active_accomplishment_creation(x, z, y, activity_pred)
                        st.session_state.ls_structure = ls
                        goto_intentionality()
            else:
                ls = generate_active_accomplishment_creation(x, y, pred)
                st.session_state.ls_structure = ls
                goto_intentionality()
            navigation_buttons()

        # --- ACTIVE ACCOMPLISHMENT: CONSUMPTION ---
        elif st.session_state.ls_step == 'aa_consumption':
            AKT = st.session_state.ls_akt
            is_causative = AKT == "causative active accomplishment"
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            z = st.session_state.ls_z
            pred = st.session_state.ls_pred
            
            if is_causative:
                with st.form(key="form_aa_consumption_caus"):
                    st.info(f"Enter the activity performed by **{z}** (e.g., *eat*, *drink*):")
                    activity_pred = st.text_input("Activity", label_visibility="collapsed")
                    if st.form_submit_button("Generate structure"):
                        activity_pred = activity_pred.lower().replace(" ", ".")
                        ls = generate_causative_active_accomplishment_consumption(x, z, y, activity_pred)
                        st.session_state.ls_structure = ls
                        goto_intentionality()
            else:
                ls = generate_active_accomplishment_consumption(x, y, pred)
                st.session_state.ls_structure = ls
                goto_intentionality()
            navigation_buttons()

        # --- ACTIVE ACCOMPLISHMENT: MOTION ---
        elif st.session_state.ls_step == 'aa_motion':
            AKT = st.session_state.ls_akt
            is_causative = AKT == "causative active accomplishment"
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            locus = st.session_state.ls_locus
            pred = st.session_state.ls_pred
            
            # Check if we already have locative info
            if locus != "Ø":
                goto('aa_motion_direction')
            else:
                with st.form(key="form_aa_motion_loc"):
                    st.info("Enter the location (destination or source, without preposition):")
                    location = st.text_input("Location", label_visibility="collapsed")
                    if st.form_submit_button("Continue"):
                        st.session_state.ls_locus = location
                        goto('aa_motion_direction')
            navigation_buttons()

        elif st.session_state.ls_step == 'aa_motion_direction':
            locus = st.session_state.ls_locus
            st.info(f"Is **{locus}** the source or the destination?")
            c1, c2 = st.columns(2)
            c1.button("Source (from)", use_container_width=True, key="aa_source", 
                     on_click=create_goto_callback('aa_motion_generate', ls_is_destination=False))
            c2.button("Destination (to)", use_container_width=True, key="aa_dest", 
                     on_click=create_goto_callback('aa_motion_generate', ls_is_destination=True))
            navigation_buttons()

        elif st.session_state.ls_step == 'aa_motion_generate':
            AKT = st.session_state.ls_akt
            is_causative = AKT == "causative active accomplishment"
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            locus = st.session_state.ls_locus
            pred = st.session_state.ls_pred
            is_destination = st.session_state.ls_is_destination
            
            # Check if verb is a known motion verb
            motion_type = None
            for m_type, verbs in VERBS_MOTION.items():
                if pred in verbs:
                    motion_type = m_type
                    break
            
            # Use motion type if found, otherwise use the original predicate
            motion_pred = motion_type if motion_type else pred
            
            if is_causative:
                with st.form(key="form_aa_motion_caus"):
                    st.info(f"Enter the activity performed by **{y}** (e.g., *run*, *walk*):")
                    activity_pred = st.text_input("Activity", label_visibility="collapsed")
                    if st.form_submit_button("Generate structure"):
                        activity_pred = activity_pred.lower().replace(" ", ".")
                        ls = generate_causative_active_accomplishment_motion(x, y, activity_pred, locus, is_destination)
                        st.session_state.ls_structure = ls
                        goto_intentionality()
            else:
                ls = generate_active_accomplishment_motion(x, pred, locus, is_destination)
                st.session_state.ls_structure = ls
                goto_intentionality()
            navigation_buttons()

        # --- ACTIVE ACCOMPLISHMENT: OTHER ---
        elif st.session_state.ls_step == 'aa_other':
            AKT = st.session_state.ls_akt
            is_causative = AKT == "causative active accomplishment"
            x = st.session_state.ls_x
            y = st.session_state.ls_y
            z = st.session_state.ls_z
            pred = st.session_state.ls_pred
            
            with st.form(key="form_aa_other"):
                st.info("Enter the result state predicate (e.g., for 'wipe clean' enter *clean*):")
                result_pred = st.text_input("Result state", label_visibility="collapsed")
                if st.form_submit_button("Generate structure"):
                    result_pred = result_pred.lower().replace(" ", ".")
                    if is_causative:
                        affected = z if z != "Ø" else y
                        ls = f"[<b>do'</b> ({x}, Ø)] CAUSE [<b>do'</b> ({affected}, [<b>{pred}'</b> ({affected}, {y})]) ∧ PROC <b>{result_pred}'</b> ({y}) ∧ FIN <b>{result_pred}'</b> ({y})]"
                    else:
                        ls = generate_active_accomplishment_other(x, y, pred, result_pred)
                    st.session_state.ls_structure = ls
                    goto_intentionality()
            navigation_buttons()

        # --- INTENTIONALITY ---
        elif st.session_state.ls_step == 'intentionality':
            AKT = st.session_state.ls_akt
            x = st.session_state.ls_x
            ls = st.session_state.ls_structure
            
            static_types = ["state", "causative state"]
            
            if AKT in static_types or x == "Ø":
                goto('result')
            else:
                st.info(f"Does **{x}** act intentionally? (DO operator)")
                c1, c2 = st.columns(2)
                
                def _do_yes():
                    ls_with_do = apply_DO(st.session_state.ls_x, st.session_state.ls_structure)
                    st.session_state.ls_structure_with_do = ls_with_do
                    st.session_state.ls_structure = ls_with_do
                    st.session_state.ls_step = 'result'
                
                def _do_no():
                    st.session_state.ls_step = 'result'
                
                c1.button("Yes", use_container_width=True, key="do_yes", on_click=_do_yes)
                c2.button("No", use_container_width=True, key="do_no", on_click=_do_no)
            navigation_buttons()

        # --- RESULT ---
        elif st.session_state.ls_step == 'result':
            st.markdown("### Logical Structure")
            ls = st.session_state.ls_structure
            st.markdown(f'<div class="ls-result">{ls}</div>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            st.info("Would you like to add operators to the logical structure?")
            c1, c2 = st.columns(2)
            c1.button("Yes, add operators", use_container_width=True, 
                     on_click=create_goto_callback('select_operators'))
            c2.button("No, finish", use_container_width=True, 
                     on_click=create_goto_callback('final'))
            
            navigation_buttons()

        # --- SELECT OPERATORS ---
        elif st.session_state.ls_step == 'select_operators':
            st.markdown("#### **Operator selection**")
            st.info("Check the operators you want to add and enter their values:")
    
            with st.form(key="form_ops"):
                selected_ops = []
        
                # Clausal operators (indices 0-3)
                st.write("**Clausal operators:**")
                for i, op in enumerate(OPERATORS[:4]):
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        checked = st.checkbox(op.description, key=f"op_check_{i}")
                    with col2:
                        if op.requires_value:
                            value = st.text_input(
                                f"Value for {op.code}",
                                placeholder=f"e.g.: {op.examples}",
                                key=f"op_val_{i}",
                                label_visibility="collapsed"
                            )
                        else:
                            value = None
                    if checked:
                        selected_ops.append((i, op.code, value))
        
                # Core operators (indices 4-7)
                st.write("**Core operators:**")
                for i, op in enumerate(OPERATORS[4:8], start=4):
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        checked = st.checkbox(op.description, key=f"op_check_{i}")
                    with col2:
                        if op.requires_value:
                            value = st.text_input(
                                f"Value for {op.code}",
                                placeholder=f"e.g.: {op.examples}",
                                key=f"op_val_{i}",
                                label_visibility="collapsed"
                            )
                        else:
                            value = None
                    if checked:
                        selected_ops.append((i, op.code, value))
        
                # Nuclear operators (indices 8-10)
                st.write("**Nuclear operators:**")
                for i, op in enumerate(OPERATORS[8:], start=8):
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        checked = st.checkbox(op.description, key=f"op_check_{i}")
                    with col2:
                        if op.requires_value:
                            value = st.text_input(
                                f"Value for {op.code}",
                                placeholder=f"e.g.: {op.examples}",
                                key=f"op_val_{i}",
                                label_visibility="collapsed"
                            )
                        else:
                            value = None
                    if checked:
                        selected_ops.append((i, op.code, value))
        
                if st.form_submit_button("Continue", use_container_width=True):
                    if selected_ops:
                        ops_values = []
                        for idx, code, value in selected_ops:
                            if value:
                                value = value.upper()
                                if code == 'STA' and value == 'NEG':
                                    value = 'NEG +'
                            ops_values.append((code, value))
                
                        st.session_state.ls_ops_values = ops_values
                
                        ls_base = st.session_state.ls_structure
                        ls_with_ops = add_operators_to_ls(ls_base, ops_values)
                        st.session_state.ls_structure_final = ls_with_ops
                    else:
                        st.session_state.ls_structure_final = st.session_state.ls_structure
            
                    goto('final')
    
            navigation_buttons()

        # --- FINAL ---
        elif st.session_state.ls_step == 'final':
            st.markdown("### Final Result")
            
            ls_final = st.session_state.get('ls_structure_final', st.session_state.ls_structure)
            st.markdown(f'<div class="ls-result">{ls_final}</div>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True) 

            with st.expander("Copy or download logical structure (plain text, LaTeX, or image)"):
                ls_copyable = clean_html_ls(ls_final)
                ls_latex = convert_ls_to_latex(ls_final)
                
                st.write("**Plain text:**")
                st.code(ls_copyable, language=None)
                
                st.write("**LaTeX:**")
                st.code(ls_latex, language="latex")
                
                st.write("**Image:**")
                image_bytes = generate_ls_image(ls_final)
                st.download_button(
                    label="Download as PNG",
                    data=image_bytes,
                    file_name="logical_structure.png",
                    mime="image/png"
                )

            st.write("---")
            st.button("Analyze another clause", use_container_width=True, 
                     key="another_final", on_click=reset_analysis)

if __name__ == "__main__":
    st.set_page_config(
        page_title="LS Generator (English)",
        page_icon="🔤",
        layout="wide"
    )
    st.title("🔤 Logical Structure Generator (English)")
    show_ls_assistant()