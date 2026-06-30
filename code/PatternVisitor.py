from curses.ascii import controlnames

from lark import visitors

from SymbolTable import SymbolTable
from Transformer import Robba, Mestier, Block, ReturnStatement, GenericVar, Ambress_Ambress, OpBin
from Transformer import Parametro
from SemanticError import SemanticError
from Transformer import Costruttore
from Transformer import Variabile, Numr, Boolean, Stringa, Carattr
from Transformer import Dichiarazione, TipoDato
from code.Transformer import Assegnamento


class AnalisiSemantica:
    def __init__(self):
        self.errori = []
        symbolTable : SymbolTable
        self.tipi_risolti = {}

    def visit(self, node):
        class_name = node.__class__.__name__
        method_name = f'visit_{class_name}'
        method = getattr(self, method_name, self.generic_visit)

        risultato =method(node)
        if risultato is not None and isinstance(risultato, str):
            self.tipi_risolti[id(node)] = risultato

        return risultato

    def generic_visit(self, node):
        raise Exception(f"Nessun metodo visit_{node.__class__.__name__}")

    def errore(self, msg):
        self.errori.append(msg)

    def visit_start(self,node):
        self.symbolTable = SymbolTable()
        self.symbolTable.enterScope()

        for kid in node.children:
            self.visit(kid)

        self.symbolTable.exitScope()


    def visit_Robba(self,node :Robba):
        self.symbolTable.addId(node.nome,node)
        self.symbolTable.enterScope()

        self.visit(node.costruttore)

        for kid in node.variabili:
            self.visit(kid)

        for kid in node.funzioni:
            self.visit(kid)

        self.symbolTable.exitScope()

    def visit_Mestier(self,node: Mestier):
        #inserisce il nome della funzione nello scope precendente e
        # ne crea uno nuovo per lo scope della funzione
        self.symbolTable.addId(node.nome,node)
        self.symbolTable.enterScope()

        #visita i nodi figli riguardo alla funzione
        for kid in node.parametri:
            self.visit(kid)
            self.tipi_risolti[id(kid.nome)] = str(kid.tipo)

        self.visit(node.corpo)

        self.symbolTable.exitScope()

    def visit_Numr(self,node: Numr):
        return "Numr"

    def visit_Boolean(self , node: Boolean):
        return "Boolean"

    def visit_Stringa(self , node: Stringa):
        return "Stringa"

    def visit_GenericVar(self, nodo):
        return "burdell"

    def _compatibili(self, tipo_atteso, tipo_trovato):
        tipo_atteso = str(tipo_atteso)
        tipo_trovato = str(tipo_trovato)
        if tipo_atteso == "burdell":  # burdell = tipo generico, accetta tutto
            return True
        return tipo_atteso == tipo_trovato


    def visit_Parametro(self, node: Parametro):
        # Recuperiamo il nome della variabile (visto che node.nome è un oggetto Variabile)
        nome_var = node.nome.nome
        tipo_var = node.tipo

        # Controlla se il parametro è già stato dichiarato nello scope corrente (duplicato)
        if self.symbol_table.lookup_current_scope(nome_var):
            raise SemanticError(f"NNNNNNNNNNOOOOOOOOOOOOO ma che è fatt!!!!!: Parametro duplicato '{nome_var}'")

        # Inserisce il parametro nella Symbol Table come variabile valida in questo scope
        self.symbol_table.insert(nome_var, tipo_var)


    def visit_Costruttore(self,node : Costruttore):
         self.symbolTable.enterScope()

         for par in node.parametri:
             self.visit(par)
             self.tipi_risolti[id(par.nome)] = str(par.tipo)

         self.visit(node.corpo)
         self.symbolTable.exitScope()

    def visit_Block(self , node: Block):
        for element in node.statements:
            self.visit(element)

    #da continuare a modificare questo metodo
    def visit_ReturnStatement(self,node : ReturnStatement):
        if not isinstance(node.valor , Variabile):
            return self.visit(node.valor)
        elif self.symbolTable.lookup(node.valor) is None:
                raise SemanticError(f"Stat accort: Non è stata dichiarata la variabile '{node}'")
        return None

    #fa la visit del for che sarebbe ambress_ambress
    def visit_Ambress_Ambress(self,node : Ambress_Ambress):
        self.symbolTable.enterScope()
        self.symbolTable.addId(node.dichiarazione.nome,node.dichiarazione)

        if not isinstance(node.condizione,bool):
            raise SemanticError(f"Ma ch stai facen!!!!!: non puoi inserire una espressione che ha come risultato un valore diverso da boolean")
        self.symbolTable.exitScope()

    def visit_OpBin(self,node:OpBin):
        co = self.visit(node.left)
        ci = self.visit(node.right)

        if co == Boolean and ci == Boolean:
            if self.control_Ope_Bool(node.op):
                return "Bool"

        if co == "Numr" and ci == "Numr":
            if self.control_Ope_Aritmetic(node.op):
                return "Numr"

        if co == "Stringa" and ci == "Stringa":
            if node.op == "+":
                return "Stringa"

        raise SemanticError(
            f"MACCCCCCCCCHHHHHHHH STAI FACENNNNN!!!!!!!: i tipi delle variabili sono diversi: "
            f"a sinistra è {co} e a destra è {ci}"
        )


    def visit_Dichiarazione(self,node : Dichiarazione):

        tipo_dichiarato = node.tipo.nome  # es. "Numr", "Boolean", "Stringa"
        nome_variabile = node.nome.nome

        if node.valore is not None:
            tipo_valore = self.visit(node.valore)  # visita l'espressione, ottiene la stringa del tipo

        if self.symbolTable.probe(node.nome):
            raise SemanticError(f"Errore ")

         if not self._compatibili(tipo_dichiarato, tipo_valore):
             raise SemanticError(
                 f"Errore di tipo (riga {node.tipo.linea}, colonna {node.tipo.colonna}): "
                 f"la variabile '{nome_variabile}' è dichiarata come '{tipo_dichiarato}' "
                 f"ma le viene assegnato un valore di tipo '{tipo_valore}'")

         return None


    def visit_Assegnamento(self,node : Assegnamento):
        if(self.symbolTable.lookup(node.name) == None):
            raise SemanticError(f"NNNNNNOOOOOOOOOOOO che stai Facen: variabile {node.name}")

    def control_Ope_Bool(self,oper : str):
        if oper == "<=" or oper == "<" or oper == ">=" or oper == ">" or oper == "==" or oper == "!=":
            return True
        else:
            return False

    def control_Ope_Aritmetic(self,oper : str):
        if oper == "+" or oper == "-" or oper == "*" or oper == "/" or oper == "%":
            return True
        else:
            return False



