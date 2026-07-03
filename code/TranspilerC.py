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

    def indentazione(self, riga):
        self.output.append("    " * self.indent + riga)

    def get_output(self):
        return "\n".join(self.output)

    def tipo_di(self, nodo):
        return self.tipi_risolti[id(nodo)]

    def nuova_temp(self):
        self.temp_counter += 1
        return f"__tmp{self.temp_counter}"

    def tipo_c(self, tipo_scart):
        return self.TIPI_C.get(str(tipo_scart), str(tipo_scart))

    # ── dispatcher per ISTRUZIONI (scrivono in output, non ritornano) ──
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

    # ── dispatcher per ESPRESSIONI (ritornano stringhe) ─────────────
    def visita_espr(self, node):
        method = getattr(self, f"visita_espr_{node.__class__.__name__}", None)
        if method is None:
            raise Exception(f"Non so generare espressione per {node.__class__.__name__}")
        return method(node)

    # ── radice ────────────────────────────────────────────────────
    def visit_Start(self, node):
        self.indentazione("#include <stdio.h>")
        self.indentazione("#include <stdbool.h>")
        self.indentazione("#include <string.h>")
        self.indentazione("")
        for decl in node.program:
            self.visit(decl)
            self.indentazione("")

    # ── funzioni ──────────────────────────────────────────────────
    def visit_Mestier(self, node: Mestier):
        tipo_ritorno = self.tipo_c(node.ritorno)
        nome = str(node.nome.nome)
        if nome == "Uè":
            nome = "main"

        params = ", ".join(
            f"{self.tipo_c(p.tipo)} {p.nome.nome}"
            for p in node.parametri
        )

        self.indentazione(f"{tipo_ritorno} {nome}({params}) {{")
        self.indent += 1
        self.visit(node.corpo)
        self.indent -= 1
        self.indentazione("}")

    def visit_Parametro(self, node):
        pass  # gestito inline dentro visit_Mestier/visit_Costruttore

    # ── classi → struct + funzioni con prefisso ─────────────────────
    def visit_Robba(self, node: Robba):
        nome_classe = str(node.nome.nome)

        self.indentazione(f"typedef struct {{")
        self.indent += 1
        for v in node.variabili:
            tipo_c = self.tipo_c(v.tipo)
            self.indentazione(f"{tipo_c} {v.nome.nome};")
        self.indent -= 1
        self.indentazione(f"}} {nome_classe};")
        self.indentazione("")

        if node.costruttore:
            params = ", ".join(
                f"{self.tipo_c(p.tipo)} {p.nome.nome}"
                for p in node.costruttore.params
            )
            self.indentazione(f"{nome_classe} {nome_classe}_init({params}) {{")
            self.indent += 1
            self.indentazione(f"{nome_classe} self;")
            self.visit(node.costruttore.corpo)
            self.indentazione("return self;")
            self.indent -= 1
            self.indentazione("}")
            self.indentazione("")

        for f in node.funzioni:
            tipo_ritorno = self.tipo_c(f.ritorno)
            nome_metodo = str(f.nome.nome)
            params = ", ".join(
                f"{self.tipo_c(p.tipo)} {p.nome.nome}"
                for p in f.parametri
            )
            firma = f"{nome_classe}* self" + (f", {params}" if params else "")
            self.indentazione(f"{tipo_ritorno} {nome_classe}_{nome_metodo}({firma}) {{")
            self.indent += 1
            self.visit(f.corpo)
            self.indent -= 1
            self.indentazione("}")
            self.indentazione("")

    # ── blocco ────────────────────────────────────────────────────
    def visit_Block(self, node: Block):
        for stmt in node.statements:
            self.visit(stmt)

    # ── dichiarazione ─────────────────────────────────────────────
    def visit_Dichiarazione(self, node: Dichiarazione):
        tipo_c = self.tipo_c(node.tipo.nome)
        nome = str(node.nome.nome)
        if node.valore is not None:
            valore = self.visita_espr(node.valore)
            self.indentazione(f"{tipo_c} {nome} = {valore};")
        else:
            self.indentazione(f"{tipo_c} {nome};")

    # ── assegnamento ──────────────────────────────────────────────
    def visit_Assegnamento(self, node: Assegnamento):
        valore = self.visita_espr(node.value)
        self.indentazione(f"{node.name} = {valore};")

    # ── swap (usa tipo_di!) ──────────────────────────────────────
    def visit_swap(self, node):
        # assumendo un nodo dedicato per lo swap con left/right come oggetti Variabile
        tipo = self.tipo_di(node.left)
        tipo_c = self.tipo_c(tipo)
        tmp = self.nuova_temp()
        sx = node.left.nome
        dx = node.right.nome
        self.indentazione(f"{tipo_c} {tmp} = {sx};")
        self.indentazione(f"{sx} = {dx};")
        self.indentazione(f"{dx} = {tmp};")

    # ── if ────────────────────────────────────────────────────────
    def visit_Mettimmca(self, node: Mettimmca):
        cond = self.visita_espr(node.condizione)
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

    # ── while ─────────────────────────────────────────────────────
    def visit_Aspe(self, node: Aspe):
        cond = self.visita_espr(node.Condizione)
        self.indentazione(f"while ({cond}) {{")
        self.indent += 1
        self.visit(node.Corpo)
        self.indent -= 1
        self.indentazione("}")

    # ── for ───────────────────────────────────────────────────────
    def visit_Ambress_Ambress(self, node: Ambress_Ambress):
        # genera init/step come frammenti senza il punto e virgola finale del ciclo for classico
        init = self._genera_init_for(node.dichiarazione)
        cond = self.visita_espr(node.condizione)
        step = self._genera_step_for(node.VarOperation)

        self.indentazione(f"for ({init}; {cond}; {step}) {{")
        self.indent += 1
        self.visit(node.Corpo)
        self.indent -= 1
        self.indentazione("}")

    def _genera_init_for(self, dich):
        tipo_c = self.tipo_c(dich.tipo.nome)
        nome = dich.nome.nome
        valore = self.visita_espr(dich.valore)
        return f"{tipo_c} {nome} = {valore}"

    def _genera_step_for(self, op):
        # op è un OpBin con op="++" o simile, con left come Variabile
        nome = op.left.nome
        if op.op in ("++",):
            return f"{nome}++"
        if op.op in ("--",):
            return f"{nome}--"
        return f"{nome} {op.op} {self.visita_espr(op.right)}"

    # ── return ────────────────────────────────────────────────────
    def visit_ReturnStatement(self, node: ReturnStatement):
        if node.valore is None:
            self.indentazione("return;")
        else:
            valore = self.visita_espr(node.valore)
            self.indentazione(f"return {valore};")

    # ── chiamata come istruzione standalone ─────────────────────────
    def visit_CallStmt(self, node: CallStmt):
        nome = str(node.nome_func.nome)
        args = ", ".join(self.visita_espr(a) for a in node.args)
        self.indentazione(f"{nome}({args});")

    # ══════════════════════════════════════════════════════════════
    #  ESPRESSIONI — ritornano stringhe
    # ══════════════════════════════════════════════════════════════

    def visita_espr_Numr(self, node):
        return str(node.value if node.value != int(node.value) else int(node.value))

    def visita_espr_Boolean(self, node):
        return "true" if node.value else "false"

    def visita_espr_Stringa(self, node):
        return f'"{node.value}"'

    def visita_espr_Carattr(self, node):
        return f"'{node.value}'"

    def visita_espr_Variabile(self, node):
        return str(node.nome)

    def visita_espr_OpBin(self, node):
        op_c = {"and": "&&", "or": "||", "not": "!"}.get(node.op, node.op)
        sx = self.visita_espr(node.left)
        if node.right is None:
            return f"{op_c}{sx}"
        dx = self.visita_espr(node.right)
        return f"({sx} {op_c} {dx})"

    def visita_espr_CallStmt(self, node):
        nome = str(node.nome_func.nome)
        args = ", ".join(self.visita_espr(a) for a in node.args)
        return f"{nome}({args})"