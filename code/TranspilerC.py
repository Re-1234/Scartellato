
class TranspilerC:
    def __init__(self, tipi_risolti):
        self.tipi_risolti = tipi_risolti
        self.output = []
        self.indent = 0

    TIPI_C = {
        "numr": "int",
        "lota": "bool",
        "nbruogglio": "char*",
        "lettr": "char",
        "vacant": "void",
    }

    def visit(self, node):
        if isinstance(node, list):
            for n in node:
                self.visit(n)
            return
        if node is None:
            return
        method = getattr(self, f"visit_{node.__class__.__name__}", self.generic_visit)
        return method(node)

    def generic_visit(self, node):
        raise Exception(f"Non so generare codice per {node.__class__.__name__}")

    #aggiunge una riga di codice all'output rispettando l'indentazione
    def indentazione(self, riga):
        self.output.append("    " * self.indent + riga)

    # unisce tutte le righe accumulate in self.output in un'unica stringa
    def get_output(self):
        return "\n".join(self.output)

    def tipo_di(self, nodo):
        return self.tipi_risolti[id(nodo)]

    def visit_Mestier(self, nodo):
        tipo_c = self.TIPI_C.get(str(nodo.ritorno), str(nodo.ritorno))
        nome = str(nodo.nome.nome)

        self.indentazione(f"{tipo_c} {nome}() {{")
        self.indent += 1
        self.visit(nodo.corpo)
        self.indent -= 1
        self.indentazione("}")

    def visit_Block(self, nodo):
        for stmt in nodo.statements:
            self.visit(stmt)