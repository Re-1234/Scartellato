"""Modulo di Analisi Semantica basato sul Pattern Visitor.

Questo modulo implementa la classe `AnalisiSemantica`, che attraversa l'Abstract
Syntax Tree (AST) generato dal parser per eseguire la validazione dei tipi,
la gestione degli scope mediante una Tabella dei Simboli (SymbolTable) e la
rilevazione di errori semantici prima della fase di generazione del codice.
"""

from AnalisiSintattica.AST import righe_nodi
from code.AnalisiSemantica.SemanticError import SemanticError
from code.AnalisiSemantica.SymbolTable import SymbolTable
from code.AnalisiSintattica.Transformer import *


class AnalisiSemantica:
    """Analizzatore semantico per l'AST basato sul Pattern Visitor.

    Attraversa i nodi del dell'AST invocando dinamicamente il metodo `visit_<NomeNodo>`
    corrispondente al tipo di ciascun nodo. Risolve i tipi delle espressioni,
    gestisce lo scope delle variabili e delle funzioni, traccia il tipo dinamico
    ('burdell') e accumula gli eventuali errori semantici rilevati nel sorgente.

    Attributes:
        errori (list): Elenco delle stringhe contenenti i messaggi di errore semantico.
        symbolTable (SymbolTable): Istanza della tabella dei simboli per tracciare variabili/funzioni e scope.
        tipi_risolti (dict): Dizionario ID del nodo AST -> Tipo di dato calcolato/risolto.
        burdell_info (dict): Dizionario ID del nodo AST -> Booleano (True se è un tipo dinamico 'burdell').
        print_types (dict): Dizionario ID del nodo AST -> Tipo di dato usato per formattare la stampa/lettura.
        funzione_corrente (Mestier|None): Riferimento al nodo della funzione attualmente in fase di analisi.
        dentro_ciclo (int): Livello di annidamento corrente nei cicli (usato per validare l'istruzione 'break').
        array_elementi_tipi (dict): Tracciamento dei tipi dei singoli elementi per gli array dinamici.
    """

    def __init__(self):
        """Inizializza le strutture dati per l'analisi semantica."""
        self.errori = []  # Lista che raccoglierà gli errori semantici trovati
        symbolTable: SymbolTable  # Dichiarazione di tipo per l'istanza di SymbolTable
        self.tipi_risolti = {}  # Mappa id(nodo) -> tipo di dato identificato
        self.burdell_info = {}  # Mappa id(nodo) -> True/False per il tipo dinamico 'burdell'
        self.print_types = {}  # Mappa id(nodo) -> tipo usato per la stampa (%d, %s, %c...)
        self.funzione_corrente = None  # Mantiene la funzione su cui stiamo lavorando (per verificare i return)
        self.dentro_ciclo = 0  # Contatore per verificare di essere dentro un ciclo per il 'break'
        self.array_elementi_tipi = {}  # Mappa nome_array -> lista ordinata dei tipi degli elementi inseriti

    # ══════════════════════════════════════════════════════════════
    #   DISPATCHER VISITOR (Cuore del Pattern Visitor)
    # ══════════════════════════════════════════════════════════════

    def visit(self, node):
        """Metodo centrale del Pattern Visitor per il dispatching dinamico sui nodi AST.

        Determina il nome della classe del nodo e invoca il corrispondente metodo `visit_<NomeClasse>`.
        Se il metodo specifico non esiste, ripiega su `generic_visit`.

        Args:
            node: Il nodo dell'AST da analizzare.

        Returns:
            Any: Il tipo di dato risolto (sotto forma di stringa) o il risultato della visita.
        """
        class_name = node.__class__.__name__  # Ricava il nome della classe del nodo (es. 'Numr', 'OpBin')
        method_name = f'visit_{class_name}'  # Costruisce il nome del metodo da invocare (es. 'visit_Numr')
        method = getattr(self, method_name,
                         self.generic_visit)  # Cerca il metodo nella classe, fallback su generic_visit

        # Stampa di debug per tracciare il percorso della visita
        print(f"[VISIT] {class_name}")
        risultato = method(node)  # Esegue il metodo visitor trovato passando il nodo

        # Se il metodo restituisce un tipo espresso come stringa, salviamo il tipo associandolo all'ID del nodo
        if risultato is not None and isinstance(risultato, str):
            self.tipi_risolti[id(node)] = risultato  # Registra il tipo risolto nel dizionario
            print(f"  → tipo risolto: {risultato}")  # Stampa di debug del tipo identificato

        return risultato  # Restituisce il risultato dell'analisi del nodo

    def generic_visit(self, node):
        """Fallback chiamato quando non esiste un metodo `visit_<NomeClasse>` per il nodo.

        Args:
            node: Il nodo non gestito.

        Raises:
            Exception: Solleva un'eccezione indicando che il nodo non possiede un visitor.
        """
        raise Exception(f"Nessun metodo visit_{node.__class__.__name__}")

    def errore(self, msg: str):
        """Registra un nuovo messaggio di errore semantico nella lista degli errori.

        Args:
            msg (str): Descrizione dell'errore.
        """
        self.errori.append(msg)  # Aggiunge il messaggio alla lista degli errori registrati

    # ══════════════════════════════════════════════════════════════
    #   PROGRAMMA E STRUTTURE PRINCIPALI
    # ══════════════════════════════════════════════════════════════

    def visit_Start(self, node: Start):
        """Visita il nodo radice dell'AST (l'intero programma).

        Effettua un'analisi a due passaggi:
        1. Registra le firme di tutte le funzioni globali per consentire la ricorsione/chiamate anticipate.
        2. Analizza semanticamente ogni singolo nodo del programma.

        Args:
            node (Start): Nodo radice del programma.
        """
        self.symbolTable = SymbolTable()  # Inizializza la tabella dei simboli principale

        # PASSO 1: Registriamo la firma di tutte le funzioni del file prima di analizzare i corpi
        for kid in node.program:  # Cicla su tutte le dichiarazioni top-level del programma
            if isinstance(kid, Mestier):  # Se la dichiarazione è una funzione ('Mestier')
                self.symbolTable.addId(kid.nome.nome,
                                       kid)  # La aggiunge alla SymbolTable per supportare chiamate anticipate

        # PASSO 2: Analisi semantica standard di tutti gli elementi
        for kid in node.program:  # Cicla nuovamente su ogni elemento del programma
            self.visit(kid)  # Invoca la visita semantica per il nodo corrente

        # Verifichiamo se ci sono funzioni chiamate ma che non sono mai state dichiarate
        errori = self.symbolTable.check_pending()
        if errori:
            self.errori.append(f"ERRORE: Funzioni usate ma mai dichiarate: {errori}")
            return

    def visit_Robba(self, node: Robba):
        """Visita la dichiarazione di una classe ('Robba').

        Crea un nuovo scope per i campi, il costruttore e i metodi della classe.

        Args:
            node (Robba): Il nodo della classe.
        """
        self.symbolTable.addId(node.nome.nome, node)  # Inserisce il nome della classe nello scope globale
        self.symbolTable.enterScope()  # Apre un nuovo scope isolato per i membri della classe

        for kid in node.variabili:  # Analizza la dichiarazione di tutti i campi/variabili della classe
            self.visit(kid)

        if node.costruttore is not None:  # Se la classe definisce un costruttore esplicito
            self.visit(node.costruttore)  # Analizza il costruttore

        for kid in node.funzioni:  # Analizza tutti i metodi appartenenti alla classe
            self.visit(kid)

        errori = self.symbolTable.check_pending()  # Controlla se ci sono chiamate pendenti non risolte nella classe
        if errori:
            self.errori.append(f"Funzioni usate ma mai dichiarate: {errori}")
            return

        self.symbolTable.exitScope()  # Chiude lo scope della classe e torna allo scope precedente

    def visit_Costruttore(self, node: Costruttore):
        """Visita il costruttore di una classe, verificando parametri e corpo.

        Args:
            node (Costruttore): Il nodo del costruttore.
        """
        self.symbolTable.enterScope()  # Apre un nuovo scope locale dedicato al costruttore
        for par in node.parametri:  # Cicla su tutti i parametri accettati dal costruttore
            self.visit(par)  # Visita il parametro per registrarlo nello scope
            self.tipi_risolti[id(par.nome)] = str(par.tipo)  # Associa il tipo dichiarato al nome del parametro

        self.visit(node.corpo)  # Visita il blocco di codice contenuto nel corpo del costruttore
        self.symbolTable.printTable()  # Stampa di debug della SymbolTable per lo scope corrente
        self.symbolTable.exitScope()  # Chiude lo scope del costruttore

    # ══════════════════════════════════════════════════════════════
    #   LITERAL E TIPI PRIMITIVI
    # ══════════════════════════════════════════════════════════════

    def visit_Numr(self, node: Numr) -> str:
        """Risolve il tipo dei valori letterali numerici interi/float.

        Returns:
            str: Il tipo del linguaggio 'numr'.
        """
        return "numr"  # Restituisce il tipo identificativo per i numeri

    def visit_Boolean(self, node: Boolean) -> str:
        """Risolve il tipo dei valori letterali booleani.

        Returns:
            str: Il tipo del linguaggio 'lota'.
        """
        return "lota"  # Restituisce il tipo identificativo per i booleani

    def visit_Stringa(self, node: Stringa) -> str:
        """Risolve il tipo dei valori letterali testo/stringa.

        Returns:
            str: Il tipo del linguaggio 'nbruogglio'.
        """
        return "nbruogglio"  # Restituisce il tipo identificativo per le stringhe

    def visit_Carattr(self, node: Carattr) -> str:
        """Risolve il tipo dei valori letterali singolo carattere.

        Returns:
            str: Il tipo del linguaggio 'lettr'.
        """
        return "lettr"  # Restituisce il tipo identificativo per i singoli caratteri

    def visit_Variabile(self, node: Variabile):
        """Visita l'accesso a una variabile, ricavandone il tipo dalla SymbolTable.

        Gestisce anche l'accesso indicizzato a elementi di un array dinamico ('burdell').

        Args:
            node (Variabile): Il nodo dell'utilizzo variabile.

        Returns:
            str | None: Il tipo risolto della variabile o dell'elemento dell'array.
        """
        info = self.symbolTable.lookup(node.nome)  # Cerca le informazioni della variabile nella SymbolTable
        if info is None:  # Se la variabile non è presente nella SymbolTable
            riga = righe_nodi.get(id(node),
                                  "sconosciuta")  # Tenta di recuperare la riga del sorgente dal dizionario dei nodi
            self.errori.append(f"riga {riga}: variabile '{node.nome}' non dichiarata")  # Registra l'errore semantico
            return

        # Verifica se la variabile è stata dichiarata come array
        is_array = self.symbolTable.is_array(node.nome) if hasattr(self.symbolTable, 'is_array') else False

        # Lettura indicizzata di un array 'burdell' dinamico: risolvi il tipo REALE dell'elemento letto
        if is_array and getattr(node, 'index', -1) != -1:
            tipo_dichiarato = info['tipo'] if isinstance(info, dict) else info
            if tipo_dichiarato == "burdell":  # Se l'array è eterogeneo 'burdell'
                idx = self._indice_costante(node.index)  # Estrae il valore numerico dell'indice
                tipi_tracciati = self.array_elementi_tipi.get(node.nome, [])  # Recupera la sequenza di tipi inseriti
                if idx is not None and 0 <= idx < len(tipi_tracciati):
                    tipo_reale = tipi_tracciati[idx]  # Recupera il tipo specifico salvato a quell'indice
                    self.burdell_info[id(node)] = True  # Segna che la variabile origina da un tipo burdell
                    return tipo_reale
                else:
                    self.burdell_info[id(node)] = True  # Fallback a 'burdell' se l'indice non è tracciabile
                    return "burdell"

        if isinstance(info, dict):
            self.burdell_info[id(node)] = info.get('is_burdell', False)  # Memorizza se la variabile è dinamica
            return info.get('tipo', 'burdell')  # Restituisce il tipo corrente memorizzato
        self.burdell_info[id(node)] = False  # Non è dinamica
        return info  # Restituisce il tipo memorizzato direttamente

    def _indice_costante(self, indice):
        """Helper interno per estrarre il valore numerico intero da un espressione indice dell'AST.

        Args:
            indice: Valore o nodo AST rappresenta l'indice.

        Returns:
            int | None: L'intero Python o None se l'indice è un'espressione complessa non valutabile a compile-time.
        """
        if isinstance(indice, int):  # Se è già un intero nativo Python
            return indice
        if isinstance(indice, Numr):  # Se è un nodo AST letterale numerico
            try:
                return int(indice.value)
            except (TypeError, ValueError):
                return None
        if hasattr(indice, 'value'):  # Se ha un attributo value generico
            try:
                return int(indice.value)
            except (TypeError, ValueError):
                return None
        return None

    # ══════════════════════════════════════════════════════════════
    #   FUNZIONI E PARAMETRI
    # ══════════════════════════════════════════════════════════════

    def visit_Mestier(self, node: Mestier):
        """Visita la dichiarazione di una funzione ('Mestier').

        Inserisce la funzione nello scope corrente e ne crea uno nuovo per il corpo.
        Valida la presenza del `return` in caso di funzioni con valore di ritorno non nullo.

        Args:
            node (Mestier): Il nodo della funzione.
        """
        nome = node.nome.nome  # Nome della funzione
        info = self.symbolTable.lookup(nome)  # Cerca se era già presente o pendente nella SymbolTable

        if isinstance(info, dict) and info.get('pending'):  # Se la funzione era usata prima di essere dichiarata
            if getattr(self, 'classe_corrente', None) is None:  # Se non ci troviamo in una classe
                self.symbolTable.resolve_pending(nome, node)  # Risolve le chiamate pendenti precedentemente registrate
                self.symbolTable.addId(nome, node)  # Inserisce la funzione completa
        else:
            self.symbolTable.addId(nome, node)  # Registra la funzione nella SymbolTable

        self.symbolTable.enterScope()  # Apre il nuovo scope isolato per i parametri e il corpo
        self.funzione_corrente = node  # Imposta il contesto di funzione corrente per i controlli di return

        for kid in node.parametri:  # Visita tutti i parametri formali della funzione
            self.visit(kid)

        self.visit(node.corpo)  # Visita il blocco delle istruzioni del corpo della funzione

        # Se la funzione deve restituire un valore (!= 'vacant'), verifica che ci sia un return valido
        if node.ritorno != 'vacant' and not self._ha_return(node.corpo):
            self.errori.append(f"ERRORE: Funzione '{node.nome.nome}' deve avere un return di tipo '{node.ritorno}'")

        self.symbolTable.printTable()  # Stampa di debug della tabella simboli prima di uscire
        self.funzione_corrente = None  # Reset della funzione corrente
        self.symbolTable.exitScope()  # Chiude lo scope locale della funzione

    def visit_Parametro(self, node: Parametro):
        """Visita un parametro formale di una funzione registrandolo nello scope della funzione.

        Args:
            node (Parametro): Nodo del parametro.
        """
        nome_var = node.nome.nome  # Nome identificativo del parametro
        tipo_var = node.tipo.nome  # Tipo dichiarato per il parametro
        is_array = node.nome.is_array  # Identifica se il parametro è un array

        if self.symbolTable.probe(
                nome_var):  # Controlla se nello scope corrente esiste già un parametro con lo stesso nome
            self.errori.append(f"NNNNNNNNNNOOOOOOOOOOOOO ma che è fatt!!!!!: Parametro duplicato '{nome_var}'")
            return

        # Crea le informazioni dettagliate del parametro da registrare
        info_parametro = {
            'tipo': tipo_var,
            'is_array': is_array
        }
        self.symbolTable.addId(nome_var, info_parametro)  # Registra il parametro nella SymbolTable
        self.tipi_risolti[id(node.nome)] = tipo_var  # Associa il tipo risolto all'ID del nodo del nome
        self.burdell_info[id(node.nome)] = (tipo_var == 'burdell')  # Imposta se si tratta di un tipo burdell

    def visit_ReturnStatement(self, node: ReturnStatement):
        """Visita l'istruzione di ritorno (`return`) e verifica la compatibilità con il tipo restituito dalla funzione.

        Args:
            node (ReturnStatement): Nodo dell'istruzione di return.

        Returns:
            str: Il tipo di dato del valore restituito dall'istruzione.
        """
        # Visita l'espressione restituita per determinarne il tipo (se vuota restituisce 'vacant')
        tipo_valore = self.visit(node.valore) if node.valore is not None else "vacant"

        if self.funzione_corrente is not None:  # Se l'istruzione si trova all'interno di una funzione
            tipo_atteso = str(self.funzione_corrente.ritorno)  # Tipo di ritorno dichiarato nella firma della funzione

            # Verifica che il tipo dell'espressione sia compatibile con quello della funzione
            if not self._compatibili(tipo_atteso, tipo_valore):
                self.errori.append(f"ERRORE: Return di tipo '{tipo_valore}' ma la funzione "
                                   f"'{self.funzione_corrente.nome.nome}' ritorna '{tipo_atteso}'")

            # Verifica la corrispondenza delle dimensioni (array vs valore scalare)
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

    def _ha_return(self, block: Block) -> bool:
        """Helper ricorsivo per verificare la presenza di una chiamata `return` in un blocco di codice.

        Args:
            block (Block): Blocco di istruzioni da controllare.

        Returns:
            bool: True se trova un return valido nel blocco o in tutte le sue ramificazioni, False altrimenti.
        """
        for stmt in block.statements:  # Itera su ciascuna istruzione nel blocco
            if isinstance(stmt, ReturnStatement) and stmt.valore is not None:
                return True  # Trovato un return con valore presente direttamente

            # Ispeziona ricorsivamente i blocchi condizionali (if/else)
            if isinstance(stmt, Mettimmca):
                if self._ha_return(stmt.allora):
                    return True
                if stmt.altrimenti and self._ha_return(stmt.altrimenti):
                    return True
            # Ispeziona ricorsivamente i cicli while ('Aspe')
            if isinstance(stmt, Aspe):
                if self._ha_return(stmt.Corpo):
                    return True
            # Ispeziona ricorsivamente i cicli for ('Ambress_Ambress')
            if isinstance(stmt, Ambress_Ambress):
                if self._ha_return(stmt.Corpo):
                    return True
        return False  # Nessun return trovato nel percorso analizzato

    def visit_Block(self, node: Block):
        """Visita un blocco sequenziale di istruzioni.

        Args:
            node (Block): Nodo blocco contenente la lista degli statement.
        """
        for element in node.statements:  # Visita in sequenza ogni istruzione contenuta nel blocco
            self.visit(element)

    # ══════════════════════════════════════════════════════════════
    #   OGGETTI E CHIAMATE
    # ══════════════════════════════════════════════════════════════

    def visit_ChiamataCostruttore(self, node: ChiamataCostruttore):
        """Visita la creazione di un'istanza di classe, controllando argomenti e tipi del costruttore.

        Args:
            node (ChiamataCostruttore): Nodo della chiamata al costruttore.

        Returns:
            str | None: Il nome della classe istanziata in caso di successo.
        """
        nome_classe_attesa = self._tipo_atteso_costruttore  # Nome della classe ricavato dalla dichiarazione corrente

        classe = self.symbolTable.lookup(nome_classe_attesa)  # Cerca la definizione della classe nella SymbolTable
        if classe is None or not isinstance(classe, Robba):
            self.errori.append(f"'{nome_classe_attesa}' non è una classe valida")
            return

        parametri_attesi = classe.costruttore.parametri if classe.costruttore else []
        args = node.parametri or []

        # Controlla che il numero di parametri passati corrisponda al costruttore della classe
        if len(args) != len(parametri_attesi):
            self.errori.append(
                f"ERRORE: MMMMMMMMMMMMMMAAAAAAAAAAAAAAAA CCCHHHHEEE SSSTTTTTAAAAIIIII FFFFFACCCCCENEEEENNNN: il numero di argomenti pasati{args.__str__()} è diverso da quanto si aspetta il costruttore {parametri_attesi.__str__()}")
            return

        for arg in args:  # Visita gli argomenti forniti alla chiamata
            self.visit(arg)

        return nome_classe_attesa  # Restituisce il nome della classe come tipo dell'oggetto

    def visit_ChiamataOggetto(self, node: ChiamataOggetto):
        """Visita la chiamata ad un metodo appartenente a una classe (`oggetto.metodo(argomenti)`).

        Args:
            node (ChiamataOggetto): Nodo della chiamata di metodo su oggetto.

        Returns:
            str | None: Il tipo di ritorno del metodo invocato.
        """
        nome_var = node.nome.nome if hasattr(node.variabile, 'nome') else str(node.variabile)
        print(nome_var)
        tipo_var = self.symbolTable.lookup(nome_var)  # Cerca l'istanza dell'oggetto nello scope corrente
        print(tipo_var)
        tipo_nome = tipo_var['tipo'] if isinstance(tipo_var, dict) else tipo_var
        print(tipo_nome)

        if tipo_nome is None:
            self.errori.append(f"Variabile '{nome_var}' non dichiarata")
            return

        classe = self.symbolTable.lookup(tipo_nome)  # Recupera la definizione della classe dell'oggetto
        if not isinstance(classe, Robba):
            self.errori.append(f"'{nome_var}' non è un'istanza di una classe")
            return

        nome_metodo = node.variabile.nome if hasattr(node.nome, 'nome') else str(node.nome)
        # Cerca il metodo tra quelli definiti nella classe
        metodo = next((f for f in classe.funzioni if str(f.nome.nome) == nome_metodo), None)

        if metodo is None:
            self.errori.append(f"Metodo '{nome_metodo}' non esiste nella classe '{tipo_nome}'")
            return None

        args = node.Parametri or []
        # Verifica la quantità degli argomenti forniti
        if len(args) != len(metodo.parametri):
            self.errori.append(f"'{nome_metodo}' si aspetta {len(metodo.parametri)} argomenti, ricevuti {len(args)}")
            return None

        for arg in args:  # Analizza semanticamente ciascun argomento
            self.visit(arg)

        return str(metodo.ritorno)  # Restituisce il tipo di ritorno dichiarato per il metodo

    def visit_AccessoCampo(self, node: AccessoCampo):
        """Visita l'accesso diretto ad una proprietà/campo di una classe (`istanza.campo`).

        Args:
            node (AccessoCampo): Nodo di accesso al campo.

        Returns:
            str | None: Il tipo di dato del campo selezionato.
        """
        nome_var = node.variabile.nome
        tipo_var = self.symbolTable.lookup(nome_var)  # Cerca la variabile dell'oggetto nella SymbolTable
        tipo_nome = tipo_var['tipo'] if isinstance(tipo_var, dict) else tipo_var

        if tipo_nome is None:
            self.errori.append(f"Variabile '{nome_var}' non dichiarata")
            return

        classe = self.symbolTable.lookup(tipo_nome)  # Cerca la classe di appartenenza nella SymbolTable
        if not isinstance(classe, Robba):
            self.errori.append(f"'{nome_var}' non è un'istanza di una classe")
            return

        nome_campo = node.campo.nome
        # Cerca il campo tra le variabili membro della classe
        campo = next((v for v in classe.variabili if str(v.nome.nome) == nome_campo), None)

        if campo is None:
            self.errori.append(f"Campo '{nome_campo}' non esiste nella classe '{tipo_nome}'")

        self.tipi_risolti[id(node)] = campo.tipo.nome  # Associa il tipo del campo all'ID del nodo corrente
        return campo.tipo.nome  # Restituisce il tipo del campo

    def visit_CallStmt(self, node: CallStmt):
        """Visita l'invocazione di una funzione globale (`CallStmt`).

        Args:
            node (CallStmt): Nodo della chiamata a funzione.

        Returns:
            str: Il tipo restituito dalla funzione o 'sconosciuto' se la funzione è pendente.
        """
        nome_funzione = node.nome_func.nome
        funzione = self.symbolTable.lookup(nome_funzione)  # Cerca la funzione globale nella SymbolTable

        # Se la funzione non è ancora stata definita nel file, la segna come pendente
        if funzione is None or (isinstance(funzione, dict) and funzione.get('pending')):
            self.symbolTable.declare_pending(nome_funzione, None)
            for arg in node.args:
                self.visit(arg)  # Analizza comunque gli argomenti della chiamata
            return "sconosciuto"

        if not isinstance(funzione, Mestier):
            self.errori.append(f"'{nome_funzione}' non è una funzione")
            return

        # Controlla la corrispondenza del numero di argomenti
        if len(node.args) != len(funzione.parametri):
            self.errori.append(f"'{nome_funzione}' si aspetta {len(funzione.parametri)} argomenti, "
                               f"ricevuti {len(node.args)}"
                               )
            return

        for arg in node.args:  # Analizza ciascun argomento della chiamata
            self.visit(arg)

        return str(funzione.ritorno)  # Restituisce il tipo di ritorno della funzione

    # ══════════════════════════════════════════════════════════════
    #   ISTRUZIONI DI CONTROLLO DEL FLUSSO E CICLI
    # ══════════════════════════════════════════════════════════════

    def visit_Ambress_Ambress(self, node: Ambress_Ambress):
        """Visita il ciclo iterativo 'Ambress_Ambress' (`for`).

        Crea uno scope locale per l'inizializzazione dell'indice e incrementa il contatore del ciclo.

        Args:
            node (Ambress_Ambress): Nodo del ciclo for.
        """
        self.symbolTable.enterScope()  # Apre lo scope del ciclo
        if node.dichiarazione is not None:  # Analizza la dichiarazione dell'indice (es. `numr i = 0`)
            self.visit(node.dichiarazione)

        tipo_cond = self.visit(node.condizione)  # Valuta il tipo espresso nella condizione
        if tipo_cond != "lota":
            self.errori.append(
                f"BOTT_A_MUR: Ma ch stai facen!!!!! e mis '{tipo_cond}'! non puoi inserire una espressione che ha come risultato un valore diverso da boolean")
            return

        if node.VarOperation is not None:  # Analizza l'operazione di incremento del ciclo
            self.visit(node.VarOperation)

        self.dentro_ciclo += 1  # Incrementa il contatore per autorizzare l'uso del 'break'
        self.visit(node.Corpo)  # Visita le istruzioni del corpo del ciclo
        self.dentro_ciclo -= 1  # Ripristina il contatore del ciclo

        self.symbolTable.exitScope()  # Chiude lo scope del ciclo

    def visit_Aspe(self, node: Aspe):
        """Visita il ciclo 'Aspe' (`while`).

        Verifica che la condizione sia un valore booleano ('lota') o intero ('numr').

        Args:
            node (Aspe): Nodo del ciclo while.
        """
        tipo_cond = self.visit(node.Condizione)  # Valuta l'espressione condizionale
        if tipo_cond != "lota" and tipo_cond != "numr":
            self.errori.append(f"La condizione del while deve essere booleana, o numr trovato '{tipo_cond}'")
            return

        self.symbolTable.enterScope()  # Apre uno scope per le variabili locali del corpo
        self.dentro_ciclo += 1  # Segnala che siamo all'interno di un ciclo
        self.visit(node.Corpo)  # Visita il blocco di codice contenuto nel ciclo
        self.dentro_ciclo -= 1  # Ripristina lo stato fuori dal ciclo

        self.symbolTable.printTable()  # Stampa di debug
        self.symbolTable.exitScope()  # Chiude lo scope

    def visit_Mettimmca(self, node: Mettimmca):
        """Visita il blocco condizionale 'Mettimmca' (`if` / `else`).

        Args:
            node (Mettimmca): Nodo condizionale.
        """
        tipo_cond = self.visit(node.condizione)  # Valuta il tipo dell'espressione condizionale
        if tipo_cond != "lota":
            self.errori.append(f"La condizione dell'if deve essere booleana, trovato '{tipo_cond}'")
            return

        self.symbolTable.enterScope()  # Scope per il ramo 'if'
        self.visit(node.allora)  # Visita il corpo del ramo 'if'
        self.symbolTable.exitScope()

        if node.altrimenti is not None:  # Se è presente un ramo 'else'
            self.symbolTable.enterScope()  # Scope per il ramo 'else'
            self.visit(node.altrimenti)  # Visita il corpo del ramo 'else'
            self.symbolTable.exitScope()

    # ══════════════════════════════════════════════════════════════
    #   OPERAZIONI BINARIE ED ESPRESSIONI COMPLESSE
    # ══════════════════════════════════════════════════════════════

    def visit_OpBin(self, node: OpBin):
        """Visita un'operazione binaria o unaria, validando tipi, operatori e mutazioni dinamiche.

        Args:
            node (OpBin): Nodo dell'operazione binaria/unaria.

        Returns:
            str | None: Il tipo di dato calcolato dell'espressione.
        """
        # --- CASO 1: Operatore Unario Sx (manca l'operando sinistro, es. `not a` o `!!a`) ---
        if node.left is None:
            rv = self.visit(node.right)
            if node.op in ('not', '!!'):
                if rv != 'lota':
                    self.errori.append(f"NOO MA CHE E FATT :'{node.op}' è applicabile solo a un valore di tipo lota")
                    return
                return 'lota'
            return rv

        lv = self.visit(node.left)  # Visita l'operando sinistro

        # --- CASO 2: Operatore Unario Dx (manca l'operando destro, es. `i++` o `i--`) ---
        if node.right is None:
            if node.op in ('++', '--'):
                if lv != 'numr' and lv != 'burdell':
                    self.errori.append(f"NOO MA CHE E FATT : '{node.op}' applicabile solo a numr e burdell")
                    return
                return 'numr'

        rv = self.visit(node.right)  # Visita l'operando destro

        # --- CASO 3: Gestione dettagliata delle operazioni sugli ARRAY ---
        if isinstance(node.left, Variabile) and self.symbolTable.is_array(node.left.nome):
            nome_array = node.left.nome
            info_array = self.symbolTable.lookup(nome_array)
            tipo_array = info_array['tipo'] if isinstance(info_array, dict) else info_array
            is_dinamico = (tipo_array == "burdell")

            # Operazioni sull'INTERO ARRAY (senza notazione di indice, es. `arr -= elem`)
            if node.left.index == -1:
                if node.op not in ("-=", "+="):
                    self.errori.append(
                        f"NOO MA CHE E FATT: su un array puoi usare solo '-=' (inserisci) "
                        f"o '+=' (rimuovi), non '{node.op}'")
                    return tipo_array

                if is_dinamico:
                    if node.op == "-=":  # Aggiunta di un nuovo elemento
                        self.array_elementi_tipi.setdefault(nome_array, []).append(rv)
                    return "burdell"
                else:
                    if rv != tipo_array:
                        self.errori.append(
                            f"NOO MA CHE E FATT: impossibile inserire un valore di tipo "
                            f"'{rv}' in un array di '{tipo_array}'")
                    return tipo_array

            # Operazioni su un SINGOLO ELEMENTO dell'array mediante indice (es. `arr[0] = val`)
            else:
                if node.op not in ("=", "-", "+", "*", "/", "<->", "<", ">", "==", "!=", ">=", "<="):
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

        # Fallback secondario controlli array indicizzati
        if isinstance(node.left, Variabile) and self.symbolTable.is_array(node.left.nome) and node.left.index != -1:
            if node.op not in ("=", "-", "+", "<->", "<", ">"):
                self.errori.append(
                    f"ERRORE: NOO MA CHE E FATT : Con la notazione indice sull'array non puoi concatenare , hai usato '{node.op}'")
                return
            info_array = self.symbolTable.lookup(node.left.nome)
            tipo_array = info_array['tipo'] if isinstance(info_array, dict) else info_array
            tipo_valore = rv

            if tipo_array != "burdell" and tipo_array != tipo_valore:
                self.errori.append(
                    f"ERRORE: NOO MA CHE E FATT: Impossibile aggiungere/rimuovere un valore di tipo '{tipo_valore}' "
                    f"da un array di '{tipo_array}'")
                return
            return tipo_array

        # --- CASO 4: Gestione tipo dinamico 'BURDELL' ---
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

        # --- CASO 5: Tipi BOOLEANI ('lota') ---
        if lv == "lota" or rv == "lota":
            if self.control_Ope_Logici(node.op):
                if lv != "lota" or rv != "lota":
                    self.errori.append(
                        f"ERRORE: NOO MA CHE E FATT : L'operatore logico '{node.op}' richiede operandi booleani ('lota'), trovati '{lv}' e '{rv}'")
                return "lota"

            elif self.control_Ope_Confronto(node.op):
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
                self.errori.append(
                    f"ERRORE: NOO MA CHE E FATT : Operatore '{node.op}' non applicabile con il tipo lota")
                return "lota"

        # --- CASO 6: Tipi NUMERICI ('numr') ---
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

        # --- CASO 7: Tipi STRINGA E CARATTERI ('nbruogglio' / 'lettr') ---
        if lv == "nbruogglio" and rv == "nbruogglio":
            if node.op in ("+", "-=", "+="):
                return 'nbruogglio'
            if self.control_Ope_Confronto(node.op):
                return 'lota'

        if lv == "nbruogglio" and rv == "lettr":
            if node.op in ("+", "-=", "+="):
                return 'nbruogglio'
            if self.control_Ope_Confronto(node.op):
                return 'lota'

        if lv == "lettr" and rv == "nbruogglio":
            if node.op in ("+", "-=", "+="):
                return 'nbruogglio'
            if self.control_Ope_Confronto(node.op):
                return 'lota'

        # --- CASO 8: Concatenazione tra STRINGHE e NUMERI ---
        if lv == "nbruogglio" and rv == "numr":
            if node.op in ("+", "*=", "-="):
                return "nbruogglio"

        if lv == "numr" and rv == "nbruogglio":
            if node.op == '+':
                return 'nbruogglio'

            if node.op in ("+=", "-="):
                info_var = self.symbolTable.lookup(node.left.nome) if isinstance(node.left, Variabile) else None
                is_dinamica = isinstance(info_var, dict) and info_var.get('is_burdell')

                if isinstance(node.left, Variabile) and is_dinamica:
                    self.tipi_risolti[
                        id(node.left)] = lv  # Mantiene il tipo vecchio per l'accesso prima della riassegnazione
                    self.symbolTable.update(node.left.nome, {'tipo': "nbruogglio", 'is_burdell': True})
                    return "nbruogglio"
                self.errori.append(f"ERRORE: Impossibile fare '{node.op}' tra  {lv}' e  {rv}: "
                                   f"'{node.left.nome if isinstance(node.left, Variabile) else '?'}' "
                                   f"è numr fisso e non può cambiare tipo")

        # --- CASO 9: ASSEGNAMENTO SEMPLICE (`=`) ---
        if node.op == '=':
            if isinstance(node.left, Variabile):
                nome = node.left.nome
                info_var = self.symbolTable.lookup(nome)

                is_dinamica = isinstance(info_var, dict) and info_var.get('is_burdell')
                tipo_attuale = info_var['tipo'] if isinstance(info_var, dict) else info_var

                if is_dinamica:
                    if rv == "burdell":
                        self.errori.append(
                            f"ERRORE: NOO MA CHE E FATT: Impossibile assegnare un tipo 'burdell' a un'altra variabile 'burdell' ('{nome}')")
                        return "burdell"

                    self.symbolTable.update(nome, {'tipo': rv,
                                                   'is_burdell': True})  # Cambia il tipo contenuto mantenendola dinamica
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

        # --- CASO 10: SCAMBIO / SWAP (`<->`) ---
        if node.op == '<->':
            if not self._compatibili(lv, rv):
                self.errori.append(f"ERRORE: Swap non valido: '{lv}' vs '{rv}'")
            return lv

        self.errori.append(f"ERRORE: BOTT A MUR : Tipi incompatibili: '{lv}' e '{rv}' con operatore '{node.op}'")

    def visit_Dichiarazione(self, node: Dichiarazione):
        """Visita la dichiarazione di una nuova variabile o array.

        Verifica che non sia già stata dichiarata nello scope corrente e ne convalida il valore iniziale.

        Args:
            node (Dichiarazione): Nodo della dichiarazione.
        """
        tipo_dichiarato = node.tipo.nome  # Tipo di dato dichiarato
        nome_variabile = node.nome.nome  # Nome identificativo
        is_array = node.nome.is_array  # Identifica se è un array

        if self.symbolTable.probe(nome_variabile):  # Controlla ridichiarazioni nello scope corrente
            self.errori.append(f"ERRORE: Variabile '{nome_variabile}' già dichiarata")

        tipo_finale = tipo_dichiarato
        if is_array and tipo_dichiarato == 'burdell':
            self.array_elementi_tipi[nome_variabile] = []  # Inizializza il tracciamento dei tipi per l'array dinamico

        if node.valore is not None:
            if isinstance(node.valore, ChiamataCostruttore):
                self._tipo_atteso_costruttore = tipo_dichiarato  # Passa lo stato per la verifica del costruttore
                tipo_valore = self.visit(node.valore)
            else:
                tipo_valore = self.visit(node.valore)

            if tipo_dichiarato == 'burdell':
                if tipo_valore == 'burdell':
                    self.errori.append(
                        f"ERRORE: NOO MA CHE E FATT: Impossibile inizializzare la variabile burdell '{nome_variabile}' con un valore di tipo 'burdell'")
                    return

                # Registra la variabile come dinamica
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

        self.tipi_risolti[id(node.nome)] = tipo_finale  # Memorizza il tipo calcolato per la variabile
        self.burdell_info[id(node.nome)] = (tipo_dichiarato == 'burdell')

    # ══════════════════════════════════════════════════════════════
    #   INPUT / OUTPUT
    # ══════════════════════════════════════════════════════════════

    def visit_Arape_a_vocca(self, node: Arape_a_vocca):
        """Visita l'istruzione di stampa su schermo ('Arape_a_vocca').

        Args:
            node (Arape_a_vocca): Nodo dell'operazione di output.
        """
        variabili = node.variabili
        print(variabili)
        if node.valore is not None:
            self.tipi_risolti[id(node.valore)] = "nbruogglio"  # La stringa di formato fissa è 'nbruogglio'

        if variabili:
            for variabile in variabili:
                tipo_rilevato = self.visit(variabile)  # Identifica il tipo dell'espressione da stampare
                self.print_types[
                    id(variabile)] = tipo_rilevato  # Memorizza il tipo per permettere al Transpiler di usare la % corretta in C

    def visit_Ric(self, node: Ric):
        """Visita l'istruzione di lettura/input ('Ric').

        Args:
            node (Ric): Nodo dell'operazione di input.
        """
        variabili = node.variabile if isinstance(node.variabile, list) else [node.variabile]

        for v in variabili:
            tipo_rilevato = self.visit(v)  # Ricava il tipo della variabile in cui salvare l'input

            if not tipo_rilevato and hasattr(v, 'nome'):
                tipo_rilevato = self.symbolTable.lookup(str(v.nome))  # Fallback dalla SymbolTable

            self.print_types[id(v)] = tipo_rilevato  # Salva il tipo per la `scanf` del Transpiler

    # ══════════════════════════════════════════════════════════════
    #   HELPER PER OPERATORI E CONTROLLI
    # ══════════════════════════════════════════════════════════════

    def control_Ope_Logici(self, oper: str) -> bool:
        """Verifica se l'operatore fornito è un operatore strettamente logico.

        Args:
            oper (str): Simbolo dell'operatore.

        Returns:
            bool: True se logico, False altrimenti.
        """
        return oper in {"and", "or", "not", "!!"}

    def control_Ope_Confronto(self, oper: str) -> bool:
        """Verifica se l'operatore fornito è un operatore di confronto relazionale.

        Args:
            oper (str): Simbolo dell'operatore.

        Returns:
            bool: True se è un confronto, False altrimenti.
        """
        return oper in {"<=", "<", ">=", ">", "==", "!="}

    def control_Ope_Aritmetic(self, oper: str) -> bool:
        """Verifica se l'operatore fornito è un operatore aritmetico.

        Args:
            oper (str): Simbolo dell'operatore.

        Returns:
            bool: True se aritmetico, False altrimenti.
        """
        return oper in {"+", "-", "*", "/", "%"}

    def control_Ope_Assign(self, oper: str, tipe: str) -> bool:
        """Verifica se l'operatore di assegnamento è compatibile con il tipo di dato specificato.

        Args:
            oper (str): Operatore (es. `=`, `+=`).
            tipe (str): Nome del tipo di dato.

        Returns:
            bool: True se l'operazione di assegnamento è valida per quel tipo.
        """
        if tipe == "numr":
            return oper in {"=", "+=", "-=", "%=", "*=", "/="}
        elif tipe == "nbruogglio":
            return oper in {"=", "+="}
        elif tipe in ("lota", "lettr"):
            return oper == "="
        return False

    def visit_Break(self, node):
        """Visita l'istruzione di interruzione `break`, validando che sia posizionata dentro un ciclo.

        Args:
            node: Nodo dell'istruzione break.
        """
        if self.dentro_ciclo == 0:
            self.errori.append(
                "ERRORE: Errore Semantico: Uè! O' 'stut_tutt' s'adda ausà sulo rint' a nu ciclo (aspe o ambress_ambress)! TRADOTTO : il token break si deve usare solamente nei cicli")

    def _compatibili(self, tipo_atteso: str, tipo_trovato: str) -> bool:
        """Verifica la compatibilità dei tipi tra il tipo atteso e il tipo reale riscontrato.

        Args:
            tipo_atteso (str): Tipo richiesto dalla dichiarazione o firma.
            tipo_trovato (str): Tipo calcolato nell'analisi dell'espressione.

        Returns:
            bool: True se compatibili, False altrimenti.
        """
        if tipo_atteso == "sconosciuto" or tipo_trovato == "sconosciuto":
            return True
        if tipo_atteso == "burdell":  # Il tipo dinamico 'burdell' accetta qualsiasi assegnamento
            return True
        return tipo_atteso == tipo_trovato

    def getErrori(self) -> list:
        """Restituisce la lista di tutti gli errori semantici accumulati durante la visita dell'AST.

        Returns:
            list: Lista di messaggi di errore (stringhe).
        """
        return self.errori