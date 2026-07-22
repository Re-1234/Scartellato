from AnalisiSintattica.AST import righe_nodi
from code.AnalisiSemantica.SemanticError import SemanticError
from code.AnalisiSemantica.SymbolTable import SymbolTable

from code.AnalisiSintattica.Transformer import *


class AnalisiSemantica:
    def __init__(self):
        self.errori = []
        symbolTable: SymbolTable
        self.tipi_risolti = {}
        self.burdell_info = {}
        self.print_types = {}
        self.funzione_corrente = None
        self.dentro_ciclo = 0
        self.array_elementi_tipi = {}


    def visit(self, node):
        class_name = node.__class__.__name__
        method_name = f'visit_{class_name}'
        method = getattr(self, method_name, self.generic_visit)
        # stampa di debug: controllo del VISIT chiamato
        print(f"[VISIT] {class_name}")
        risultato = method(node)

        if risultato is not None and isinstance(risultato, str):
            self.tipi_risolti[id(node)] = risultato
            print(f"  → tipo risolto: {risultato}")  #  mostra il tipo restituito
        return risultato

    def generic_visit(self, node):
        raise Exception(f"Nessun metodo visit_{node.__class__.__name__}")

    def errore(self, msg):
        self.errori.append(msg)


    #   ---PROGRAM---
    def visit_Start(self, node):
        self.symbolTable = SymbolTable()
        # PASSO 1: Registriamo la firma di tutte le funzioni del file
        for kid in node.program:
            if isinstance(kid, Mestier):
                self.symbolTable.addId(kid.nome.nome, kid)

        # PASSO 2: Analisi semantica standard
        for kid in node.program:
            self.visit(kid)

        errori = self.symbolTable.check_pending()
        if errori:
            self.errori.append(f"ERRORE: Funzioni usate ma mai dichiarate: {errori}")
            return

    #   ---CLASSE---
    def visit_Robba(self, node: Robba):
        self.symbolTable.addId(node.nome.nome, node)
        self.symbolTable.enterScope()

        for kid in node.variabili:
            self.visit(kid)

        if node.costruttore is not None:
            self.visit(node.costruttore)

        for kid in node.funzioni:
            self.visit(kid)

        errori = self.symbolTable.check_pending()
        if errori:
            self.errori.append(f"Funzioni usate ma mai dichiarate: {errori}")
            return

        self.symbolTable.exitScope()

    def visit_Costruttore(self, node: Costruttore):

        self.symbolTable.enterScope()
        for par in node.parametri:
            self.visit(par)
            self.tipi_risolti[id(par.nome)] = str(par.tipo)

        self.visit(node.corpo)
        self.symbolTable.printTable()
        self.symbolTable.exitScope()



    #   ----TIPI-----
    def visit_Numr(self, node: Numr):
        return "numr"

    def visit_Boolean(self, node: Boolean):
        return "lota"

    def visit_Stringa(self, node: Stringa):
        return "nbruogglio"

    def visit_Carattr(self, node: Carattr):
        return "lettr"

    def visit_Variabile(self, node: Variabile):
        info = self.symbolTable.lookup(node.nome)
        if info is None:
            riga = righe_nodi.get(id(node), "sconosciuta")
            self.errori.append(f"riga {riga}: variabile '{node.nome}' non dichiarata")
            return

        is_array = self.symbolTable.is_array(node.nome) if hasattr(self.symbolTable, 'is_array') else False

        # Lettura indicizzata di un array 'burdell' dinamico: risolvi il tipo REALE
        if is_array and getattr(node, 'index', -1) != -1:
            tipo_dichiarato = info['tipo'] if isinstance(info, dict) else info
            if tipo_dichiarato == "burdell":
                idx = self._indice_costante(node.index)
                tipi_tracciati = self.array_elementi_tipi.get(node.nome, [])
                if idx is not None and 0 <= idx < len(tipi_tracciati):
                    tipo_reale = tipi_tracciati[idx]
                    self.burdell_info[id(node)] = True
                    return tipo_reale
                else:
                    self.burdell_info[id(node)] = True
                    return "burdell"

        if isinstance(info, dict):
            self.burdell_info[id(node)] = info.get('is_burdell', False)
            return info.get('tipo', 'burdell')
        self.burdell_info[id(node)] = False
        return info

    def _indice_costante(self, indice):
        """Prova a estrarre un intero Python da un indice, qualunque sia la sua rappresentazione."""
        if isinstance(indice, int):
            return indice
        if isinstance(indice, Numr):  # nodo AST letterale numerico
            try:
                return int(indice.value)
            except (TypeError, ValueError):
                return None
        if hasattr(indice, 'value'):
            try:
                return int(indice.value)
            except (TypeError, ValueError):
                return None
        return None


    #   ---FUNZIONI-----
    def visit_Mestier(self, node: Mestier):
        """inserisce il nome della funzione nello scope precendente e
           ne crea uno nuovo per lo scope della funzione
        """
        nome = node.nome.nome
        info = self.symbolTable.lookup(nome)

        if isinstance(info, dict) and info.get('pending'):
            if getattr(self, 'classe_corrente', None) is None:
                self.symbolTable.resolve_pending(nome, node)
                self.symbolTable.addId(nome, node)
        else:
            self.symbolTable.addId(nome, node)

        self.symbolTable.enterScope()
        self.funzione_corrente = node

        for kid in node.parametri:
            self.visit(kid)  # visit_Parametro ora si occupa di tutto in modo completo

        self.visit(node.corpo)
        if node.ritorno != 'vacant' and not self._ha_return(node.corpo):
            self.errori.append(f"ERRORE: Funzione '{node.nome.nome}' deve avere un return di tipo '{node.ritorno}'")

        self.symbolTable.printTable()
        self.funzione_corrente = None
        self.symbolTable.exitScope()


    def visit_Parametro(self, node: Parametro):
        nome_var = node.nome.nome
        tipo_var = node.tipo.nome
        is_array = node.nome.is_array

        if self.symbolTable.probe(nome_var):
            self.errori.append(f"NNNNNNNNNNOOOOOOOOOOOOO ma che è fatt!!!!!: Parametro duplicato '{nome_var}'")
            return
        # Inseriamo il dizionario completo fin da subito
        info_parametro = {
            'tipo': tipo_var,
            'is_array': is_array
        }
        self.symbolTable.addId(nome_var, info_parametro)
        self.tipi_risolti[id(node.nome)] = tipo_var
        self.burdell_info[id(node.nome)] = (tipo_var == 'burdell')

    def visit_ReturnStatement(self, node: ReturnStatement):
        tipo_valore = self.visit(node.valore) if node.valore is not None else "vacant"

        if self.funzione_corrente is not None:
            tipo_atteso = str(self.funzione_corrente.ritorno)
            if not self._compatibili(tipo_atteso, tipo_valore):
                self.errori.append(f"ERRORE: Return di tipo '{tipo_valore}' ma la funzione "
                    f"'{self.funzione_corrente.nome.nome}' ritorna '{tipo_atteso}'")

            # nuovo controllo: shape (array vs scalare)
            if isinstance(node.valore, Variabile):
                is_array_valore = self.symbolTable.is_array(node.valore.nome)
            else:
                is_array_valore = False

            funzione_vuole_array = getattr(self.funzione_corrente, 'is_array', False)

            if funzione_vuole_array and not is_array_valore:
                self.errori.append(f"La funzione '{self.funzione_corrente.nome.nome}' deve ritornare un array, "
                    f"ma '{node.valore.nome}' non lo è")
                return
            if not funzione_vuole_array and is_array_valore:
                self.errori.append(f"La funzione '{self.funzione_corrente.nome.nome}' ritorna uno scalare, "
                    f"ma '{node.valore.nome}' è un array")
                return
        return tipo_valore

    def _ha_return(self, block: Block):
        for stmt in block.statements:
            if isinstance(stmt, ReturnStatement) and stmt.valore is not None:
                return True
            # controlla anche dentro if/while/for
            if isinstance(stmt, Mettimmca):
                if self._ha_return(stmt.allora):
                    return True
                if stmt.altrimenti and self._ha_return(stmt.altrimenti):
                    return True
            if isinstance(stmt, Aspe):
                if self._ha_return(stmt.Corpo):
                    return True
            if isinstance(stmt, Ambress_Ambress):
                if self._ha_return(stmt.Corpo):
                    return True
        return False


    def visit_Block(self, node: Block):
        for element in node.statements:
            self.visit(element)

    def visit_ChiamataCostruttore(self, node: ChiamataCostruttore):
        nome_classe_attesa = self._tipo_atteso_costruttore  # letto dallo stato temporaneo

        classe = self.symbolTable.lookup(nome_classe_attesa)
        if classe is None or not isinstance(classe, Robba):
            self.errori.append(f"'{nome_classe_attesa}' non è una classe valida")
            return
        parametri_attesi = classe.costruttore.parametri if classe.costruttore else []
        args = node.parametri or []

        if len(args) != len(parametri_attesi):
            self.errori.append(f"ERRORE: MMMMMMMMMMMMMMAAAAAAAAAAAAAAAA CCCHHHHEEE SSSTTTTTAAAAIIIII FFFFFACCCCCENEEEENNNN: il numero di argomenti pasati{args.__str__()} è diverso da quanto si aspetta il costruttore {parametri_attesi.__str__()}")
            return
        for arg in args:
            self.visit(arg)

        return nome_classe_attesa

    def visit_ChiamataOggetto(self, node: ChiamataOggetto):
        nome_var = node.nome.nome if hasattr(node.variabile, 'nome') else str(node.variabile)
        print(nome_var)
        tipo_var = self.symbolTable.lookup(nome_var) #controllo se nomevar è presente nello scope
        print(tipo_var)
        tipo_nome = tipo_var['tipo'] if isinstance(tipo_var, dict) else tipo_var
        print(tipo_nome)

        if tipo_nome is None:
            self.errori.append(f"Variabile '{nome_var}' non dichiarata")
            return
        classe = self.symbolTable.lookup(tipo_nome)
        if not isinstance(classe, Robba):
            self.errori.append(f"'{nome_var}' non è un'istanza di una classe")
            return
        nome_metodo = node.variabile.nome if hasattr(node.nome, 'nome') else str(node.nome)
        metodo = next((f for f in classe.funzioni if str(f.nome.nome) == nome_metodo), None)

        if metodo is None:
            self.errori.append(f"Metodo '{nome_metodo}' non esiste nella classe '{tipo_nome}'")
            return None

        args = node.Parametri or []
        if len(args) != len(metodo.parametri):
            self.errori.append(f"'{nome_metodo}' si aspetta {len(metodo.parametri)} argomenti, ricevuti {len(args)}")
            return None

        for arg in args:
            self.visit(arg)

        return str(metodo.ritorno)

    def visit_AccessoCampo(self, node: AccessoCampo):
        nome_var = node.variabile.nome
        tipo_var = self.symbolTable.lookup(nome_var)
        tipo_nome = tipo_var['tipo'] if isinstance(tipo_var, dict) else tipo_var

        if tipo_nome is None:
            self.errori.append(f"Variabile '{nome_var}' non dichiarata")
            return
        classe = self.symbolTable.lookup(tipo_nome)
        if not isinstance(classe, Robba):
            self.errori.append(f"'{nome_var}' non è un'istanza di una classe")
            return

        nome_campo = node.campo.nome
        campo = next((v for v in classe.variabili if str(v.nome.nome) == nome_campo), None)

        if campo is None:
            self.errori.append(f"Campo '{nome_campo}' non esiste nella classe '{tipo_nome}'")

        self.tipi_risolti[id(node)] = campo.tipo.nome
        return campo.tipo.nome

    def visit_CallStmt(self, node: CallStmt):
        nome_funzione = node.nome_func.nome
        funzione = self.symbolTable.lookup(nome_funzione)

        if funzione is None or (isinstance(funzione, dict) and funzione.get('pending')):
            self.symbolTable.declare_pending(nome_funzione, None)
            for arg in node.args:
                self.visit(arg)
            return "sconosciuto"


        if not isinstance(funzione, Mestier):
            self.errori.append(f"'{nome_funzione}' non è una funzione")
            return
        if len(node.args) != len(funzione.parametri):
            self.errori.append(f"'{nome_funzione}' si aspetta {len(funzione.parametri)} argomenti, "
                               f"ricevuti {len(node.args)}"
                               )
            return

        for arg in node.args:
            self.visit(arg)

        return str(funzione.ritorno)

    #   ---CICLI---
    def visit_Ambress_Ambress(self, node: Ambress_Ambress):
        self.symbolTable.enterScope()
        if node.dichiarazione is not None:  #dichiarazione non fatta
            self.visit(node.dichiarazione)

        tipo_cond = self.visit(node.condizione)
        if tipo_cond != "lota":
            self.errori.append(f"BOTT_A_MUR: Ma ch stai facen!!!!! e mis '{tipo_cond}'! non puoi inserire una espressione che ha come risultato un valore diverso da boolean")
            return



        if node.VarOperation is not None:
            self.visit(node.VarOperation)

        self.dentro_ciclo += 1
        self.visit(node.Corpo)
        self.dentro_ciclo -= 1

        self.symbolTable.exitScope()

    def visit_Aspe(self, node: Aspe):
        tipo_cond = self.visit(node.Condizione)
        if tipo_cond != "lota" and tipo_cond != "numr":
            self.errori.append(f"La condizione del while deve essere booleana, o numr trovato '{tipo_cond}'")
            return

        self.symbolTable.enterScope()

        self.dentro_ciclo += 1
        self.visit(node.Corpo)
        self.dentro_ciclo -= 1

        self.symbolTable.printTable()
        self.symbolTable.exitScope()


    #   ---IF---
    def visit_Mettimmca(self, node: Mettimmca):
        tipo_cond = self.visit(node.condizione)
        if tipo_cond != "lota":
            self.errori.append(f"La condizione dell'if deve essere booleana, trovato '{tipo_cond}'")
            return


        self.symbolTable.enterScope()
        self.visit(node.allora)
        self.symbolTable.exitScope()

        if node.altrimenti is not None:
            self.symbolTable.enterScope()
            self.visit(node.altrimenti)
            self.symbolTable.exitScope()


    #   ---VALUTAZIONE E ASSEGNAMENTO---
    def visit_OpBin(self, node: OpBin):
        #controllo se mancano gli operatori di sinistra in caso positivo controllo se è un operazione di negazione
        if node.left is None:
            rv = self.visit(node.right)
            if node.op in ('not', '!!'):
                if rv != 'lota':
                    self.errori.append(f"NOO MA CHE E FATT :'{node.op}' è applicabile solo a un valore di tipo lota")
                    return
                return 'lota'
            return rv

        lv = self.visit(node.left)

        if node.right is None:
            if node.op in ('++', '--'):
                if lv != 'numr' and lv != 'burdell':
                    self.errori.append(f"NOO MA CHE E FATT : '{node.op}' applicabile solo a numr e burdell")
                    return
                return 'numr'


        rv = self.visit(node.right)

        #gestione array
        if isinstance(node.left, Variabile) and self.symbolTable.is_array(node.left.nome):
            nome_array = node.left.nome
            info_array = self.symbolTable.lookup(nome_array)
            tipo_array = info_array['tipo'] if isinstance(info_array, dict) else info_array
            is_dinamico = (tipo_array == "burdell")

            # CASO 1: SENZA INDICE -> inserimento/rimozione con -= e +=
            if node.left.index == -1:
                if node.op not in ("-=", "+="):
                    self.errori.append(
                        f"NOO MA CHE E FATT: su un array puoi usare solo '-=' (inserisci) "
                        f"o '+=' (rimuovi), non '{node.op}'")
                    return tipo_array

                if is_dinamico:
                    # array eterogeneo 'burdell ][': accetta qualunque tipo,
                    # ma tiene traccia dell'ordine di inserimento
                    if node.op == "-=":
                        self.array_elementi_tipi.setdefault(nome_array, []).append(rv)
                    return "burdell"
                else:
                    # array tipizzato (es. numr ][): il valore deve combaciare
                    if rv != tipo_array:
                        self.errori.append(
                            f"NOO MA CHE E FATT: impossibile inserire un valore di tipo "
                            f"'{rv}' in un array di '{tipo_array}'")
                    return tipo_array

            else:
                if node.op not in ("=", "-", "+","*","/","<->", "<", ">", "==", "!=", ">=", "<="):
                    self.errori.append(
                        f"NOO MA CHE E FATT: con la notazione a indice non puoi "
                        f"concatenare, hai usato '{node.op}'")
                    return tipo_array

                if is_dinamico:
                    tipi_tracciati = self.array_elementi_tipi.get(nome_array, [])
                    idx = self._indice_costante(node.left.index)
                    if idx is not None and 0 <= idx < len(tipi_tracciati):
                        tipo_elemento_reale = tipi_tracciati[idx]
                    else:
                        tipo_elemento_reale = "burdell"

                    if self.control_Ope_Confronto(node.op):
                        return "lota"
                    return tipo_elemento_reale
                else:
                    if self.control_Ope_Confronto(node.op):
                        return "lota"
                    if tipo_array != rv and node.op in ("=", "-", "+", "<->"):
                        self.errori.append(
                            f"NOO MA CHE E FATT: tipi incompatibili tra elemento "
                            f"dell'array '{tipo_array}' e valore '{rv}'")
                    return tipo_array


                if is_dinamico:
                    print(f"[DEBUG] index={node.left.index!r} tipo={type(node.left.index)}")
                    tipi_tracciati = self.array_elementi_tipi.get(nome_array, [])
                    if isinstance(node.left.index, int) and 0 <= node.left.index < len(tipi_tracciati):
                        # conosciamo il tipo REALE inserito a quell'indice
                        return tipi_tracciati[node.left.index]
                    else:
                        # indice non costante o non ancora tracciato: fallback generico
                        return "burdell"
                else:
                    if tipo_array != rv and node.op == "=":
                        self.errori.append(
                            f"NOO MA CHE E FATT: tipi incompatibili tra elemento "
                            f"dell'array '{tipo_array}' e valore '{rv}'")
                    return tipo_array


        if isinstance(node.left, Variabile) and self.symbolTable.is_array(node.left.nome) and node.left.index != -1:
            if node.op not in ("=", "-", "+", "<->","<",">"):
                self.errori.append(f"ERRORE: NOO MA CHE E FATT : Con la notazione indice sull'array non puoi concatenare , hai usato '{node.op}'")
                return
            info_array = self.symbolTable.lookup(node.left.nome)
            tipo_array = info_array['tipo'] if isinstance(info_array, dict) else info_array
            tipo_valore = rv

            if tipo_array != "burdell" and tipo_array != tipo_valore:
                self.errori.append(f"ERRORE: NOO MA CHE E FATT: Impossibile aggiungere/rimuovere un valore di tipo '{tipo_valore}' "
                    f"da un array di '{tipo_array}'")
                return
            return tipo_array



        if lv == "burdell" or rv == "burdell":
            if isinstance(node.left, Variabile) and lv == "burdell":
                info_l = self.symbolTable.lookup(node.left.nome)
                lv = info_l['tipo'] if isinstance(info_l, dict) else info_l

            if isinstance(node.right, Variabile) and rv == "burdell":
                info_r = self.symbolTable.lookup(node.right.nome)
                rv = info_r['tipo'] if isinstance(info_r, dict) else info_r

            if lv == "burdell" and node.op != '=':
                nome = node.left.nome if isinstance(node.left, Variabile) else "?"
                self.errori.append(f"ERRORE: '{nome}' è 'burdell' non ancora inizializzata: "
                    f"il primo utilizzo deve essere un'assegnazione semplice '=', non '{node.op}'")
                return

        # LOTA
        if lv == "lota" or rv == "lota":
            if self.control_Ope_Logici(node.op):
                # Operatori logici (and, or, !!)
                if lv != "lota" or rv != "lota":
                    self.errori.append(
                        f"ERRORE: NOO MA CHE E FATT : L'operatore logico '{node.op}' richiede operandi booleani ('lota'), trovati '{lv}' e '{rv}'")
                return "lota"

            elif self.control_Ope_Confronto(node.op):
                # Operatori di confronto (==, !=)
                if lv != rv:
                    self.errori.append(f"ERRORE: BOTT_A_MUR: Impossibile confrontare '{lv}' e '{rv}' con '{node.op}'")
                return "lota"

            elif self.control_Ope_Assign(node.op, "lota"):
                if node.op == '=' and isinstance(node.left, Variabile):
                    info_var = self.symbolTable.lookup(node.left.nome)
                    is_dinamica = isinstance(info_var, dict) and info_var.get('is_burdell')
                    if is_dinamica:
                        self.symbolTable.update(node.left.nome, {'tipo': rv, 'is_burdell': True})
                        self.tipi_risolti[id(node.left)] = rv
                        return rv
                if lv != rv:
                    self.errori.append(f"ERRORE: Impossibile assegnare '{rv}' a '{lv}' con l'operatore '{node.op}'")
                return "lota"

            else:
                self.errori.append(f"ERRORE: NOO MA CHE E FATT : Operatore '{node.op}' non applicabile con il tipo lota")
                return "lota"

            # NUMR (Numeri)
        if lv == "numr" and rv == "numr":
            if self.control_Ope_Aritmetic(node.op):
                return 'numr'
            if self.control_Ope_Confronto(node.op):
                return 'lota'
            if self.control_Ope_Assign(node.op, "numr"):
                return 'numr'
            if self.control_Ope_Logici(node.op):
                self.errori.append(
                    f"ERRORE: NOO MA CHE E FATT : L'operatore logico '{node.op}' non è applicabile a numeri ('numr')")
                return 'lota'

        # NBRUOGGLIO
        if lv == "nbruogglio" and rv == "nbruogglio":
            if node.op in ("+", "-=", "+="):
                return 'nbruogglio'
            if self.control_Ope_Confronto(node.op):
                return 'lota'

        if lv == "nbruogglio" and rv == "lettr" :
            if node.op in ("+", "-=", "+="):
                return 'nbruogglio'
            if self.control_Ope_Confronto(node.op):
                return 'lota'

        if lv == "lettr" and rv == "nbruogglio" :
            if node.op in ("+", "-=", "+="):
                return 'nbruogglio'
            if self.control_Ope_Confronto(node.op):
                return 'lota'

        # NBRUOGGLIO con NUMR (prepend/append del numero come stringa)
        if lv == "nbruogglio" and rv == "numr":
            if node.op in ("+","+=", "-="):
                return "nbruogglio"

        if lv == "numr" and rv == "nbruogglio":
            if node.op == '+':
                return 'nbruogglio'

            if node.op in ("+=", "-="):
                info_var = self.symbolTable.lookup(node.left.nome) if isinstance(node.left, Variabile) else None
                is_dinamica = isinstance(info_var, dict) and info_var.get('is_burdell')

                if isinstance(node.left, Variabile) and is_dinamica:
                    # tipi_risolti[id(node.left)] deve restare il tipo VECCHIO (lv),
                    # perché il transpiler usa QUESTO stesso nodo per leggere il valore
                    # attuale prima di riassegnarlo — se lo metti a "nbruogglio" legge
                    # il campo sbagliato della union mentre il tag è ancora TIPO_NUMR.
                    self.tipi_risolti[id(node.left)] = lv  # ← era "nbruogglio", ora lv
                    self.symbolTable.update(node.left.nome, {'tipo': "nbruogglio", 'is_burdell': True})
                    return "nbruogglio"
                self.errori.append(f"ERRORE: Impossibile fare '{node.op}' tra  {lv}' e  {rv}: "
                    f"'{node.left.nome if isinstance(node.left, Variabile) else '?'}' "
                    f"è numr fisso e non può cambiare tipo")

        # ASSEGNAMENTO
        if node.op == '=':
            if isinstance(node.left, Variabile):
                nome = node.left.nome
                info_var = self.symbolTable.lookup(nome)

                # Capiamo se è dinamica e qual è il suo tipo attuale
                is_dinamica = isinstance(info_var, dict) and info_var.get('is_burdell')
                tipo_attuale = info_var['tipo'] if isinstance(info_var, dict) else info_var

                if is_dinamica:
                    # BLOCCO: Non puoi assegnare un tipo "burdell" a un altro burdell
                    if rv == "burdell":
                        self.errori.append(
                            f"ERRORE: NOO MA CHE E FATT: Impossibile assegnare un tipo 'burdell' a un'altra variabile 'burdell' ('{nome}')")
                        return "burdell"

                    # SALVIAMO IL NUOVO TIPO MANTENENDOLA DINAMICA
                    self.symbolTable.update(nome, {'tipo': rv, 'is_burdell': True})
                    self.tipi_risolti[id(node.left)] = rv
                    return rv
                else:
                    if not self._compatibili(tipo_attuale, rv):
                        self.errori.append(f"ERRORE: Impossibile assegnare '{rv}' a '{nome}' "
                                           f"che è di tipo '{tipo_attuale}'")
                    return tipo_attuale

        if rv == "burdell" and node.op != '=':
            nome = node.right.nome if isinstance(node.right, Variabile) else "?"
            self.errori.append(f"ERRORE: '{nome}' è 'burdell' non ancora inizializzata: "
                f"il primo utilizzo deve essere un'assegnazione semplice '=', non '{node.op}'")

        # SWAP
        if node.op == '<->':
            if not self._compatibili(lv, rv):
                self.errori.append(f"ERRORE: Swap non valido: '{lv}' vs '{rv}'")
            return lv

        self.errori.append(f"ERRORE: BOTT A MUR : Tipi incompatibili: '{lv}' e '{rv}' con operatore '{node.op}'")

    def visit_Dichiarazione(self, node: Dichiarazione):
        tipo_dichiarato = node.tipo.nome #tipo var
        nome_variabile = node.nome.nome  #nome var
        is_array = node.nome.is_array    #controllo per determinare se una variabile è una array

        if self.symbolTable.probe(nome_variabile): # controllo sullo scope corrente
            self.errori.append(f"ERRORE: Variabile '{nome_variabile}' già dichiarata")

        tipo_finale = tipo_dichiarato
        if is_array and tipo_dichiarato == 'burdell':
            self.array_elementi_tipi[nome_variabile] = []

        if node.valore is not None:
            if isinstance(node.valore, ChiamataCostruttore):
                self._tipo_atteso_costruttore = tipo_dichiarato
                tipo_valore = self.visit(node.valore)
            else:
                tipo_valore = self.visit(node.valore)

            if tipo_dichiarato == 'burdell':
                # BLOCCO: Non puoi inizializzare un burdell con un altro burdell
                if tipo_valore == 'burdell':
                    self.errori.append(
                        f"ERRORE: NOO MA CHE E FATT: Impossibile inizializzare la variabile burdell '{nome_variabile}' con un valore di tipo 'burdell'")
                    return

                self.symbolTable.addId(nome_variabile, {'tipo': tipo_valore, 'is_burdell': True, 'is_array': is_array})
                tipo_finale = tipo_valore
            else:
                if not self._compatibili(tipo_dichiarato, tipo_valore):
                    self.errori.append(f"ERRORE: (riga {node.tipo.linea}, col {node.tipo.colonna}): "
                        f"'{nome_variabile}' dichiarata come '{tipo_dichiarato}' "
                        f"ma assegnato '{tipo_valore}'")
                self.symbolTable.addId(nome_variabile,
                                       {'tipo': tipo_dichiarato, 'is_burdell': False, 'is_array': is_array})
        else:
            is_dinamico = (tipo_dichiarato == 'burdell')
            self.symbolTable.addId(nome_variabile,
                                   {'tipo': tipo_dichiarato, 'is_burdell': is_dinamico, 'is_array': is_array})

        self.tipi_risolti[id(node.nome)] = tipo_finale
        self.burdell_info[id(node.nome)] = (tipo_dichiarato == 'burdell')


    def visit_Arape_a_vocca(self,node : Arape_a_vocca):
        variabili = node.variabili
        print(variabili)
        if node.valore is not None:
            #  Il testo fisso (node.valore) è una stringa costante. Non lo visitiamo.
            self.tipi_risolti[id(node.valore)] = "nbruogglio"

        if variabili:
            for variabile in variabili:
                tipo_rilevato = self.visit(variabile)
                self.print_types[id(variabile)] = tipo_rilevato

    def visit_Ric(self, node: Ric):
        # 1. Uniformiamo node.variabile in una lista di nodi
        variabili = node.variabile if isinstance(node.variabile, list) else [node.variabile]

        # 2. Iteriamo su ogni variabile dell'istruzione ric()
        for v in variabili:
            tipo_rilevato = self.visit(v)

            # Fallback se self.visit(v) non ritorna direttamente la stringa del tipo
            if not tipo_rilevato and hasattr(v, 'nome'):
                tipo_rilevato = self.symbolTable.lookup(str(v.nome))

            # SALVA IL TIPO IN print_types!
            # Ora il Transpiler troverà "nbruogglio" tramite id(var) e genererà %s!
            self.print_types[id(v)] = tipo_rilevato

    def control_Ope_Logici(self, oper: str) -> bool:
        """Operatori strettamente logici (richiedono e restituiscono 'lota')"""
        return oper in {"and", "or", "not", "!!"}

    def control_Ope_Confronto(self, oper: str):
        if oper in {"<=", "<", ">=", ">", "==", "!="}:
            return True
        else:
            return False

    def control_Ope_Aritmetic(self, oper: str) -> bool:
        """Operatori aritmetici (applicabili a 'numr')"""
        return oper in {"+", "-", "*", "/", "%"}

    def control_Ope_Assign(self, oper: str, tipe: str) -> bool:
        """Operatori di assegnamento validi per ciascun tipo"""
        if tipe == "numr":
            return oper in {"=", "+=", "-=", "%=", "*=", "/="}
        elif tipe == "nbruogglio":  # Corretto: 'nbruogglio' al posto di 'str'
            return oper in {"=", "+="}
        elif tipe in ("lota", "lettr"):
            return oper == "="
        return False

    def visit_Break(self, node):
        if self.dentro_ciclo == 0:
              self.errori.append("ERRORE: Errore Semantico: Uè! O' 'stut_tutt' s'adda ausà sulo rint' a nu ciclo (aspe o ambress_ambress)! TRADOTTO : il token break si deve usare solamente nei cicli")

    def _compatibili(self, tipo_atteso, tipo_trovato):
        if tipo_atteso == "sconosciuto" or tipo_trovato == "sconosciuto":
            return True
        if tipo_atteso == "burdell":
            return True
        return tipo_atteso == tipo_trovato

    def getErrori(self):
        return self.errori