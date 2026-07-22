"""Modulo Transpiler per la traduzione dell'Abstract Syntax Tree (AST) in codice C.

Questo modulo definisce la classe `Transpiler`, responsabile di percorrere l'AST
prodotto dal parser e tradurre ogni nodo nel corrispondente codice sorgente C,
gestendo tipi di dato, allocazione memoria, strutture e funzioni.
"""

from code.AnalisiSintattica.Transformer import *
from code.utility import accesso_base, calcola_tipo, risolvi_chiamata, wrappa_burdell
from code.utility import *


class Transpiler:
    """Traduttore da AST del linguaggio sorgente a codice C nativo.

    La classe trasforma le strutture sintattiche del dialetto in codice C valido,
    gestendo le conversioni di tipo, la generazione di macro per array dinamici,
    la gestione delle classi tramite `struct` e la gestione della memoria.

    Attributes:
        TIPI_C (dict): Mappatura dai tipi del linguaggio ai tipi C corrispondenti.
        PAROLE_RISERVATE_C (set): Insieme delle parole chiave del linguaggio C.
        OPERATORI_C (dict): Mappatura e inversione degli operatori aritmetici/logici.
        HEADER (str): Definizione del codice C di supporto (gc base, array dinamici, Burdell).
    """

    # --- MAPPATURA DEI TIPI DI DATO ---
    TIPI_C = {
        "numr": "int",  # Interi
        "lota": "bool",  # Booleani
        "nbruogglio": "char*",  # Stringhe (puntatori a carattere)
        "lettr": "char",  # Caratteri singoli
        "vacant": "void",  # Vuoto / Nessun valore di ritorno
        "burdell": "Burdell",  # Tipo dinamico / eterogeneo
    }

    # --- PAROLE RISERVATE DEL C ---
    PAROLE_RISERVATE_C = {
        "auto", "break", "case", "char", "const", "continue", "default", "do",
        "double", "else", "enum", "extern", "float", "for", "goto", "if",
        "inline", "int", "long", "register", "restrict", "return", "short",
        "signed", "sizeof", "static", "struct", "switch", "typedef", "union",
        "unsigned", "void", "volatile", "while", "_Bool", "_Complex", "_Imaginary",
        "bool", "true", "false"
    }

    # --- MAPPATURA E INVERSIONE OPERATORI ---
    OPERATORI_C = {
        "-": "+",  # Inversione intenzionale dell'addizione/sottrazione
        "+": "-",
        "/": "*",  # Inversione intenzionale della moltiplicazione/divisione
        "*": "/",

        "-=": "+=",
        "+=": "-=",
        "/=": "*=",
        "*=": "/=",

        "and": "&&",
        "or": "||",
        "not": "!",
        "!!": "!",
    }

    # --- HEADER C INIETTATO ALL'INIZIO ---
    HEADER = """
               // --- GESTIONE E TRACCIAMENTO MEMORIA ALLOCATA ---
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
                       if (_mem_count < MAX_ALLOCS) _mem_tracker[_mem_count++] = new_ptr;
                   } else {
                       for (int i = 0; i < _mem_count; i++) {
                           if (_mem_tracker[i] == old_ptr) {
                               _mem_tracker[i] = new_ptr;
                               return new_ptr;
                           }
                       }
                       if (_mem_count < MAX_ALLOCS) _mem_tracker[_mem_count++] = new_ptr;
                   }
                   return new_ptr;
               }

               static inline void b_free(void* ptr) {
                   if (!ptr) return;
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


               // --- MACRO PER DEFINIZIONE ARRAY DINAMICI IN C ---
               #define ARRAY_CHUNK 50                                                
               #define DEFINE_ARRAY(TYPE, NAME, EQ)                                  \\
               typedef struct {                                                      \\
                   TYPE *dati;                                                       \\
                   int size;                                                         \\
                   int capacity;                                                     \\
               } NAME##_array;                                                       \\
                                                                                       \\
               static inline void NAME##_array_init(NAME##_array *a) {               \\
                   a->dati = NULL; a->size = 0; a->capacity = 0;                     \\
               }                                                                     \\
                                                                                       \\
               static inline void NAME##_array_append(NAME##_array *a, TYPE val) {   \\
                if (a->size >= a->capacity) {                                     \\
                       int new_capacity = a->capacity + ARRAY_CHUNK;                 \\
                       TYPE *temp = b_realloc(a->dati, new_capacity * sizeof(TYPE));   \\
                       if (!temp) {                                                  \\
                           fprintf(stderr, "Errore: realloc fallita in %s_array!\\n", #NAME); \\
                           exit(1);                                                  \\
                       }                                                             \\
                       a->dati = temp;                                               \\
                       a->capacity = new_capacity;                                   \\
                   }                                                                 \\
                   a->dati[a->size++] = val;                                         \\
               }                                                                       \\
                                                                                       \\
              static inline void NAME##_array_free(NAME##_array *a) {               \\
                   if (a->dati) b_free(a->dati);                                       \\
                   a->dati = NULL; a->size = 0; a->capacity = 0;                     \\
               }                                                                      \\
                                                                                       \\
              static inline bool NAME##_array_contains(NAME##_array *a, TYPE val) {  \\
                   for (int i = 0; i < a->size; i++) {                                 \\
                       if (EQ(a->dati[i], val))                                        \\
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


               // --- STRUCT E FUNZIONI TIPO DINAMICO (Burdell) ---
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

               char* burdell_concat_str_char(const char* s, char c) {
                   if(!s) s = "";
                   size_t len = strlen(s);
                   char* res = (char*)b_malloc(len + 2);
                   strcpy(res, s);
                   res[len] = c;
                   res[len + 1] = '\\0';
                   return res;
               }

               char* burdell_concat_char_str(char c, const char* s) {
                   if(!s) s = "";
                   size_t len = strlen(s);
                   char* res = (char*)b_malloc(len + 2);
                   res[0] = c;
                   strcpy(res + 1, s);
                   return res;
               }
               """

    def __init__(self, tipi_risolti: dict, burdell_info: dict, print_types: dict):
        """Inizializza il Transpiler con i dati ricavati dall'analisi semantica.

        Args:
            tipi_risolti (dict): Dizionario contenente i tipi risolti associati agli ID dei nodi.
            burdell_info (dict): Mappa che indica quali nodi sono gestiti come tipo 'Burdell'.
            print_types (dict): Mappa per la determinazione del formato di stampa dei nodi.
        """
        self.tipi_risolti = tipi_risolti
        self.burdell_info = burdell_info
        self.print_types = print_types
        self.output = []
        self.indent = 0
        self.temp_counter = 0
        self.classe_corrente = None
        self.campi_classe = set()
        self.metodi_classe = set()
        self.in_costruttore = False
        self.in_main = False
        self.var_burdell = set()
        self.campi_burdell_classe = set()
        self.var_array = {}
        self.var_locali_shadow = set()
        self.var_classe = {}
        self.var_array_puntatore = set()

    def indentazione(self, riga: str):
        """Aggiunge una riga di codice al buffer di output applicando il livello di indentazione corrente.

        Args:
            riga (str): La riga di codice da formattare.
        """
        self.output.append("    " * self.indent + riga)

    def get_output(self) -> str:
        """Restituisce il codice C completo generato.

        Returns:
            str: Il codice sorgente C risultante unito da a capo.
        """
        return "\n".join(self.output)

    def nuova_temp(self) -> str:
        """Genera un nome di variabile temporanea univoco.

        Returns:
            str: Identificatore univoco del tipo `__tmp1`, `__tmp2`, ecc.
        """
        self.temp_counter += 1
        return f"__tmp{self.temp_counter}"

    def tipo_c(self, tipo_scart: str) -> str:
        """Converte il tipo del linguaggio sorgente nel tipo nativo C corrispondente.

        Args:
            tipo_scart (str): Nome del tipo sorgente.

        Returns:
            str: Tipo C corrispondente o il nome della classe stessa in caso di tipo custom.
        """
        return self.TIPI_C.get(str(tipo_scart), str(tipo_scart))

    def tipo_di(self, nodo) -> str:
        """Determina il tipo di un nodo consultando la tabella semantica o la struttura del nodo.

        Args:
            nodo: Il nodo dell'AST da analizzare.

        Returns:
            str | None: Il nome del tipo inferito o `None` se non reperibile.
        """
        if nodo is None:
            return None
        chiave = id(nodo)
        if chiave in self.tipi_risolti:
            return self.tipi_risolti[chiave]

        if isinstance(nodo, Variabile):
            return "numr"
        if isinstance(nodo, Numr):
            return "numr"

        return None

    def operatore_c(self, op: str) -> str:
        """Restituisce l'operatore C equivalente a quello fornito in input.

        Args:
            op (str): L'operatore del linguaggio sorgente.

        Returns:
            str: L'operatore tradotto per C.
        """
        return self.OPERATORI_C.get(op, op)

    # ── DISPATCHER ISTRUZIONI E ESPRESSIONI ──────────────────────────

    def visit(self, node):
        """Esegue il dispatching dinamico sulle istruzioni basandosi sulla classe del nodo.

        Args:
            node: Il nodo o la lista di nodi da visitare.

        Raises:
            Exception: Se non viene trovato alcun generatore per il nodo istruzione.
        """
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

    def espr(self, node) -> str:
        """Esegue il dispatching dinamico per la valutazione delle espressioni.

        Args:
            node: Il nodo espressione da convertire.

        Returns:
            str: La stringa contenente il frammento di codice C generato.

        Raises:
            Exception: Se non viene trovato alcun generatore per il nodo espressione.
        """
        method_name = f"espr_{node.__class__.__name__}"
        method = getattr(self, method_name, None)
        if method is None:
            raise Exception(f"Nessun generatore ESPRESSIONE per {node.__class__.__name__}")
        return method(node)

    def visit_Block(self, node: Block):
        """Traduce un blocco di istruzioni sequenziali.

        Args:
            node (Block): Il nodo blocco contenente gli statement.
        """
        for stmt in node.statements:
            self.visit(stmt)

    # ══════════════════════════════════════════════════════════════
    #   CLASSI E METODI
    # ══════════════════════════════════════════════════════════════

    def visit_Robba(self, node: Robba):
        """Traduce la dichiarazione di una classe ('Robba') in una struct C e relative funzioni.

        Args:
            node (Robba): Il nodo AST che definisce una classe.
        """
        nome_classe = str(node.nome.nome)

        self.campi_classe = {v.nome.nome for v in node.variabili}
        self.campi_burdell_classe = {v.nome.nome for v in node.variabili if v.tipo.nome == "burdell"}

        self.metodi_classe = {str(f.nome.nome) for f in node.funzioni}
        self.classe_corrente = nome_classe

        # 1. Definizione struct C
        self.indentazione(f"typedef struct {{")
        self.indent += 1
        for v in node.variabili:
            tipo_c = self.tipo_c(v.tipo.nome)
            self.indentazione(f"{tipo_c} {v.nome.nome};")
        self.indent -= 1
        self.indentazione(f"}} {nome_classe};")

        # 2. Prototipi dei metodi con puntatore 'self'
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

        # 3. Costruttore della classe
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

        # 4. Traduzione dei corpi dei metodi
        for f in node.funzioni:
            self.visit(f)
            self.indentazione("")

        self.classe_corrente = None
        self.campi_classe = set()
        self.campi_burdell_classe = set()
        self.metodi_classe = set()
        self.var_locali_shadow = set()

    def visit_ChiamataOggetto(self, node: ChiamataOggetto):
        """Traduce l'invocazione di un metodo di un oggetto come istruzione isolata.

        Args:
            node (ChiamataOggetto): Il nodo rappresentante la chiamata di metodo.
        """
        self.indentazione(f"{genera_chiamata_oggetto(self, node)};")

    def espr_ChiamataOggetto(self, node: ChiamataOggetto) -> str:
        """Traduce l'invocazione di un metodo di un oggetto come espressione.

        Args:
            node (ChiamataOggetto): Il nodo della chiamata.

        Returns:
            str: Frammento C della chiamata a funzione.
        """
        return genera_chiamata_oggetto(self, node)

    def espr_Variabile(self, node: Variabile) -> str:
        """Traduce il riferimento a una variabile, considerando indici, puntatori e tipi union.

        Args:
            node (Variabile): Il nodo variabile.

        Returns:
            str: Nome o espressione di accesso alla variabile in C.
        """
        nome_var = str(node.nome)

        if node.is_array and node.index != -1:
            indice_c = self.espr(node.index) if hasattr(node.index, '__class__') and not isinstance(node.index, (int,
                                                                                                                 str)) else str(
                node.index)
            accesso = "->" if nome_var in self.var_array_puntatore else "."
            return f"{nome_var}{accesso}dati[{indice_c}]"

        base = accesso_base(self, nome_var)
        if self.burdell_info.get(id(node), False):
            tipo_corrente = self.tipo_di(node)
            return f"{base}.val.{tipo_corrente}"
        return base

    def visit_Dichiarazione(self, node: Dichiarazione):
        """Traduce la dichiarazione di una nuova variabile o istanza.

        Args:
            node (Dichiarazione): Il nodo della dichiarazione.
        """
        nome_raw = str(node.nome.nome)
        nome = c_nome(self, nome_raw)
        is_array = node.nome.is_array

        if self.classe_corrente is not None and nome in self.campi_classe:
            self.var_locali_shadow.add(nome)

        if is_array:
            tipo_elemento = node.tipo.nome
            self.var_array[nome] = tipo_elemento
            if self.indent == 0:
                if tipo_elemento == "burdell":
                    self.indentazione(f"ArrayDinamico {nome}= {{0}};")
                else:
                    self.indentazione(f"{tipo_elemento}_array {nome} = {{0}};")

            else:
                if tipo_elemento == "burdell":
                    self.indentazione(f"ArrayDinamico {nome};")
                    self.indentazione(f"arr_init(&{nome});")
                else:
                    self.indentazione(f"{tipo_elemento}_array {nome};")
                    self.indentazione(f"{tipo_elemento}_array_init(&{nome});")
            return

        tipo_dichiarato = node.tipo.nome

        if tipo_dichiarato == "burdell":
            tipo_c = "Burdell"
        elif tipo_dichiarato not in self.TIPI_C:
            self.var_classe[nome] = tipo_dichiarato
            tipo_c = tipo_dichiarato
        else:
            tipo_c = self.tipo_c(tipo_dichiarato)

        if node.valore is not None:
            if isinstance(node.valore, ChiamataCostruttore):
                valore = genera_chiamata_costruttore(self, node.valore, tipo_dichiarato)
            else:
                valore = self.espr(node.valore)
                if node.tipo.nome == "burdell":
                    gia_burdell_struct = (
                            isinstance(node.valore, Variabile)
                            and getattr(node.valore, 'is_array', False)
                            and node.valore.index != -1
                            and self.var_array.get(str(node.valore.nome)) == "burdell"
                    )
                    if not gia_burdell_struct:
                        valore = wrappa_burdell(self, node.valore)
            self.indentazione(f"{tipo_c} {nome} = {valore};")

    def _genera_prototipo_mestier(self, node: Mestier):
        """Genera la firma / prototipo in C per una funzione globale.

        Args:
            node (Mestier): Il nodo funzione di cui generare il prototipo.
        """
        nome_raw = str(node.nome.nome)

        if nome_raw == "Uè":
            nome = "main"
            tipo_ritorno = "int"
        else:
            nome = c_nome(self, nome_raw)
            if node.is_array:
                tipo_ritorno = "ArrayDinamico" if node.ritorno == "burdell" else f"{node.ritorno}_array"
            else:
                tipo_ritorno = self.tipo_c(node.ritorno)

        parametri = node.parametri or []
        if isinstance(parametri, str):
            parametri = []

        params_parts = []
        for p in parametri:
            nome_p = c_nome(self, str(p.nome.nome))

            if getattr(p.nome, 'is_array', False):
                tipo_elem = p.tipo.nome
                tipo_c_param = f"{tipo_elem}_array*" if tipo_elem != "burdell" else "ArrayDinamico*"
            else:
                tipo_c_param = self.tipo_c(p.tipo.nome)

            params_parts.append(f"{tipo_c_param} {nome_p}")

        params = ", ".join(params_parts)
        self.indentazione(f"{tipo_ritorno} {nome}({params});")

    def visit_Mestier(self, node: Mestier):
        """Traduce la definizione di una funzione ('Mestier') o dell'entrypoint 'Uè' (main).

        Args:
            node (Mestier): Il nodo rappresentante la funzione.
        """
        nome_raw = str(node.nome.nome)

        if node.is_array:
            tipo_ritorno = "ArrayDinamico" if node.ritorno == "burdell" else f"{node.ritorno}_array"
        else:
            tipo_ritorno = self.tipo_c(node.ritorno)

        is_main = (nome_raw == "Uè")
        if is_main:
            nome = "main"
            tipo_ritorno = "int"
        else:
            nome = c_nome(self, nome_raw)

        self.in_main = is_main

        params_parts = []
        if self.classe_corrente is not None:
            params_parts.append(f"{self.classe_corrente}* self")

        parametri = node.parametri or []
        if isinstance(parametri, str):
            parametri = []

        for p in parametri:
            p_nome = c_nome(self, str(p.nome.nome))

            if p.nome.is_array:
                self.var_array[p_nome] = p.tipo.nome
                self.var_array_puntatore.add(p_nome)
            elif p.tipo.nome == "burdell":
                self.var_burdell.add(p_nome)

        for p in parametri:
            p_nome = c_nome(self, str(p.nome.nome))

            if p.nome.is_array:
                tipo_elem = self.var_array.get(p_nome, p.tipo.nome)
                tipo_c_param = f"{tipo_elem}_array*" if tipo_elem != "burdell" else "ArrayDinamico*"
            else:
                tipo_c_param = self.tipo_c(p.tipo.nome)

            params_parts.append(f"{tipo_c_param} {p_nome}")

        params = ", ".join(params_parts)
        nome_finale = f"{self.classe_corrente}_{nome}" if self.classe_corrente else nome

        self.indentazione(f"{tipo_ritorno} {nome_finale}({params}) {{")
        self.indent += 1

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
    #   OPERAZIONI BINARIE
    # ══════════════════════════════════════════════════════════════

    def visit_OpBin(self, node: OpBin):
        """Traduce un'operazione binaria usata come istruzione (es. assegnamento, incremento, swap).

        Args:
            node (OpBin): Il nodo operazione binaria.

        Raises:
            Exception: Se l'operatore non è gestito come istruzione standalone.
        """
        if node.op == "=":
            is_lato_sx_burdell = False
            if isinstance(node.left, Variabile):
                is_lato_sx_burdell = self.burdell_info.get(id(node.left), False)
                if is_lato_sx_burdell:
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
                    valore_wrappato = wrappa_burdell(self, node.right)
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

            sx_is_burdell = isinstance(node.left, Variabile) and self.burdell_info.get(id(node.left), False)
            sx = self.espr(node.left)
            dx = self.espr(node.right)

            if tipo_sx == "nbruogglio" or tipo_dx == "nbruogglio":
                if tipo_sx == "nbruogglio" and tipo_dx == "nbruogglio":
                    risultato = f"burdell_concat({sx}, {dx})"
                elif tipo_sx == "nbruogglio" and tipo_dx == "numr":
                    risultato = f"burdell_concat_str_num({sx}, {dx})"
                elif tipo_sx == "numr" and tipo_dx == "nbruogglio":
                    risultato = f"burdell_concat_num_str({sx}, {dx})"
                elif tipo_sx == "nbruogglio" and tipo_dx == "lettr":
                    risultato = f"burdell_concat_str_char({sx}, {dx})"
                elif tipo_sx == "lettr" and tipo_dx == "nbruogglio":
                    risultato = f"burdell_concat_char_str({sx}, {dx})"
                else:
                    risultato = f"burdell_concat({sx}, {dx})"

                sx_assign = accesso_base(self, str(node.left.nome)) if isinstance(node.left, Variabile) else sx
                if sx_is_burdell:
                    self.indentazione(f"{sx_assign} = burdell_da_nbruogglio({risultato});")
                else:
                    self.indentazione(f"{sx_assign} = {risultato};")
                return

            op_c = self.operatore_c(node.op)
            self.indentazione(f"{sx} {op_c} {dx};")
            return

        raise Exception(f"OpBin con operatore '{node.op}' non gestito come istruzione")

    def espr_OpBin(self, node: OpBin) -> str:
        """Traduce un'operazione binaria/unaria all'interno di un'espressione.

        Args:
            node (OpBin): Il nodo operazione binaria.

        Returns:
            str: Espressione C formattata.

        Raises:
            Exception: Se vengono trovati operatori non ammessi nelle espressioni.
        """
        if node.op in ("=", "<->"):
            raise Exception(f"'{node.op}' non può comparire dentro un'espressione")

        if node.left is None:
            dx = self.espr(node.right)
            op_c = self.operatore_c(node.op)
            return f"{op_c}({dx})"

        tipo_sx = self.tipo_di(node.left)
        tipo_dx = self.tipo_di(node.right) if node.right is not None else None

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

        if tipo_sx == "nbruogglio" and tipo_dx == "lettr":
            sx = self.espr(node.left)
            dx = self.espr(node.right)
            if node.op in ("+", "-"):
                return f"burdell_concat_str_char({sx}, {dx})"

        if tipo_sx == "lettr" and tipo_dx == "nbruogglio":
            sx = self.espr(node.left)
            dx = self.espr(node.right)
            if node.op in ("+", "-"):
                return f"burdell_concat_char_str({sx}, {dx})"

        op_c = self.operatore_c(node.op)

        sx = self.espr(node.left)
        if node.right is None:
            return f"{sx}{op_c}"

        dx = self.espr(node.right)
        return f"({sx} {op_c} {dx})"

    # ══════════════════════════════════════════════════════════════
    #   PUNTO DI INGRESSO (Start)
    # ══════════════════════════════════════════════════════════════

    def visit_Start(self, node: Start):
        """Traduce l'intero programma partendo dal nodo radice dell'AST.

        Args:
            node (Start): Nodo principale del programma AST.
        """
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

    # ── CONTROLLO FLUSSO ─────────────────────────────────────────────

    def visit_Break(self, node):
        """Traduce l'istruzione di interruzione di un ciclo (`break`).

        Args:
            node: Il nodo break.
        """
        self.indentazione("break;\n")

    def visit_Mettimmca(self, node: Mettimmca):
        """Traduce l'istruzione condizionale 'Mettimmca' (`if` / `else`).

        Args:
            node (Mettimmca): Il nodo condizionale.
        """
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
        """Traduce il ciclo iterativo 'Aspe' (`while`).

        Args:
            node (Aspe): Il nodo del ciclo while.
        """
        cond = self.espr(node.Condizione)
        self.indentazione(f"while ({cond}) {{")
        self.indent += 1
        self.visit(node.Corpo)
        self.indent -= 1
        self.indentazione("}")

    def visit_Ambress_Ambress(self, node: Ambress_Ambress):
        """Traduce il ciclo iterativo 'Ambress_Ambress' (`for`).

        Args:
            node (Ambress_Ambress): Il nodo del ciclo for.
        """
        init = self._for_init(node.dichiarazione)
        cond = self.espr(node.condizione)
        step = self._for_step(node.VarOperation)

        self.indentazione(f"for ({init}; {cond}; {step}) {{")
        self.indent += 1
        self.visit(node.Corpo)
        self.indent -= 1
        self.indentazione("}")

    def _for_init(self, dich) -> str:
        """Costruisce la clausola di inizializzazione per il ciclo for C.

        Args:
            dich: Nodo dichiarazione del ciclo.

        Returns:
            str: Stringa C di inizializzazione (es. `int i = 0`).
        """
        tipo_c = self.tipo_c(dich.tipo.nome)
        nome = dich.nome.nome
        valore = self.espr(dich.valore)
        return f"{tipo_c} {nome} = {valore}"

    def _for_step(self, op: OpBin) -> str:
        """Costruisce l'espressione di incremento/passo per il ciclo for C.

        Args:
            op (OpBin): Nodo dell'operazione di incremento.

        Returns:
            str: Espressione C del passo.
        """
        sx = self.espr(op.left)
        if op.op in ("++", "--"):
            return f"{sx}{op.op}"
        op_c = self.operatore_c(op.op)
        dx = self.espr(op.right)
        return f"{sx} {op_c} {dx}"

    def visit_ReturnStatement(self, node: ReturnStatement):
        """Traduce l'istruzione di ritorno (`return`).

        Args:
            node (ReturnStatement): Il nodo del return.
        """
        if node.valore is None:
            if getattr(self, "in_main", False):
                self.indentazione("return 0;")
            else:
                self.indentazione("return;")
        else:
            valore = self.espr(node.valore)
            self.indentazione(f"return {valore};")

    # ── CHIAMATE A FUNZIONE ──────────────────────────────────────────

    def visit_CallStmt(self, node: CallStmt):
        """Traduce una chiamata a funzione usata come istruzione singola.

        Args:
            node (CallStmt): Il nodo della chiamata.
        """
        nome_c, args = risolvi_chiamata(self, node)
        self.indentazione(f"{nome_c}({', '.join(args)});")

    def espr_CallStmt(self, node: CallStmt) -> str:
        """Traduce una chiamata a funzione all'interno di un'espressione.

        Args:
            node (CallStmt): Il nodo della chiamata.

        Returns:
            str: Stringa di chiamata C.
        """
        nome_c, args = risolvi_chiamata(self, node)
        return f"{nome_c}({', '.join(args)})"

    # ── INPUT / OUTPUT ───────────────────────────────────────────────

    def visit_Arape_a_vocca(self, node: Arape_a_vocca):
        """Traduce la stampa su stdout ('Arape_a_vocca') in una chiamata `printf` in C.

        Args:
            node (Arape_a_vocca): Nodo per l'operazione di output.
        """
        stringa_formato = ""
        argomenti_c = []

        if getattr(node, 'valore', None) is not None:
            testo_pulito = str(node.valore).replace("??", "")
            stringa_formato += testo_pulito

        if getattr(node, 'variabili', None):
            for var in node.variabili:
                valore_c = self.espr(var)

                if valore_c.startswith('"') and valore_c.endswith('"'):
                    testo_fisso = valore_c[1:-1]
                    testo_fisso = testo_fisso.replace("%", "%%")

                    if stringa_formato and not stringa_formato.endswith(" ") and not testo_fisso.startswith(" "):
                        stringa_formato += " "

                    stringa_formato += testo_fisso

                else:
                    tipo = self.print_types.get(id(var))

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
                        argomenti_c.append(f"({valore_c}) ? \"true\" : \"false\"")
                    elif tipo == "burdell":
                        stringa_formato += "%s"
                        argomenti_c.append(f"burdell_a_stringa({valore_c})")
                    else:
                        stringa_formato += "%s"
                        argomenti_c.append(valore_c)

        stringa_formato += "\\n"

        if argomenti_c:
            tutti_gli_argomenti = ", ".join(argomenti_c)
            self.indentazione(f'printf("{stringa_formato}", {tutti_gli_argomenti});')
        else:
            self.indentazione(f'printf("{stringa_formato}");')
        self.indentazione('fflush(stdout);')

    def visit_Ric(self, node: Ric):
        """Traduce l'input da tastiera ('Ric') in una chiamata `scanf` in C.

        Args:
            node (Ric): Nodo per l'operazione di lettura da stdin.
        """
        stringa_formato = ""
        argomenti_c = []

        if getattr(node, 'variabile', None):
            variabili = node.variabile if isinstance(node.variabile, list) else [node.variabile]

            for var in variabili:
                valore_c = self.espr(var) if hasattr(self, 'espr') else self.visit(var)

                nome_var = str(var.nome) if hasattr(var, 'nome') else str(var)
                tipo = self.print_types.get(id(var))

                if not tipo and hasattr(self, 'tabella_simboli'):
                    simbolo = self.tabella_simboli.get(nome_var)
                    if hasattr(simbolo, 'tipo'):
                        tipo = simbolo.tipo
                    elif isinstance(simbolo, str):
                        tipo = simbolo

                if stringa_formato:
                    stringa_formato += " "

                if tipo == "nbruogglio":
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
                    stringa_formato += "%d"
                    argomenti_c.append(f"&{valore_c}")

        if argomenti_c:
            tutti_gli_argomenti = ", ".join(argomenti_c)
            self.indentazione(f'scanf("{stringa_formato}", {tutti_gli_argomenti});')

    # ══════════════════════════════════════════════════════════════
    #   LITERAL E PRIMITIVI
    # ══════════════════════════════════════════════════════════════

    def espr_Numr(self, node: Numr) -> str:
        """Traduce un valore letterale numerico.

        Args:
            node (Numr): Nodo valore numerico.

        Returns:
            str: Il valore sotto forma di stringa numerica per C.
        """
        v = node.value
        return str(int(v)) if v == int(v) else str(v)

    def espr_Boolean(self, node: Boolean) -> str:
        """Traduce un valore booleano sorgente in 'true' o 'false'.

        Args:
            node (Boolean): Nodo booleano.

        Returns:
            str: `"true"` o `"false"`.
        """
        return "true" if str(node.value) == "sasicchj" else "false"

    def espr_Stringa(self, node: Stringa) -> str:
        """Traduce una stringa letterale racchiudendola tra doppi apici C.

        Args:
            node (Stringa): Nodo valore testuale.

        Returns:
            str: Stringa formattata con doppi apici.
        """
        return f'"{node.value}"'

    def espr_Carattr(self, node: Carattr) -> str:
        """Traduce un singolo carattere letterale racchiudendolo tra apici singoli.

        Args:
            node (Carattr): Nodo singolo carattere.

        Returns:
            str: Carattere racchiuso in apici singoli.
        """
        return f"'{node.value}'"

    def espr_AccessoCampo(self, node) -> str:
        """Traduce l'accesso ad un campo/proprietà di uno struct (`istanza.campo`).

        Args:
            node: Il nodo di accesso al campo.

        Returns:
            str: Espressione di accesso al campo in C.
        """
        nome_var = str(node.variabile.nome)
        nome_campo = str(node.campo.nome)
        base = accesso_base(self, nome_var)
        return f"{base}.{nome_campo}"