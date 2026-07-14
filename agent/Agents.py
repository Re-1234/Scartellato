import json

from lark.load_grammar import GRAMMAR_ERRORS

from agent.anthropicAPI import call_llm
import re
from lark import Lark

from code.Compilatore import compilatore

# Parser costruito UNA volta sola fuori dalla funzione (fuori dal ciclo!),
# altrimenti ricompili la grammatica ad ogni singola chiamata: costoso e inutile.


GRAMMAR_L = """
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

PRODUCTIONS = ["start", "main_def", "main_opzione", "top_level",
               "blocco", "istruzione" , "dichiarazione" , "for_stmt","while_stmt","if_stmt","return_stmt","nome_var","assegnamento_composto"
               ,"tipo","classe","membro","metodi","costruttore","campi","funzione","sezione_parametri",
               "parametro","dichiarazione_for","valutazione","for_corpo","expr_or","expr_and","expr_eq","expr_rel",
               "expr_add","expr_mul","expr_unary","expr_primary"]

FEW_SHOT_EXAMPLES = """
        
"""

SYSTEM_SPEC = f""" Sei lo Spec Designer per la generazione di programmi in Scartellato.
NON scrivi codice . Produci una specifica STRUTTURALE (forma , non funzione ).
GRAMMATICA :
{ GRAMMAR_L }
FORMATO DI USCITA esatto :
TITOLO : <una riga >
COSTRUTTI RICHIESTI : <lista separata da virgole >
STRUTTURA : <2 -4 frasi sulla forma >"""


SYSTEM_WRITER = f"""Sei un Code Writer . Ricevi una specifica strutturale
e scrivi un programma in Scartellato che la rispetta .
GRAMMATICA :
{ GRAMMAR_L }
ESEMPI :
{ FEW_SHOT_EXAMPLES }
Rispondi SOLO con il codice del programma , niente altro ."""


SYSTEM_REPAIR = f"""Sei un riparatore di programmi nel linguaggio Scartellato.
Ricevi un programma con errori e i messaggi del compilatore .
Riscrivi il programma correggendo SOLO gli errori segnalati .
Mantieni il piu ’ possibile la struttura originale .
GRAMMATICA :
{ GRAMMAR_L }
Rispondi SOLO con il programma corretto ."""


SYSTEM_GENERATE_TESTER = f""" sei un generatore di casi di test del programma che ti viene 
dato come parametro e mi devi Rispondi SOLAMENTE con tutti i casi di test e deve coprire
tutti i casi possibili riguradanti il programma
"""

#qua invochiamo Lark per prendere il pars tree
_parser = Lark(GRAMMAR_L, start="start", parser="lalr")

def write_code ( spec : str ) -> str :
        user = f" SPECIFICA :\n{ spec }\n\ nScrivi il programma in Scartellato."
        return extract_code ( call_llm ( system = SYSTEM_WRITER , user = user , temperature =0.7))
# Repair : identico alla prima ora
def repair_program ( program : str , errors : list [ str ]) -> str :
    user = f" PROGRAMMA :\n{ program }\n\ nERRORI :\n" + "\n". join ( errors )
    return extract_code ( call_llm ( system = SYSTEM_REPAIR , user = user , temperature =0.2) )




def design_spec ( state : dict ) -> str :
    coverage_report = "\n". join (
        f"- {p}: {n} volte " + (" <-- sotto - coperto " if n < 3 else "")
        for p , n in state [" coverage "]. items ()
    )
    user = f""" COSTRUTTI GIA ’ COPERTI :
    { coverage_report }
        Produci una spec per un programma di 8 -15 righe che includa almeno un costrutto sotto - coperto .
        NON descrivere lo scopo del programma , solo la forma ."""
    return call_llm ( system = SYSTEM_SPEC , user = user , temperature =0.7)


def test_code (program : str):
    user = f"""PROGRAMMA: {program} \n genera i casi di testa"""
    return extract_code(call_llm(system= SYSTEM_GENERATE_TESTER , user = user, temperature = 0.5))

def new_state () -> dict :
    return {
        " coverage ": {p : 0 for p in PRODUCTIONS }, # quante volte ogni costrutto e’ stato usato
        " valid_programs ": [] , # programmi che hanno compilato
        " all_attempts ": 0, # totale chiamate LLM ( per cost )
        " total_tokens ": 0, # token consumati ( per cost )
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

""" Rimuove eventuali fence markdown e whitespace di troppo ."""
    # rimuove ‘‘‘ linguaggio ... ‘‘‘
def extract_code ( raw : str ) -> str :
    fenced = re . search (r" ‘ ‘ ‘(?:\w+) ?\n (.*?) ‘‘‘", raw , re . DOTALL )
    if fenced :
        return fenced . group (1) . strip ()
    return raw . strip ()


def run_pipeline ( n_programs : int , max_repairs : int = 5) -> dict :
    state = new_state ()
    for i in range ( n_programs ):
        # 1. Spec Designer decide la forma del prossimo programma
        spec = design_spec (state)
        # 2. Code Writer la traduce in L
        program = write_code ( spec )
        # 3. Loop di repair
        for attempt in range ( max_repairs + 1) :
            result = compilatore(program)
            if result . ok :



                state [" valid_programs "]. append ( program )
                update_coverage ( state , program )
                break
            program = repair_program ( program , result . errors )
    # se esce dal for senza break , e’ fallito : si ricomincia con un nuovo seme
        state [" all_attempts "] += 1
        print (f"[{i +1}/{ n_programs }] validi : { len ( state ["valid_programs"])} , "
        f" coverage : { sum (1 for v in state ["coverage"]. values () if v >0) }/{ len (
        PRODUCTIONS )}")
        return state


def compute_metrics ( state : dict , n_requested : int ) -> dict :
    valid = state [" valid_programs "]
    coverage = state [" coverage "]
    return {
        " validity_rate ": len ( valid ) / n_requested if n_requested else 0 ,
        " n_valid ": len ( valid ) ,
        " coverage_pct ": sum (1 for v in coverage . values () if v > 0) / len ( coverage ) ,
        " coverage_detail ": dict ( coverage ) ,
        " diversity_unique ": len ( set ( valid ) ) / len ( valid ) if valid else 0,
        " avg_attempts_per_valid ": state [" all_attempts "] / len ( valid ) if valid else
        float (" inf ") ,
    }

# Uso:
final_state = run_pipeline ( n_programs =100)
metrics = compute_metrics ( final_state , n_requested =100)
print (json . dumps ( metrics , indent =2) )
