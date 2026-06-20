from tkinter import Variable

from Transformer import *

class AST_Transformer(Transformer):
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

    def dichiarazione(self, figli):
        if len(figli) == 5: # tipo nome_var ASSIGN valore TERMINATORE
            tipo = str(figli[0])
            nome = str(figli[1])
            valore = figli[3]
            return Dichiarazione(tipo, nome, valore)
        else:  # tipo nome_var TERMINATORE
            tipo = str(figli[0])
            nome = str(figli[1])
            return Dichiarazione(tipo, nome, None)
