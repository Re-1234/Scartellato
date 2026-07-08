from Transformer import *


class TranspilerC:
    TIPI_C = {
        "numr": "int",
        "lota": "bool",
        "nbruogglio": "char*",
        "lettr": "char",
        "vacant": "void",
        "burdell": "void*",
    }

    def __init__(self, tipi_risolti: dict):
        self.tipi_risolti = tipi_risolti
        self.output = []
        self.indent = 0
        self.temp_counter = 0
        self.classe_corrente = None   # serve per generare self.campo dentro i metodi

    # ── utility di stampa ────────────────────────────────────────────
    def indentazione(self, riga):
        self.output.append("    " * self.indent + riga)

    def get_output(self):
        return "\n".join(self.output)

    def nuova_temp(self):
        self.temp_counter += 1
        return f"__tmp{self.temp_counter}"

    def tipo_c(self, tipo_scart):
        return self.TIPI_C.get(str(tipo_scart), str(tipo_scart))

    def tipo_di(self, nodo):
        chiave = id(nodo)
        if chiave not in self.tipi_risolti:
            raise Exception(f"Tipo non risolto per {nodo!r}")
        return self.tipi_risolti[chiave]

    # ── dispatcher ISTRUZIONI ────────────────────────────────────────
    def visit(self, node):
        if isinstance(node, list):
            for n in node:
                self.visit(n)
            return
        if node is None:
            return
        method_name = f"visit_{node.__class__.__name__}"
        method = getattr(self, method_name, None)
        if method is None:
            raise Exception(f"Nessun generatore ISTRUZIONE per {node.__class__.__name__}")
        method(node)

    # ── dispatcher ESPRESSIONI ───────────────────────────────────────
    def espr(self, node):
        method_name = f"espr_{node.__class__.__name__}"
        method = getattr(self, method_name, None)
        if method is None:
            raise Exception(f"Nessun generatore ESPRESSIONE per {node.__class__.__name__}")
        return method(node)

    # ══════════════════════════════════════════════════════════════
    #   RADICE
    # ══════════════════════════════════════════════════════════════
    def visit_Start(self, node: Start):
        self.indentazione("#include <stdio.h>")
        self.indentazione("#include <stdbool.h>")
        self.indentazione("#include <string.h>")
        self.indentazione("#include <stdlib.h>")
        self.indentazione("")
        for decl in node.program:
            self.visit(decl)
            self.indentazione("")

    # ══════════════════════════════════════════════════════════════
    #   FUNZIONI  (e main, che è un Mestier con nome 'Uè')
    # ══════════════════════════════════════════════════════════════
    def visit_Mestier(self, node: Mestier):
        tipo_ritorno = self.tipo_c(node.ritorno)
        nome = str(node.nome.nome)

        # Capiamo se siamo nel main
        is_main = (nome == "Uè")
        if is_main:
            nome = "main"
            tipo_ritorno = "int"

        # Memorizziamo lo stato temporaneamente per le espressioni/istruzioni interne
        self.in_main = is_main

        params_parts = []
        if self.classe_corrente is not None:
            params_parts.append(f"{self.classe_corrente}* self")

        for p in node.parametri:
            params_parts.append(f"{self.tipo_c(p.tipo.nome)} {p.nome.nome}")

        params = ", ".join(params_parts)
        nome_finale = f"{self.classe_corrente}_{nome}" if self.classe_corrente else nome

        self.indentazione(f"{tipo_ritorno} {nome_finale}({params}) {{")
        self.indent += 1

        self.visit(node.corpo)

        # Aggiungiamo return 0 DI SALVATAGGIO solo se non c'è già un return alla fine
        if is_main:
            ha_return = False
            if node.corpo and hasattr(node.corpo, 'statements') and node.corpo.statements:
                if isinstance(node.corpo.statements[-1], ReturnStatement):
                    ha_return = True

            if not ha_return:
                self.indentazione("return 0;")

        self.indent -= 1
        self.indentazione("}")
        self.in_main = False  # Resettiamo lo stato

    # ══════════════════════════════════════════════════════════════
    #   CLASSI → struct + funzioni con prefisso
    # ══════════════════════════════════════════════════════════════
    def visit_Robba(self, node: Robba):
        nome_classe = str(node.nome.nome)

        # struct con i campi
        self.indentazione(f"typedef struct {{")
        self.indent += 1
        for v in node.variabili:
            tipo_c = self.tipo_c(v.tipo.nome)
            self.indentazione(f"{tipo_c} {v.nome.nome};")
        self.indent -= 1
        self.indentazione(f"}} {nome_classe};")
        self.indentazione("")

        # costruttore → funzione NomeClasse_init
        if node.costruttore is not None:
            params = ", ".join(
                f"{self.tipo_c(p.tipo.nome)} {p.nome.nome}"
                for p in node.costruttore.parametri
            )
            self.indentazione(f"{nome_classe} {nome_classe}_init({params}) {{")
            self.indent += 1
            self.indentazione(f"{nome_classe} self;")
            self.classe_corrente_init = nome_classe   # per generare "self.campo" invece di "campo"
            self.visit(node.costruttore.corpo)
            self.indentazione("return self;")
            self.indent -= 1
            self.indentazione("}")
            self.indentazione("")

        # metodi → funzioni NomeClasse_metodo(NomeClasse* self, ...)
        self.classe_corrente = nome_classe
        for f in node.funzioni:
            self.visit(f)
            self.indentazione("")
        self.classe_corrente = None

    # ══════════════════════════════════════════════════════════════
    #   BLOCCO
    # ══════════════════════════════════════════════════════════════
    def visit_Block(self, node: Block):
        for stmt in node.statements:
            self.visit(stmt)

    # ══════════════════════════════════════════════════════════════
    #   DICHIARAZIONE
    # ══════════════════════════════════════════════════════════════
    def visit_Dichiarazione(self, node: Dichiarazione):
        tipo_c = self.tipo_c(node.tipo.nome)
        nome = str(node.nome.nome)
        if node.valore is not None:
            valore = self.espr(node.valore)
            self.indentazione(f"{tipo_c} {nome} = {valore};")
        else:
            self.indentazione(f"{tipo_c} {nome};")

    # ══════════════════════════════════════════════════════════════
    #   OpBin COME ISTRUZIONE  ( = e <-> )
    # ══════════════════════════════════════════════════════════════
    def visit_OpBin(self, node: OpBin):
        if node.op == "=":
            sx = self.espr(node.left)
            dx = self.espr(node.right)
            self.indentazione(f"{sx} = {dx};")
            return

        if node.op == "<->":
            tipo = self.tipo_di(node.left)
            tipo_c = self.tipo_c(tipo)
            tmp = self.nuova_temp()
            sx = self.espr(node.left)
            dx = self.espr(node.right)
            self.indentazione(f"{tipo_c} {tmp} = {sx};")
            self.indentazione(f"{sx} = {dx};")
            self.indentazione(f"{dx} = {tmp};")
            return

        if node.op in ("++", "--"):
            sx = self.espr(node.left)
            self.indentazione(f"{sx}{node.op};")
            return

        raise Exception(f"OpBin con operatore '{node.op}' non gestito come istruzione")

    # ══════════════════════════════════════════════════════════════
    #   IF
    # ══════════════════════════════════════════════════════════════
    def visit_Mettimmca(self, node: Mettimmca):
        cond = self.espr(node.condizione)
        self.indentazione(f"if ({cond}) {{")
        self.indent += 1
        self.visit(node.allora)
        self.indent -= 1
        if node.altrimenti is not None:
            self.indentazione("} else {")
            self.indent += 1
            self.visit(node.altrimenti)
            self.indent -= 1
        self.indentazione("}")

    # ══════════════════════════════════════════════════════════════
    #   WHILE
    # ══════════════════════════════════════════════════════════════
    def visit_Aspe(self, node: Aspe):
        cond = self.espr(node.Condizione)
        self.indentazione(f"while ({cond}) {{")
        self.indent += 1
        self.visit(node.Corpo)
        self.indent -= 1
        self.indentazione("}")

    # ══════════════════════════════════════════════════════════════
    #   FOR
    # ══════════════════════════════════════════════════════════════
    def visit_Ambress_Ambress(self, node: Ambress_Ambress):
        init = self._for_init(node.dichiarazione)
        cond = self.espr(node.condizione)
        step = self._for_step(node.VarOperation)

        self.indentazione(f"for ({init}; {cond}; {step}) {{")
        self.indent += 1
        self.visit(node.Corpo)
        self.indent -= 1
        self.indentazione("}")

    def _for_init(self, dich):
        # dich è una Dichiarazione: costruiamo l'init SENZA punto e virgola finale
        tipo_c = self.tipo_c(dich.tipo.nome)
        nome = dich.nome.nome
        valore = self.espr(dich.valore)
        return f"{tipo_c} {nome} = {valore}"

    def _for_step(self, op: OpBin):
        # op è OpBin con op="++"/"--" o un normale assegnamento incrementale
        sx = self.espr(op.left)
        if op.op in ("++", "--"):
            return f"{sx}{op.op}"
        dx = self.espr(op.right)
        return f"{sx} {op.op} {dx}"

    # ══════════════════════════════════════════════════════════════
    #   RETURN
    # ══════════════════════════════════════════════════════════════
    def visit_ReturnStatement(self, node: ReturnStatement):
        if node.valore is None:
            # Se siamo nel main, un return vuoto deve sputare 0 per non far arrabbiare il GCC
            if getattr(self, "in_main", False):
                self.indentazione("return 0;")
            else:
                self.indentazione("return;")
        else:
            valore = self.espr(node.valore)
            self.indentazione(f"return {valore};")

    # ══════════════════════════════════════════════════════════════
    #   CHIAMATA COME ISTRUZIONE
    # ══════════════════════════════════════════════════════════════
    def visit_CallStmt(self, node: CallStmt):
        nome = str(node.nome_func.nome)
        args = ", ".join(self.espr(a) for a in node.args)
        self.indentazione(f"{nome}({args});")

    # ══════════════════════════════════════════════════════════════
    #   ESPRESSIONI
    # ══════════════════════════════════════════════════════════════
    def espr_Numr(self, node: Numr):
        v = node.value
        return str(int(v)) if v == int(v) else str(v)

    def espr_Boolean(self, node: Boolean):
        # node.value è un Token('BOOLEAN', 'sasicchj') o 'friariell'
        return "true" if str(node.value) == "sasicchj" else "false"

    def espr_Stringa(self, node: Stringa):
        return f'"{node.value}"'

    def espr_Carattr(self, node: Carattr):
        return f"'{node.value}'"

    def espr_Variabile(self, node: Variabile):
        return str(node.nome)

    def espr_OpBin(self, node: OpBin):
        if node.op in ("=", "<->"):
            raise Exception(f"'{node.op}' non può comparire dentro un'espressione")

        op_c = {"and": "&&", "or": "||", "not": "!"}.get(node.op, node.op)

        sx = self.espr(node.left)
        if node.right is None:
            return f"{sx}{op_c}"  # es. incremento_destro c++

        dx = self.espr(node.right)
        return f"({sx} {op_c} {dx})"

    def espr_CallStmt(self, node: CallStmt):
        nome = str(node.nome_func.nome)
        args = ", ".join(self.espr(a) for a in node.args)
        return f"{nome}({args})"