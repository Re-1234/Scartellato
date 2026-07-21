import os
import platform
import re
import subprocess
import shutil

from lark import Lark, UnexpectedToken, UnexpectedCharacters

from code.AnalisiSintattica.AST import *
from code.AnalisiSemantica.PatternVisitor import AnalisiSemantica
from code.AnalisiSemantica.Transpiler import *

from estrai_test_cases import estrai_test_cases


def trova_gcc():
    """Cerca gcc nel PATH di sistema. Se non lo trova, prova percorsi comuni di fallback su Windows."""
    percorso_gcc = shutil.which("gcc")
    if percorso_gcc:
        return percorso_gcc

    # Fallback: percorsi comuni di installazione MSYS2 su Windows,
    # nel caso l'utente non abbia configurato il PATH di sistema
    if platform.system() == "Windows":
        candidati = [
            r"C:\msys64\ucrt64\bin\gcc.exe",
            r"C:\msys64\mingw64\bin\gcc.exe",
            r"C:\msys64\clang64\bin\gcc.exe",
        ]
        for c in candidati:
            if os.path.exists(c):
                return c

    return None


def generatore(analisiSemantica, esegui=True):
    """Genera il codice C, lo compila con gcc e (se esegui=True) lo lancia,
    catturando lo stdout del programma invece di lasciarlo solo stampare
    a schermo. Ritorna lo stdout catturato (str), oppure None se non è
    stato eseguito (esegui=False) o se qualcosa è andato storto."""
    transpiler = Transpiler(analisiSemantica.tipi_risolti, analisiSemantica.burdell_info, analisiSemantica.print_types)
    transpiler.visit(ast)
    codice_c = transpiler.get_output()

    output_path = "output.c"
    cartella_corrente = os.path.dirname(os.path.abspath(__file__))
    percorso_sorgente = os.path.join(cartella_corrente, output_path)

    with open(percorso_sorgente, "w") as f:
        f.write(codice_c)
    print(f"📄 File '{percorso_sorgente}' creato con successo.")
    print(codice_c)

    sistema = platform.system()
    nome_eseguibile = "scartellato.exe" if sistema == "Windows" else "scartellato"
    percorso_output = os.path.join(cartella_corrente, nome_eseguibile)

    percorso_gcc = trova_gcc()
    if percorso_gcc is None:
        print("❌ Errore: Il comando 'gcc' non è stato trovato nel sistema.")
        print("Assicurati che GCC sia installato correttamente e aggiunto al PATH (variabili d'ambiente).")
        return None

    comando = [percorso_gcc, percorso_sorgente, "-o", percorso_output]

    # Assicura che la cartella di gcc sia nel PATH del sottoprocesso,
    # utile se gcc è stato trovato tramite fallback e non tramite PATH di sistema
    env = os.environ.copy()
    cartella_gcc = os.path.dirname(percorso_gcc)
    if cartella_gcc not in env["PATH"]:
        env["PATH"] = cartella_gcc + os.pathsep + env["PATH"]

    try:
        processo = subprocess.run(comando, capture_output=True, text=True, env=env)

        print("Return code:", processo.returncode)

        if processo.returncode == 0:
            print("✅ Compilazione completata con successo!\n")

            if not esegui:
                # Serve per i programmi con 'ric' (scanf): li compiliamo per
                # controllare che non ci siano errori, ma non li lanciamo,
                # altrimenti resterebbero bloccati in attesa di input.
                return None

            print("-" * 30)
            print("🚀 OUTPUT DEL PROGRAMMA C:")

            esec_comando = [percorso_output] if sistema == "Windows" else [f"./{nome_eseguibile}"]
            processo_run = subprocess.run(esec_comando, cwd=cartella_corrente,
                                           capture_output=True, text=True)
            print(processo_run.stdout)
            if processo_run.stderr:
                print("stderr:", processo_run.stderr)

            print("-" * 30)
            return processo_run.stdout
        else:
            print("❌ Errore di compilazione nel codice C:")
            print(processo.stderr)
            return None

    except FileNotFoundError:
        print("❌ Errore: Il comando 'gcc' non è stato trovato nel sistema.")
        print("Assicurati che GCC sia installato correttamente e aggiunto al PATH (variabili d'ambiente).")
        return None


class CompileResult:
    def __init__(self, ok: bool, errors: list[str] | None = None, output: str = ""):
        self.ok = ok
        self.errors = errors or []
        self.output = output


