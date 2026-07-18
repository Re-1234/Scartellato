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

GRAMMAR_L = r"""//tipo di dati
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
        PRINT: "arape_a_vocca"


        %ignore /\s+/
        %ignore /\/\/[^\n]*/
        %ignore /\/\*[\s\S]*\*\//



        start:  top_level* main_def top_level*
             |  top_level+

        main_def: [VOID] MAIN TONDASINISTRA TONDADESTRA GRAFFASINISTRA blocco GRAFFADESTRA -> main

        ?top_level: funzione
                  | classe
                  | dichiarazione

        //  BLOCCO E ISTRUZIONI

        blocco: istruzione*

        ?istruzione: dichiarazione
                   | for_stmt
                   | while_stmt
                   | if_stmt
                   | break_stmt
                   | return_stmt
                   | nome_var ASSIGN assegnamento_composto TERMINATORE  -> assegnazione
                   | nome_var MENOUGUALE assegnamento_composto TERMINATORE  -> menouguale
                   | nome_var ADDIZIONEUGUALE assegnamento_composto TERMINATORE -> addizioneuguale
                   | nome_var SWAP nome_var TERMINATORE  -> swap
                   | CHIAMATA ":" nome_var_semplice ")" ("guagliuni" ":" expr_primary ("," expr_primary)*)? "(" TERMINATORE -> call_stmt
                   | PRINT TONDASINISTRA STRINGA (ADDIZIONE expr_primary)* TONDADESTRA TERMINATORE -> stampante
                   | nome_var_semplice "." nome_var_semplice TONDASINISTRA (expr_primary ("," expr_primary)*)? TONDADESTRA TERMINATORE -> chiamata_oggetto
                   | nome_var_semplice "." nome_var_semplice -> accesso_campo




        // RETURN E BREAK

        return_stmt: CCASTA  nome_var TERMINATORE ->returnstatement
                   | CCASTA TERMINATORE   ->returnstatement

        break_stmt: BREAK TERMINATORE             -> break_statement

        // DICHIARAZIONI DI VARIABILI

        dichiarazione: tipo nome_var ASSIGN assegnamento_composto TERMINATORE
                     | tipo nome_var TERMINATORE

        ?tipo: GEN_TYPE -> tipo
            | LOTA_TK -> tipo
            | NUMR_TK -> tipo
            | NBRUOGGLIO_TK -> tipo
            | LETTER_TK -> tipo
            | ID -> tipo

        ?nome_var: ID -> variabile_semplice
                | QUADRATASINISTRA QUADRATADESTRA ID  -> variabile_array
                | QUADRATASINISTRA NUMERO QUADRATADESTRA ID  -> variabile_array

        ?nome_var_semplice: ID -> variabile_semplice


        //CLASSI

        ?classe: ROBA nome_var_semplice GRAFFASINISTRA membro*  costruttore membro* GRAFFADESTRA -> robba

        ?membro: campi
               | metodi

        // COSTRUTTORE
        costruttore: O_MAST TONDASINISTRA sezione_parametri TONDADESTRA GRAFFASINISTRA blocco GRAFFADESTRA -> costruttore

        ?campi: dichiarazione
             | campi dichiarazione


        ?metodi: funzione
              | metodi funzione



        // FUNZIONI

        funzione: tipo MESTIER  nome_var_semplice TONDASINISTRA sezione_parametri TONDADESTRA GRAFFASINISTRA blocco GRAFFADESTRA -> funzione_semplice
                | tipo QUADRATASINISTRA QUADRATADESTRA MESTIER  nome_var_semplice TONDASINISTRA sezione_parametri TONDADESTRA GRAFFASINISTRA blocco GRAFFADESTRA -> funzione_array
                | VOID MESTIER  nome_var_semplice TONDASINISTRA sezione_parametri TONDADESTRA GRAFFASINISTRA blocco GRAFFADESTRA -> funzione_void


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
                    | nome_var_semplice "." O_MAST TONDASINISTRA (expr_primary ("," expr_primary)*)? TONDADESTRA -> chiamata_costruttore
                    | nome_var_semplice "." nome_var_semplice -> accesso_campo
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
{
""",
]


def _valida_few_shot() -> None:
    log_step("valida_few_shot:start", n_esempi=len(_FEW_SHOT_PROGRAMS))
    problemi = []
    for i, prog in enumerate(_FEW_SHOT_PROGRAMS, start=1):
        try:
            _parser.parse(prog)
        except Exception as e:
            problemi.append(f"Esempio {i}: {e}")
    if problemi:
        log_step("valida_few_shot:errore", problemi=problemi)
        raise RuntimeError(
            "Uno o piu' esempi few-shot NON sono validi rispetto alla grammatica "
            "(erano stati scritti a mano senza poter eseguire Lark). Correggili "
            "in FEW_SHOT_EXAMPLES / _FEW_SHOT_PROGRAMS prima di lanciare la "
            "pipeline:\n" + "\n".join(problemi)
        )
    log_step("valida_few_shot:ok")


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


