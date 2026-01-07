import streamlit as st
import spacy
from dataclasses import dataclass
from enum import Enum
from typing import Optional

# --- 1. CLASSES AND ENUMS ---

class Aktionsart(Enum):
    STATE = "state"
    CAUSATIVE_STATE = "causative state"
    ACHIEVEMENT = "achievement"
    CAUSATIVE_ACHIEVEMENT = "causative achievement"
    SEMELFACTIVE = "semelfactive"
    CAUSATIVE_SEMELFACTIVE = "causative semelfactive"
    ACTIVE_ACCOMPLISHMENT = "active accomplishment"
    CAUSATIVE_ACTIVE_ACCOMPLISHMENT = "causative active accomplishment"
    ACCOMPLISHMENT = "accomplishment"
    CAUSATIVE_ACCOMPLISHMENT = "causative accomplishment"
    ACTIVITY = "activity"
    CAUSATIVE_ACTIVITY = "causative activity"
    PROCESS = "process"
    CAUSATIVE_PROCESS = "causative process"

@dataclass
class Features:
    causative: Optional[bool] = None
    stative: Optional[bool] = None
    punctual: Optional[bool] = None
    telic: Optional[bool] = None
    dynamic: Optional[bool] = None

@dataclass
class ClauseData:
    gerund: str = ""
    participle: str = ""
    infinitive: str = ""
    subject: str = ""
    postverbal: str = ""
    person_number: str = "3s"

# --- 2. DICTIONARIES AND AUXILIARIES ---

BE_PRESENT = {
    '1s': "am", '2s': "are", '3s': "is",
    '1p': "are", '2p': "are", '3p': "are"
}

BE_PAST = {
    '1s': "was", '2s': "were", '3s': "was",
    '1p': "were", '2p': "were", '3p': "were"
}

HAVE_PRESENT = {
    '1s': "have", '2s': "have", '3s': "has",
    '1p': "have", '2p': "have", '3p': "have"
}

