import os
import platform
from lark import Lark, UnexpectedToken, UnexpectedCharacters
from .AST import *
from .PatternVisitor import AnalisiSemantica
from .TranspilerC import *
import subprocess
import shutil



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
    transpiler = TranspilerC(analisiSemantica.tipi_risolti)
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
        ast = AST_Transformer().transform(tree)
    except UnexpectedToken as e:
        return CompileResult(False, [f"Errore sintattico riga {e.line}, col {e.column}: token inatteso {e.token!r}, attesi {e.expected}"])
    except UnexpectedCharacters as e:
        return CompileResult(False, [f"Errore lessicale: carattere inatteso {e.char!r}"])

    analisiSemantica = AnalisiSemantica()
    analisiSemantica.visit(ast)

    if analisiSemantica.errori:
        return CompileResult(False, list(analisiSemantica.errori))

    generatore(analisiSemantica)
    return CompileResult(True)


if __name__ == "__main__":
    compilatore("""
                numr ] [ mestier pippo ) guagliuni :  numr a , numr b ( } 
                   nbruogglio r = ??a + b??  !
                   numr ][ s !
                   numr c1 = 4 !
                   s+= c1 !
                   lota d = sasicchj !
                   nbruogglio x = ??2?? !
                   r -=  c1 + x !
                
                    //controllo di burdell
                    burdell z !
                    z = a+b !
                    z=r!
                    
                    aspe)2( }
                        z = r !
                        burdell p !
                        p= z!
                        z += r !
                        arape_a_vocca)??ciao??(!
                    {
                   
                   //return 
                   ccàsta s!
                {
            
        """)