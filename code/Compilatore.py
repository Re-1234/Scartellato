import lark
from lark import Lark, grammar



def compilatore(source: str) -> str:
   Grammar = (r"""
               //tipo di dati
           
               BOOLEAN : /"true"|"false"/
               NUMR: /\d+?(.\d+)/
               NBRUGGLIO: /\w+/
               ID: /[a-zA-Z_]\w*/ 
               LETTR: [/w]
               VACANT = "void"
               
              //operazioni
               MEN: "+"
               PIU: "-"           
               DIVIS: "*"
               MOLTIP: "/"
               ASSIGN: "="
               SOMMASSIGN: "-="
               MENASSIGN: "+="
               DIVISASSIGN: "*="
               PERASSIGN: "/="
               
              //operazioni logiche          
               MAGGIOR: ">"
               MINOR: "<"
               MAGGIORUGUALE: ">="
               MINORUGUALE: "<="
               EQUALS: "=="
               DIVERS: "!="
               
              //PARENTESSI 
               TONDASINISTRA: ")"
               TONDADESTRA: "("
               GRAFFASINISTRA: "}"
               GRAFFADESTRA: "{"
               QUADRATASINISTRA: "]"
               QUADRATADESTRA: "["
               
               //Keyword
               METTIMCA: "mettimcà"
               ALLORFAACCUSSI: "allor_fa_accussi"
               
               
               //classi
               ROBA: "roba"
               
               //cicli
               ASPE: "aspe"
               MARONN: "maronn"
               
               //funzione
               MESTIER: "mestier"
               
               //utilizzi generali
               VIRGULET: "\\?"
               NUNCSTANIENT: "NULL"
               SCCASCIA: "sccascià"
               CCASTA: "ccàsta"
               
               %ignore: /\s+/
               %ignore: /\/\/[^\n]*/
               %ignore: /\/\*[\s\S]*\*\//
            
                
           """
    )