IRREGULARS = {
    "be": {"ger": "being", "pp": "been"},
    "have": {"ger": "having", "pp": "had"},
    "do": {"ger": "doing", "pp": "done"},
    "go": {"ger": "going", "pp": "gone"},
    "say": {"ger": "saying", "pp": "said"},
    "make": {"ger": "making", "pp": "made"},
    "get": {"ger": "getting", "pp": "gotten"},
    "know": {"ger": "knowing", "pp": "known"},
    "think": {"ger": "thinking", "pp": "thought"},
    "take": {"ger": "taking", "pp": "taken"},
    "see": {"ger": "seeing", "pp": "seen"},
    "come": {"ger": "coming", "pp": "come"},
    "want": {"ger": "wanting", "pp": "wanted"},
    "look": {"ger": "looking", "pp": "looked"},
    "use": {"ger": "using", "pp": "used"},
    "find": {"ger": "finding", "pp": "found"},
    "give": {"ger": "giving", "pp": "given"},
    "tell": {"ger": "telling", "pp": "told"},
    "work": {"ger": "working", "pp": "worked"},
    "call": {"ger": "calling", "pp": "called"},
    "try": {"ger": "trying", "pp": "tried"},
    "ask": {"ger": "asking", "pp": "asked"},
    "need": {"ger": "needing", "pp": "needed"},
    "feel": {"ger": "feeling", "pp": "felt"},
    "become": {"ger": "becoming", "pp": "become"},
    "leave": {"ger": "leaving", "pp": "left"},
    "put": {"ger": "putting", "pp": "put"},
    "mean": {"ger": "meaning", "pp": "meant"},
    "keep": {"ger": "keeping", "pp": "kept"},
    "let": {"ger": "letting", "pp": "let"},
    "begin": {"ger": "beginning", "pp": "begun"},
    "seem": {"ger": "seeming", "pp": "seemed"},
    "help": {"ger": "helping", "pp": "helped"},
    "talk": {"ger": "talking", "pp": "talked"},
    "turn": {"ger": "turning", "pp": "turned"},
    "start": {"ger": "starting", "pp": "started"},
    "show": {"ger": "showing", "pp": "shown"},
    "hear": {"ger": "hearing", "pp": "heard"},
    "play": {"ger": "playing", "pp": "played"},
    "run": {"ger": "running", "pp": "run"},
    "move": {"ger": "moving", "pp": "moved"},
    "live": {"ger": "living", "pp": "lived"},
    "believe": {"ger": "believing", "pp": "believed"},
    "bring": {"ger": "bringing", "pp": "brought"},
    "happen": {"ger": "happening", "pp": "happened"},
    "write": {"ger": "writing", "pp": "written"},
    "sit": {"ger": "sitting", "pp": "sat"},
    "stand": {"ger": "standing", "pp": "stood"},
    "lose": {"ger": "losing", "pp": "lost"},
    "pay": {"ger": "paying", "pp": "paid"},
    "meet": {"ger": "meeting", "pp": "met"},
    "include": {"ger": "including", "pp": "included"},
    "continue": {"ger": "continuing", "pp": "continued"},
    "set": {"ger": "setting", "pp": "set"},
    "learn": {"ger": "learning", "pp": "learned"},
    "change": {"ger": "changing", "pp": "changed"},
    "lead": {"ger": "leading", "pp": "led"},
    "understand": {"ger": "understanding", "pp": "understood"},
    "watch": {"ger": "watching", "pp": "watched"},
    "follow": {"ger": "following", "pp": "followed"},
    "stop": {"ger": "stopping", "pp": "stopped"},
    "create": {"ger": "creating", "pp": "created"},
    "speak": {"ger": "speaking", "pp": "spoken"},
    "read": {"ger": "reading", "pp": "read"},
    "allow": {"ger": "allowing", "pp": "allowed"},
    "add": {"ger": "adding", "pp": "added"},
    "spend": {"ger": "spending", "pp": "spent"},
    "grow": {"ger": "growing", "pp": "grown"},
    "open": {"ger": "opening", "pp": "opened"},
    "walk": {"ger": "walking", "pp": "walked"},
    "win": {"ger": "winning", "pp": "won"},
    "offer": {"ger": "offering", "pp": "offered"},
    "remember": {"ger": "remembering", "pp": "remembered"},
    "love": {"ger": "loving", "pp": "loved"},
    "consider": {"ger": "considering", "pp": "considered"},
    "appear": {"ger": "appearing", "pp": "appeared"},
    "buy": {"ger": "buying", "pp": "bought"},
    "wait": {"ger": "waiting", "pp": "waited"},
    "serve": {"ger": "serving", "pp": "served"},
    "die": {"ger": "dying", "pp": "died"},
    "send": {"ger": "sending", "pp": "sent"},
    "expect": {"ger": "expecting", "pp": "expected"},
    "build": {"ger": "building", "pp": "built"},
    "stay": {"ger": "staying", "pp": "stayed"},
    "fall": {"ger": "falling", "pp": "fallen"},
    "cut": {"ger": "cutting", "pp": "cut"},
    "reach": {"ger": "reaching", "pp": "reached"},
    "kill": {"ger": "killing", "pp": "killed"},
    "remain": {"ger": "remaining", "pp": "remained"},
    "suggest": {"ger": "suggesting", "pp": "suggested"},
    "raise": {"ger": "raising", "pp": "raised"},
    "pass": {"ger": "passing", "pp": "passed"},
    "sell": {"ger": "selling", "pp": "sold"},
    "require": {"ger": "requiring", "pp": "required"},
    "report": {"ger": "reporting", "pp": "reported"},
    "decide": {"ger": "deciding", "pp": "decided"},
    "pull": {"ger": "pulling", "pp": "pulled"},
    "break": {"ger": "breaking", "pp": "broken"},
    "teach": {"ger": "teaching", "pp": "taught"},
    "eat": {"ger": "eating", "pp": "eaten"},
    "drive": {"ger": "driving", "pp": "driven"},
    "drink": {"ger": "drinking", "pp": "drunk"},
    "sing": {"ger": "singing", "pp": "sung"},
    "swim": {"ger": "swimming", "pp": "swum"},
    "fly": {"ger": "flying", "pp": "flown"},
    "draw": {"ger": "drawing", "pp": "drawn"},
    "forget": {"ger": "forgetting", "pp": "forgotten"},
    "hit": {"ger": "hitting", "pp": "hit"},
    "catch": {"ger": "catching", "pp": "caught"},
    "sleep": {"ger": "sleeping", "pp": "slept"},
    "throw": {"ger": "throwing", "pp": "thrown"},
    "wake": {"ger": "waking", "pp": "woken"},
    "wear": {"ger": "wearing", "pp": "worn"},
    "choose": {"ger": "choosing", "pp": "chosen"},
    "hide": {"ger": "hiding", "pp": "hidden"},
}

