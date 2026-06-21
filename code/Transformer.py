from dataclasses import dataclass

from typing import Any

@dataclass(frozen=True)
class Numr:
    value: float

@dataclass(frozen=True)
class OpBin:
    op: str
    left: object
    right: object

@dataclass(frozen=True)
class Boolean:
    value: bool

@dataclass(frozen=True)
class Stringa:
    value: str

@dataclass(frozen=True)
class Carattr:
    value: str
    def __post_init__(self):
        if len(self.value) != 1:
            raise ValueError("value deve contenere un solo carattere")

@dataclass(frozen=True)
class GenericVar:
    value: Any

@dataclass(frozen=True)
class Variabile:
    value : str

@dataclass(frozen=True)
class Dichiarazione :
    tipo: object
    op: OpBin


@dataclass(frozen=True)
class Mettimmca:
    op: OpBin
    allora: object
    altrimenti: object

@dataclass(frozen=True)
class Parametro:
        tipo: str
        nome: str
        is_array: bool = False

@dataclass(frozen=True)
class Mestier:
        nome: str
        parametri: list[Parametro]
        ritorno: object
        corpo : list[object]
        is_array: bool = False


@dataclass(frozen=True)
class Robba:
      nome: str
      variabili: list[object]
      funzioni: list[Mestier]

@dataclass(frozen=True)
class Aspe:
      Condizione: object
      Corpo: list[object]

@dataclass(frozen=True)
class Ambress_Ambress:
      Condizione: OpBin
      dichiarazione: Dichiarazione
      VarOp: object
      Corpo: list[object]

@dataclass(frozen=True)
class ReturnStatement:
      valor: object

