from tkinter import Variable

from Transformer import *

class AST_Transformer(Transformer):
    def numero (self,figli):
        token = figli[0]
        return Numr(value=float(token))

    def variabile (self,figli):
        token = figli[0]
        return Variabile(value=str(token))

    def stringa (self,figli):
        token =figli[0]
        return Stringa(value=token)

    def boolean (self,figli):
        token = figli[0]
        return Boolean(value=token)



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
