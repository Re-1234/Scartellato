from lark import Lark, UnexpectedToken, UnexpectedCharacters


def compilatore(source: str) -> str:

    
    parser = Lark.open("grammatica.lark",parser="lalr",propagate_positions=True)
    tree = parser.parse(source)
    for token in parser.lex(source):
        print(token)

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



compilatore("""maradona ) nbruogglio ] [ args ( }
        nbruogglio a = ??sifasf23??!
        nbruogglio v = ??sapposto??!
        mettimcà )v!=a( }
            numr s = 5 !
        { allor_fa_accussi}
            var z=9!
        {
        
        var c = a+v !
        
    {
""")