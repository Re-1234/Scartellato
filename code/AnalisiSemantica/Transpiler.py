from code.AnalisiSintattica.Transformer import *
from code.utility import accesso_base, calcola_tipo, risolvi_chiamata, wrappa_burdell
from code.utility import *


class Transpiler:
    TIPI_C = {
        "numr": "int",
        "lota": "bool",
        "nbruogglio": "char*",
        "lettr": "char",
        "vacant": "void",
        "burdell": "Burdell",
    }

    OPERATORI_C = {
        "-": "+",  # ADDIZIONE: '-' nel sorgente -> '+' in C
        "+": "-",  # MENO: '+' nel sorgente -> '-' in C
        "/": "*",  # MOLTIPLICA: '/' nel sorgente -> '*' in C
        "*": "/",  # DIVISIONE: '*' nel sorgente -> '/' in C

        "-=": "+=",  # ADDIZIONEUGUALE: '-=' -> '+=' in C
        "+=": "-=",  # MENOUGUALE: '+=' -> '-=' in C
        "/=": "*=",  # MOLTIPLICAUGUALE: '/=' -> '*=' in C
        "*=": "/=",  # DIVISIONEUGUALE: '*=' -> '/=' in C

        "and": "&&",
        "or": "||",
        "not": "!",
        "!!": "!",
    }

    HEADER = """
                #define MAX_ALLOCS 10000
               static void* _mem_tracker[MAX_ALLOCS];
               static int _mem_count = 0;

               static inline void* b_malloc(size_t size) {
                   void* ptr = malloc(size);
                   if (!ptr) { fprintf(stderr, "Errore fatale: Memoria esaurita!\\n"); exit(1); }
                   if (_mem_count < MAX_ALLOCS) {
                       _mem_tracker[_mem_count++] = ptr;
                   }
                   return ptr;
               }

               static inline void* b_realloc(void* old_ptr, size_t size) {
                   void* new_ptr = realloc(old_ptr, size);
                   if (!new_ptr && size > 0) { fprintf(stderr, "Errore fatale: Memoria esaurita!\\n"); exit(1); }

                   if (!old_ptr) {
                       // Se il vecchio puntatore era NULL, si comporta come una malloc
                       if (_mem_count < MAX_ALLOCS) _mem_tracker[_mem_count++] = new_ptr;
                   } else {
                       // Cerca il vecchio puntatore nel tracker e aggiornalo con la nuova posizione
                       for (int i = 0; i < _mem_count; i++) {
                           if (_mem_tracker[i] == old_ptr) {
                               _mem_tracker[i] = new_ptr;
                               return new_ptr;
                           }
                       }
                       // Se non l'ha trovato (strano ma possibile), lo aggiunge come nuovo
                       if (_mem_count < MAX_ALLOCS) _mem_tracker[_mem_count++] = new_ptr;
                   }
                   return new_ptr;
               }

               static inline void b_free(void* ptr) {
                   if (!ptr) return;
                   // Cerca il puntatore nel tracker, liberalo e setta a NULL per b_free_all
                   for (int i = 0; i < _mem_count; i++) {
                       if (_mem_tracker[i] == ptr) {
                           free(ptr);
                           _mem_tracker[i] = NULL; 
                           return;
                       }
                   }
               }

               static inline void b_free_all(void) {
                   for (int i = 0; i < _mem_count; i++) {
                       if (_mem_tracker[i]) {
                           free(_mem_tracker[i]);
                           _mem_tracker[i] = NULL;
                       }
                   }
                   _mem_count = 0;
               }



               #define ARRAY_CHUNK 50                                                
               #define DEFINE_ARRAY(TYPE, NAME, EQ)                                  \\
               typedef struct {                                                      \\
                   TYPE *data;                                                       \\
                   int size;                                                         \\
                   int capacity;                                                     \\
               } NAME##_array;                                                       \\
                                                                                       \\
               static inline void NAME##_array_init(NAME##_array *a) {               \\
                   a->data = NULL; a->size = 0; a->capacity = 0;                     \\
               }                                                                     \\
                                                                                       \\
               static inline void NAME##_array_append(NAME##_array *a, TYPE val) {   \\
                if (a->size >= a->capacity) {                                     \\
                       int new_capacity = a->capacity + ARRAY_CHUNK;                 \\
                       TYPE *temp = b_realloc(a->data, new_capacity * sizeof(TYPE));   \\
                       if (!temp) {                                                  \\
                           fprintf(stderr, "Errore: realloc fallita in %s_array!\\n", #NAME); \\
                           exit(1);                                                  \\
                       }                                                             \\
                       a->data = temp;                                               \\
                       a->capacity = new_capacity;                                   \\
                   }                                                                 \\
                   a->data[a->size++] = val;                                         \\
               }                                                                       \\
                                                                                       \\
                                                                                       \\
              static inline void NAME##_array_free(NAME##_array *a) {               \\
                   if (a->data) b_free(a->data);                                       \\
                   a->data = NULL; a->size = 0; a->capacity = 0;                     \\
               }                                                                      \\
                                                                                       \\
              static inline bool NAME##_array_contains(NAME##_array *a, TYPE val) {  \\
                   for (int i = 0; i < a->size; i++) {                                 \\
                       if (EQ(a->data[i], val))                                        \\
                           return true;                                                \\
                   }                                                                   \\
                   return false;                                                       \\
              }                                                                        

               #define EQ_NUM(a,b)  ((a) == (b))                                       
               #define EQ_STR(a,b)  (strcmp((a),(b)) == 0)                             
               #define EQ_BOOL(a,b) ((a) == (b))                                       

               DEFINE_ARRAY(int, numr, EQ_NUM)                                         
               DEFINE_ARRAY(char*, nbruogglio, EQ_STR)                                 
               DEFINE_ARRAY(bool, lota, EQ_BOOL)                                       


           typedef enum { TIPO_NUMR, TIPO_LOTA, TIPO_NBRUOGGLIO, TIPO_LETTR } TagBurdell;
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


           Burdell burdell_da_numr(int v) {
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
                       char* res = (char*)b_malloc(strlen(s1) + strlen(s2) + 1);
                       strcpy(res, s1); strcat(res, s2);
                       return res;
                   }
                   char* burdell_concat_str_num(const char* s, int n) {
                       if(!s) s = "";
                       char* res = (char*)b_malloc(strlen(s) + 32);
                       sprintf(res, "%s%d", s, n);
                       return res;
                   }
                   char* burdell_concat_num_str(int n, const char* s) {
                       if(!s) s = "";
                       char* res = (char*)b_malloc(strlen(s) + 32);
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


                      void arr_init(ArrayDinamico* a) {
                          a->dati = NULL; a->len = 0; a->cap = 0;
                      }

                      void arr_append(ArrayDinamico* a, Burdell v) {
                        if (a->len >= a->cap) {
                              int new_cap = a->cap == 0 ? 4 : a->cap * 2;
                              Burdell* temp = b_realloc(a->dati, new_cap * sizeof(Burdell));
                              if (!temp) {
                                  fprintf(stderr, "Errore: realloc fallita in ArrayDinamico!\\n");
                                  exit(1);
                              }
                              a->dati = temp;
                              a->cap = new_cap;
                          }
                          a->dati[a->len++] = v;
                      }

                       bool arr_contains(ArrayDinamico* a, Burdell v) {
                          for (int i = 0; i < a->len; i++)
                              if (burdell_equals(a->dati[i], v)) return true;
                          return false;
                      }

                      void arr_free(ArrayDinamico* a) {
                          if (a->dati) b_free(a->dati);
                          a->dati = NULL; a->len = 0; a->cap = 0;
                      }


                      """



    def __init__(self, tipi_risolti: dict, burdell_info: dict, print_types: dict):
            self.tipi_risolti = tipi_risolti
            self.burdell_info = burdell_info
            self.print_types = print_types
            self.output = []
            self.indent = 0
            self.temp_counter = 0
            self.classe_corrente = None   # serve per generare self.campo dentro i metodi
            self.campi_classe = set()
            self.metodi_classe = set()
            self.in_costruttore = False
            self.in_main = False   #controllo se siamo all'interno del main
            self.var_burdell = set()
            self.campi_burdell_classe = set()
            self.var_array = {}
            self.var_locali_shadow = set()  # nomi dichiarati localmente che oscurano campi di classe
            self.var_classe = {}
            self.var_array_puntatore = set()


    def indentazione(self, riga):
        self.output.append("    " * self.indent + riga)


    def get_output(self):
        return "\n".join(self.output)


    def nuova_temp(self):
        self.temp_counter += 1
        return f"__tmp{self.temp_counter}"


    def tipo_c(self, tipo_scart):
        # ricerca nei TIPI.C chiave - valore, se non trova la chiave, fa fallback  sul valore originale
        return self.TIPI_C.get(str(tipo_scart), str(tipo_scart))

    def tipo_di(self, nodo):
        if nodo is None:
            return None
        chiave = id(nodo)
        if chiave in self.tipi_risolti:
            return self.tipi_risolti[chiave]

        # Fallback per nodi non registrati nell'analisi semantica (es. indici di array)
        if isinstance(nodo, Variabile):
            return "numr"
        if isinstance(nodo, Numr):
            return "numr"

        return None

    def operatore_c(self, op: str) -> str:
        """Traduce l'operatore di Scartellato nel corrispondente operatore C."""
        return self.OPERATORI_C.get(op, op)


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

    def visit_Block(self, node: Block):
        for stmt in node.statements:
             self.visit(stmt)

    # ══════════════════════════════════════════════════════════════
    #   CLASSI
    # ══════════════════════════════════════════════════════════════

    def visit_Robba(self, node: Robba):
        nome_classe = str(node.nome.nome)

        self.campi_classe = {v.nome.nome for v in node.variabili}
        self.campi_burdell_classe = {v.nome.nome for v in node.variabili if v.tipo.nome == "burdell"}

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
            self.indentazione(f"{nome_classe} self = {{0}};")
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
        self.campi_burdell_classe = set()
        self.metodi_classe = set()
        self.var_locali_shadow = set()

    def visit_ChiamataOggetto(self, node: ChiamataOggetto):
        self.indentazione(f"{genera_chiamata_oggetto(self,node)};")

    def espr_ChiamataOggetto(self, node: ChiamataOggetto):
        return genera_chiamata_oggetto(self,node)

    def espr_Variabile(self, node: Variabile):
            nome_var = str(node.nome)

            if node.is_array and node.index != -1:
                indice_c = self.espr(node.index) if hasattr(node.index, '__class__') and not isinstance(node.index,(int, str)) else str(  node.index)
                accesso = "->" if nome_var in self.var_array_puntatore else "."
                return f"{nome_var}{accesso}data[{indice_c}]"

            base = accesso_base(self, nome_var)
            if self.burdell_info.get(id(node), False):
                tipo_corrente = self.tipo_di(node)
                return f"{base}.val.{tipo_corrente}"
            return base

    def visit_Dichiarazione(self, node: Dichiarazione):
        nome = str(node.nome.nome)
        is_array = node.nome.is_array

        if self.classe_corrente is not None and nome in self.campi_classe:
            self.var_locali_shadow.add(nome)

        if is_array:
            tipo_elemento = node.tipo.nome
            self.var_array[nome] = tipo_elemento  # ← nota: ora è un DICT, non un set

            if tipo_elemento == "burdell":
                self.indentazione(f"ArrayDinamico {nome};")
                self.indentazione(f"arr_init(&{nome});")   #inizializza i valori  di default
            else:
                self.indentazione(f"{tipo_elemento}_array {nome};")
                self.indentazione(f"{tipo_elemento}_array_init(&{nome});") #inizializza i valori di default
            return

        tipo_dichiarato = node.tipo.nome

        if tipo_dichiarato == "burdell":
            tipo_c = "Burdell"

        elif tipo_dichiarato not in self.TIPI_C:
            self.var_classe[nome] = tipo_dichiarato
            tipo_c = tipo_dichiarato
        else:
            tipo_c = self.tipo_c(tipo_dichiarato) # traduzione del tipo



        if node.valore is not None:
            if isinstance(node.valore, ChiamataCostruttore):
                valore = genera_chiamata_costruttore(self,node.valore, tipo_dichiarato)
            else:
                valore = self.espr(node.valore)
                if node.tipo.nome == "burdell":
                    valore = wrappa_burdell(self,node.valore)
            self.indentazione(f"{tipo_c} {nome} = {valore};")
        else:
            default = {"numr": "0", "lota": "false", "nbruogglio": '""', "lettr": "'\\0'",
                       "burdell": "burdell_da_numr(0)"}.get(node.tipo.nome, "0")
            self.indentazione(f"{tipo_c} {nome} = {default};")

    def _genera_prototipo_mestier(self, node: Mestier):
        nome = str(node.nome.nome)

        if node.is_array:
            tipo_ritorno = "ArrayDinamico" if node.ritorno == "burdell" else f"{node.ritorno}_array"
        else:
            tipo_ritorno = self.tipo_c(node.ritorno)

        parametri = node.parametri or []
        if isinstance(parametri, str):
            parametri = []

        params_parts = []
        for p in parametri:
            nome_p = str(p.nome.nome)
            # Verifichiamo se il parametro è un array usando getattr per sicurezza
            if getattr(p.nome, 'is_array', False):
                tipo_elem = p.tipo.nome
                tipo_c_param = f"{tipo_elem}_array*" if tipo_elem != "burdell" else "ArrayDinamico*"
            else:
                tipo_c_param = self.tipo_c(p.tipo.nome)
            params_parts.append(f"{tipo_c_param} {nome_p}")

        params = ", ".join(params_parts)
        self.indentazione(f"{tipo_ritorno} {nome}({params});")

    def visit_Mestier(self, node: Mestier):
        nome = str(node.nome.nome)  # nome della funzione

        if node.is_array:
            # se non è un array Burdell allora è uno dei casi dell'header
            tipo_ritorno = "ArrayDinamico" if node.ritorno == "burdell" else f"{node.ritorno}_array"
        else:
            tipo_ritorno = self.tipo_c(node.ritorno)

        is_main = (nome == "Uè")  # true se siamo nel main
        if is_main:
            nome = "main"
            tipo_ritorno = "int"

        self.in_main = is_main

        # ---- parametri  ----
        params_parts = []
        if self.classe_corrente is not None:  # se assegnato allora ci troviamo nella classe
            params_parts.append(f"{self.classe_corrente}* self")

        parametri = node.parametri or []
        if isinstance(parametri, str):
            parametri = []

        for p in parametri:
            if p.nome.is_array:
                self.var_array[str(p.nome.nome)] = p.tipo.nome
                self.var_array_puntatore.add(str(p.nome.nome))

        for p in parametri:
            if p.nome.is_array:
                tipo_elem = self.var_array.get(str(p.nome.nome), p.tipo.nome)
                tipo_c_param = f"{tipo_elem}_array*" if tipo_elem != "burdell" else "ArrayDinamico*"
            else:
                tipo_c_param = self.tipo_c(p.tipo.nome)
            params_parts.append(f"{tipo_c_param} {p.nome.nome}")

        params = ", ".join(params_parts)
        nome_finale = f"{self.classe_corrente}_{nome}" if self.classe_corrente else nome

        self.indentazione(f"{tipo_ritorno} {nome_finale}({params}) {{")
        self.indent += 1

        # ---- corpo ----

        if is_main:
            self.indentazione("atexit(b_free_all);")

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
        self.var_array_puntatore = set()

    # ══════════════════════════════════════════════════════════════
    #   OpBin COME ISTRUZIONE  ( = , <-> , +=, -=, ecc. )
    # ══════════════════════════════════════════════════════════════
    def visit_OpBin(self, node: OpBin):
        if node.op == "=":
            is_lato_sx_burdell = False
            if isinstance(node.left, Variabile):
                is_lato_sx_burdell = self.burdell_info.get(id(node.left), False)
                if is_lato_sx_burdell:
                    # assegnamento all'INTERA struct Burdell, non al campo .val.xxx
                    sx = accesso_base(self, str(node.left.nome))
                else:
                    sx = self.espr(node.left)
            else:
                sx = self.espr(node.left)

            dx = self.espr(node.right)
            tipo_sx = calcola_tipo(self, node.left)
            tipo_dx = calcola_tipo(self, node.right)

            if is_lato_sx_burdell:
                dx = f"burdell_da_{tipo_dx}({dx})"
            elif tipo_sx == "nbruogglio" and tipo_dx == "numr":
                dx = f'burdell_concat_num_str({dx}, "")'

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
                tipo_elemento = self.var_array[nome_array]

                if tipo_elemento == "burdell":
                    valore_wrappato = wrappa_burdell(self,node.right)
                    if node.op == "-=":
                        self.indentazione(f"arr_append(&{nome_array}, {valore_wrappato});")
                    elif node.op == "+=":
                        self.indentazione(
                            f'if (!arr_contains(&{nome_array}, {valore_wrappato})) {{ '
                            f'fprintf(stderr, "Elemento non presente nell\\\'array\\n"); exit(1); }}'
                        )
                    return

                else:
                    valore_espr = self.espr(node.right)
                    if node.op == "-=":
                        self.indentazione(f"{tipo_elemento}_array_append(&{nome_array}, {valore_espr});")
                        return

                    elif node.op == "+=":
                        self.indentazione(
                            f'if (!{tipo_elemento}_array_contains(&{nome_array}, {valore_espr})) {{ '
                            f'fprintf(stderr, "Elemento non presente nell\\\'array\\n"); exit(1); }}'
                        )
                        return

            tipo_sx = calcola_tipo(self, node.left)
            tipo_dx = calcola_tipo(self, node.right)

            # ECCO LA MODIFICA CHIAVE! Usiamo l'helper per riconoscere sia i burdell locali che di classe.
            sx_is_burdell = isinstance(node.left, Variabile) and self.burdell_info.get(id(node.left), False)

            sx = self.espr(node.left)  # se burdell: già "z.val.nbruogglio" grazie alla nuova espr_Variabile
            dx = self.espr(node.right)

            # GESTIONE STRINGHE
            if tipo_sx == "nbruogglio" and tipo_dx == "nbruogglio":
                sx = self.espr(node.left)
                dx = self.espr(node.right)
                if node.op == "==":
                    return f"(strcmp({sx}, {dx}) == 0)"
                elif node.op == "!=":
                    return f"(strcmp({sx}, {dx}) != 0)"
                elif node.op == "<":
                    return f"(strcmp({sx}, {dx}) < 0)"
                elif node.op == ">":
                    return f"(strcmp({sx}, {dx}) > 0)"
                elif node.op == "<=":
                    return f"(strcmp({sx}, {dx}) <= 0)"
                elif node.op == ">=":
                    return f"(strcmp({sx}, {dx}) >= 0)"
                elif node.op == "-":  # In Scartellato '-' è l'addizione/concatenazione
                    return f"burdell_concat({sx}, {dx})"

            # Caso base (es. numr += numr)
            op_c = self.operatore_c(node.op)
            self.indentazione(f"{sx} {op_c} {dx};")
            return
        raise Exception(f"OpBin con operatore '{node.op}' non gestito come istruzione")

    def espr_OpBin(self, node: OpBin):
        if node.op in ("=", "<->"):
            raise Exception(f"'{node.op}' non può comparire dentro un'espressione")

        if node.left is None:  # operatore prefisso unario (es. !!, not)
            dx = self.espr(node.right)
            op_c = self.operatore_c(node.op)
            return f"{op_c}({dx})"

        tipo_sx = self.tipo_di(node.left)
        tipo_dx = self.tipo_di(node.right) if node.right is not None else None

        # GESTIONE STRINGHE
        if tipo_sx == "nbruogglio" and tipo_dx == "nbruogglio":
            sx = self.espr(node.left)
            dx = self.espr(node.right)
            if node.op == "==":
                return f"(strcmp({sx}, {dx}) == 0)"
            elif node.op == "!=":
                return f"(strcmp({sx}, {dx}) != 0)"
            elif node.op == "+":  # In Scartellato '+' è l'addizione/concatenazione
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

        # GESTIONE OPERATORI BASE CON TRADUZIONE IN C
        op_c = self.operatore_c(node.op)

        sx = self.espr(node.left)
        if node.right is None:
            return f"{sx}{op_c}"

        dx = self.espr(node.right)
        return f"({sx} {op_c} {dx})"



    # ══════════════════════════════════════════════════════════════
    #   RADICE
    # ══════════════════════════════════════════════════════════════

    def visit_Start(self, node: Start):
        self.indentazione("#include <stdio.h>")
        self.indentazione("#include <stdbool.h>")
        self.indentazione("#include <string.h>")
        self.indentazione("#include <stdlib.h>")
        self.indentazione("")

        self.indentazione(self.HEADER)


        for decl in node.program:
            if isinstance(decl, Mestier) and str(decl.nome.nome) != "Uè":
                self._genera_prototipo_mestier(decl)
        self.indentazione("")

        for decl in node.program:
            self.visit(decl)
            self.indentazione("")



    def visit_Break(self, node):
        self.indentazione("break;\n")

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
        op_c = self.operatore_c(op.op)
        dx = self.espr(op.right)
        return f"{sx} {op_c} {dx}"

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

    def visit_CallStmt(self, node: CallStmt):
        nome_c, args = risolvi_chiamata(self,node)
        self.indentazione(f"{nome_c}({', '.join(args)});")

    #per le espressioni chiamata durante le assegnazioni
    def espr_CallStmt(self, node: CallStmt):
        nome_c, args = risolvi_chiamata(self, node)
        return f"{nome_c}({', '.join(args)})"

    def visit_Arape_a_vocca(self, node: Arape_a_vocca):
        """ Genera un UNICO printf in C unendo le stringhe fisse """

        stringa_formato = ""
        argomenti_c = []

        # 1. Prendiamo il primo pezzo di testo (se presente)
        if getattr(node, 'valore', None) is not None:
            # Puliamo i punti interrogativi
            testo_pulito = str(node.valore).replace("??", "")
            stringa_formato += testo_pulito

        # 2. Iteriamo su tutti gli altri elementi (variabili o altre stringhe)
        if getattr(node, 'variabili', None):
            for var in node.variabili:
                # Otteniamo come si scriverebbe in C (es. "d", oppure '"valore di test "')
                valore_c = self.espr(var)

                # TRUCCO: Se il valore valutato è racchiuso tra virgolette, è una stringa fissa!
                if valore_c.startswith('"') and valore_c.endswith('"'):
                    testo_fisso = valore_c[1:-1]
                    testo_fisso = testo_fisso.replace("%", "%%")

                    # CONTROLLO SPAZIATURE ---
                    # Se la stringa di formato ha già qualcosa, non finisce con spazio,
                    # e il nuovo testo non inizia con spazio, inseriamo uno spazio in mezzo.
                    if stringa_formato and not stringa_formato.endswith(" ") and not testo_fisso.startswith(" "):
                        stringa_formato += " "

                    stringa_formato += testo_fisso

                else:
                    # È una VERA variabile
                    tipo = self.print_types.get(id(var))

                    # --- NUOVO CONTROLLO SPAZIATURE PER LE VARIABILI ---
                    if stringa_formato and not stringa_formato.endswith(" "):
                        stringa_formato += " "

                    if tipo == "numr":
                        stringa_formato += "%d"
                        argomenti_c.append(valore_c)
                    elif tipo == "nbruogglio":
                        stringa_formato += "%s"
                        argomenti_c.append(valore_c)

                    elif tipo == "lettr":
                        stringa_formato += "%c"
                        argomenti_c.append(valore_c)

                    elif tipo == "lota":
                        stringa_formato += "%s"
                        # Traduciamo in true/false letterale come in Java
                        argomenti_c.append(f"({valore_c}) ? \"true\" : \"false\"")

                    elif tipo == "burdell":
                        stringa_formato += "%s"
                        argomenti_c.append(f"burdell_a_stringa({valore_c})")

                    else:
                        # Fallback di sicurezza
                        stringa_formato += "%s"
                        argomenti_c.append(valore_c)

        # Aggiungiamo il rinvio a capo finale
        stringa_formato += "\\n"

        # 3. Generiamo la riga C finale
        if argomenti_c:
            tutti_gli_argomenti = ", ".join(argomenti_c)
            self.indentazione(f'printf("{stringa_formato}", {tutti_gli_argomenti});')
        else:
            # Stampa puramente testuale se alla fine non ci sono variabili
            self.indentazione(f'printf("{stringa_formato}");')
        self.indentazione('fflush(stdout);')

    def visit_Ric(self, node: Ric):
        """ Genera la scanf in C per le variabili da leggere """

        stringa_formato = ""
        argomenti_c = []

        if getattr(node, 'variabile', None):
            variabili = node.variabile if isinstance(node.variabile, list) else [node.variabile]

            for var in variabili:
                valore_c = self.espr(var) if hasattr(self, 'espr') else self.visit(var)

                # 1. RECUPERO DEL NOME DELLA VARIABILE COME STRINGA (es. "v")
                nome_var = str(var.nome) if hasattr(var, 'nome') else str(var)

                # 2. RECUPERO ROBUSTO DEL TIPO
                tipo = self.print_types.get(id(var))

                if not tipo and hasattr(self, 'tabella_simboli'):
                    simbolo = self.tabella_simboli.get(nome_var)

                    # Se la tabella dei simboli contiene un oggetto (es. simbolo.tipo)
                    if hasattr(simbolo, 'tipo'):
                        tipo = simbolo.tipo
                    elif isinstance(simbolo, str):
                        tipo = simbolo

                if stringa_formato:
                    stringa_formato += " "

                # 3. MAPPATURA DEI TIPI PER SCANF
                if tipo == "nbruogglio":
                    # Per le stringhe in C (%s): NESSUNA '&'
                    stringa_formato += "%s"
                    argomenti_c.append(valore_c)

                elif tipo == "numr":
                    stringa_formato += "%d"
                    argomenti_c.append(f"&{valore_c}")

                elif tipo == "lettr":
                    stringa_formato += " %c"
                    argomenti_c.append(f"&{valore_c}")

                elif tipo == "lota":
                    stringa_formato += "%d"
                    argomenti_c.append(f"&{valore_c}")

                else:
                    # FALLBACK SE IL TIPO NON È STATO TROVATO
                    # Se il nome della variabile è "v" o contiene "str", forziamo %s
                    stringa_formato += "%d"
                    argomenti_c.append(f"&{valore_c}")

        if argomenti_c:
            tutti_gli_argomenti = ", ".join(argomenti_c)
            self.indentazione(f'scanf("{stringa_formato}", {tutti_gli_argomenti});') # ══════════════════════════════════════════════════════════════
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

    def espr_AccessoCampo(self, node):
        nome_var = str(node.variabile.nome)
        nome_campo = str(node.campo.nome)
        base = accesso_base(self,nome_var)
        return f"{base}.{nome_campo}"
