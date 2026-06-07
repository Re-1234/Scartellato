from lark import Lark


def compilatore(source: str) -> str:

    
    parser = Lark.open("grammatica.lark",parser="lalr")
    for token in parser.lex(source):
        print(token)
    tree=parser.parse(source)
    print(tree.pretty())

compilatore("""maradona ) nbruogglio ] [ args ( }
        nbruogglio a = ??sifasf23??!
        nbruogglio v = ??sapposto??!
        
        var c = a+v !
        
    {
""")