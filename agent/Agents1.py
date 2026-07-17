import json
import re
import time
import subprocess
from lark import Lark

from code.Compilatore import compilatore

"""
Pipeline a 2 agenti per la generazione di programmi in Scartellato.

AGENTE 1 - GENERATOR
    Genera codice Scartellato da zero, usando few-shot (5 esempi validi
    rispetto alla grammatica). Se una generazione precedente e' fallita
    (compilazione o test), riceve un feedback puntuale su cosa non ha
    funzionato e riprova.

AGENTE 2 - REPAIR/TESTER (due ruoli, stesso agente)
    - ruolo REPAIR: il programma generato non compila -> lo ripara sulla
      base degli errori del compilatore, mantenendo la struttura originale.
    - ruolo TESTER: il programma compila -> genera i casi di test, li
      inserisce nel programma, e produce anche l'elenco degli output
      attesi (in modo da poterli confrontare con lo stdout reale).

FLUSSO per ogni programma richiesto:
    1. generate_code()                          [Agente 1]
    2. loop di compilazione:
         compilatore(programma)
           -> ok:    passa al punto 3
           -> ko:    repair_program()            [Agente 2 - repair]
                     ripete la compilazione (fino a max_repairs)
                     se esaurisce i tentativi -> feedback al Generator, torna al punto 1
    3. test_code()                               [Agente 2 - tester]
       genera programma_con_test + output_attesi
    4. esegui_programma(programma_con_test)      -> stdout reale
    5. confronto stdout reale vs output_attesi
         -> uguali:  programma valido, salvato
         -> diversi: feedback dettagliato al Generator, torna al punto 1
                      (fino a max_regenerations)
"""

# ============================================================
# GRAMMATICA (invariata rispetto all'originale)
# ============================================================

