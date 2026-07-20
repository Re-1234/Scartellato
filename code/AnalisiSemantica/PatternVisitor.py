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

        for kid in node.program:
            self.visit(kid)

        errori = self.symbolTable.check_pending()
        if errori:
            self.errori.append(f"Funzioni usate ma mai dichiarate: {errori}")

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
        if isinstance(info, dict):
            self.burdell_info[id(node)] = info.get('is_burdell', False)
            return info.get('tipo', 'burdell')
        self.burdell_info[id(node)] = False
        return info


    def _compatibili(self, tipo_atteso, tipo_trovato):
            if tipo_atteso == "burdell":
                return True
            return tipo_atteso == tipo_trovato


    #   ---FUNZIONI-----
    def visit_Mestier(self, node: Mestier):
        """inserisce il nome della funzione nello scope precendente e
           ne crea uno nuovo per lo scope della funzione
        """
        nome = node.nome.nome
        info = self.symbolTable.lookup(nome)

        if isinstance(info, dict) and info.get('pending'):
            if getattr(self, 'classe_corrente', None) is not None:  #controllo che il metodo sia solo della classe
                # È un metodo di classe: NON risolve i pending del main
                pass
            else:
                # È una funzione globale: risolve il pending
                self.symbolTable.resolve_pending(nome,node)
                self.symbolTable.addId(nome, node)
        else:
            self.symbolTable.addId(nome, node)


        self.symbolTable.enterScope()
        self.funzione_corrente = node

        for kid in node.parametri:
            self.visit(kid)
            self.tipi_risolti[id(kid.nome)] = str(kid.tipo)

        self.visit(node.corpo)
        if node.ritorno != 'vacant' and not self._ha_return(node.corpo):
            self.errori.append(f"Funzione '{node.nome.nome}' deve avere un return di tipo '{node.ritorno}'")
        self.symbolTable.printTable()

        self.funzione_corrente = None
        self.symbolTable.exitScope()



    def visit_Parametro(self, node: Parametro):
        # Recuperiamo il nome della variabile (visto che node.nome è un oggetto Variabile)
        nome_var = node.nome.nome
        tipo_var = node.tipo.nome

        # Controlla se il parametro è già stato dichiarato nello scope corrente (duplicato)
        if self.symbolTable.probe(nome_var):
            self.errori.append(f"NNNNNNNNNNOOOOOOOOOOOOO ma che è fatt!!!!!: Parametro duplicato '{nome_var}'")

        # Inserisce il parametro nella Symbol Table come variabile valida in questo scope
        self.symbolTable.addId(nome_var, tipo_var)
        self.tipi_risolti[id(node.nome)] = tipo_var
        self.burdell_info[id(node.nome)] = (tipo_var == 'burdell')

    def visit_ReturnStatement(self, node: ReturnStatement):
        tipo_valore = self.visit(node.valore) if node.valore is not None else "vacant"

        if self.funzione_corrente is not None:
            tipo_atteso = str(self.funzione_corrente.ritorno)
            if not self._compatibili(tipo_atteso, tipo_valore):
                self.errori.append(f"Return di tipo '{tipo_valore}' ma la funzione "
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
            if not funzione_vuole_array and is_array_valore:
                self.errori.append(f"La funzione '{self.funzione_corrente.nome.nome}' ritorna uno scalare, "
                    f"ma '{node.valore.nome}' è un array")

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

        parametri_attesi = classe.costruttore.parametri if classe.costruttore else []
        args = node.parametri or []

        if len(args) != len(parametri_attesi):
            self.errori.append(f"MMMMMMMMMMMMMMAAAAAAAAAAAAAAAA CCCHHHHEEE SSSTTTTTAAAAIIIII FFFFFACCCCCENEEEENNNN: il numero di argomenti pasati{args.__str__()} è diverso da quanto si aspetta il costruttore {parametri_attesi.__str__()}")
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

        classe = self.symbolTable.lookup(tipo_nome)
        if not isinstance(classe, Robba):
            self.errori.append(f"'{nome_var}' non è un'istanza di una classe")

        nome_metodo = node.variabile.nome if hasattr(node.nome, 'nome') else str(node.nome)
        metodo = next((f for f in classe.funzioni if str(f.nome.nome) == nome_metodo), None)

        if metodo is None:
            self.errori.append(f"Metodo '{nome_metodo}' non esiste nella classe '{tipo_nome}'")

        args = node.Parametri or []
        if len(args) != len(metodo.parametri):
            self.errori.append(f"'{nome_metodo}' si aspetta {len(metodo.parametri)} argomenti, ricevuti {len(args)}")

        for arg in args:
            self.visit(arg)

        return str(metodo.ritorno)

    def visit_AccessoCampo(self, node: AccessoCampo):
        nome_var = node.variabile.nome
        tipo_var = self.symbolTable.lookup(nome_var)
        tipo_nome = tipo_var['tipo'] if isinstance(tipo_var, dict) else tipo_var

        if tipo_nome is None:
            self.errori.append(f"Variabile '{nome_var}' non dichiarata")

        classe = self.symbolTable.lookup(tipo_nome)
        if not isinstance(classe, Robba):
            self.errori.append(f"'{nome_var}' non è un'istanza di una classe")

        nome_campo = node.campo.nome
        campo = next((v for v in classe.variabili if str(v.nome.nome) == nome_campo), None)

        if campo is None:
            self.errori.append(f"Campo '{nome_campo}' non esiste nella classe '{tipo_nome}'")

        self.tipi_risolti[id(node)] = campo.tipo.nome
        return campo.tipo.nome

    def visit_CallStmt(self, node: CallStmt):
        nome_funzione = node.nome_func.nome
        funzione = self.symbolTable.lookup(nome_funzione)
        if funzione is None:
            # inserisco come pending
            self.symbolTable.declare_pending(nome_funzione, None)
            for arg in node.args:
                self.visit(arg)
            return None

        if isinstance(funzione, dict) and funzione.get('pending'):
            for arg in node.args:
                self.visit(arg)
            return None

        if not isinstance(funzione, Mestier):
            self.errori.append(f"'{nome_funzione}' non è una funzione")

        if len(node.args) != len(funzione.parametri):
            self.errori.append(f"'{nome_funzione}' si aspetta {len(funzione.parametri)} argomenti, "
                               f"ricevuti {len(node.args)}"
                               )

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

        self.symbolTable.enterScope()
        self.visit(node.allora)
        self.symbolTable.exitScope()

        if node.altrimenti is not None:
            self.symbolTable.enterScope()
            self.visit(node.altrimenti)
            self.symbolTable.exitScope()


    #   ---VALUTAZIONE E ASSEGNAMENTO---
    def visit_OpBin(self, node: OpBin):
        #vedo se non ci stanno gli operatori di sinistra se non ci stanno facciamo il controllo se è un operazione di negazione
        if node.left is None:
            rv = self.visit(node.right)
            if node.op in ('not', '!!'):
                if rv != 'lota':
                    self.errori.append(f"'{node.op}' è applicabile solo a un valore di tipo lota")
                return 'lota'
            return rv

        lv = self.visit(node.left)

        if node.right is None:
            if node.op in ('++', '--'):
                if lv != 'numr' and lv != 'burdell':
                    self.errori.append(f"'{node.op}' applicabile solo a numr e burdell")
                return 'numr'


        rv = self.visit(node.right)

        if isinstance(node.left, Variabile) and self.symbolTable.is_array(node.left.nome) and node.left.index == -1:
            if node.op not in ("-=", "+="):
                self.errori.append(f"Su un array puoi usare solo '-=' (aggiungi) o '+=' (rimuovi), non '{node.op}'")
            info_array = self.symbolTable.lookup(node.left.nome)
            tipo_array = info_array['tipo'] if isinstance(info_array, dict) else info_array
            tipo_valore = rv

            if tipo_array != "burdell" and tipo_array != tipo_valore:
                self.errori.append(f"Impossibile aggiungere/rimuovere un valore di tipo '{tipo_valore}' "
                    f"da un array di '{tipo_array}'")
            return tipo_array


        if isinstance(node.left, Variabile) and self.symbolTable.is_array(node.left.nome) and node.left.index != -1:
            if node.op not in ("=", "-", "+", "<->"):
                self.errori.append(f" NOO MA CHE E FATT : Con la notazione indice sull'array non puoi concatenare -= +=, non '{node.op}'")
            info_array = self.symbolTable.lookup(node.left.nome)
            tipo_array = info_array['tipo'] if isinstance(info_array, dict) else info_array
            tipo_valore = rv

            if tipo_array != "burdell" and tipo_array != tipo_valore:
                self.errori.append(f"Impossibile aggiungere/rimuovere un valore di tipo '{tipo_valore}' "
                    f"da un array di '{tipo_array}'")
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
                self.errori.append(f"'{nome}' è 'burdell' non ancora inizializzata: "
                    f"il primo utilizzo deve essere un'assegnazione semplice '=', non '{node.op}'")

        # LOTA
        if lv == "lota" or rv == "lota":
            if node.op in ("+=", "-="):
                self.errori.append(f"Operatore '{node.op}' non applicabile a lota")
            if self.control_Ope_Bool(node.op):
                return "lota"

        # NUMR
        if lv == "numr" and rv == "numr":
            if self.control_Ope_Aritmetic(node.op): return 'numr'
            if self.control_Ope_Bool(node.op):      return 'lota'
            if self.control_Ope_Assign(node.op, "numr"): return 'numr'

        # NBRUOGGLIO
        if lv == "nbruogglio" and rv == "nbruogglio":
            if node.op in ("+", "-=", "+="):
                return 'nbruogglio'
            if self.control_Ope_Bool(node.op):
                self.errori.append(f"BOTT_A_MUR: Ma che stai facenn!!!!! non puoi fare operazioni booleane con tipo {lv}e tipo {rv}")


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
                self.errori.append(f"Impossibile fare '{node.op}' tra  {lv}' e  {rv}: "
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
                    # SALVIAMO IL NUOVO TIPO MANTENENDOLA DINAMICA
                    self.symbolTable.update(nome, {'tipo': rv, 'is_burdell': True})
                    self.tipi_risolti[id(node.left)] = rv
                    return rv
                else:
                    if not self._compatibili(tipo_attuale, rv):
                        self.errori.append(f"Impossibile assegnare '{rv}' a '{nome}' "
                            f"che è di tipo '{tipo_attuale}'")
                    return tipo_attuale

        if rv == "burdell" and node.op != '=':
            nome = node.right.nome if isinstance(node.right, Variabile) else "?"
            self.errori.append(f"'{nome}' è 'burdell' non ancora inizializzata: "
                f"il primo utilizzo deve essere un'assegnazione semplice '=', non '{node.op}'")

        # SWAP
        if node.op == '<->':
            if not self._compatibili(lv, rv):
                self.errori.append(f"Swap non valido: '{lv}' vs '{rv}'")
            return lv

        self.errori.append(f"BOTT A MUR : Tipi incompatibili: '{lv}' e '{rv}' con operatore '{node.op}'")

    def visit_Dichiarazione(self, node: Dichiarazione):
        tipo_dichiarato = node.tipo.nome
        nome_variabile = node.nome.nome
        is_array = node.nome.is_array

        if self.symbolTable.probe(nome_variabile):
            self.errori.append(f"Variabile '{nome_variabile}' già dichiarata")

        tipo_finale = tipo_dichiarato
        if node.valore is not None:
            if isinstance(node.valore, ChiamataCostruttore):
                self._tipo_atteso_costruttore = tipo_dichiarato
                self.visit(node.valore)
                tipo_valore = self.visit(node.valore)
            else:
                tipo_valore = self.visit(node.valore)

            if tipo_dichiarato == 'burdell':
                self.symbolTable.addId(nome_variabile, {'tipo': tipo_valore, 'is_burdell': True, 'is_array': is_array})
                tipo_finale = tipo_valore
            else:
                if not self._compatibili(tipo_dichiarato, tipo_valore):
                    self.errori.append(f"Errore (riga {node.tipo.linea}, col {node.tipo.colonna}): "
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




    def control_Ope_Bool(self, oper: str):
        if oper in {"<=", "<", ">=", ">", "==", "!=", "and", "or", "not"}:
            return True
        else:
            return False

    def control_Ope_Aritmetic(self, oper: str):
        if oper in {"+" , "-" , "*" ,"/" , "%"}:
            return True
        else:
            return False

    def control_Ope_Assign(self , oper: str,tipe:str):
        if tipe == "numr":
            if oper in {"=", "+=" , "-=" , "%=" , "*=" , "/="}:
                return True
            else:
                return False
        elif tipe == "str":
            if oper == "=" or oper == "+=":
                return True
            else:
                return False
        return None

    def visit_Break(self, node):
        if self.dentro_ciclo == 0:
              self.errori.append("Errore Semantico: Uè! O' 'stut_tutt' s'adda ausà sulo rint' a nu ciclo (aspe o ambress_ambress)!")

    def getErrori(self):
        return self.errori