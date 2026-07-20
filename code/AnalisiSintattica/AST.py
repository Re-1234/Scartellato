from dataclasses import is_dataclass, fields

from lark import Transformer, Token, Tree, v_args
from code.AnalisiSintattica.Transformer import *

righe_nodi: dict[int, int] = {}

class AST_Transformer(Transformer):
    TOKEN_DA_SCARTARE = {
        'TONDASINISTRA', 'TONDADESTRA',
        'GRAFFASINISTRA', 'GRAFFADESTRA',
        'QUADRATADESTRA','QUADRATASINISTRA', 'METTIMCA', 'ALLORFAACCUSSI',
        'ROBA' , 'MESTIER', 'VIRGOLA', 'TERMINATORE', 'O_MAST', 'ASSIGN', 'AMBRESS_AMBRESS', 'CHIAMATA',
        'PARAMETRI_TK', 'CCASTA',  'SCCASCIA','ASPE','PRINT'
    }



    def filtra(self, figli): #funzione per filtrare i token non necessari
        return [c for c in figli
                if not (hasattr(c, 'type') and c.type in self.TOKEN_DA_SCARTARE)]




    # TIPI PRIMITIVI
    @v_args(meta=True)
    def numero (self,figli,meta):
        token = figli[0]
        nodo =Numr(value=float(token))
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def stringa (self,figli,meta):
        token =figli[0]
        nodo=Stringa(value=str(token[2:-2]))
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def boolean (self,figli,meta):
        token = figli[0]
        nodo=Boolean(value=token)
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def carattere (self,figli,meta):
        token = figli[0]
        nodo=Carattr(value=str(token[1:-1]))
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def swap(self, figli,meta):
        left,swap, right = self.filtra(figli)
        nodo=OpBin(op=str(swap),left=left ,right=right)
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def tipo(self, figli,meta):
        token = figli[0]  # Il token grezzo (es. Token('NUMR_TK', 'numr'))
        nodo = TipoDato(nome=token.value,linea=token.line,colonna=token.column)
        righe_nodi[id(nodo)] = meta.line
        return nodo

    #OPERAZIONI BINARIE
    @v_args(meta=True)
    def somma (self,figli,meta):
        var1 = figli[0]
        operatore = figli[1]
        var2 = figli[2]
        nodo=OpBin(op=str(operatore), left=var1, right=var2)
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def negato (self ,figli,meta):
        operatore = self.filtra(figli)[0]
        variabile = self.filtra(figli)[1]
        nodo = OpBin(op = str(operatore),left = None,right = variabile)
        righe_nodi[id(nodo)] = meta.line
        return nodo
    
    
    @v_args(meta=True)
    def incremento_destro(self,figli,meta):
        variabile = self.filtra(figli)[0]
        operatore = self.filtra(figli)[1]
        nodo=OpBin(op=str(operatore), left=variabile, right=None)
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def incremento_sinistro(self, figli,meta):
        operatore  = self.filtra(figli)[0]
        variabile= self.filtra(figli)[1]
        nodo=OpBin(op=str(operatore), left=variabile, right=None)
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def decremento_destro(self, figli,meta):
        variabile = self.filtra(figli)[0]
        operatore = self.filtra(figli)[1]
        nodo=OpBin(op=str(operatore), left=variabile, right=None)
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def decremento_sinistro(self, figli,meta):
        operatore = self.filtra(figli)[0]
        variabile= self.filtra(figli)[1]
        nodo=OpBin(op=str(operatore), left=variabile, right=None)
        righe_nodi[id(nodo)] = meta.line
        return nodo


    @v_args(meta=True)
    def maggiore(self,figli,meta):
        print("maggiore figli:")
        for i, f in enumerate(figli):
            print(f"  [{i}] {type(f).__name__} → {f!r}")
        nodo= OpBin(op=">", left=figli[0], right=figli[2])
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def maggioreuguale(self,figli,meta):
        nodo =OpBin(op=">=", left=figli[0], right=figli[2])
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def minore(self, figli,meta):
        nodo = OpBin(op="<", left=figli[0], right=figli[2])
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def minoreuguale(self, figli,meta):
        nodo= OpBin(op="<=", left=figli[0], right=figli[2])
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def uguale(self,figli,meta):
        variabile1 = self.filtra(figli)[0]
        operatore = self.filtra(figli)[1]
        variabile2 = self.filtra(figli)[2]
        print("FIGLI equals:")
        for i, f in enumerate(figli):
            print(f"  [{i}] {type(f).__name__} → {f!r}")

        nodo=OpBin(op= str(operatore),left=variabile1,right=variabile2)
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def addizioneuguale(self,figli,meta):
        left , op1 , right = self.filtra(figli)
        nodo=OpBin(op = str(op1),left = left , right = right)
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def menouguale(self,figli,meta):
        left , op1 , right = self.filtra(figli)
        nodo=OpBin(op = str(op1),left = left , right = right)
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def diverso(self,figli,meta):
        left , op1 , right = self.filtra(figli)
        nodo = OpBin(op = str(op1),left = left , right = right)
        righe_nodi[id(nodo)] = meta.line
        return nodo


    @v_args(meta=True)
    def divisioneuguale(self, figli,meta):
        left, op1, right = self.filtra(figli)
        nodo=OpBin(op=str(op1), left=left, right=right)
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def moltiplicauguale(self,figli,meta):
        left, op1, right = self.filtra(figli)
        nodo =OpBin(op=str(op1), left=left, right=right)
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def decremento_uguale(self, figli,meta):
        left, op1, right = self.filtra(figli)
        nodo=OpBin(op=str(op1), left=left, right=right)
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def incremento_uguale(self,figli,meta):
        left, op1, right = self.filtra(figli)
        nodo= OpBin(op=str(op1), left=left, right=right)
        righe_nodi[id(nodo)] = meta.line
        return nodo


    @v_args(meta=True)
    def and_exp(self,figli,meta):
         left , op1 , right = self.filtra(figli)
         nodo=OpBin(op = str(op1),left = left , right = right)
         righe_nodi[id(nodo)] = meta.line
         return nodo

    @v_args(meta=True)
    def or_exp(self,figli,meta):
        left,op1,right = self.filtra(figli)
        nodo=OpBin(op = str(op1),left = left , right = right)
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def sottrazione (self,figli,meta):
        var1 = figli[0]
        operatore = self.filtra(figli)[1]
        var3 = self.filtra(figli)[2]
        nodo=OpBin(op = str(operatore),left = var1, right = var3)
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def moltiplicazione(self, figli,meta):
        var1 = self.filtra(figli)[0]
        operatore = self.filtra(figli)[1]
        var3 = self.filtra(figli)[2]
        nodo=OpBin(op=str(operatore), left=var1, right=var3)
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def divisione(self, figli,meta):
       var1,operatore, var3 = self.filtra(figli)
       nodo=OpBin(op=str(operatore), left = var1, right = var3)
       righe_nodi[id(nodo)] = meta.line
       return nodo

    @v_args(meta=True)
    def resto(self,figli,meta):
        var1 = self.filtra(figli)[0]
        operatore = self.filtra(figli)[1]
        var3 = self.filtra(figli)[2]
        nodo = OpBin(op = str(operatore), left = var1, right = var3)
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def variabile_semplice(self, figli,meta):
        id_token = self.filtra(figli)[0]
        nodo= Variabile(nome=str(id_token), index=-1, is_array=False)
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def variabile_array(self, figli,meta):
        nodi = self.filtra(figli)
        if len(nodi) == 2:
            id_token,index_tok  = nodi  # [NUMERO, ID]
            nodo=Variabile(nome=str(id_token), index=int(index_tok), is_array=True)
            righe_nodi[id(nodo)] = meta.line
            return nodo
        else:
            id_token = nodi[0]  # solo [ID], array senza dimensione
            nodo= Variabile(nome=str(id_token), index=-1, is_array=True)
            righe_nodi[id(nodo)] = meta.line
            return nodo

    @v_args(meta=True)
    def dichiarazione(self, figli,meta):
        nodi = self.filtra(figli)
        tipo = nodi[0]
        nome = nodi[1]
        valore = nodi[2] if len(nodi) > 2 else None
        nodo =Dichiarazione(tipo=tipo, nome=nome, valore=valore)
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def assegnazione(self,figli,meta):
        var1 = self.filtra(figli)[0]
        var2 = self.filtra(figli)[1]
        nodo=OpBin(op='=', left=var1, right=var2)
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def aspe(self,figli,meta):
        condition , corpo = self.filtra(figli)
        nodo=Aspe(condition, corpo)
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def mettimca_completo(self,figli,meta):
        print("METTIMCA completo figli:")
        for i, f in enumerate(figli):
            print(f"  [{i}] {type(f).__name__} → {f!r}")
        op, allora, altrimenti = self.filtra(figli)
        nodo=Mettimmca(op,allora,altrimenti)
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def mettimca_senzaelse(self,figli,meta):
        print("METTIMCA no else figli:")
        for i, f in enumerate(figli):
            print(f"  [{i}] {type(f).__name__} → {f!r}")
        op , allora = self.filtra(figli)
        nodo= Mettimmca(op,allora,altrimenti=None)
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def ritornaStatem(self,figli,meta):
        valor = self.filtra(figli)
        nodo= ReturnStatement(valor)
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def blocco(self, figli,meta):
        nodo= Block(statements=figli)
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def sezione_parametri(self, figli,meta):
        nodo=[f for f in figli if isinstance(f, Parametro)]
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def parametro(self, figli,meta):
        tipo, value = self.filtra(figli)
        print("parametri figli:")
        for i, f in enumerate(figli):
            print(f"  [{i}] {type(f).__name__} → {f!r}")
        nodo=Parametro(tipo=tipo, nome = value)
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def main(self, figli,meta):

        nodi = self.filtra(figli)
        print("FIGLI MAIN_DEF", flush=True)
        for i, f in enumerate(figli) :
            print(f"  [{i}] {type(f).__name__} → {f!r}", flush=True)

        if len(nodi) == 2:
            nome,corpo =nodi
            ritorno= "vacant"
            nodo= Mestier(ritorno=str(ritorno), nome=Variabile(nome=str(nome),index = -1,is_array=False),parametri=[],corpo=corpo,is_array=False)
            righe_nodi[id(nodo)] = meta.line
            return  nodo
        elif len(nodi) == 3:
            ritorno, nome, corpo = nodi
            nodo=Mestier(ritorno=str(ritorno), nome=Variabile(nome=str(nome),index = -1,is_array=False),parametri=[],corpo=corpo,is_array=False)
            righe_nodi[id(nodo)] = meta.line
            return  nodo

    @v_args(meta=True)
    def funzione_semplice(self, figli,meta):
        tipo, nome, parametri, blocco = self.filtra(figli)
        if parametri is None:
            lista = []
        elif isinstance(parametri, list):
            # Se è già una lista (es. [P1, P2]), la teniamo così com'è!
            lista = parametri
        else:
            lista = [parametri]
        nodo =Mestier(ritorno=tipo.nome, nome=nome,parametri=lista,corpo=blocco,is_array=False)
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def funzione_array(self, figli,meta):

        tipo, nome, parametri, blocco = self.filtra(figli)
        print("FIGLI func array")
        for i, f in enumerate(figli):
            print(f"  [{i}] {type(f).__name__} → {f!r}")
        if parametri is None:
            lista = []
        elif isinstance(parametri, list):
            # Se è già una lista (es. [P1, P2]), la teniamo così com'è!
            lista = parametri
        else:
            lista = [parametri]
        nodo=Mestier(ritorno=tipo.nome, nome=nome,parametri=lista,corpo=blocco, is_array=True)
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def funzione_void(self, figli,meta):
        tipo, nome, parametri, blocco = self.filtra(figli)
        if parametri is None:
            lista = []
        elif isinstance(parametri, list):
            # Se è già una lista (es. [P1, P2]), la teniamo così com'è!
            lista = parametri
        else:
            lista = [parametri]
        nodo=Mestier (ritorno=str(tipo), nome=nome,parametri=lista,corpo=blocco,is_array=False)
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def costruttore(self, figli,meta):
        parametri , corpo = self.filtra(figli)
        print("FIGLI COSTRUTTORE:")
        for i, f in enumerate(figli):
            print(f"  [{i}] {type(f).__name__} → {f!r}")
        if parametri is None:
            lista = []
        elif isinstance(parametri, list):
            # Se è già una lista (es. [P1, P2]), la teniamo così com'è!
            lista = parametri
        else:
            lista = [parametri]
        nodo=Costruttore(parametri=lista, corpo=corpo)
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def robba(self , figli,meta):
        nodi= self.filtra(figli)

        print("CLASSE FIGLI")
        for i, f in enumerate(figli):
            print(f"  [{i}] {type(f).__name__} → {f!r}")

        nome =nodi[0]
        costruttore = None
        variabili = []
        funzioni = []

        for nodo in nodi[1:]:
            tipo_nodo = type(nodo).__name__   #uso reflection per vedere il tipo del nodo

            if tipo_nodo == "Costruttore":
                costruttore = nodo
            elif tipo_nodo == 'Dichiarazione':
                variabili.append(nodo)
            elif tipo_nodo == 'Mestier':
                funzioni.append(nodo)
            elif tipo_nodo == "list":
                variabili.extend(nodo)

        nodo=Robba(nome=nome, costruttore=costruttore, variabili=variabili, funzioni=funzioni)
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def campi(self, figli,meta):
        risultato = []
        for f in figli:
            tipo_nodo = type(f).__name__
            if tipo_nodo == "list":
                risultato.extend(f)
            else:
                risultato.append(f)
        nodo=risultato
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def ambress_ambress(self,figli,meta):
        declaration, condizione , varOp, corpo = self.filtra(figli)
        nodo=Ambress_Ambress(declaration, condizione, varOp,corpo )
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def call_stmt(self, figli,meta):
        nodi = self.filtra(figli)
        nomefunc = nodi[0]  # Variabile con il nome della funzione
        args = nodi[1:]  # lista di tutti gli argomenti dopo il nome
        nodo=CallStmt(nome_func=nomefunc , args=args)
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def returnstatement(self, figli,meta):
        nodi = self.filtra(figli)
        valore = nodi[0] if len(nodi) > 0 else None
        nodo=ReturnStatement(valore)
        righe_nodi[id(nodo)] = meta.line
        return nodo

    def break_statement(self, figli):
        return Break()

    @v_args(meta=True)
    def chiamata_oggetto(self,figli,meta):

        print("CHIAMATA oggetto figli:")
        for i, f in enumerate(figli):
            print(f"  [{i}] {type(f).__name__} → {f!r}")
        nodi = self.filtra(figli)
        nome = nodi[0]
        variabili = nodi[1]
        parametri1 = nodi[2:] if len(nodi) > 2 else None
        nodo=  ChiamataOggetto(nome = nome , variabile = variabili , Parametri = parametri1)
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def chiamata_costruttore(self,figli,meta):

        print("CHIAMATA COSTRUTTORE figli:")
        for i, f in enumerate(figli):
            print(f"  [{i}] {type(f).__name__} → {f!r}")
        nodi = self.filtra(figli)
        nomevar =nodi[0]
        parametri = nodi[1:] if len(nodi) > 2 else None
        nodo=ChiamataCostruttore(nome=nomevar,parametri=parametri)
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def accesso_campo(self,figli,meta):
        variabile,campo = self.filtra(figli)
        nodo=AccessoCampo(variabile=variabile, campo=campo)
        righe_nodi[id(nodo)] = meta.line
        return nodo

    # RADICE DELL ALBERO
    @v_args(meta=True)
    def start(self, figli,meta):
        """La regola 'start' ha un solo figlio: l'espressione intera."""
        nodi = self.filtra(figli)
        print(" FIGLI START")
        for i, f in enumerate(figli):
            print(f"  [{i}] {type(f).__name__} → {f!r}")
        nodo=Start(program=nodi)
        righe_nodi[id(nodo)] = meta.line
        return nodo

    @v_args(meta=True)
    def stampante(self, figli,meta):
        print(" FIGLI stampa ")
        for i, f in enumerate(figli):
            print(f"  [{i}] {type(f).__name__} → {f!r}")

        elementi = self.filtra(figli)

        elementi_puliti = [
            f for f in elementi
            if getattr(f, 'type', None) != 'ADDIZIONE' and str(f) != '-'
        ]

        # 3. Estrai i dati dalla lista pulita locale
        valore1 = str(elementi_puliti[0])
        variabili1 = elementi_puliti[1:]
        nodo=Arape_a_vocca(valore = valore1,variabili = variabili1)
        righe_nodi[id(nodo)] = meta.line
        return nodo