GRAMMAR_L = r"""
        BOOLEAN.2 : "sasicchj"|"friariell"
        LOTA_TK: "lota"                 // token per boolean
        NUMERO: /\d+(\.\d+)?e?/
        NUMR_TK: "numr"
        STRINGA: /\?\?[^?]*\?\?/
        NBRUOGGLIO_TK: "nbruogglio"
        ID: /[a-zA-Z_]\w*/
        CARATTERE:  /\?[^?]\?/
        LETTER_TK: "lettr"
        VOID: "vacant"
        GEN_TYPE: "burdell"    //variabile generica

        //operazioni
        DIVISIONEUGUALE: "*="
        MOLTIPLICAUGUALE: "/="
        ADDIZIONEUGUALE: "-="
        MENOUGUALE: "+="
        MENO: "+"
        ADDIZIONE: "-"
        MOLTIPLICA:"/"
        DIVISIONE: "*"
        ASSIGN: "="
        PLUSPLUS: "++"
        MENMEN: "--"
        RESTO: "%"

        //operazioni logiche
        OR: "or" | "||"
        AND: "and" | "&&"
        NOT: "not" | "!!"
        EQUALS: "=="
        DIVERSO: "!="
        MAGGIORE: ">"
        MAGGIOREUGUALE: ">="
        MINORE: "<"
        MINOREUGUALE: "<="

        //PARENTESSI
        TONDASINISTRA: ")"
        TONDADESTRA: "("
        GRAFFASINISTRA: "}"
        GRAFFADESTRA: "{"
        QUADRATASINISTRA: "]"
        QUADRATADESTRA: "["

        //Keyword
        METTIMCA: "mettimcà"                    //if
        ALLORFAACCUSSI: "allor_fa_accussi"     //else
        ROBA: "robba"                         //classe
        O_MAST: "o_mast"               //costruttore
        ASPE: "aspe"                        //while
        AMBRESS_AMBRESS: "ambressAmbress"  //for
        MESTIER: "mestier"           //funzione
        MAIN: "Uè"                  //main
        NULL: "Nuncsta_nient"      //null
        BREAK: "stut_tutt"      //break
        CCASTA: "ccàsta"         //return
        TERMINATORE: "!"        //fine istruzione
        CHIAMATA: "jamm_ja"    // keyword per chiamata a funzione
        SWAP: "<->"           //swap dei valori
        PARAMETRI_TK: "guagliuni" // elenco di parametri

        %ignore /\s+/
        %ignore /\/\/[^\n]*/
        %ignore /\/\*[\s\S]*\*\//



        start:  top_level* main_def top_level*
             |  top_level+

        main_def: main_opzione MAIN TONDASINISTRA TONDADESTRA GRAFFASINISTRA blocco GRAFFADESTRA -> main

        ?main_opzione: VOID |


        ?top_level: funzione
                  | classe
                  | dichiarazione

        //  BLOCCO E ISTRUZIONI

        blocco: istruzione*

        ?istruzione: dichiarazione
                   | for_stmt
                   | while_stmt
                   | if_stmt
                   | return_stmt
                   | nome_var ASSIGN assegnamento_composto TERMINATORE  -> assegnazione
                   | nome_var MENOUGUALE assegnamento_composto TERMINATORE  -> menouguale
                   | nome_var ADDIZIONEUGUALE assegnamento_composto TERMINATORE -> addizioneuguale
                   | nome_var SWAP nome_var TERMINATORE  -> swap
                   | CHIAMATA ":" nome_var ")" ("guagliuni" ":" expr_primary ("," expr_primary)*)? "(" TERMINATORE -> call_stmt

        // RETURN E BREAK

        return_stmt: BREAK TERMINATORE
                   | CCASTA  nome_var TERMINATORE ->returnstatement
                   | CCASTA TERMINATORE   ->returnstatement

        // DICHIARAZIONI DI VARIABILI

        dichiarazione: tipo nome_var ASSIGN assegnamento_composto TERMINATORE
                     | tipo nome_var TERMINATORE

        ?tipo: GEN_TYPE -> tipo
            | LOTA_TK -> tipo
            | NUMR_TK -> tipo
            | NBRUOGGLIO_TK -> tipo
            | LETTER_TK -> tipo

        ?nome_var: ID -> variabile_semplice
                | QUADRATASINISTRA QUADRATADESTRA ID  -> variabile_array
                | QUADRATASINISTRA NUMERO QUADRATADESTRA ID  -> variabile_array

        //CLASSI

        ?classe: ROBA nome_var GRAFFASINISTRA membro*  costruttore membro* GRAFFADESTRA -> robba

        ?membro: campi
               | metodi

        // COSTRUTTORE
        costruttore: O_MAST TONDASINISTRA sezione_parametri TONDADESTRA GRAFFASINISTRA blocco GRAFFADESTRA -> costruttore

        ?campi: dichiarazione
             | campi dichiarazione


        ?metodi: funzione
              | metodi funzione



        // FUNZIONI

        funzione: tipo MESTIER  nome_var TONDASINISTRA sezione_parametri TONDADESTRA GRAFFASINISTRA blocco GRAFFADESTRA -> funzione_semplice
                | tipo QUADRATASINISTRA QUADRATADESTRA MESTIER  nome_var TONDASINISTRA sezione_parametri TONDADESTRA GRAFFASINISTRA blocco GRAFFADESTRA -> funzione_array
                | VOID MESTIER  nome_var TONDASINISTRA sezione_parametri TONDADESTRA GRAFFASINISTRA blocco GRAFFADESTRA -> funzione_void


        ?sezione_parametri: "guagliuni" ":" parametro ("," parametro)*
                 |

        parametro: tipo nome_var

        // IF

        ?if_stmt: METTIMCA TONDASINISTRA assegnamento_composto TONDADESTRA GRAFFASINISTRA blocco GRAFFADESTRA -> mettimca_senzaelse
               | METTIMCA TONDASINISTRA assegnamento_composto TONDADESTRA GRAFFASINISTRA blocco GRAFFADESTRA ALLORFAACCUSSI GRAFFASINISTRA blocco GRAFFADESTRA -> mettimca_completo
               | METTIMCA TONDASINISTRA assegnamento_composto TONDADESTRA istruzione ALLORFAACCUSSI istruzione -> mettimca_completo


        // WHILE

        while_stmt: ASPE TONDASINISTRA assegnamento_composto TONDADESTRA GRAFFASINISTRA blocco GRAFFADESTRA -> aspe
                  | ASPE TONDASINISTRA assegnamento_composto TONDADESTRA istruzione -> aspe

        // FOR

        for_stmt: AMBRESS_AMBRESS TONDASINISTRA TERMINATORE assegnamento_composto TERMINATORE TONDADESTRA for_corpo -> ambress_ambress
                | AMBRESS_AMBRESS TONDASINISTRA dichiarazione_for assegnamento_composto TERMINATORE valutazione TONDADESTRA for_corpo -> ambress_ambress
                | AMBRESS_AMBRESS TONDASINISTRA nome_var TERMINATORE assegnamento_composto TERMINATORE valutazione TONDADESTRA for_corpo -> ambress_ambress


        dichiarazione_for: tipo nome_var ASSIGN assegnamento_composto TERMINATORE ->dichiarazione


        valutazione :  nome_var PLUSPLUS -> incremento_destro
                    |  PLUSPLUS  nome_var -> incremento_sinistra
                    |  MENMEN  nome_var -> decremento_sinistro
                    |  nome_var MENMEN -> decremento_destro
                    |

        ?for_corpo: "}" blocco "{"
                 | istruzione




        // ESPRESSIONI

        ?assegnamento_composto: nome_var DIVISIONEUGUALE  expr_or
                             | nome_var  MOLTIPLICAUGUALE expr_or
                             | nome_var  ADDIZIONEUGUALE  expr_or
                             | nome_var  MENOUGUALE       expr_or
                             | expr_or

        ?expr_or: expr_or OR expr_and -> or_exp
            | expr_and

        ?expr_and: expr_and AND expr_eq -> and_exp
                | expr_eq

        ?expr_eq: expr_eq EQUALS expr_rel  -> uguale
               | expr_eq DIVERSO expr_rel  -> diverso
               | expr_rel

        ?expr_rel: expr_rel MAGGIORE      expr_add  -> maggiore
                | expr_rel MAGGIOREUGUALE expr_add  -> maggioreuguale
                | expr_rel MINORE         expr_add  -> minore
                | expr_rel MINOREUGUALE   expr_add  -> minoreuguale
                | expr_add

        ?expr_add: expr_add ADDIZIONE expr_mul -> somma
                | expr_add MENO      expr_mul -> sottrazione
                | expr_mul

        ?expr_mul: expr_mul MOLTIPLICA expr_unary  -> moltiplicazione
                | expr_mul DIVISIONE  expr_unary  -> divisione
                | expr_mul RESTO      expr_unary  -> resto
                | expr_unary

        ?expr_unary: NOT expr_unary
                  | PLUSPLUS   expr_primary  -> incremento
                  | MENMEN     expr_primary -> decremento
                  | expr_primary PLUSPLUS -> incremento_destro
                  | expr_primary MENMEN   -> decremento_destro
                  | expr_primary

        ?expr_primary: TONDASINISTRA assegnamento_composto TONDADESTRA
                    | NUMERO  -> numero
                    | BOOLEAN -> boolean
                    | STRINGA -> stringa
                    | CARATTERE -> carattere
                    | ID       -> variabile_semplice
"""

