

from Transformer import *

class AST_Transformer(Transformer):
    TOKEN_DA_SCARTARE = {
        'TONDASINISTRA', 'TONDADESTRA',
        'GRAFFASINISTRA', 'GRAFFADESTRA',
         'VIRGOLA', 'ASSIGN', 'TERMINATORE',
     }



    def filtra(self, children): #funzione per filtrare i token non necessari
        return [c for c in children
                if not (hasattr(c, 'type') and c.type in self.TOKEN_DA_SCARTARE)]


    # TIPI PRIMITIVI
    def numero (self,figli):
        token = figli[0]
        return Numr(value=float(token))

    def variabile (self,figli):
        token = figli[0]
        return Variabile(value=str(token))

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


    def nome_semplice(self, children):
        id_token = self.filtra(children)[0]
        return str(id_token), False

    def nome_array(self, children):
        id_token = self.filtra(children)[0]
        return str(id_token), True

    #OPERAZIONI BINARIE
    def somma (self,figli):
        var1 = figli[0]
        operatore = figli[1]
        var3 = figli[2]
        return OpBin(operatore, var1, var3)


    def sottrazione (self,figli):
        var1 = figli[0]
        operatore = figli[1]
        var3 = figli[2]
        return OpBin(operatore, var1, var3)

    def moltiplicazione(self, figli):
        var1 = figli[0]
        operatore = figli[1]
        var3 = figli[2]
        return OpBin(operatore, var1, var3)

    def divisione(self, figli):
        var1 = figli[0]
        operatore = figli[1]
        var3 = figli[2]
        return OpBin(operatore, var1, var3)


    def dichiarazione(self, figli):
        if len(figli) == 5: # tipo nome_var ASSIGN valore TERMINATORE
            tipo = str(figli[0])
            nome = str(figli[1])
            valore = figli[3]
            return Dichiarazione(tipo=tipo, nome=nome, valore=valore)
        else:  # tipo nome_var TERMINATORE
            tipo = str(figli[0])
            nome = str(figli[1])
            return Dichiarazione(tipo, nome=nome, valore=None)

    def parametri(self, children):
        return list(children)

    def funzione_semplice(self, children):
        tipo, nome, parametri, blocco = self.filtra(children)
        return Mestier(tipo, nome,parametri,blocco,is_array=False)

    def funzione_array(self, children):
        tipo, nome, parametri, blocco = self.filtra(children)
        return Mestier(tipo, nome,parametri,blocco, is_array=True)

    def funzione_void(self, children):
        tipo, nome, parametri, blocco = self.filtra(children)
        return Mestier (tipo, nome,parametri,blocco)