def stampa_ast(nodo, prefisso="", e_ultimo=True, e_radice=True):
    if e_radice:
        ramo = ""
        ext  = ""
    else:
        ramo = "└─ " if e_ultimo else "├─ "
        ext  = "   " if e_ultimo else "│  "

    # Token grezzo — ignora
    if isinstance(nodo, Token):
        return

    # Tree non trasformato
    if isinstance(nodo, Tree):
        print(f"{prefisso}{ramo}[Tree non trasformato: {nodo.data}]")
        return

    # None
    if nodo is None:
        print(f"{prefisso}{ramo}None")
        return

    # Primitivi
    if isinstance(nodo, (int, float, str, bool)):
        print(f"{prefisso}{ramo}{repr(nodo)}")
        return

    # Lista
    if isinstance(nodo, list):
        if not nodo:
            print(f"{prefisso}{ramo}[]")
            return
        print(f"{prefisso}{ramo}[lista]")
        for i, el in enumerate(nodo):
            stampa_ast(el, prefisso + ext, i == len(nodo) - 1, False)
        return

    # Dataclass — caso generale
    if is_dataclass(nodo):
        # etichetta compatta per i nodi foglia (un solo campo primitivo)
        campi = fields(nodo)

        # nodi con rappresentazione inline
        if isinstance(nodo, Numr):
            print(f"{prefisso}{ramo}Numr({nodo.value})")
            return
        if isinstance(nodo, Boolean):
            print(f"{prefisso}{ramo}Boolean({nodo.value})")
            return
        if isinstance(nodo, Stringa):
            print(f"{prefisso}{ramo}Stringa({repr(nodo.value)})")
            return
        if isinstance(nodo, Carattr):
            print(f"{prefisso}{ramo}Carattr({repr(nodo.value)})")
            return

        if isinstance(nodo, Variabile):
            arr = "[]" if nodo.is_array else ""
            print(f"{prefisso}{ramo}Variabile({arr}{repr(str(nodo.nome))})")
            return

        # nodi composti — stampa nome classe poi ogni campo
        print(f"{prefisso}{ramo}{type(nodo).__name__}")
        for i, campo in enumerate(campi):
            valore = getattr(nodo, campo.name)
            ultimo_campo = i == len(campi) - 1
            ramo_c = "└─ " if ultimo_campo else "├─ "
            ext_c  = "   " if ultimo_campo else "│  "
            print(f"{prefisso}{ext}{ramo_c}{campo.name}:")
            stampa_ast(
                valore,
                prefisso + ext + ext_c,
                True,
                False
            )
        return

    # Fallback
    print(f"{prefisso}{ramo}??? {type(nodo).__name__}  {nodo!r}")