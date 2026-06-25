from SymbolTable import SymbolTable
from Transformer import Robba, Mestier
from Transformer import Parametro


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


    def visit_Robba(self,node):
        self.symbolTable.addId(node.nome,node)
        self.symbolTable.enterScope()

        for kid in node.program:
            self.visit(kid)

        for kid in node.funzioni:
            self.visit(kid)

        self.symbolTable.exitScope()

    def visit_Mestier(self,node):
        self.symbolTable.addId(node.nome,node)
        self.symbolTable.enterScope()

        for kid in node.parametri:
            self.visit(kid)

        for kid in node.corpo:
            self.visit(kid)

        self.symbolTable.exitScope()


    def visit_Parametro(self,node):
        node.tipo = self.visit(node)



    def 