PERSONS_DICT = {
    "1s": "1st person singular (I)",
    "2s": "2nd person singular (You)",
    "3s": "3rd person singular (He/She/It)",
    "1p": "1st person plural (We)",
    "2p": "2nd person plural (You)",
    "3p": "3rd person plural (They)"
}

@st.cache_resource
def load_nlp():
    try: return spacy.load("en_core_web_sm")
    except: return None

nlp = load_nlp()

def generate_english_forms(lemma: str):
    """Generates Gerund and Past Participle using dictionary + heuristic rules."""
    lemma = lemma.lower().strip()
    
    if lemma in IRREGULARS:
        return IRREGULARS[lemma]["ger"], IRREGULARS[lemma]["pp"]
    
    # Gerund
    if lemma.endswith("ie"):
        ger = lemma[:-2] + "ying"
    elif lemma.endswith("e") and not lemma.endswith("ee"):
        ger = lemma[:-1] + "ing"
    else:
        is_cvc = (len(lemma) > 2 
                  and lemma[-1] not in "aeiouwyx" 
                  and lemma[-2] in "aeiou" 
                  and lemma[-3] not in "aeiou")
        is_unstressed_ending = lemma.endswith(("er", "en", "el", "it"))
        if is_cvc and not is_unstressed_ending:
            ger = lemma + lemma[-1] + "ing"
        else:
            ger = lemma + "ing"
    
    # Past Participle (Regular)
    if lemma.endswith("e"):
        pp = lemma + "d"
    else:
        is_cvc = (len(lemma) > 2 
                  and lemma[-1] not in "aeiouwyx" 
                  and lemma[-2] in "aeiou" 
                  and lemma[-3] not in "aeiou")
        is_unstressed_ending = lemma.endswith(("er", "en", "el", "it"))
        if is_cvc and not is_unstressed_ending:
            pp = lemma + lemma[-1] + "ed"
        else:
            pp = lemma + "ed"
    
    return ger, pp

def detect_person_number(doc, verb_token, idx):
    """Deduces Person/Number based on the Subject found by spaCy."""
    subj_token = None
    for token in doc:
        if token.head == verb_token and "subj" in token.dep_:
            subj_token = token
            break
    
    if not subj_token:
        return "3s"
    
    text = subj_token.text.lower()
    
    if text == "i": return "1s"
    if text == "you": return "2s"
    if text == "we": return "1p"
    if text == "they": return "3p"
    if text in ["he", "she", "it"]: return "3s"
    
    morph = subj_token.morph.to_dict()
    number = morph.get("Number", "Sing")
    
    if number == "Plur":
        return "3p"
    else:
        return "3s"

def analyze_automatically(clause, data):
    """Uses spaCy to analyze the clause structure and morphology."""
    if not nlp: return False, "", ""
    
    doc = nlp(clause)
    verb_token = None
    
    for token in doc:
        if token.dep_ == "ROOT" and token.pos_ in ["VERB", "AUX"]:
            verb_token = token
            break
    
    if not verb_token:
        for token in doc:
            if token.pos_ in ["VERB", "AUX"]:
                verb_token = token
                break
    
    if not verb_token and len(doc) <= 2:
        for token in doc:
            if token.pos_ not in ["DET", "PRON"]:
                verb_token = token
                break
    
    if not verb_token: return False, "", ""
    
    lemma = verb_token.lemma_.lower()
    ger, pp = generate_english_forms(lemma)
    
    if not ger or not pp: return False, "", ""
    
    data.infinitive = lemma
    data.gerund = ger
    data.participle = pp
    data.person_number = detect_person_number(doc, verb_token, verb_token.i)
    
    idx = verb_token.i
    data.subject = doc[:idx].text.strip()
    data.postverbal = doc[idx+1:].text.strip()
    
    return True, verb_token.text, lemma

