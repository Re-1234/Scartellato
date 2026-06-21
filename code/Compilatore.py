from lark import Lark, UnexpectedToken, UnexpectedCharacters

from AST import *

def stampa_ast(nodo, prefisso="", e_ultimo=True, e_radice=True):
    if e_radice:
        ramo = ""
        estensione = ""
    else:
        ramo = "└─ " if e_ultimo else "├─ "
        estensione = "   " if e_ultimo else "│  "

    if nodo is None:
        print(f"{prefisso}{ramo}None")
        return

    if isinstance(nodo, (int, float, str, bool)):
        print(f"{prefisso}{ramo}{repr(nodo)}")
        return

    if isinstance(nodo, list):
        print(f"{prefisso}{ramo}[lista]")
        for i, elemento in enumerate(nodo):
            ultimo = i == len(nodo) - 1
            stampa_ast(elemento, prefisso + estensione, ultimo, False)
        return

    if isinstance(nodo, Numr):
        print(f"{prefisso}{ramo}Numr({nodo.value})")

    elif isinstance(nodo, Boolean):
        print(f"{prefisso}{ramo}Boolean({nodo.value})")

    elif isinstance(nodo, Stringa):
        print(f"{prefisso}{ramo}Stringa({repr(nodo.value)})")

    elif isinstance(nodo, Variabile):
        print(f"{prefisso}{ramo}Variabile({repr(nodo.value)})")

    elif isinstance(nodo, OpBin):
        print(f"{prefisso}{ramo}OpBin({repr(str(nodo.op))})")
        stampa_ast(nodo.left,  prefisso + estensione, False, False)
        stampa_ast(nodo.right, prefisso + estensione, True,  False)

    elif isinstance(nodo, Dichiarazione):
        print(f"{prefisso}{ramo}Dichiarazione(tipo={repr(nodo.tipo)})")
        stampa_ast(nodo.op, prefisso + estensione, True, False)

    elif isinstance(nodo, Mettimmca):
        print(f"{prefisso}{ramo}Mettimmca")
        stampa_ast(nodo.op,     prefisso + estensione, False, False)
        stampa_ast(nodo.allora, prefisso + estensione, nodo.altrimenti is None, False)
        if nodo.altrimenti is not None:
            stampa_ast(nodo.altrimenti, prefisso + estensione, True, False)

    elif isinstance(nodo, Mestier):
        print(f"{prefisso}{ramo}Mestier({repr(nodo.nome)})")

    elif isinstance(nodo, Robba):
        print(f"{prefisso}{ramo}Robba({repr(nodo.nome)})")

    elif isinstance(nodo, Aspe):
        print(f"{prefisso}{ramo}Aspe")
        stampa_ast(nodo.Condizione, prefisso + estensione, False, False)

    elif isinstance(nodo, Ambress_Ambress):
        print(f"{prefisso}{ramo}Ambress_Ambress")

    elif isinstance(nodo, ReturnStatement):
        print(f"{prefisso}{ramo}ReturnStatement")
        stampa_ast(nodo.valor, prefisso + estensione, True, False)

    else:
        print(f"{prefisso}{ramo}??? {type(nodo).__name__}")




def compilatore(source: str) -> str:
    global tree
    parser = Lark.open("grammatica.lark", parser="lalr", propagate_positions=True)
    for token in parser.lex(source):
        print(token,repr(token))

    """gestione degli errori"""
    try:
        tree = parser.parse(source)
        print(tree.pretty())
    except UnexpectedToken as e:
        print(f"Errore sintattico alla riga {e.line}, col {e.column}")
        print(f"Token inatteso: {e.token!r}")
        print(f"Token attesi: {e.expected}")
        print(e.get_context(source))
    except UnexpectedCharacters as e:
        print(f"Errore lessicale: {e.char!r}")


    ast =  AST_Transformer().transform(tree)
    stampa_ast(ast)

compilatore(""" 

            vacant mestier pippo ) numr a , numr b ( } 
               nbruogglio r = a + b !
            {

             robba mimmo}
                nbruogglio r = ??sdfdaf?? !
                vacant mestier classeFunzioneMimmo) ( }
                    burdell a = r !
                {

            {

             vacant Uè ) nbruogglio ] [ args ( }
                nbruogglio a = ??sifasf23?? !
                nbruogglio v = ??sapposto?? !
                mettimcà ) v == a ( }
                    numr s = 5 !
                { allor_fa_accussi }
                    burdell z = 9 !
                {
                burdell c = a - v !
                lota d = sasicchj!
              ambressAmbress ) numr c= 5 ! c<8 ! c++( }
                mettimcà ) 3<4( }
                    s = 4+2 !
                { 
              {
            {

    """)