PRODUCTIONS = [
    "start", "main_def", "main_opzione", "top_level",
    "blocco", "istruzione", "dichiarazione", "for_stmt", "while_stmt", "if_stmt",
    "return_stmt", "nome_var", "assegnamento_composto",
    "tipo", "classe", "membro", "metodi", "costruttore", "campi", "funzione", "sezione_parametri",
    "parametro", "dichiarazione_for", "valutazione", "for_corpo", "expr_or", "expr_and", "expr_eq",
    "expr_rel", "expr_add", "expr_mul", "expr_unary", "expr_primary", ]

# Parser costruito una volta sola fuori dal ciclo (ricompilarlo ad ogni
# chiamata sarebbe costoso e inutile).
_parser = Lark(GRAMMAR_L, start="start", parser="lalr")

# ============================================================
# FEW-SHOT: 5 esempi di programmi Scartellato validi
# ============================================================
# NOTA IMPORTANTE: questi esempi sono stati scritti a mano seguendo la
# grammatica LALR sopra (attenzione: TONDASINISTRA=")" e TONDADESTRA="("
# sono scambiati rispetto all'intuizione, cosi' come GRAFFASINISTRA="}" e
# GRAFFADESTRA="{"). Non ho potuto eseguire `lark` in questo ambiente
# (nessun accesso alla rete per installarlo), quindi al primo avvio la
# pipeline li valida automaticamente con `_parser.parse()` in
# `_valida_few_shot()`: se anche solo uno non parsa, fallisce subito con
# un errore chiaro invece di propagare esempi rotti al Generator.

