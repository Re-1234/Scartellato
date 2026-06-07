from lark import Lark


def compilatore(source: str) -> str:


    parser = Lark.open("grammatica.lark",parser="lalr")
    for token in parser.lex(source):
        print(token)

compilatore("nbruogglio a = ??sifasf23??!")