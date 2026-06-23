from lark import Transformer

from Transformer import *

class AST_Transformer(Transformer):
    TOKEN_DA_SCARTARE = {
        'TONDASINISTRA', 'TONDADESTRA',
        'GRAFFASINISTRA', 'GRAFFADESTRA',
        'QUADRATADESTRA','QUADARATASINISTRA', 'METTIMCA', 'ALLORFAACCUSSI'
         ,'ROBA' , 'MESTIER', 'VIRGOLA', 'TERMINATORE',
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

    def swap_stmt(self, items):
        left, right = items
        return SwapStmt(left=str(left), right=str(right))

    def variabile_semplice(self, figli):
        id_token = self.filtra(figli)[0]
        return str(id_token), False

    def variabile_array(self, figli):
        id_token = self.filtra(figli)[0]
        return str(id_token), True

    #OPERAZIONI BINARIE
    def somma (self,figli):
        var1 = figli[0]
        operatore = figli[1]
        var3 = figli[2]
        return OpBin(operatore, var1, var3)

    def plusplus(self,figli):
        variabile = self.filtra(figli)[0]
        operatore = self.filtra(figli)[1]
        return OpBin(operatore, variabile,None)

    def menmen(self,figli):
        variabile = self.filtra(figli)[0]
        operatore = self.filtra(figli)[1]
        return OpBin(operatore,variabile,None)

    def uguale(self,figli):
        variabile1 = self.filtra(figli)[0]
        operatore = self.filtra(figli)[1]
        variabile2 = self.filtra(figli)[2]
        return OpBin(operatore,variabile1,variabile2)


    def sottrazione (self,figli):
        var1 = figli[0]
        operatore = self.filtra(figli)[1]
        var3 = self.filtra(figli)[2]
        return OpBin(operatore, var1, var3)

    def moltiplicazione(self, figli):
        var1 = self.filtra(figli)[0]
        operatore = self.filtra(figli)[1]
        var3 = self.filtra(figli)[2]
        return OpBin(operatore, var1, var3)

    def divisione(self, figli):
       var1,operatore, var3 = self.filtra(figli)
       return OpBin(operatore, var1, var3)


    def resto(self,figli):
        variabile1 = self.filtra(figli)[0]
        operatore = self.filtra(figli)[1]
        variabile2 = self.filtra(figli)[2]
        return OpBin(operatore,variabile1,variabile2)


    


    def dichiarazione(self, figli):
        if len(figli) == 5: # tipo nome_var ASSIGN valore TERMINATORE
            tipo = str(figli[0])
            nome = str(figli[1])
            assign = str(figli[2])
            valore = figli[3]
            opBin = OpBin(assign, tipo, valore)
            return Dichiarazione(tipo=tipo, op=opBin)
        else:  # tipo nome_var TERMINATORE
            tipo = str(figli[0])
            nome = str(figli[1])
            opBin = OpBin("", nome , None)
            return Dichiarazione(tipo, opBin)
    def parametri(self, figli):
        return list(figli)

    def aspe(self,figli):
        condition , corpo = self.filtra(figli)
        return Aspe(condition, corpo)

    def mettimca_completo(self,figli):
        print("FIGLI FILTRATI:", self.filtra(figli)) #debug
        op , allora , altrimenti = self.filtra(figli)
        return Mettimmca(op,allora,altrimenti)

    def mettimca_senzaElse(self,figli):
        op , allora ,altrimenti = self.filtra(figli)
        return Mettimmca(op,allora,altrimenti)


    def ritornaStatem(self,figli):
        valor = self.filtra(figli)
        return ReturnStatement(valor)

    def funzione_semplice(self, figli):
        tipo, nome, parametri, blocco = self.filtra(figli)
        return Mestier(tipo, nome,parametri,blocco,is_array=False)

    def funzione_array(self, figli):
        tipo, nome, parametri, blocco = self.filtra(figli)
        return Mestier(tipo, nome,parametri,blocco, is_array=True)

    def funzione_void(self, figli):
        tipo, nome, parametri, blocco = self.filtra(figli)
        return Mestier (tipo, nome,parametri,blocco)

    def robba(self , figli):
        nome , variabili , funzioni = self.filtra(figli)
        return Robba(nome, variabili, funzioni)

    def ambress_ambress(self,figli):
        tipo, corpo,dichiarazione ,operatore = self.filtra(figli)
        return Ambress_Ambress(tipo, dichiarazione, operatore,corpo )

    def start(self, figli):
        """La regola 'start' ha un solo figlio: l'espressione intera."""
        return figli[0]