FEW_SHOT_EXAMPLES = r"""
    ESEMPIO 1 - dichiarazione semplice in main:
    Uè)( }
    numr x = 5!
    {

    ESEMPIO 2 - if senza else:
    Uè)( }
    numr x = 5!
    mettimcà) x > 3 ( }
    numr y = 1!
    {
    {

    ESEMPIO 3 - while:
    Uè)( }
    numr x = 0!
    aspe) x < 10 ( }
    x += 1!
    {
    {

    ESEMPIO 4 - for con dichiarazione, condizione e incremento:
    Uè)( }
    ambressAmbress) numr i = 0! i < 5! i++( }
    numr y = i!
    {
    {

    ESEMPIO 5 - funzione void definita fuori dal main e chiamata dentro il main:
    vacant mestier saluta ) guagliuni : numr n ( }
    numr doppio = n!
    {

    Uè)( }
    jamm_ja : saluta ) guagliuni : 5 ( !
    {
"""

_FEW_SHOT_PROGRAMS = [
    """Uè)( }
    numr x = 5!
    {""",
    """Uè)( }
numr x = 5!
mettimcà) x > 3 ( }
numr y = 1!
{
{""",
    """Uè)( }
numr x = 0!
aspe) x < 10 ( }
x += 1!
{
{""",
    """Uè)( }
ambressAmbress) numr i = 0! i < 5! i++( }
numr y = i!
{
{""",
    """vacant mestier saluta ) guagliuni : numr n ( }
numr doppio = n!
{

Uè)( }
jamm_ja : saluta ) guagliuni : 5 ( !
{""",
]


def _valida_few_shot() -> None:
    """Verifica che tutti gli esempi few-shot siano sintatticamente validi
    rispetto alla grammatica. Va chiamata all'avvio della pipeline: se un
    esempio e' rotto e' molto meglio scoprirlo subito che scoprirlo dopo
    100 generazioni fallite per colpa di un few-shot sbagliato."""
    problemi = []
    for i, prog in enumerate(_FEW_SHOT_PROGRAMS, start=1):
        try:
            _parser.parse(prog)
        except Exception as e:
            problemi.append(f"Esempio {i}: {e}")
    if problemi:
        raise RuntimeError(
            "Uno o piu' esempi few-shot NON sono validi rispetto alla grammatica "
            "(erano stati scritti a mano senza poter eseguire Lark). Correggili "
            "in FEW_SHOT_EXAMPLES / _FEW_SHOT_PROGRAMS prima di lanciare la "
            "pipeline:\n" + "\n".join(problemi)
        )


# ============================================================
# CONFIG DI ESECUZIONE - punto da adattare al runtime reale
# ============================================================
# Compilatore.compilatore(programma) fa SOLO il check sintattico/semantico
# (result.ok / result.errors): non esegue il programma. Per fare da tester
# serve pero' eseguirlo davvero e leggerne lo stdout, quindi questa parte
# va collegata al motore di esecuzione che avete (interprete Python
# sull'AST, transpiler + subprocess, VM, ecc). Finche' non e' collegata
# solleva un errore esplicito, per non confrontare in silenzio due stringhe
# vuote e dichiarare "successo" a caso.

OUTPUT_FUNCTION_NAME = "arape_a_vocca"


