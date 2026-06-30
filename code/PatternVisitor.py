from lark import visitors

from SymbolTable import SymbolTable
from Transformer import Robba, Mestier, Block, ReturnStatement, GenericVar, Ambress_Ambress
from Transformer import Parametro
from SemanticError import SemanticError
from Transformer import Costruttore
from Transformer import Variabile, Numr, Boolean, Stringa, Carattr


class AnalisiSemantica:
    symbolTable : SymbolTable

    def visit(self, node):
        class_name = node.__class__.__name__
        method_name = f'visit_{class_name}'
        method = getattr(self, method_name, self.generic_visit)
        return method(node)

    def generic_visit(self, node):
        raise Exception(f"Nessun metodo visit_{node.__class__.__name__}")

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

        self.visit(node.corpo)

        self.symbolTable.exitScope()

    def visit_Numr(self,node: Numr):
        return "Numr"

    def visit_Boolean(self , node: Boolean):
        return "Boolean"

    def visit_Stringa(self , node: Stringa):
        return "Stringa"

    def visit_GenericVar(self , node: GenericVar):
        #controllo del tipo del valore assegnato alla variabile generica
        if isinstance(node.value , float | int):
            return "Numr"
        elif isinstance(node.value , bool):
            return "Boolean"
        elif isinstance(node.value , str):
            return "Stringa"
        elif isinstance(node.value , Carattr):
            return "Carattr"
        else:
            raise SemanticError(f"Uglio ma che cazz hai miss!!!!!:Una variabile generica non puo avere valori diversi da Numr , Boolean ,Stringa , Carattr")

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

        if isinstance(node.VarOperation):

        self.symbolTable.exitScope()
