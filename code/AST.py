from lark import Transformer

from Transformer import *

class AST_Transformer(Transformer):
    TOKEN_DA_SCARTARE = {
        'TONDASINISTRA', 'TONDADESTRA',
        'GRAFFASINISTRA', 'GRAFFADESTRA',
        'QUADRATADESTRA','QUADRATASINISTRA', 'METTIMCA', 'ALLORFAACCUSSI',
        'ROBA' , 'MESTIER', 'VIRGOLA', 'TERMINATORE', 'FRAVCATOR', 'ASSIGN', 'AMBRESS_AMBRESS', 'CHIAMATA',
        'PARAMETRI_TK'
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
        swap,left, right = self.filtra(figli)
        return OpBin(op=str(swap),left=left ,right=right)

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


    def sottrazione (self,figli):
        var1 = figli[0]
        operatore = self.filtra(figli)[1]
        var3 = self.filtra(figli)[2]
        return OpBin(op=operatore, left=var1, right=var3)

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
        return Variabile(nome=id_token, is_array=False)

    def variabile_array(self, figli):
        id_token = self.filtra(figli)[0]
        return Variabile(nome=id_token, is_array=True)

    def dichiarazione(self, figli):
        nodi = self.filtra(figli)
        tipo = str(nodi[0])
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

    def sezione_parametri(self, figli):
        return [f for f in figli if isinstance(f, Parametro)]

    def ritornaStatem(self,figli):
        valor = self.filtra(figli)
        return ReturnStatement(valor)

    def blocco(self, figli):
        return Block(statements=figli)

    def parametri(self, figli):
        type, value = self.filtra(figli)
        return Parametro(nome=type, value= value)

    def funzione_semplice(self, figli):
        tipo, nome, parametri, blocco = self.filtra(figli)
        return Mestier(tipo, nome,parametri,blocco,is_array=False)

    def funzione_array(self, figli):
        tipo, nome, parametri, blocco = self.filtra(figli)
        return Mestier(tipo, nome,parametri,blocco, is_array=True)

    def funzione_void(self, figli):
        tipo, nome, parametri, blocco = self.filtra(figli)
        return Mestier (tipo, nome,parametri,blocco)

    def costruttore(self, figli):
        parametri , corpo = self.filtra(figli)
        print("FIGLI COSTRUTTORE:")
        for i, f in enumerate(figli):
            print(f"  [{i}] {type(f).__name__} → {f!r}")
        return Costruttore(parametri, corpo)

    def robba(self , figli):
        nome , costruttore, variabili , funzioni = self.filtra(figli)
        return Robba(nome, costruttore, variabili, funzioni)

    def ambress_ambress(self,figli):
        declaration, condizione , varOp, corpo = self.filtra(figli)
        return Ambress_Ambress(declaration, condizione, varOp,corpo )

    def call_stmt(self, figli):
        nodi = self.filtra(figli)
        nomefunc = nodi[0]  # Variabile con il nome della funzione
        args = nodi[1:]  # lista di tutti gli argomenti dopo il nome
        return CallStmt(nome_func=nomefunc , args=args)

    def start(self, figli):
        """La regola 'start' ha un solo figlio: l'espressione intera."""
        return Start(program=figli)