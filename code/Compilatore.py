from lark import Lark, UnexpectedToken, UnexpectedCharacters


def compilatore(source: str) -> str:
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
                mettimcà ) v != a ( }
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
