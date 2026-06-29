class SymbolTable:

    def __init__(self):
        self.table = {}
        self.stack = []

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

    def getStack(self):
        return self.stack
