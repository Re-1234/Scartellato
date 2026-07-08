from lark import Transformer

from Transformer import *

class AST_Transformer(Transformer):
    TOKEN_DA_SCARTARE = {
        'TONDASINISTRA', 'TONDADESTRA',
        'GRAFFASINISTRA', 'GRAFFADESTRA',
        'QUADRATADESTRA','QUADRATASINISTRA', 'METTIMCA', 'ALLORFAACCUSSI',
        'ROBA' , 'MESTIER', 'VIRGOLA', 'TERMINATORE', 'O_MAST', 'ASSIGN', 'AMBRESS_AMBRESS', 'CHIAMATA',
        'PARAMETRI_TK', 'CCASTA',  'SCCASCIA','ASPE'
    }



    def filtra(self, figli): #funzione per filtrare i token non necessari
        return [c for c in figli
                if not (hasattr(c, 'type') and c.type in self.TOKEN_DA_SCARTARE)]


    #RADICE DELL ALBERO
    def start(self,figli):
        return Start(program=figli)

    # TIPI PRIMITIVI
    def numero (self,figli):
        token = figli[0]
        return Numr(value=float(token))

    def stringa (self,figli):
        token =figli[0]
        return Stringa(value=str(token[2:-2]))

    def boolean (self,figli):
        token = figli[0]
        return Boolean(value=token)

    def carattere (self,figli):
        token = figli[0]
        return Carattr(value=str(token[1:-1]))
    def genType (self,figli):
        token = figli[0]
        return  GenericVar(value=token)

    def swap(self, figli):
        left,swap, right = self.filtra(figli)
        return OpBin(op=str(swap),left=left ,right=right)

    def tipo(self, figli):
        token = figli[0]  # Il token grezzo (es. Token('NUMR_TK', 'numr'))
        return TipoDato(
            nome=token.value,
            linea=token.line,
            colonna=token.column
        )

    #OPERAZIONI BINARIE
    def somma (self,figli):
        var1 = figli[0]
        operatore = figli[1]
        var2 = figli[2]
        return OpBin(op=str(operatore), left=var1, right=var2)

    def incremento_destro(self,figli):
        variabile = self.filtra(figli)[0]
        operatore = self.filtra(figli)[1]
        return OpBin(op=str(operatore), left=variabile, right=None)

    def menmen(self,figli):
        variabile = self.filtra(figli)[0]
        operatore = self.filtra(figli)[1]
        return OpBin(op=str(operatore), left=variabile, right=None)

    def minore(self, figli):
        return OpBin(op="<", left=figli[0], right=figli[2])

    def uguale(self,figli):
        variabile1 = self.filtra(figli)[0]
        operatore = self.filtra(figli)[1]
        variabile2 = self.filtra(figli)[2]
        print("FIGLI equals:")
        for i, f in enumerate(figli):
            print(f"  [{i}] {type(f).__name__} → {f!r}")
        return OpBin(op= str(operatore),left=variabile1,right=variabile2)

    def and_exp(self,figli):
         left , op1 , right = self.filtra(figli)
         return OpBin(op = str(op1),left = left,right = right)

    def or_exp(self,figli):
        left,op1,right = self.filtra(figli)
        return OpBin(op = str(op1),left = left,right = right)

    def sottrazione (self,figli):
        var1 = figli[0]
        operatore = self.filtra(figli)[1]
        var3 = self.filtra(figli)[2]
        return OpBin(op= str(operatore), left=var1, right=var3)

    def moltiplicazione(self, figli):
        var1 = self.filtra(figli)[0]
        operatore = self.filtra(figli)[1]
        var3 = self.filtra(figli)[2]
        return OpBin(op=operatore, left=var1, right=var3)

    def divisione(self, figli):
       var1,operatore, var3 = self.filtra(figli)
       return OpBin(op=operatore, left=var1, right=var3)


    def resto(self,figli):
        var1 = self.filtra(figli)[0]
        operatore = self.filtra(figli)[1]
        var3 = self.filtra(figli)[2]
        return OpBin(op=operatore, left=var1, right=var3)

    def variabile_semplice(self, figli):
        id_token = self.filtra(figli)[0]
        return Variabile(nome=str(id_token), is_array=False)

    def variabile_array(self, figli):
        id_token = self.filtra(figli)[0]
        return Variabile(nome=str(id_token), is_array=True)

    def dichiarazione(self, figli):
        nodi = self.filtra(figli)
        tipo = nodi[0]
        nome = nodi[1]
        valore = nodi[2] if len(nodi) > 2 else None
        return Dichiarazione(tipo=tipo, nome=nome, valore=valore)

    def assegnazione(self,figli):
        var1 = self.filtra(figli)[0]
        var2 = self.filtra(figli)[1]
        return OpBin(op='=', left=var1, right=var2)

    def aspe(self,figli):
        condition , corpo = self.filtra(figli)
        return Aspe(condition, corpo)

    def mettimca_completo(self,figli):
        print("METTIMCA figli:")
        for i, f in enumerate(figli):
            print(f"  [{i}] {type(f).__name__} → {f!r}")
        op, allora, altrimenti = self.filtra(figli)
        return Mettimmca(op,allora,altrimenti)

    def mettimca_senzaelse(self,figli):
        op , allora = self.filtra(figli)
        return Mettimmca(op,allora,altrimenti=None)


    def ritornaStatem(self,figli):
        valor = self.filtra(figli)
        return ReturnStatement(valor)

    def blocco(self, figli):
        return Block(statements=figli)

    def sezione_parametri(self, figli):
        return [f for f in figli if isinstance(f, Parametro)]

    def parametro(self, figli):
        tipo, value = self.filtra(figli)
        print("parametri figli:")
        for i, f in enumerate(figli):
            print(f"  [{i}] {type(f).__name__} → {f!r}")
        return Parametro(tipo=tipo, nome = value)

    def main(self, figli):
        nodi = self.filtra(figli)
        print("FIGLI MAIN_DEF")
        for i, f in enumerate(figli):
            print(f"  [{i}] {type(f).__name__} → {f!r}")
        ritorno,nome,corpo =nodi
        return Mestier(ritorno=str(ritorno), nome=Variabile(nome=str(nome), is_array=False),parametri="",corpo=corpo,is_array=False)


    def funzione_semplice(self, figli):
        tipo, nome, parametri, blocco = self.filtra(figli)
        return Mestier(ritorno=tipo.nome, nome=nome,parametri=parametri,corpo=blocco,is_array=False)

    def funzione_array(self, figli):

        tipo, nome, parametri, blocco = self.filtra(figli)
        print("FIGLI func array")
        for i, f in enumerate(figli):
            print(f"  [{i}] {type(f).__name__} → {f!r}")
        return Mestier(ritorno=tipo.nome, nome=nome,parametri=parametri,corpo=blocco, is_array=True)

    def funzione_void(self, figli):
        tipo, nome, parametri, blocco = self.filtra(figli)
        return Mestier (ritorno=str(tipo), nome=nome,parametri=parametri,corpo=blocco,is_array=False)

    def costruttore(self, figli):
        parametri , corpo = self.filtra(figli)
        print("FIGLI COSTRUTTORE:")
        for i, f in enumerate(figli):
            print(f"  [{i}] {type(f).__name__} → {f!r}")
        return Costruttore(parametri, corpo)

    def robba(self , figli):
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

        return Robba(nome=nome, costruttore=costruttore, variabili=variabili, funzioni=funzioni)

    def campi(self, figli):
        risultato = []
        for f in figli:
            tipo_nodo = type(f).__name__
            if tipo_nodo == "list":
                risultato.extend(f)
            else:
                risultato.append(f)
        return risultato


    def ambress_ambress(self,figli):
        declaration, condizione , varOp, corpo = self.filtra(figli)
        return Ambress_Ambress(declaration, condizione, varOp,corpo )

    def call_stmt(self, figli):
        nodi = self.filtra(figli)
        nomefunc = nodi[0]  # Variabile con il nome della funzione
        args = nodi[1:]  # lista di tutti gli argomenti dopo il nome
        return CallStmt(nome_func=nomefunc , args=args)

    def returnstatement(self, figli):
        nodi = self.filtra(figli)
        valore = nodi[0] if len(nodi) > 0 else None
        return ReturnStatement(valore)

    def start(self, figli):
        """La regola 'start' ha un solo figlio: l'espressione intera."""
        nodi = self.filtra(figli)
        print(" FIGLI START")
        for i, f in enumerate(figli):
            print(f"  [{i}] {type(f).__name__} → {f!r}")

        return Start(program=nodi)