def compilatore(source: str, esegui: bool = True) -> CompileResult:
    """Compila (e, se esegui=True, esegue) il codice sorgente passato.
    esegui=False va usato per i programmi che contengono 'ric' (scanf),
    per non restare bloccati in attesa di input da tastiera."""
    global tree
    global ast
    parser = Lark.open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "grammatica.lark"),
        parser="lalr", propagate_positions=True
    )

    try:
        tree = parser.parse(source)
        print(tree.pretty())
        ast = AST_Transformer().transform(tree)
        stampa_ast(ast)
    except UnexpectedToken as e:
        print(f"Errore sintattico alla riga {e.line}, col {e.column}")
        print(f"Token inatteso: {e.token!r}")
        print(f"Token attesi: {e.expected}")
        print(e.get_context(source))
        return CompileResult(False,
                             [f"Errore sintattico riga {e.line}, col {e.column}: token inatteso {e.token!r}, attesi {e.expected}"])
    except UnexpectedCharacters as e:
        print(f"Errore lessicale: {e.char!r}")
        return CompileResult(False, [f"Errore lessicale: carattere inatteso {e.char!r}"])

    analisiSemantica = AnalisiSemantica()
    analisiSemantica.visit(ast)

    if analisiSemantica.getErrori():
        print(analisiSemantica.getErrori())
        return CompileResult(False, analisiSemantica.getErrori())

    output_programma = generatore(analisiSemantica, esegui=esegui)
    return CompileResult(True, output=output_programma or "")


# ---------------------------------------------------------------------------
# Esecuzione dei test case letti da "Categori Partion"
# ---------------------------------------------------------------------------

RE_SCANF = re.compile(r'\bric\s*\)')


def richiede_input_utente(codice: str) -> bool:
    """True se il programma usa 'ric' (scanf): in quel caso l'output
    dipende da cosa digita l'utente e non ha senso eseguirlo in automatico
    confrontandolo con un oracolo fisso."""
    return bool(RE_SCANF.search(codice))


def normalizza(testo: str) -> str:
    """Normalizza spazi/maiuscole per un confronto tollerante."""
    testo = testo.strip().lower()
    testo = re.sub(r'\s+', ' ', testo)
    return testo


def confronta(oracolo: str, ottenuto: str, manuale: bool) -> str:
    """Ritorna 'OK', 'FALLITO', 'DA VERIFICARE' o 'MANUALE'."""
    if manuale:
        return "MANUALE (test con scanf: compilazione riuscita, esecuzione da fare a mano)"

    if not oracolo.strip():
        return "DA VERIFICARE (nessun oracolo indicato nel file)"

    n_oracolo = normalizza(oracolo)
    n_ottenuto = normalizza(ottenuto)

    if not n_ottenuto:
        return "FALLITO (nessun output prodotto)"

    if n_oracolo == n_ottenuto:
        return "OK"
    if n_oracolo in n_ottenuto or n_ottenuto in n_oracolo:
        return "OK (match parziale)"
    return "DA VERIFICARE (output diverso dall'oracolo, controllare a mano)"


def esegui_test(test: dict):
    """Lancia compilatore() sul codice del test e restituisce (output, manuale)."""
    manuale = richiede_input_utente(test["codice"])
    try:
        risultato = compilatore(test["codice"], esegui=not manuale)
    except Exception as e:
        return f"ECCEZIONE PYTHON: {e!r}", manuale

    if risultato is None:
        return "(nessun CompileResult restituito)", manuale

    if not risultato.ok:
        return "ERRORE: " + " | ".join(risultato.errors), manuale

    if manuale:
        return "COMPILATO OK - richiede input utente (scanf)", manuale

    if risultato.output:
        return risultato.output, manuale

    return "(compilazione OK, ma nessun output prodotto)", manuale


def esegui_tutti_i_test(percorso_file: str = "Categori Partion.txt"):
    tests = estrai_test_cases(percorso_file)

    ok, fail, boh, manuale_count = 0, 0, 0, 0

    for i, test in enumerate(tests, start=1):
        print(f"\n===== Test case {i}: {test['categoria']} - {test['nome']} =====")
        if test["stato"]:
            print(f"Stato annotato nel file: {test['stato']}")
        if test["note"]:
            print(f"Note: {test['note']}")

        ottenuto, manuale = esegui_test(test)
        esito = confronta(test["oracolo"], ottenuto, manuale)

        print(f"Oracolo atteso:\n  {test['oracolo'] or '(non specificato)'}")
        print(f"Risultato ottenuto:\n  {ottenuto}")
        print(f"Esito: {esito}")

        if esito.startswith("MANUALE"):
            manuale_count += 1
        elif esito.startswith("OK"):
            ok += 1
        elif esito.startswith("FALLITO") or esito.startswith("ERRORE") or esito.startswith("ECCEZIONE"):
            fail += 1
        else:
            boh += 1

    print(f"\n===== Riepilogo: {len(tests)} test totali | OK: {ok} | FALLITI: {fail} | "
          f"DA VERIFICARE: {boh} | MANUALI (scanf): {manuale_count} =====")


if __name__ == "__main__":
    import sys
    percorso = sys.argv[1] if len(sys.argv) > 1 else "Test Case"
    esegui_tutti_i_test(percorso)