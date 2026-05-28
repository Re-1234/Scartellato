import lark
from lark import Lark, grammar

Grammar = (r"""
           //tipo di dati
           
           BOOLEAN : /"true"|"false"/
           NUMR: /\d+?(.\d+)/
           NBRUGGLIO: /\w+/
           ID: /[a-zA-Z_]\w*/ 
           LETTR: [/w]
           VACANT = "void"
           
           MEN: "+"
           PIU: "-"           
           DIVIS: "*"
           MOLTIP: "/"
           ASSIGN: "="
           
           MAGGIOR: ">"
           MINOR: "<"
           MAGGIORUGUALE: ">="
           MINORUGUALE: 
           %ignore: /\s+/
           """
)
