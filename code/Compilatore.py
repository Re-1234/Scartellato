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
numr ][arr !

vacant mestier riempi )( }
    arr -= 8 !
    arr -= 3 !
    arr -= 5 !
    arr -= 1 !
    arr -= 9 !
    arr -= 2 !
    arr -= 7 !
    arr -= 4 !
{

vacant mestier merge ) guagliuni : numr sinistra, numr centro, numr destra ( }
    numr ][temp !
    numr i = sinistra !
    numr j = centro + 1 !

    aspe ) i <= centro ( }
        temp -= arr]i[ !
        i++ !
    {
    aspe ) j <= destra ( }
        temp -= arr]j[ !
        j++ !
    {

    numr metaSinistra = centro - sinistra !
    numr totale = destra - sinistra !
    numr p1 = 0 !
    numr p2 = metaSinistra + 1 !
    numr k = sinistra !

    aspe ) p1 <= metaSinistra and p2 <= totale ( }
        mettimmcà ) temp]p1[ <= temp]p2[ ( }
            arr]k[ = temp]p1[ !
            p1++ !
        { allor_fa_accussi }
            arr]k[ = temp]p2[ !
            p2++ !
        {
        k++ !
    {

    aspe ) p1 <= metaSinistra ( }
        arr]k[ = temp]p1[ !
        p1++ !
        k++ !
    {

    aspe ) p2 <= totale ( }
        arr]k[ = temp]p2[ !
        p2++ !
        k++ !
    {
{

vacant mestier mergeSort ) guagliuni : numr sinistra, numr destra ( }
    mettimmcà ) sinistra < destra ( }
        numr centro = )sinistra + destra( / 2 !
        jamm_ja : mergeSort ) guagliuni : sinistra, centro ( !
        jamm_ja : mergeSort ) guagliuni : centro + 1, destra ( !
        jamm_ja : merge ) guagliuni : sinistra, centro, destra ( !
    {
{

vacant mestier stampaArray ) guagliuni : numr n ( }
    numr i = 0 !
    aspe ) i <= n ( }
        arape_a_vocca ) ??Elemento: ?? - arr]i[ ( !
        i++ !
    {
{

vacant Uè)( }
    jamm_ja : riempi )( !
    arape_a_vocca ) ??Array prima dell'ordinamento:?? ( !
    jamm_ja : stampaArray ) guagliuni : 7 ( !
    jamm_ja : mergeSort ) guagliuni : 0, 7 ( !
    arape_a_vocca ) ??Array dopo l'ordinamento:?? ( !
    jamm_ja : stampaArray ) guagliuni : 7 ( !
{
""")

