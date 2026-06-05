import lark
from lark import Lark, grammar



def compilatore(source: str) -> str:
   valore = 2
   valore = "ciao"
   Grammar = (r"""
               //tipo di dati
               
               BOOLEAN : /"true"|"false"/
               BOOLEAN1: "boolean"
               NUMR: /\d+?(.\d+) /
               NUMR1: "numer
               STRINGA: "??"/\w+/"??"
               NBRUOGGLIO: "nbruogglio"
               ID: /[a-zA-Z_]\w*/ 
               CARATTR: "?" /[/w]/ "?" 
               LETTER: "lettr"
               //
               VOID: "vacant"
               //tipo generico   
               TYP: "var" 
            
              //operazioni
               DIVISIONEUGUALE: "*="
               MOLTIPLICAUGUALE: "/="
               ADDIZIONEUGUALE: "-="
               MENOUGUALE: "+="
               MENO: "+"
               ADDIZIONE: "-"
               MOLTIPLICA:"/"
               DIVISIONE: "*"
               ASSIGN: "="
               PLUSPLUS: "++"
               MENMEN: "--"
               RESTO: "%"
               
              //operazioni logiche          
               OR: "or" | "||" 
               AND: "and" | "&&"
               NOT: "not" | "!"
               EQUALS: "==" 
               DIVERSO: "!=" 
               MAGGIORE: ">"
               MAGGIOREUGUALE: ">="
               MINORE: "<"
               MINOREUGUALE: "<="
               
              //PARENTESSI 
               TONDASINISTRA: ")"
               TONDADESTRA: "("
               GRAFFASINISTRA: "}"
               GRAFFADESTRA: "{"
               QUADRATASINISTRA: "]"
               QUADRATADESTRA: "["
               //Keyword
               //if
               METTIMCA: "mettimcà"
               //else
               ALLORFAACCUSSI: "allor_fa_accussi"
               //classi
               ROBA: "roba"
               //ciclo while
               ASPE: "aspe"
               //il ciclo for
               MARONN: "maronn"
               //funzione
               MESTIER: "mestier"
               //main
               MAIN: "maradona"
               //utilizzi generali
               VIRGULET: "\\?"
               //il null
               NUNCSTANIENT: "NULL"
               //break
               SCCASCIA: "sccascià"
               //return
               CCASTA: "ccàsta"
               TERMINATOR: ";"
               
               
               %ignore /\s+/
               %ignore /\/\/[^\n]*/
               %ignore /\/\*[\s\S]*\*\//        
               start: /\s\S/     
           """
    )