def build_prog(past: bool, data: ClauseData) -> str:
    be = BE_PAST[data.person_number] if past else BE_PRESENT[data.person_number]
    parts = [data.subject, f"{be} {data.gerund}", data.postverbal]
    return " ".join(p for p in parts if p)

def build_perfect(data: ClauseData) -> str:
    have = HAVE_PRESENT[data.person_number]
    parts = [data.subject, f"{have} {data.participle}", data.postverbal]
    return " ".join(p for p in parts if p)

def build_stop(data: ClauseData) -> str:
    parts = [data.subject or "(subject)", f"stopped {data.gerund}", data.postverbal]
    return " ".join(p for p in parts if p)

# --- NAVIGATION ---
def go_to(step):
    st.session_state.history.append(st.session_state.akt_step)
    st.session_state.akt_step = step
    st.rerun()

def go_back():
    if st.session_state.history:
        current_step = st.session_state.akt_step
        if current_step == 'cleanup':
            st.session_state.features.causative = None
            st.session_state.non_causative_variant = ""
        elif current_step == 'stativity':
            st.session_state.data = ClauseData()
        elif current_step == 'punctuality':
            st.session_state.features.stative = None
        elif current_step == 'telicity':
            st.session_state.features.punctual = None
        elif current_step == 'dynamicity':
            st.session_state.features.telic = None
        elif current_step == 'result':
            st.session_state.features.dynamic = None
        
        st.session_state.akt_step = st.session_state.history.pop()
        st.rerun()

def restart_analysis():
    for key in ['akt_step', 'history', 'features', 'data', 'original_clause', 'current_clause', 'clean_clause', 'non_causative_variant', 'paraphrase']:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

def navigation_buttons():
    st.write("---")
    c1, c2 = st.columns([1, 1])
    if c1.button("← Back", use_container_width=True):
        go_back()
    if c2.button("Start new analysis", use_container_width=True):
        restart_analysis()

def elegant_list(items: list):
    html_items = ""
    for item in items:
        html_items += f'<div style="display: flex; align-items: flex-start; margin-bottom: 8px;"><div style="color: #4A90E2; margin-right: 10px; font-weight: bold;">•</div><div style="line-height: 1.4;">{item}</div></div>'
    st.markdown(f'<div style="margin-bottom: 15px;">{html_items}</div>', unsafe_allow_html=True)

# --- 3. INTERFACE ---

