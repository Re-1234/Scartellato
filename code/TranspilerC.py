from Transformer import *

class TranspilerC:
    TIPI_C = {
        "numr": "int",
        "lota": "bool",
        "nbruogglio": "char*",
        "lettr": "char",
        "vacant": "void",
        "burdell": "Burdell",
    }

    def __init__(self, tipi_risolti: dict):
        self.tipi_risolti = tipi_risolti
        self.output = []
        self.indent = 0
        self.temp_counter = 0
        self.classe_corrente = None   # serve per generare self.campo dentro i metodi
        self.campi_classe = set()
        self.metodi_classe = set()
        self.in_costruttore = False
        self.in_main = False
        self.var_burdell = set()
        self.var_array = set()

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

        self.indentazione("typedef enum { TIPO_NUMR, TIPO_LOTA, TIPO_NBRUOGGLIO, TIPO_LETTR } TagBurdell;")
        self.indentazione("")
        self.indentazione("""
            typedef struct {
                TagBurdell tag;
                union {
                    int numr;
                    bool lota;
                    char* nbruogglio;
                    char lettr;
                } val;
            } Burdell;
            
            typedef struct {
                Burdell* dati;
                int len;
                int cap;
            } ArrayDinamico;
            
            
        """)
        self.indentazione("""Burdell burdell_da_numr(int v) {
                Burdell b; b.tag = TIPO_NUMR; b.val.numr = v; return b;
            }
            Burdell burdell_da_lota(bool v) {
                Burdell b; b.tag = TIPO_LOTA; b.val.lota = v; return b;
            }
            Burdell burdell_da_nbruogglio(char* v) {
                Burdell b; b.tag = TIPO_NBRUOGGLIO; b.val.nbruogglio = v; return b;
            }
            Burdell burdell_da_lettr(char v) {
                Burdell b; b.tag = TIPO_LETTR; b.val.lettr = v; return b;
            }
            
            char* burdell_concat(const char* s1, const char* s2) {
                if(!s1) s1 = ""; if(!s2) s2 = "";
                char* res = malloc(strlen(s1) + strlen(s2) + 1);
                strcpy(res, s1); strcat(res, s2);
                return res;
            }
            char* burdell_concat_str_num(const char* s, int n) {
                if(!s) s = "";
                char* res = malloc(strlen(s) + 32);
                sprintf(res, "%s%d", s, n);
                return res;
            }
            char* burdell_concat_num_str(int n, const char* s) {
                if(!s) s = "";
                char* res = malloc(strlen(s) + 32);
                sprintf(res, "%d%s", n, s);
                return res;
            }
            int burdell_equals(Burdell a, Burdell b) {
                if (a.tag != b.tag) return 0;
                switch (a.tag) {
                    case TIPO_NUMR: return a.val.numr == b.val.numr;
                    case TIPO_LOTA: return a.val.lota == b.val.lota;
                    case TIPO_NBRUOGGLIO: return strcmp(a.val.nbruogglio, b.val.nbruogglio) == 0;
                    case TIPO_LETTR: return a.val.lettr == b.val.lettr;
                }
                return 0;
            }
        """)
        self.indentazione("""
        void arr_init(ArrayDinamico* a) {
            a->dati = NULL; a->len = 0; a->cap = 0;
        }
        
        void arr_append(ArrayDinamico* a, Burdell v) {
            if (a->len >= a->cap) {
                a->cap = a->cap == 0 ? 4 : a->cap * 2;
                a->dati = realloc(a->dati, a->cap * sizeof(Burdell));
            }
            a->dati[a->len++] = v;
        }
        void arr_remove_value(ArrayDinamico* a, Burdell v) {
            for (int i = 0; i < a->len; i++) {
                if (burdell_uguale(a->dati[i], v)) {
                    for (int j = i; j < a->len - 1; j++) a->dati[j] = a->dati[j+1];
                    a->len--;
                    return;
                }
            }
        }
        
        """)

        for decl in node.program:
            self.visit(decl)
            self.indentazione("")

    # ══════════════════════════════════════════════════════════════
    #   FUNZIONI
    # ══════════════════════════════════════════════════════════════
    def visit_Mestier(self, node: Mestier):
        nome = str(node.nome.nome)

        if node.is_array:
            tipo_ritorno = "ArrayDinamico"
        else:
            tipo_ritorno = self.tipo_c(node.ritorno)

        is_main = (nome == "Uè")
        if is_main:
            nome = "main"
            tipo_ritorno = "int"

        self.in_main = is_main

        params_parts = []
        if self.classe_corrente is not None:
            params_parts.append(f"{self.classe_corrente}* self")

        parametri = node.parametri or []
        if isinstance(parametri, str):
            # caso "main": parametri è una stringa vuota, nessun parametro reale
            parametri = []

        for p in parametri:
            if p.tipo.nome == "burdell":
                self.var_burdell.add(str(p.nome.nome))
            params_parts.append(f"{self.tipo_c(p.tipo.nome)} {p.nome.nome}")

        params = ", ".join(params_parts)
        nome_finale = f"{self.classe_corrente}_{nome}" if self.classe_corrente else nome

        self.indentazione(f"{tipo_ritorno} {nome_finale}({params}) {{")
        self.indent += 1

        self.visit(node.corpo)

        if is_main:
            ha_return = False
            if node.corpo and hasattr(node.corpo, 'statements') and node.corpo.statements:
                if isinstance(node.corpo.statements[-1], ReturnStatement):
                    ha_return = True

            if not ha_return:
                self.indentazione("return 0;")

        self.indent -= 1
        self.indentazione("}")
        self.in_main = False

    # ══════════════════════════════════════════════════════════════
    #   CLASSI
    # ══════════════════════════════════════════════════════════════
    def visit_Robba(self, node: Robba):
        nome_classe = str(node.nome.nome)

        self.campi_classe = {v.nome.nome for v in node.variabili}
        self.metodi_classe = {str(f.nome.nome) for f in node.funzioni}
        # Impostiamo la classe corrente GIA' PRIMA del costruttore, così le
        # chiamate a metodi della stessa classe fatte dentro il costruttore
        # vengono riconosciute correttamente (vedi _risolvi_chiamata).
        self.classe_corrente = nome_classe

        self.indentazione(f"typedef struct {{")
        self.indent += 1
        for v in node.variabili:
            tipo_c = self.tipo_c(v.tipo.nome)
            self.indentazione(f"{tipo_c} {v.nome.nome};")
        self.indent -= 1
        self.indentazione(f"}} {nome_classe};")

        self.indentazione(f"// Prototipi dei metodi della classe {nome_classe}")
        for f in node.funzioni:
            if f.is_array:
                tipo_ritorno = "ArrayDinamico"
            else:
                tipo_ritorno = self.tipo_c(f.ritorno)
            nome_metodo = str(f.nome.nome)

            params_parts = [f"{nome_classe}* self"]
            for p in f.parametri:
                tipo_c_param = self.tipo_c(p.tipo.nome)
                if p.nome.is_array:
                    tipo_c_param += "*"
                params_parts.append(f"{tipo_c_param} {p.nome.nome}")
            params = ", ".join(params_parts)

            self.indentazione(f"{tipo_ritorno} {nome_classe}_{nome_metodo}({params});")
        self.indentazione("")

        if node.costruttore is not None:
            params_list = []
            for p in node.costruttore.parametri:
                tipo_c_param = self.tipo_c(p.tipo.nome)
                if p.nome.is_array:
                    tipo_c_param += "*"
                params_list.append(f"{tipo_c_param} {p.nome.nome}")
            params = ", ".join(params_list)

            self.indentazione(f"{nome_classe} {nome_classe}_init({params}) {{")
            self.indent += 1
            self.indentazione(f"{nome_classe} self;")
            self.in_costruttore = True
            self.visit(node.costruttore.corpo)
            self.in_costruttore = False
            self.indentazione("return self;")
            self.indent -= 1
            self.indentazione("}")
            self.indentazione("")

        for f in node.funzioni:
            self.visit(f)
            self.indentazione("")

        self.classe_corrente = None
        self.campi_classe = set()
        self.metodi_classe = set()

    # ══════════════════════════════════════════════════════════════
    #   BLOCCO & DICHIARAZIONE
    # ══════════════════════════════════════════════════════════════
    def visit_Block(self, node: Block):
        for stmt in node.statements:
            self.visit(stmt)

    def visit_Dichiarazione(self, node: Dichiarazione):
        nome = str(node.nome.nome)
        is_array = node.nome.is_array

        if is_array:
            self.var_array.add(nome)
            self.indentazione(f"ArrayDinamico {nome};")
            self.indentazione(f"arr_init(&{nome});")
            return  # gli array non hanno valore iniziale nel tuo linguaggio, quindi ci fermiamo qui

        if node.tipo.nome == "burdell":
            self.var_burdell.add(nome)
            tipo_c = "Burdell"
        else:
            tipo_c = self.tipo_c(node.tipo.nome)

        if node.valore is not None:
            valore = self.espr(node.valore)
            if node.tipo.nome == "burdell":
                valore = self._wrappa_burdell(node.valore)
            self.indentazione(f"{tipo_c} {nome} = {valore};")
        else:
            default = {"numr": "0", "lota": "false", "nbruogglio": '""', "lettr": "'\\0'",
                       "burdell": "burdell_da_numr(0)"}.get(node.tipo.nome, "0")
            self.indentazione(f"{tipo_c} {nome} = {default};")

    # ══════════════════════════════════════════════════════════════
    #   OpBin COME ISTRUZIONE  ( = , <-> , +=, -=, ecc. )
    # ══════════════════════════════════════════════════════════════
    def visit_OpBin(self, node: OpBin):
        if node.op == "=":
            if isinstance(node.left, Variabile):
                sx = self._accesso_base(str(node.left.nome))
            else:
                sx = self.espr(node.left)

            dx = self.espr(node.right)

            # Se a sinistra ho una var dinamica, inscatolo il lato destro
            if isinstance(node.left, Variabile) and str(node.left.nome) in self.var_burdell:
                dx = self._wrappa_burdell(node.right)

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

        if node.op in ("+=", "-=", "*=", "/=", "%="):
            if isinstance(node.left, Variabile) and str(node.left.nome) in self.var_array:
                nome_array = str(node.left.nome)
                tipo_elemento = self._calcola_tipo(node.right)
                valore_wrappato = self._wrappa_valore_per_tipo(node.right, tipo_elemento)

                if node.op == "-=":
                    self.indentazione(f"arr_append(&{nome_array}, {valore_wrappato});")
                elif node.op == "+=":
                    self.indentazione(f"arr_remove_value(&{nome_array}, {valore_wrappato});")
                else:
                    raise Exception(f"Operatore '{node.op}' non supportato sugli array")
                return

            sx = self.espr(node.left)
            dx = self.espr(node.right)

            # Usa il calcolatore infallibile per dedurre i tipi
            tipo_sx = self._calcola_tipo(node.left)
            tipo_dx = self._calcola_tipo(node.right)

            # GESTIONE SICURA DELLE STRINGHE (se dx o sx è nbruogglio)
            if tipo_sx == "nbruogglio" or tipo_dx == "nbruogglio":

                # --- APPEND (-=) : sx = sx + dx ---
                if node.op == "-=":
                    if tipo_sx == "nbruogglio" and tipo_dx == "numr":
                        self.indentazione(f"{sx} = burdell_concat_str_num({sx}, {dx});")
                    elif tipo_sx == "numr" and tipo_dx == "nbruogglio":
                        self.indentazione(f"{sx} = burdell_concat_num_str({sx}, {dx});")
                    else:
                        # Entrambi nbruogglio
                        self.indentazione(f"{sx} = burdell_concat({sx}, {dx});")
                    return

                # --- PREPEND (+=) : sx = dx + sx ---
                elif node.op == "+=":
                    if tipo_sx == "nbruogglio" and tipo_dx == "numr":
                        # Aggiungo un numero all'inizio di una stringa
                        self.indentazione(f"{sx} = burdell_concat_num_str({dx}, {sx});")
                    elif tipo_sx == "numr" and tipo_dx == "nbruogglio":
                        # Aggiungo una stringa all'inizio di un numero
                        self.indentazione(f"{sx} = burdell_concat_str_num({dx}, {sx});")
                    else:
                        # Entrambi nbruogglio, inverto l'ordine
                        self.indentazione(f"{sx} = burdell_concat({dx}, {sx});")
                    return

            # Caso base (es. numr += numr)
            self.indentazione(f"{sx} {node.op} {dx};")
            return

        raise Exception(f"OpBin con operatore '{node.op}' non gestito come istruzione")

    # ══════════════════════════════════════════════════════════════
    #   COSTRUTTI DI CONTROLLO
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

    def visit_Aspe(self, node: Aspe):
        cond = self.espr(node.Condizione)
        self.indentazione(f"while ({cond}) {{")
        self.indent += 1
        self.visit(node.Corpo)
        self.indent -= 1
        self.indentazione("}")

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
        tipo_c = self.tipo_c(dich.tipo.nome)
        nome = dich.nome.nome
        valore = self.espr(dich.valore)
        return f"{tipo_c} {nome} = {valore}"

    def _for_step(self, op: OpBin):
        sx = self.espr(op.left)
        if op.op in ("++", "--"):
            return f"{sx}{op.op}"
        dx = self.espr(op.right)
        return f"{sx} {op.op} {dx}"

    def visit_ReturnStatement(self, node: ReturnStatement):
        if node.valore is None:
            if getattr(self, "in_main", False):
                self.indentazione("return 0;")
            else:
                self.indentazione("return;")
        else:
            valore = self.espr(node.valore)
            self.indentazione(f"return {valore};")

    # ── chiamate a funzione/metodo ───────────────────────────────────
    def _risolvi_chiamata(self, node):
        """Restituisce (nome_c, lista_argomenti_c) per una CallStmt,
        aggiungendo prefisso di classe e 'self'/'&self' se la chiamata
        punta a un metodo della classe corrente."""
        nome = str(node.nome_func.nome)
        args = [self.espr(a) for a in node.args]

        if self.classe_corrente is not None and nome in self.metodi_classe:
            nome_c = f"{self.classe_corrente}_{nome}"
            self_arg = "&self" if self.in_costruttore else "self"
            args = [self_arg] + args
        else:
            nome_c = nome

        return nome_c, args

    def visit_CallStmt(self, node: CallStmt):
        nome_c, args = self._risolvi_chiamata(node)
        self.indentazione(f"{nome_c}({', '.join(args)});")

    # ══════════════════════════════════════════════════════════════
    #   ESPRESSIONI
    # ══════════════════════════════════════════════════════════════
    def espr_Numr(self, node: Numr):
        v = node.value
        return str(int(v)) if v == int(v) else str(v)

    def espr_Boolean(self, node: Boolean):
        return "true" if str(node.value) == "sasicchj" else "false"

    def espr_Stringa(self, node: Stringa):
        return f'"{node.value}"'

    def espr_Carattr(self, node: Carattr):
        return f"'{node.value}'"

    def espr_Variabile(self, node: Variabile):
        nome = str(node.nome)

        # 1. Se è burdell, gestisci lo spacchettamento (con il prefisso giusto sotto)
        if nome in self.var_burdell:
            tipo_in_questo_punto = self.tipo_di(node)
            base = self._accesso_base(nome)
            mappa = {
                "numr": f"{base}.val.numr",
                "lota": f"{base}.val.lota",
                "nbruogglio": f"{base}.val.nbruogglio",
                "lettr": f"{base}.val.lettr",
            }
            return mappa[tipo_in_questo_punto]

        # 2. Altrimenti, decidi il percorso base senza assumere self-> a priori
        return self._accesso_base(nome)

    def _accesso_base(self, nome):
        """Decide come accedere a 'nome': campo di classe (self./self->) o variabile normale."""
        if self.classe_corrente is not None and nome in self.campi_classe:
            return f"self.{nome}" if self.in_costruttore else f"self->{nome}"
        return nome

    def espr_OpBin(self, node: OpBin):
        if node.op in ("=", "<->"):
            raise Exception(f"'{node.op}' non può comparire dentro un'espressione")

        tipo_sx = self.tipo_di(node.left)
        tipo_dx = self.tipo_di(node.right) if node.right is not None else None

        # GESTIONE STRINGHE (ora usando le funzioni helper)
        if tipo_sx == "nbruogglio" and tipo_dx == "nbruogglio":
            sx = self.espr(node.left)
            dx = self.espr(node.right)
            if node.op == "==":
                return f"(strcmp({sx}, {dx}) == 0)"
            elif node.op == "!=":
                return f"(strcmp({sx}, {dx}) != 0)"
            elif node.op == "+":
                return f"burdell_concat({sx}, {dx})"

        if tipo_sx == "nbruogglio" and tipo_dx == "numr":
            sx = self.espr(node.left)
            dx = self.espr(node.right)
            if node.op == "+":
                return f"burdell_concat_str_num({sx}, {dx})"

        if tipo_sx == "numr" and tipo_dx == "nbruogglio":
            sx = self.espr(node.left)
            dx = self.espr(node.right)
            if node.op == "+":
                return f"burdell_concat_num_str({sx}, {dx})"

        # GESTIONE OPERATORI BASE
        op_c = {"and": "&&", "or": "||", "not": "!"}.get(node.op, node.op)

        sx = self.espr(node.left)
        if node.right is None:
            return f"{sx}{op_c}"

        dx = self.espr(node.right)
        return f"({sx} {op_c} {dx})"

    def espr_CallStmt(self, node: CallStmt):
        nome_c, args = self._risolvi_chiamata(node)
        return f"{nome_c}({', '.join(args)})"

    def _wrappa_burdell(self, nodo_valore):
        tipo = self.tipo_di(nodo_valore)
        valore_espr = self.espr(nodo_valore)
        mappa = {
            "numr": "burdell_da_numr",
            "lota": "burdell_da_lota",
            "nbruogglio": "burdell_da_nbruogglio",
            "lettr": "burdell_da_lettr",
        }
        return f"{mappa[tipo]}({valore_espr})"

    def _calcola_tipo(self, node):
        """Cerca il tipo nella symbol table, se non c'è lo deduce ricorsivamente."""
        if node is None:
            return None
        try:
            return self.tipo_di(node)
        except Exception:
            cls = node.__class__.__name__
            if cls == "Numr": return "numr"
            if cls == "Stringa": return "nbruogglio"
            if cls == "Boolean": return "lota"
            if cls == "Carattr": return "lettr"
            if cls == "OpBin":
                t_sx = self._calcola_tipo(node.left)
                t_dx = self._calcola_tipo(node.right)
                # Nel tuo linguaggio string + something = string
                if t_sx == "nbruogglio" or t_dx == "nbruogglio":
                    return "nbruogglio"
                return t_sx
            return None

    def _wrappa_valore_per_tipo(self, nodo_valore, tipo):
        valore_espr = self.espr(nodo_valore)
        mappa = {
            "numr": "burdell_da_numr",
            "lota": "burdell_da_lota",
            "nbruogglio": "burdell_da_nbruogglio",
            "lettr": "burdell_da_lettr",
        }
        return f"{mappa[tipo]}({valore_espr})"