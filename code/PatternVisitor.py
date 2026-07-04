from SymbolTable import SymbolTable
from SemanticError import SemanticError
from Transformer import *


class AnalisiSemantica:
    def __init__(self):
        self.errori = []
        symbolTable: SymbolTable
        self.tipi_risolti = {}
        self.funzione_corrente = None

    def visit(self, node):
        class_name = node.__class__.__name__
        method_name = f'visit_{class_name}'
        method = getattr(self, method_name, self.generic_visit)
        # stampa di debug: controllo del VISIT chiamato
        print(f"[VISIT] {class_name}")
        risultato = method(node)

        if risultato is not None and isinstance(risultato, str):
            self.tipi_risolti[id(node)] = risultato
            print(f"  → tipo risolto: {risultato}")  # ← mostra il tipo restituito
        return risultato

    def generic_visit(self, node):
        raise Exception(f"Nessun metodo visit_{node.__class__.__name__}")

    def errore(self, msg):
        self.errori.append(msg)


    #   ---PROGRAM---
    def visit_Start(self, node):
        self.symbolTable = SymbolTable()
        self.symbolTable.enterScope()

        for kid in node.program:
            self.visit(kid)

        self.symbolTable.exitScope()


    #   ---CLASSE---
    def visit_Robba(self, node: Robba):
        self.symbolTable.addId(node.nome, node)
        self.symbolTable.enterScope()

        for kid in node.variabili:
            self.visit(kid)

        if node.costruttore is not None:
            self.visit(node.costruttore)

        for kid in node.funzioni:
            self.visit(kid)

        self.symbolTable.exitScope()

    def visit_Costruttore(self, node: Costruttore):
        self.symbolTable.enterScope()

        for par in node.parametri:
            self.visit(par)
            self.tipi_risolti[id(par.nome)] = str(par.tipo)

        self.visit(node.corpo)
        self.symbolTable.exitScope()



    #   ----TIPI-----
    def visit_Numr(self, node: Numr):
        return "numr"

    def visit_Boolean(self, node: Boolean):
        return "lota"

    def visit_Stringa(self, node: Stringa):
        return "nbruogglio"

    def visit_Carattr(self, node: Carattr):
        return "lettr"

    def visit_GenericVar(self, nodo):
        return "burdell"

    def visit_Variabile(self, node: Variabile):
        tipo = self.symbolTable.lookup(node.nome)
        if tipo is None:
            raise SemanticError(f"Variabile '{node.nome}' non dichiarata")
        return tipo

    def _compatibili(self, tipo_atteso, tipo_trovato):
        n1 = tipo_atteso.nome if isinstance(tipo_atteso, TipoDato) else tipo_atteso
        n2 = tipo_trovato.nome if isinstance(tipo_trovato, TipoDato) else tipo_trovato
        if n1 == "burdell":
            return True
        return n1 == n2



    #   ---FUNZIONI-----
    def visit_Mestier(self, node: Mestier):
        #inserisce il nome della funzione nello scope precendente e
        # ne crea uno nuovo per lo scope della funzione
        self.symbolTable.addId(node.nome, node)
        self.symbolTable.enterScope()
        #salvataggio del nodo con la funzione corrente
        self.funzione_corrente = node

        #visita i nodi figli riguardo alla funzione
        for kid in node.parametri:
            self.visit(kid)
            self.tipi_risolti[id(kid.nome)] = str(kid.tipo)

        self.visit(node.corpo)
        self.symbolTable.printTable()  # stampa dei parametri

        # reset del valore cosi non sarà alterato in chiamate future
        self.funzione_corrente = None
        self.symbolTable.exitScope()



    def visit_Parametro(self, node: Parametro):
        # Recuperiamo il nome della variabile (visto che node.nome è un oggetto Variabile)
        nome_var = str(node.nome.nome)
        tipo_var = node.tipo

        # Controlla se il parametro è già stato dichiarato nello scope corrente (duplicato)
        if self.symbolTable.probe(nome_var):
            raise SemanticError(f"NNNNNNNNNNOOOOOOOOOOOOO ma che è fatt!!!!!: Parametro duplicato '{nome_var}'")

        # Inserisce il parametro nella Symbol Table come variabile valida in questo scope
        self.symbolTable.addId(nome_var, tipo_var)


        # da continuare a modificare questo metodo
    def visit_ReturnStatement(self, node: ReturnStatement):
        # nodo.valore contiene un nodo qualsiasi
        tipo_valore = self.visit(node.valore) if node.valore is not None else "vacant"

        if self.funzione_corrente is not None:
            tipo_atteso = str(self.funzione_corrente.ritorno)
            if not self._compatibili(tipo_atteso, tipo_valore):
                raise SemanticError(
                    f"Return di tipo '{tipo_valore}' ma la funzione "
                    f"'{self.funzione_corrente.nome.nome}' ritorna '{tipo_atteso}'"
                )

        return tipo_valore


    def visit_Block(self, node: Block):
        for element in node.statements:
            self.visit(element)


    def visit_CallStmt(self, node: CallStmt):
        nome_funzione = node.nome_func.nome
        funzione = self.symbolTable.lookup(nome_funzione)
        if funzione is None:
            raise SemanticError(f"Funzione '{nome_funzione}' non dichiarata")
        if not isinstance(funzione, Mestier):
            raise SemanticError(f"'{nome_funzione}' non è una funzione")

        if len(node.args) != len(funzione.parametri):
            raise SemanticError(
                f"'{nome_funzione}' si aspetta {len(funzione.parametri)} argomenti, "
                f"ricevuti {len(node.args)}"
            )

        for arg in node.args:
            self.visit(arg)

        return str(funzione.ritorno)

    #   ---CICLI---
    def visit_Ambress_Ambress(self, node: Ambress_Ambress):
        self.symbolTable.enterScope()
        self.visit(node.dichiarazione)

        tipo_cond = self.visit(node.condizione)
        if tipo_cond != "lota":
            raise SemanticError( f"BOTT_A_MUR: Ma ch stai facen!!!!! e mis '{tipo_cond}'! non puoi inserire una espressione che ha come risultato un valore diverso da boolean")

        self.visit(node.VarOperation)
        self.visit(node.Corpo)

        self.symbolTable.exitScope()

    def visit_Aspe(self, node: Aspe):
        tipo_cond = self.visit(node.Condizione)
        if tipo_cond != "lota":
            raise SemanticError(f"La condizione del while deve essere booleana, trovato '{tipo_cond}'")

        self.symbolTable.enterScope()
        self.visit(node.Corpo)
        self.symbolTable.exitScope()


    #   ---IF---
    def visit_Mettimmca(self, node: Mettimmca):
        tipo_cond = self.visit(node.condizione)
        if tipo_cond != "lota":
            raise SemanticError(f"La condizione dell'if deve essere booleana, trovato '{tipo_cond}'")

        self.symbolTable.enterScope()
        self.visit(node.allora)
        self.symbolTable.exitScope()

        if node.altrimenti is not None:
            self.symbolTable.enterScope()
            self.visit(node.altrimenti)
            self.symbolTable.exitScope()

    #   ---VALUTAZIONE E ASSEGNAMENTO---
    def visit_OpBin(self, node: OpBin):
        co = self.visit(node.left)

        if node.right is None:
            if node.op in ('++', '--'):
                nome = co.nome if isinstance(co, TipoDato) else co
                if nome != 'numr':
                    raise SemanticError(f"'{node.op}' applicabile solo a numr")
                return co
            raise SemanticError(f"Operatore '{node.op}' senza operando destro")

        ci = self.visit(node.right)

        # estrai sempre il nome stringa per i confronti
        nome_co = co.nome if isinstance(co, TipoDato) else co
        nome_ci = ci.nome if isinstance(ci, TipoDato) else ci

        if nome_co == "lota" and nome_ci == "lota":
            if self.control_Ope_Bool(node.op):
                return TipoDato(nome='lota', linea=None, colonna=None)

        if nome_co == "numr" and nome_ci == "numr":
            if self.control_Ope_Aritmetic(node.op):
                return TipoDato(nome='numr', linea=None, colonna=None)
            if self.control_Ope_Bool(node.op):
                return TipoDato(nome='lota', linea=None, colonna=None)
            if self.control_Ope_Assign(node.op, "numr"):
                return TipoDato(nome='numr', linea=None, colonna=None)

        if nome_co == "nbruogglio" and nome_ci == "nbruogglio":
            if node.op == "+":
                return TipoDato(nome='nbruogglio', linea=None, colonna=None)
            if self.control_Ope_Bool(node.op):
                return TipoDato(nome='lota', linea=None, colonna=None)

        raise SemanticError(
            f"MACCCCCCCCCHHHHHHHH STAI FACENNNNN!!!!!!!: "
            f"i tipi sono diversi: sinistra '{nome_co}' destra '{nome_ci}'"
        )

    def visit_Dichiarazione(self, node: Dichiarazione):

        tipo_dichiarato = node.tipo.nome  # es. "Numr", "Boolean", "Stringa"
        nome_variabile = node.nome.nome
        if node.valore is not None:
           tipo_valore = self.visit(node.valore)  # visita l'espressione, ottiene la stringa del tipo

        if self.symbolTable.probe(node.nome):
            raise SemanticError(f"Errore ")
        if node.valore is not None:
            tipo_valore = self.visit(node.valore)
            if not self._compatibili(tipo_dichiarato, tipo_valore):
                raise SemanticError(
                    f"Errore di tipo (riga {node.tipo.linea}, colonna {node.tipo.colonna}): "
                    f"la variabile '{nome_variabile}' è dichiarata come '{tipo_dichiarato}' "
                    f"ma le viene assegnato un valore di tipo '{tipo_valore}'")

        self.symbolTable.addId(nome_variabile, tipo_dichiarato)
        self.tipi_risolti[id(node.nome)] = tipo_dichiarato

        return None




    def control_Ope_Bool(self, oper: str):
        if oper == "<=" or oper == "<" or oper == ">=" or oper == ">" or oper == "==" or oper == "!=":
            return True
        else:
            return False

    def control_Ope_Aritmetic(self, oper: str):
        if oper == "+" or oper == "-" or oper == "*" or oper == "/" or oper == "%":
            return True
        else:
            return False

    def control_Ope_Assign(self , oper: str,tipe:str):
        if tipe == "numr":
            if oper == "=" or oper == "+=" or oper == "-=" or oper == "%=" or oper == "*=" or oper == "/=":
                return True
            else:
                return False
        elif tipe == "str":
            if oper == "=" or oper == "+=":
                return True
            else:
                return False
        return None
