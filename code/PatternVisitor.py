from SymbolTable import SymbolTable
from Transformer import Robba, Mestier, Block, ReturnStatement
from Transformer import Parametro
from SemanticError import SemanticError
from Transformer import Costruttore
from code.Transformer import Variabile


class TypeEnviroment:
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
        self.symbolTable.addId(node.nome,node)
        self.symbolTable.enterScope()

        for kid in node.parametri:
            self.visit(kid)

        self.visit(node.corpo)

        self.symbolTable.exitScope()


    def visit_Parametro(self, node: Parametro):
        # Recuperiamo il nome della variabile (visto che node.nome è un oggetto Variabile)
        nome_var = node.nome.nome
        tipo_var = node.tipo

        # Controlla se il parametro è già stato dichiarato nello scope corrente (duplicato)
        if self.symbol_table.lookup_current_scope(nome_var):
            raise SemanticError(f"Errore: Parametro duplicato '{nome_var}'")

        # Inserisce il parametro nella Symbol Table come variabile valida in questo scope
        self.symbol_table.insert(nome_var, tipo_var)


    def visit_Costruttore(self,node : Costruttore):
         self.symbolTable.addId(node.nome,node)
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
        if

        if isinstance(node.valor,Variabile):
            if self.symbolTable.lookup(node.valor) is None:
                raise SemanticError(f"Errore: Non è stata dichiarata la variabile '{node}'")
