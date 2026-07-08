import os
import platform
import shutil
from lark import Lark, UnexpectedToken, UnexpectedCharacters
from AST import *
from PatternVisitor import AnalisiSemantica
from TranspilerC import *
import subprocess


def generatore(analisiSemantica):
    transpiler = TranspilerC(analisiSemantica.tipi_risolti)
    transpiler.visit(ast)
    codice_c = transpiler.get_output()

    output_path="output.c"
    cartella_corrente = os.path.dirname(os.path.abspath(__file__))
    percorso_sorgente = os.path.join(cartella_corrente, output_path)

    with open(output_path, "w") as f:
         f.write(codice_c)
    print(f"📄 File '{output_path}' creato con successo.")
    print(codice_c)
    """
    sistema = platform.system()
    nome_eseguibile = "scartellato.exe" if sistema == "Windows" else "scartellato"
    percorso_output = os.path.join(cartella_corrente, nome_eseguibile)

    #cerca nelle variabili d'ambiente gcc
    comando = ["gcc", percorso_sorgente, "-o", percorso_output]

    try:
        processo = subprocess.run(comando, capture_output=True, text=True)

        if processo.returncode == 0:
            print("✅ Compilazione completata con successo!\n")

            # ESECUZIONE AUTOMATICA DEL PROGRAMMA C
            print("-" * 30)
            print("🚀 OUTPUT DEL PROGRAMMA C:")

            # Eseguiamo il programma appena creato
            esec_comando = [percorso_output] if sistema == "Windows" else [f"./{nome_eseguibile}"]
            subprocess.run(esec_comando, cwd=cartella_corrente)

            print("-" * 30)

            # decommentare la riga sotto se Python cancella il file .c dopo aver finito
            # os.remove(percorso_sorgente)

        else:
            print("❌ Errore di compilazione nel codice C:")
            print(processo.stderr)
   

    except FileNotFoundError:

        # se il comando 'gcc' non esiste nel PATH
        print("❌ Errore: Il comando 'gcc' non è stato trovato nel sistema.")
        print("Assicurati che GCC sia installato correttamente e aggiunto al PATH (variabili d'ambiente).")
"""


def compilatore(source: str) :
    global tree
    global ast
    parser = Lark.open("grammatica.lark", parser="lalr", propagate_positions=True)
    for token in parser.lex(source):
        print(token,repr(token))

    """gestione degli errori"""
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
    except UnexpectedCharacters as e:
        print(f"Errore lessicale: {e.char!r}")


    analisiSemantica = AnalisiSemantica()
    analisiSemantica.visit(ast)

    if analisiSemantica.errori:
        print("Errori semantici:")
        for e in analisiSemantica.errori:
            print(f"  - {e}")
        return

    generatore(analisiSemantica)

"""
    import subprocess
    risultato = subprocess.run(["gcc", output_path, "-o", "output.exe"], capture_output=True, text=True)
    if risultato.returncode != 0:
        print("ERRORI DI COMPILAZIONE C:")
        print(risultato.stderr)
    else:
        print("Compilazione riuscita!")
"""
compilatore("""
            numr ] [ mestier pippo ) guagliuni :  numr a , numr b ( } 
               nbruogglio r = ??a + b??  !
               numr s!
               s= a+b!
            {
                      
            robba ciro }
                numr c!
                numr s!
                nbruogglio apposo!    
                nbruogglio r = ??sdfdaf?? !
                 
                 vacant mestier classeFunzioneMimmo )  ( }
                    burdell a = r !
                {
                               
                o_mast ) ( }
                    
                    numr apposo !
                    apposo = c !
                    c=5+6+9!
                   
                    aspe)sasicchj and sasicchj(
                       jamm_ja : classeFunzioneMimmo)(!        
                {
            {
            
             vacant Uè ) ( }
                nbruogglio a = ??sifasf23?? !
                nbruogglio v = ??sapposto?? !
                numr s !
                numr b!
                 
                jamm_ja : pippo ) guagliuni :  4 , 5 (  !
                
                mettimcà ) v == a ( }
                    numr s = 5 !
                { allor_fa_accussi }
                    burdell z = 9 !
                {
                burdell c = a + v !
                lota d = sasicchj!
                d=friariell!
                
              ambressAmbress ) numr c= 5 ! c<8 ! c++( }
                mettimcà ) 3<4( }
                    s = 4+2 !
                    c <-> b !              
                { 
              {
              
              ccàsta ! 
            {
            
    """)
