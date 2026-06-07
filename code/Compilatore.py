from lark import Lark, UnexpectedToken, UnexpectedCharacters


def compilatore(source: str) -> str:

    
    parser = Lark.open("grammatica.lark",parser="lalr")
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
        
        var c = a+v !
        
    {
""")