def mostrar_detector_en():
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

    if 'akt_step' not in st.session_state:
        st.session_state.akt_step = 'start'
        st.session_state.history = []
        st.session_state.features = Features()
        st.session_state.data = ClauseData()
        st.session_state.original_clause = ""
        st.session_state.current_clause = ""
        st.session_state.clean_clause = ""
        st.session_state.non_causative_variant = ""

    label_result = ""
    if st.session_state.akt_step == 'result':
        f = st.session_state.features
        if f.stative: sub = "state"
        elif f.punctual and f.telic: sub = "achievement"
        elif f.punctual and not f.telic: sub = "semelfactive"
        elif not f.punctual and f.telic and f.dynamic: sub = "active accomplishment"
        elif not f.punctual and not f.telic and f.dynamic: sub = "activity"
        elif not f.punctual and f.telic and not f.dynamic: sub = "accomplishment"
        else: sub = "process"
        label_result = f"causative {sub}" if f.causative else sub

    col_left, col_spacer, col_right = st.columns([0.6, 0.02, 0.38])

    with col_left:
        if st.session_state.akt_step == 'start':
            st.write("This program will help you identify the aktionsart of the main predicate in a clause.")
            st.write("Please type a clause with the verb you want to test conjugated in the **simple past** (e.g., *Peter ran home*).")
            st.write("If it sounds very odd, type it in **present** (e.g., *Mary knows English*).")
            with st.form(key="form_start_en"):
                clause = st.text_input("Clause:")
                if st.form_submit_button("Start the analysis"):
                    if clause:
                        st.session_state.original_clause = clause
                        st.session_state.current_clause = clause
                        go_to('causativity')

        elif st.session_state.akt_step == 'causativity':
            st.markdown("#### **Causativity test**")
            st.write(f"Try to paraphrase *{st.session_state.current_clause}* following these models:")
            elegant_list([
                "The cat broke the vase → The cat <b>caused</b> the vase to break",
                "Ana gave Pepe a book → Ana <b>caused</b> Pepe to have a book"
            ])
            with st.form(key="form_caus_en"):
                paraphrase = st.text_input("Type your paraphrase:")
                c1, c2 = st.columns(2)
                if c1.form_submit_button("Next"):
                    if not paraphrase.strip():
                        st.session_state.features.causative = False
                        go_to('cleanup')
                    else:
                        st.session_state.paraphrase = paraphrase
                        go_to('verify_cause')
                if c2.form_submit_button("Not possible to paraphrase"):
                    st.session_state.features.causative = False
                    go_to('cleanup')
            navigation_buttons()

        elif st.session_state.akt_step == 'verify_cause':
            st.write("Consider the following:")
            elegant_list([
                f"<i>{st.session_state.paraphrase[0].upper() + st.session_state.paraphrase[1:]}</i> should preserve the meaning of <i>{st.session_state.current_clause}</i>.",
                f"<i>{st.session_state.paraphrase[0].upper() + st.session_state.paraphrase[1:]}</i> must not add new arguments nor duplicate existing ones in <i>{st.session_state.current_clause}</i>.",
                "Exclude consumption (<i>eat an apple</i>) and creation (<i>write a story</i>) readings."
            ])
            st.write(f"Does *{st.session_state.paraphrase[0].upper() + st.session_state.paraphrase[1:]}* meet these criteria?")
            c1, c2 = st.columns(2)
            if c1.button("Yes", use_container_width=True):
                go_to('basic_event')
            if c2.button("No", use_container_width=True):
                st.session_state.features.causative = False
                go_to('cleanup')
            navigation_buttons()

        elif st.session_state.akt_step == 'basic_event':
            st.write("Type the resulting event or state without the cause:")
            elegant_list([
                "<i>The cat broke the vase</i> → <i>the vase broke</i>",
                "<i>Ana gave Pepe a book</i> → <i>Pepe has a book</i>"
            ])
            with st.form(key="form_ev_bas_en"):
                ev = st.text_input("Type your answer here:")
                c1, c2 = st.columns(2)
                if c1.form_submit_button("Next", use_container_width=True):
                    if ev.strip():
                        st.session_state.features.causative = True
                        st.session_state.non_causative_variant = ev
                        st.session_state.current_clause = ev
                        go_to('cleanup')
                    else:
                        st.warning("Please enter the event or press 'I can't think of one'")
                if c2.form_submit_button("I can't think of one", use_container_width=True):
                    st.session_state.features.causative = False
                    go_to('cleanup')
            navigation_buttons()

        elif st.session_state.akt_step == 'cleanup':
            st.write(f"This is the clause we will test: *{st.session_state.current_clause}*")
            st.write("For the tests to work correctly, the clause must be 'clean'. Ensure it does **not** contain:")
            elegant_list([
                "Time expressions (e.g., <i>yesterday</i>, <i>always</i>, <i>never</i>, <i>on Monday</i>).",
                "Manner expressions (e.g., <i>quickly</i>, <i>well</i>, <i>with calm</i>).",
                "Negation (e.g., <i>not</i>, <i>never</i>)."
            ])
            st.write("Does your clause contain any of these elements?")
            c1, c2 = st.columns(2)
            if c1.button("Yes", use_container_width=True):
                go_to('fix_cleanup')
            if c2.button("No", use_container_width=True):
                st.session_state.clean_clause = st.session_state.current_clause
                go_to('morph_analysis')
            navigation_buttons()

        elif st.session_state.akt_step == 'fix_cleanup':
            with st.form(key="form_cleanup_en"):
                new_clause = st.text_input(f"Please type *{st.session_state.current_clause}* again **without** those elements (e.g., *Peter ran* instead of *Peter never ran yesterday*):")
                if st.form_submit_button("Update"):
                    if new_clause:
                        st.session_state.current_clause = new_clause
                        st.session_state.clean_clause = new_clause
                        go_to('morph_analysis')
            navigation_buttons()

        elif st.session_state.akt_step == 'morph_analysis':
            success, v_vis, l_vis = analyze_automatically(st.session_state.current_clause, st.session_state.data)
            if success:
                st.write("This is an analysis of some of the morphological and structural features of this clause:")
                d = st.session_state.data
                html_table = f"""
                <table class="tabla-analisis">
                    <tbody>
                        <tr><td><b>Verb</b></td><td>{v_vis.lower()}</td></tr>
                        <tr><td><b>Infinitive</b></td><td>{l_vis}</td></tr>
                        <tr><td><b>Gerund</b></td><td>{d.gerund}</td></tr>
                        <tr><td><b>Past Participle</b></td><td>{d.participle}</td></tr>
                        <tr><td><b>Before the verb</b></td><td>{d.subject if d.subject else "nothing"}</td></tr>
                        <tr><td><b>After the verb</b></td><td>{d.postverbal if d.postverbal else "nothing"}</td></tr>
                    </tbody>
                </table>
                """
                st.markdown(html_table, unsafe_allow_html=True)
                st.write("Is this analysis correct?")
                c1, c2 = st.columns(2)
                if c1.button("Yes", use_container_width=True): go_to('stativity')
                if c2.button("No", use_container_width=True): go_to('manual_morph')
                navigation_buttons()
            else:
                go_to('manual_morph')

        elif st.session_state.akt_step == 'manual_morph':
            with st.form(key="form_m_save_en"):
                d = st.session_state.data
                d.infinitive = st.text_input(f"Type the **infinitive** of the verb in *{st.session_state.current_clause}*:", d.infinitive)
                d.gerund = st.text_input(f"Type the **gerund** of the verb in *{st.session_state.current_clause}* (e.g., 'melting', 'telling'):", d.gerund)
                d.participle = st.text_input(f"Type the **past participle** of the verb in *{st.session_state.current_clause}* (e.g., 'melted', 'told'):", d.participle)
                d.subject = st.text_input(f"Type everything that comes **before** the verb in *{st.session_state.current_clause}*:", d.subject)
                d.postverbal = st.text_input(f"Type everything that comes **after** the verb in *{st.session_state.current_clause}*:", d.postverbal)
                idx_current = list(PERSONS_DICT.keys()).index(d.person_number) if d.person_number in PERSONS_DICT else 2
                d.person_number = st.selectbox(
                    "Select the person and number of the verb:",
                    options=list(PERSONS_DICT.keys()),
                    format_func=lambda x: PERSONS_DICT[x],
                    index=idx_current
                )
                if st.form_submit_button("Save"):
                    go_to('stativity')
            navigation_buttons()

        elif st.session_state.akt_step == 'stativity':
            st.markdown("#### **Stativity test**")
            st.write("Consider the following dialogue:")
            
            cd1, cd2, cd3 = st.columns(3)
            with cd1:
                st.markdown(f"— What happened a moment ago?<br>— <i>{st.session_state.current_clause[0].upper() + st.session_state.current_clause[1:]}</i>.", unsafe_allow_html=True)
            with cd2:
                st.markdown(f"— What happened yesterday?<br>— <i>{st.session_state.current_clause[0].upper() + st.session_state.current_clause[1:]}</i>.", unsafe_allow_html=True)
            with cd3:
                st.markdown(f"— What happened last month?<br>— <i>{st.session_state.current_clause[0].upper() + st.session_state.current_clause[1:]}</i>.", unsafe_allow_html=True)
            
            st.write(f"Do you think *{st.session_state.current_clause}* is a good answer to at least one of these questions?")
            c1, c2 = st.columns(2)
            if c1.button("Yes", use_container_width=True):
                st.session_state.features.stative = False
                go_to('punctuality')
            if c2.button("No", use_container_width=True):
                st.session_state.features.stative = True
                go_to('result')
            navigation_buttons()

        elif st.session_state.akt_step == 'punctuality':
            st.markdown("#### **Punctuality test**")
            prog_past = build_prog(True, st.session_state.data)
            st.write("Consider these expressions:")
            elegant_list([
                f"<i>{prog_past[0].upper() + prog_past[1:]} for an hour.</i>",
                f"<i>{prog_past[0].upper() + prog_past[1:]} for a month.</i>"
            ])
            st.write("Is any of these a valid expression (**without** forcing an iterative or imminent reading)?")
            c1, c2 = st.columns(2)
            if c1.button("Yes", use_container_width=True):
                st.session_state.features.punctual = False
                go_to('telicity')
            if c2.button("No", use_container_width=True):
                st.session_state.features.punctual = True
                go_to('telicity')
            navigation_buttons()

        elif st.session_state.akt_step == 'telicity':
            st.markdown("#### **Telicity test**")
            prog = build_prog(False, st.session_state.data)
            stop_expr = build_stop(st.session_state.data)
            perfect = build_perfect(st.session_state.data)
            st.write(f"Imagine that {prog} and suddenly {stop_expr}.")
            st.write(f"Would it then be true to say: *{perfect}*?")
            c1, c2 = st.columns(2)
            if c1.button("Yes", use_container_width=True):
                st.session_state.features.telic = False
                go_to('dynamicity')
            if c2.button("No", use_container_width=True):
                st.session_state.features.telic = True
                go_to('dynamicity')
            navigation_buttons()

        elif st.session_state.akt_step == 'dynamicity':
            st.markdown("#### **Dynamicity test**")
            prog = build_prog(False, st.session_state.data)
            st.write("Consider these expressions:")
            elegant_list([
                f"<i>{prog[0].upper() + prog[1:]} vigorously</i>.",
                f"<i>{prog[0].upper() + prog[1:]} forcefully</i>.",
                f"<i>{prog[0].upper() + prog[1:]} with effort</i>."
            ])
            st.write("Would any of these expressions sound natural to you?")
            c1, c2 = st.columns(2)
            if c1.button("Yes", use_container_width=True):
                st.session_state.features.dynamic = True
                go_to('result')
            if c2.button("No", use_container_width=True):
                st.session_state.features.dynamic = False
                go_to('result')
            navigation_buttons()

        elif st.session_state.akt_step == 'result':
            st.markdown("### Analysis complete")
            st.write(f"The aktionsart of the clause **{st.session_state.original_clause}** is **{label_result.upper()}**")
            
            c1, c2 = st.columns([1, 1])
            if c1.button("Analyze another predicate", use_container_width=True):
                restart_analysis()
            if c2.button("← Back to last test", use_container_width=True):
                go_back()

    with col_right:
        with st.container(border=True):
            st.markdown('<div class="header-analisis">Analysis status</div>', unsafe_allow_html=True)
            if st.session_state.original_clause:
                st.write("**Clause under analysis:**")
                st.info(st.session_state.original_clause)
            if st.session_state.non_causative_variant:
                st.write("**Non-causative variant:**")
                st.info(st.session_state.non_causative_variant)
            if st.session_state.clean_clause:
                st.write("**Clean clause:**")
                st.info(st.session_state.clean_clause)
            st.write("**Detected features:**")
            f = st.session_state.features
            row_caus = ""
            if f.causative is not None:
                row_caus = f'<div style="margin-bottom: 25px;"><span class="rasgo-elegante">[{"+" if f.causative else "-"}causative]</span></div>'
            row_others = '<div style="margin-bottom: 15px;">'
            if f.stative is not None: row_others += f'<span class="rasgo-elegante">[{"+" if f.stative else "-"}stative]</span>'
            if f.punctual is not None: row_others += f'<span class="rasgo-elegante">[{"+" if f.punctual else "-"}punctual]</span>'
            if f.telic is not None: row_others += f'<span class="rasgo-elegante">[{"+" if f.telic else "-"}telic]</span>'
            if f.dynamic is not None: row_others += f'<span class="rasgo-elegante">[{"+" if f.dynamic else "-"}dynamic]</span>'
            row_others += "</div>"
            st.markdown(row_caus + row_others, unsafe_allow_html=True)
            
            if st.session_state.akt_step == 'result':
                st.markdown('<br><div class="header-analisis">Result</div>', unsafe_allow_html=True)
                st.success(f"**{label_result.upper()}**")

if __name__ == "__main__":
    mostrar_detector_en()