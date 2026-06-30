
class TranspilerC:
    def __init__(self, symbol_table):
        self.symbol_table = symbol_table
        self.output = []
        self.indent = 0

    def visit_Assegnamento(self, nodo):
        tipo = self.symbol_table.lookup_var(nodo.nome)  # cerco il tipo di x
        val = self.visit(nodo.valore)
        self.emit(f"{nodo.nome} = {val};")

    #aggiunge una riga di codice all'output rispettando l'indentazione
    def indentazione(self, riga):
        self.output.append("    " * self.indent + riga)

    # unisce tutte le righe accumulate in self.output in un'unica stringa
    def get_output(self):
        return "\n".join(self.output)