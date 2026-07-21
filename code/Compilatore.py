import os
import platform
from lark import Lark, UnexpectedToken, UnexpectedCharacters

from code.AnalisiSintattica.AST import *
from code.AnalisiSemantica.PatternVisitor import AnalisiSemantica
import subprocess
import shutil

from code.AnalisiSemantica.Transpiler import  *


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



def generatore(analisiSemantica):
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
        return

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
            print("-" * 30)
            print("🚀 OUTPUT DEL PROGRAMMA C:")

            esec_comando = [percorso_output] if sistema == "Windows" else [f"./{nome_eseguibile}"]
            subprocess.run(esec_comando, cwd=cartella_corrente)

            print("-" * 30)
        else:
            print("❌ Errore di compilazione nel codice C:")
            print(processo.stderr)

    except FileNotFoundError:
        print("❌ Errore: Il comando 'gcc' non è stato trovato nel sistema.")
        print("Assicurati che GCC sia installato correttamente e aggiunto al PATH (variabili d'ambiente).")


class CompileResult:
    def __init__(self, ok: bool, errors: list[str] | None = None):
        self.ok = ok
        self.errors = errors or []


def compilatore(source: str) -> CompileResult:
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
        return CompileResult(False,analisiSemantica.getErrori())

    generatore(analisiSemantica)
    return CompileResult(True)


compilatore(""" 
vacant Uè ) ( }
    burdell mutante = 10 !                   // Nasce come numr
    numr contatore = 0 !
    lota condizione = sasicchj !
    
    aspe ) condizione ( }
        numr interno_while = 5 !
        mutante = ??Ora sono una stringa?? ! // mutante DIVENTA nbruogglio
        
        ambressAmbress ) numr i = 0 ! i < 10 ! i++ ( }
            burdell temporaneo = i + interno_while !  // Nasce come numr
            
            mettimcà ) temporaneo > 7 ( }
               
            { allor_fa_accussi }
                temporaneo = ??Pure io stringa?? ! // temporaneo DIVENTA nbruogglio
                mutante <-> temporaneo !     // ✅ OK: ora sono entrambe stringhe
            {
        {
        
        condizione = friariell !
    {
{
""")