class SymbolTable:
    def __init__(self):
        self.table = {}
        self.stack = []
        self.pending_globali = {}

    def enterScope(self):
        self.stack.append(self.table)
        self.table = {}

    def exitScope(self):
       self.table = self.stack.pop()

    def addId(self, symbol,name):
        self.table[symbol] = name

    def lookup(self, symbol):
        if symbol in self.table:
            return self.table[symbol]
        for scope in reversed(self.stack):
            if symbol in scope:
                return scope[symbol]
        return None

    def probe(self, symbol):
        if symbol in self.table:
            return True
        else:
            return False

    def getScope(self):
        return self.table

    def declare_pending(self, symbol, firma=None):
        self.table[symbol] = {'firma': firma, 'pending': True}
        self.pending_globali[symbol] = True

    def resolve_pending(self, symbol, nodo_funzione):
        if symbol in self.table:
            self.table[symbol] = nodo_funzione
        else:
            for scope in reversed(self.stack):
                if symbol in scope:
                    scope[symbol] = nodo_funzione
                    break
        self.pending_globali.pop(symbol, None)

    def check_pending(self):
        return list(self.pending_globali.keys())

    def getStack(self):
        return self.stack

    def printTable(self):
        print("[SYMBOL TABLE]")
        # stampa tutti gli scope nello stack (dal più esterno al più interno)
        for i, scope in enumerate(self.stack):
            print(f"  scope {i} (esterno): {scope}")
        # stampa lo scope corrente (il più interno)
        print(f"  scope {len(self.stack)} (corrente): {self.table}")

    def __str__(self):
        return f"SymbolicTable" + f"[table = {self.table}, stack = {self.stack}]"

    def update(self, symbol, name):
        """Aggiorna il valore associato a 'symbol' nello scope in cui è STATO TROVATO,
           risalendo la pila se necessario — non crea mai una nuova voce."""
        if symbol in self.table:
            self.table[symbol] = name
            return True
        for scope in reversed(self.stack):
            if symbol in scope:
                scope[symbol] = name
                return True
        return False

    def is_array(self, symbol):
        val = self.lookup(symbol)
        return isinstance(val, dict) and val.get('is_array', False)