import os
import platform
import subprocess


def esegui_programma(programma: str, timeout: float = 5.0) -> str:
    import code.Compilatore as Compilatore

    log_step("esegui_programma:start", programma=programma, timeout=timeout)

    cartella_eseguibile = os.path.dirname(os.path.abspath(Compilatore.__file__))
    sistema = platform.system()
    nome_eseguibile = "scartellato.exe" if sistema == "Windows" else "scartellato"
    percorso_eseguibile = os.path.join(cartella_eseguibile, nome_eseguibile)

    if not os.path.exists(percorso_eseguibile):
        log_step("esegui_programma:eseguibile_non_trovato", percorso=percorso_eseguibile)
        raise RuntimeError(
            f"Eseguibile non trovato in '{percorso_eseguibile}'. "
            "esegui_programma() presuppone che compilatore(programma) sia "
            "gia' stata chiamata con successo (e' generatore() a creare "
            "l'eseguibile); se manca vuol dire che la compilazione C/gcc "
            "e' fallita silenziosamente (vedi nota sotto)."
        )

    comando = [percorso_eseguibile] if sistema == "Windows" else [f"./{nome_eseguibile}"]

    try:
        risultato = subprocess.run(
            comando,
            cwd=cartella_eseguibile,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as e:
        log_step("esegui_programma:timeout", timeout=timeout)
        raise RuntimeError(
            f"Timeout ({timeout}s) durante l'esecuzione del programma"
        ) from e

    if risultato.returncode != 0:
        log_step("esegui_programma:returncode_error", returncode=risultato.returncode, stderr=risultato.stderr)
        raise RuntimeError(
            f"Il programma e' terminato con codice di uscita "
            f"{risultato.returncode}.\nstderr:\n{risultato.stderr}"
        )

    log_step("esegui_programma:end", stdout=risultato.stdout)
    return risultato.stdout


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
    match = re.search(r"```(?:\w+)?\n(.*?)```", raw, re.DOTALL)
    if match:
        code = match.group(1).strip()
        log_step("extract_code", found_block=True, code=code)
        return code
    log_step("extract_code", found_block=False, raw_fallback=raw.strip())
    return raw.strip()


def extract_code_and_expected_output(raw: str):
    blocks = re.findall(r"```(?:\w+)?\n(.*?)```", raw, re.DOTALL)
    if len(blocks) < 2:
        log_step("extract_code_and_expected_output:error", n_blocks=len(blocks), raw=raw)
        raise ValueError(
            "La risposta del tester non contiene i due blocchi attesi "
            "(programma + JSON con gli output attesi):\n" + raw
        )
    programma = blocks[0].strip()
    try:
        output_attesi = json.loads(blocks[1].strip())
    except json.JSONDecodeError as e:
        log_step("extract_code_and_expected_output:json_error", error=str(e), raw_block=blocks[1])
        raise ValueError(f"Output atteso non e' JSON valido: {e}\n{blocks[1]}")
    log_step("extract_code_and_expected_output:ok", programma=programma, output_attesi=output_attesi)
    return programma, output_attesi


def confronta_output(reale: str, attesi: list[str]) -> bool:
    righe_reali = [r.strip() for r in reale.strip().splitlines()]
    righe_attese = [r.strip() for r in attesi]
    esito = righe_reali == righe_attese
    log_step("confronta_output", righe_reali=righe_reali, righe_attese=righe_attese, esito=esito)
    return esito


# ============================================================
# AGENTE 1 - GENERATOR
# ============================================================

def generate_code(feedback: str | None = None) -> str:
    log_step("generate_code:start", feedback=feedback)
    user = "Scrivi un programma in Scartellato di 8-15 righe."
    if feedback:
        user += f"\n\nFEEDBACK sul tentativo precedente (da correggere):\n{feedback}"
    raw = call_llm(system=SYSTEM_GENERATOR, user=user, temperature=0.7)
    code = extract_code(raw)
    log_step("generate_code:end", code=code)
    return code

# ============================================================
# AGENTE 2 - ruolo REPAIR
# ============================================================

def repair_program(program: str, errors: list[str]) -> str:
    log_step("repair_program:start", program=program, errors=errors)
    user = f"PROGRAMMA:\n{program}\n\nERRORI:\n" + "\n".join(errors)
    raw = call_llm(system=SYSTEM_AGENT2_REPAIR, user=user, temperature=0.2)
    fixed = extract_code(raw)
    log_step("repair_program:end", fixed_program=fixed)
    return fixed


# ============================================================
# AGENTE 2 - ruolo TESTER
# ============================================================

def test_code(program: str) -> tuple[str, list[str]]:
    log_step("test_code:start", program=program)
    user = f"PROGRAMMA (gia' compilato con successo):\n{program}"
    raw = call_llm(system=SYSTEM_AGENT2_TESTER, user=user, temperature=0.2)
    program_con_test, output_attesi = extract_code_and_expected_output(raw)
    log_step("test_code:end", program_con_test=program_con_test, output_attesi=output_attesi)
    return program_con_test, output_attesi


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
    try:
        tree = _parser.parse(program)
    except Exception as e:
        log_step("update_coverage:parse_error", error=str(e), program=program)
        return
    used = []
    for subtree in tree.iter_subtrees():
        prod = subtree.data
        if prod in state["coverage"]:
            state["coverage"][prod] += 1
            used.append(prod)
    log_step("update_coverage:ok", produzioni_usate=used)


def compute_metrics(state: dict, n_requested: int) -> dict:
    valid = state["valid_programs"]
    coverage = state["coverage"]
    metrics = {
        "validity_rate": len(valid) / n_requested if n_requested else 0,
        "n_valid": len(valid),
        "coverage_pct": sum(1 for v in coverage.values() if v > 0) / len(coverage),
        "coverage_detail": dict(coverage),
        "diversity_unique": len(set(valid)) / len(valid) if valid else 0,
        "avg_attempts_per_valid": state["all_attempts"] / len(valid) if valid else float("inf"),
    }
    log_step("compute_metrics", metrics=metrics)
    return metrics

# ============================================================
# PIPELINE PRINCIPALE
# ============================================================

def run_pipeline(n_programs: int, max_repairs: int = 5, max_regenerations: int = 3) -> dict:
    _valida_few_shot()
    state = new_state()
    log_step("run_pipeline:start", n_programs=n_programs)

    for i in range(n_programs):
        feedback = None
        successo = False

        for regen in range(max_regenerations + 1):
            program = generate_code(feedback=feedback)
            log_step("pipeline:generate_code", i=i, regen=regen, program=program)

            compiled_ok = False
            result = None
            for attempt in range(max_repairs + 1):
                result = compilatore(program)
                log_step("pipeline:compile", i=i, regen=regen, attempt=attempt,
                          ok=result.ok, errors=getattr(result, "errors", None))
                if result.ok:
                    compiled_ok = True
                    break
                program = repair_program(program, result.errors)

            if not compiled_ok:
                feedback = (f"Il programma non compila dopo {max_repairs} tentativi di repair. "
                            f"Ultimi errori del compilatore: {result.errors if result else 'n/d'}")
                continue

            try:
                program_con_test, output_attesi = test_code(program)
            except ValueError as e:
                feedback = f"Il tester non ha prodotto una risposta valida: {e}"
                continue

            result_test = compilatore(program_con_test)
            log_step("pipeline:compile_with_tests", i=i, regen=regen, ok=result_test.ok,
                      errors=getattr(result_test, "errors", None))
            if not result_test.ok:
                feedback = f"Il programma con i test non compila piu': {result_test.errors}"
                continue

            try:
                stdout_reale = esegui_programma(program_con_test)
            except Exception as e:
                feedback = f"Errore durante l'esecuzione del programma: {e}"
                continue

            if confronta_output(stdout_reale, output_attesi):
                state["valid_programs"].append(program_con_test)
                update_coverage(state, program)
                log_step("pipeline:test_passed", i=i, regen=regen)
                successo = True
                break
            else:
                feedback = (f"I test sono falliti. Output atteso:\n{output_attesi}\n"
                            f"Output ottenuto:\n{stdout_reale}")

        state["all_attempts"] += 1
        log_step("pipeline:esito", i=i, successo=successo,
                  n_validi=len(state["valid_programs"]))

    return state

import json
import os
from time import time
import anthropic
from dotenv import load_dotenv


from dotenv import load_dotenv
import os

load_dotenv("C:\\Users\\raffa\\PycharmProjects\\Scartellato\\.env")
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def call_llm(system: str, user: str, temperature: float = 0.7) -> str:
    log_step("call_llm:start", system_preview=system[:200], user=user, temperature=temperature)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=system,
        messages=[{"role": "user", "content": user}],
        temperature=temperature,
    )
    text = response.content[0].text
    log_step("call_llm:end", response=text)
    return text



def log_step(step: str, **data) -> None:
    """Scrive una riga di log JSON con lo step corrente + dati extra.
    Stesso formato usato in call_llm, ma centralizzato per non ripetere
    apertura/chiusura del file in ogni funzione."""
    LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log.md")
    entry = {"step": step, "time": time()}
    entry.update(data)
    with open(LOG_PATH, "a", encoding="utf-8") as log:
        log.write(json.dumps(entry, ensure_ascii=False) + "\n")




if __name__ == "__main__":
    final_state = run_pipeline(n_programs=50)
    metrics = compute_metrics(final_state, n_requested=100)
    print(json.dumps(metrics, indent=2))