def esegui_programma(programma: str, timeout: float = 5.0) -> str:
    """Esegue `programma` (gia' compilato con successo) e ne restituisce lo
    stdout come stringa. Esempi di come collegarla al motore reale:

        # 1) se avete un eseguibile/interprete a riga di comando:
        risultato = subprocess.run(
            ["scartellato-run", "-"],
            input=programma, capture_output=True, text=True, timeout=timeout,
        )
        if risultato.returncode != 0:
            raise RuntimeError(risultato.stderr)
        return risultato.stdout

        # 2) se Compilatore espone anche un esecutore Python:
        from Compilatore import esegui
        return esegui(programma)
    """
    raise NotImplementedError(
        "esegui_programma() non e' ancora collegata a un motore di esecuzione "
        "reale per Scartellato. Compilatore.compilatore() fa solo il check "
        "sintattico/semantico: qui serve la funzione che ESEGUE il programma "
        "e ne cattura lo stdout. Vedi il docstring per due esempi di adapter."
    )


# ============================================================
# PROMPT DI SISTEMA
# ============================================================

SYSTEM_GENERATOR = f"""Sei l'Agente Generator per il linguaggio Scartellato.
Scrivi un programma sintatticamente valido rispetto alla grammatica seguente.

GRAMMATICA:
{GRAMMAR_L}

ESEMPI (few-shot, tutti validi rispetto alla grammatica):
{FEW_SHOT_EXAMPLES}

REGOLE:
- Rispondi SOLO con il codice del programma, racchiuso in un unico blocco ```.
- Nessun testo prima o dopo il blocco di codice.
- Se ricevi un FEEDBACK su un tentativo precedente (errori di compilazione
  o test falliti), correggi esattamente quel problema mantenendo il resto
  della struttura il piu' possibile invariato."""

SYSTEM_AGENT2_REPAIR = f"""Sei l'Agente 2 di Scartellato, in modalita' REPAIR.
Ricevi un programma con errori e i messaggi del compilatore.
Riscrivi il programma correggendo SOLO gli errori segnalati.
Mantieni il piu' possibile la struttura originale.

GRAMMATICA:
{GRAMMAR_L}

Rispondi SOLO con il programma corretto, in un unico blocco ```."""

SYSTEM_AGENT2_TESTER = f"""Sei l'Agente 2 di Scartellato, in modalita' TESTER.
Ricevi un programma che COMPILA correttamente. Devi:
1. Ideare uno o piu' casi di test significativi per la logica del programma.
2. Inserire i casi di test DENTRO il programma stesso (senza modificarne la
   logica originale), usando la funzione di libreria "{OUTPUT_FUNCTION_NAME}"
   per stampare a video i valori calcolati, in modo che possano essere letti
   da stdout una volta eseguito.
3. Calcolare tu stesso, valore per valore, quali output produrra' il
   programma una volta eseguito (una riga di stdout per ogni stampa).

GRAMMATICA:
{GRAMMAR_L}

FORMATO DI RISPOSTA ESATTO, niente altro testo:
```
<programma con i test inseriti>
```
```json
["riga di output attesa 1", "riga di output attesa 2", ...]
```"""


# ============================================================
# UTILITY
# ============================================================

def extract_code(raw: str) -> str:
    """Estrae il contenuto del primo blocco fenced ```...``` (con o senza
    linguaggio dopo i backtick). Se non trova un blocco, ripiega sul testo
    grezzo ripulito."""
    match = re.search(r"```(?:\w+)?\n(.*?)```", raw, re.DOTALL)
    if match:
        return match.group(1).strip()
    return raw.strip()


def extract_code_and_expected_output(raw: str):
    """Estrae dal messaggio del tester sia il programma (primo blocco
    fenced) sia la lista di output attesi (secondo blocco fenced, JSON).
    Ritorna la tupla (programma: str, output_attesi: list[str])."""
    blocks = re.findall(r"```(?:\w+)?\n(.*?)```", raw, re.DOTALL)
    if len(blocks) < 2:
        raise ValueError(
            "La risposta del tester non contiene i due blocchi attesi "
            "(programma + JSON con gli output attesi):\n" + raw
        )
    programma = blocks[0].strip()
    try:
        output_attesi = json.loads(blocks[1].strip())
    except json.JSONDecodeError as e:
        raise ValueError(f"Output atteso non e' JSON valido: {e}\n{blocks[1]}")
    return programma, output_attesi


