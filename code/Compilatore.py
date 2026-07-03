from lark import Lark, UnexpectedToken, UnexpectedCharacters

from AST import *

from dataclasses import fields, is_dataclass
from lark import Token, Tree

from PatternVisitor import AnalisiSemantica
from PatternVisitor import AnalisiSemantica
from TranspilerC import *


def stampa_ast(nodo, prefisso="", e_ultimo=True, e_radice=True):
    if e_radice:
        ramo = ""
        ext  = ""
    else:
        ramo = "└─ " if e_ultimo else "├─ "
        ext  = "   " if e_ultimo else "│  "

    # Token grezzo — ignora
    if isinstance(nodo, Token):
        return

    # Tree non trasformato
    if isinstance(nodo, Tree):
        print(f"{prefisso}{ramo}[Tree non trasformato: {nodo.data}]")
        return

    # None
    if nodo is None:
        print(f"{prefisso}{ramo}None")
        return

    # Primitivi
    if isinstance(nodo, (int, float, str, bool)):
        print(f"{prefisso}{ramo}{repr(nodo)}")
        return

    # Lista
    if isinstance(nodo, list):
        if not nodo:
            print(f"{prefisso}{ramo}[]")
            return
        print(f"{prefisso}{ramo}[lista]")
        for i, el in enumerate(nodo):
            stampa_ast(el, prefisso + ext, i == len(nodo) - 1, False)
        return

    # Dataclass — caso generale
    if is_dataclass(nodo):
        # etichetta compatta per i nodi foglia (un solo campo primitivo)
        campi = fields(nodo)

        # nodi con rappresentazione inline
        if isinstance(nodo, Numr):
            print(f"{prefisso}{ramo}Numr({nodo.value})")
            return
        if isinstance(nodo, Boolean):
            print(f"{prefisso}{ramo}Boolean({nodo.value})")
            return
        if isinstance(nodo, Stringa):
            print(f"{prefisso}{ramo}Stringa({repr(nodo.value)})")
            return
        if isinstance(nodo, Carattr):
            print(f"{prefisso}{ramo}Carattr({repr(nodo.value)})")
            return
        if isinstance(nodo, GenericVar):
            print(f"{prefisso}{ramo}GenericVar({repr(nodo.value)})")
            return
        if isinstance(nodo, Variabile):
            arr = "[]" if nodo.is_array else ""
            print(f"{prefisso}{ramo}Variabile({arr}{repr(str(nodo.nome))})")
            return

        # nodi composti — stampa nome classe poi ogni campo
        print(f"{prefisso}{ramo}{type(nodo).__name__}")
        for i, campo in enumerate(campi):
            valore = getattr(nodo, campo.name)
            ultimo_campo = i == len(campi) - 1
            ramo_c = "└─ " if ultimo_campo else "├─ "
            ext_c  = "   " if ultimo_campo else "│  "
            print(f"{prefisso}{ext}{ramo_c}{campo.name}:")
            stampa_ast(
                valore,
                prefisso + ext + ext_c,
                True,
                False
            )
        return

    # Fallback
    print(f"{prefisso}{ramo}??? {type(nodo).__name__}  {nodo!r}")



def compilatore(source: str, output_path: str = "output.c") :
    global tree
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

        transpiler = TranspilerC(analisiSemantica.tipi_risolti)
        transpiler.visit(ast)
        codice_c = transpiler.get_output()

        with open(output_path, "w") as f:
            f.write(codice_c)

        print(codice_c)

        import subprocess
        risultato = subprocess.run(["gcc", output_path, "-o", "output.exe"], capture_output=True, text=True)
        if risultato.returncode != 0:
            print("ERRORI DI COMPILAZIONE C:")
            print(risultato.stderr)
        else:
            print("Compilazione riuscita!")

compilatore("""
            numr ] [ mestier pippo ) guagliuni :  numr a , numr b ( } 
               nbruogglio r = ??a + b??  !
            {
            
             robba ciro }
                numr c!
                
                o_mast ) ( }
                    numr a !
                    a = c !
                {
                
                nbruogglio r = ??sdfdaf?? !
                
                vacant mestier classeFunzioneMimmo )  ( }
                    burdell a = r !
                {
            {

             vacant Uè ) nbruogglio ] [ args ( }
                nbruogglio a = ??sifasf23?? !
                nbruogglio v = ??sapposto?? !
                 
                jamm_ja : pippo ) guagliuni :  4 , 5 (  !
                
                mettimcà ) v == a ( }
                    numr s = 5 !
                { allor_fa_accussi }
                    burdell z = 9 !
                {
                burdell c = a - v !
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