def confronta_output(reale: str, attesi: list[str]) -> bool:
    """Confronto riga per riga fra stdout reale e output attesi generati
    dal tester, ignorando spazi bianchi superflui a inizio/fine riga."""
    righe_reali = [r.strip() for r in reale.strip().splitlines()]
    righe_attese = [r.strip() for r in attesi]
    return righe_reali == righe_attese


# ============================================================
# AGENTE 1 - GENERATOR
# ============================================================

def generate_code(feedback: str | None = None) -> str:
    user = "Scrivi un programma in Scartellato di 8-15 righe."
    if feedback:
        user += f"\n\nFEEDBACK sul tentativo precedente (da correggere):\n{feedback}"
    raw = call_llm(system=SYSTEM_GENERATOR, user=user, temperature=0.7)
    return extract_code(raw)


# ============================================================
# AGENTE 2 - ruolo REPAIR
# ============================================================

def repair_program(program: str, errors: list[str]) -> str:
    user = f"PROGRAMMA:\n{program}\n\nERRORI:\n" + "\n".join(errors)
    raw = call_llm(system=SYSTEM_AGENT2_REPAIR, user=user, temperature=0.2)
    return extract_code(raw)


# ============================================================
# AGENTE 2 - ruolo TESTER
# ============================================================

def test_code(program: str) -> tuple[str, list[str]]:
    user = f"PROGRAMMA (gia' compilato con successo):\n{program}"
    raw = call_llm(system=SYSTEM_AGENT2_TESTER, user=user, temperature=0.2)
    return extract_code_and_expected_output(raw)


# ============================================================
# STATO / COVERAGE / METRICHE
# ============================================================

def new_state() -> dict:
    return {
        "coverage": {p: 0 for p in PRODUCTIONS},
        "valid_programs": [],
        "all_attempts": 0,
        "total_tokens": 0,
    }


def update_coverage(state: dict, program: str) -> None:
    """Coverage precisa al 100%: parsa il programma e conta ogni
    produzione realmente usata nell'albero (tree.data)."""
    try:
        tree = _parser.parse(program)
    except Exception:
        return
    for subtree in tree.iter_subtrees():
        prod = subtree.data
        if prod in state["coverage"]:
            state["coverage"][prod] += 1


def compute_metrics(state: dict, n_requested: int) -> dict:
    valid = state["valid_programs"]
    coverage = state["coverage"]
    return {
        "validity_rate": len(valid) / n_requested if n_requested else 0,
        "n_valid": len(valid),
        "coverage_pct": sum(1 for v in coverage.values() if v > 0) / len(coverage),
        "coverage_detail": dict(coverage),
        "diversity_unique": len(set(valid)) / len(valid) if valid else 0,
        "avg_attempts_per_valid": state["all_attempts"] / len(valid) if valid else float("inf"),
    }


# ============================================================
# PIPELINE PRINCIPALE
# ============================================================

def run_pipeline(n_programs: int, max_repairs: int = 5, max_regenerations: int = 3) -> dict:
    """
    Per ogni programma richiesto:
      - il Generator (Agente 1) genera un programma, eventualmente guidato
        da un feedback sull'esito del tentativo precedente;
      - l'Agente 2 fa da REPAIR finche' il programma non compila (fino a
        max_repairs tentativi);
      - una volta che compila, l'Agente 2 fa da TESTER: inserisce i test
        nel programma e produce l'output atteso;
      - il programma con i test viene eseguito davvero e il suo stdout
        confrontato con l'output atteso;
      - se coincidono il programma e' valido e viene salvato; altrimenti
        si torna al Generator con un feedback preciso su cosa non ha
        funzionato (fino a max_regenerations rigenerazioni).
    """
    _valida_few_shot()
    state = new_state()

    import os

    import os

    LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log.md")

    with open(LOG_PATH, "w", encoding="utf-8") as log:
        for i in range(n_programs):
            feedback = None
            successo = False

            for regen in range(max_regenerations + 1):
                # --- 1. AGENTE 1: GENERATOR ---
                program = generate_code(feedback=feedback)
                log.write(json.dumps({
                    "step": "generate_code", "regen": regen, "program": program, "time": time(),
                }) + "\n")

                # --- 2. COMPILAZIONE + AGENTE 2 (repair) ---
                compiled_ok = False
                result = None
                for attempt in range(max_repairs + 1):
                    result = compilatore(program)
                    log.write(json.dumps({
                        "step": "compile", "attempt": attempt, "ok": result.ok,
                        "errors": getattr(result, "errors", None), "time": time(),
                    }) + "\n")
                    if result.ok:
                        compiled_ok = True
                        break
                    program = repair_program(program, result.errors)
                    log.write(json.dumps({
                        "step": "repair", "attempt": attempt, "program": program, "time": time(),
                    }) + "\n")

                if not compiled_ok:
                    feedback = (
                        f"Il programma non compila dopo {max_repairs} tentativi di repair. "
                        f"Ultimi errori del compilatore: {result.errors if result else 'n/d'}"
                    )
                    continue  # richiedi una nuova generazione da zero

                # --- 3. AGENTE 2: TESTER ---
                try:
                    program_con_test, output_attesi = test_code(program)
                except ValueError as e:
                    feedback = f"Il tester non ha prodotto una risposta valida: {e}"
                    continue

                # il programma con i test deve compilare a sua volta
                result_test = compilatore(program_con_test)
                log.write(json.dumps({
                    "step": "compile_with_tests", "ok": result_test.ok,
                    "errors": getattr(result_test, "errors", None), "time": time(),
                }) + "\n")
                if not result_test.ok:
                    feedback = (
                        "Il programma con i test inseriti dal tester non compila piu': "
                        f"{result_test.errors}"
                    )
                    continue

                # --- 4. ESECUZIONE E CONFRONTO STDOUT ---
                try:
                    stdout_reale = esegui_programma(program_con_test)
                except NotImplementedError:
                    raise  # errore di configurazione: va risolto, non "recuperato"
                except Exception as e:
                    feedback = f"Errore durante l'esecuzione del programma: {e}"
                    log.write(json.dumps({"step": "run_error", "error": str(e), "time": time()}) + "\n")
                    continue

                log.write(json.dumps({
                    "step": "run", "stdout": stdout_reale, "expected": output_attesi, "time": time(),
                }) + "\n")

                if confronta_output(stdout_reale, output_attesi):
                    state["valid_programs"].append(program_con_test)
                    update_coverage(state, program)
                    log.write(json.dumps({"step": "test_passed", "time": time()}) + "\n")
                    successo = True
                    break
                else:
                    feedback = (
                        "I test sono falliti. Output atteso:\n"
                        f"{output_attesi}\nOutput ottenuto dall'esecuzione:\n{stdout_reale}"
                    )
                    log.write(json.dumps({"step": "test_failed", "feedback": feedback, "time": time()}) + "\n")

            state["all_attempts"] += 1
            print(
                f"[{i + 1}/{n_programs}] esito={'OK' if successo else 'FALLITO'} "
                f"validi={len(state['valid_programs'])} "
                f"coverage={sum(1 for v in state['coverage'].values() if v > 0)}/{len(PRODUCTIONS)}"
            )

    return state


import json
import os
from time import time
import anthropic

client = anthropic.Anthropic()

print("ANTHROPIC_API_KEY presente?", "ANTHROPIC_API_KEY" in os.environ)
print("Tutte le chiavi che contengono ANTHROPIC:", [k for k in os.environ if "ANTHROPIC" in k.upper()])


def call_llm(system: str, user: str, temperature: float = 0.7) -> str:
    """Una chiamata LLM , ritorna solo la stringa del testo ."""
    import os

    LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log.md")
    log = open(LOG_PATH, "a", encoding="utf-8")
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        cache_control={"type": "ephemeral"},
        system=system,
        messages=[{"role": "user", "content": user}],
        temperature=temperature,
    )
    log.write(json.dumps({"Step": "create d'agent", "Response": response.content[0].text, "Time": time()}))
    log.close()
    return response.content[0].text


if __name__ == "__main__":
    final_state = run_pipeline(n_programs=100)
    metrics = compute_metrics(final_state, n_requested=100)
    print(json.dumps(metrics, indent=2))